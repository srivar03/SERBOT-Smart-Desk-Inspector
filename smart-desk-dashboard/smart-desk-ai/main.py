import cv2
import sqlite3
import os
import requests

from ultralytics import YOLO
from datetime import datetime

from decision_engine import DecisionEngine
from light_detector import LightDetector
from fan_detector import FanDetector


# =========================================================
# CONFIGURATION
# =========================================================

FLASK_URL = "http://127.0.0.1:5000/api/update"

DB_PATH = "../events.db"

PHOTO_FOLDER = "../static/photos"

ALLOWED_CLASSES = {
    "laptop",
    "book",
    "cell phone",
    "backpack",
    "handbag",
    "suitcase",
    "person",
    "bottle"
}

PRODUCTION_CONFIDENCE = 0.35

FAN_ROI = (0, 150, 200, 450)

MISS_TOLERANCE = 10

STARTUP_GRACE_FRAMES = 30


# =========================================================
# CREATE PHOTO FOLDER
# =========================================================

os.makedirs(
    PHOTO_FOLDER,
    exist_ok=True
)


# =========================================================
# YOLO
# =========================================================

model = YOLO(
    "yolov8s.pt"
)


# =========================================================
# CAMERA
# =========================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("ERROR: Camera could not be opened.")

    exit()


# =========================================================
# QR DETECTOR
# =========================================================

qr_detector = cv2.QRCodeDetector()


# =========================================================
# DECISION ENGINE
# =========================================================

engine = DecisionEngine(
    confirm_frames=5,
    min_confidence=PRODUCTION_CONFIDENCE,
    cooldown_seconds=600
)


# =========================================================
# LIGHT DETECTOR
# =========================================================

light_detector = LightDetector()


# =========================================================
# FAN DETECTOR
# =========================================================

fan_detector = FanDetector(
    fan_roi=FAN_ROI
)


# =========================================================
# VARIABLES
# =========================================================

current_location = None

missed_qr_frames = 0

frame_count = 0


activity = [
    "🤖 SERBOT started",
    "📷 Camera connected"
]


# =========================================================
# DATABASE
# =========================================================

def setup_database():

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_or_status TEXT,
            location TEXT,
            timestamp TEXT,
            photo_path TEXT
        )
        """
    )

    conn.commit()

    conn.close()


def log_event(
    object_or_status,
    location,
    timestamp,
    photo_path
):

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.execute(
        """
        INSERT INTO events
        (
            object_or_status,
            location,
            timestamp,
            photo_path
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            object_or_status,
            location,
            timestamp,
            photo_path
        )
    )

    conn.commit()

    conn.close()


# =========================================================
# SEND DATA TO FLASK
# =========================================================

def send_to_flask(data):

    try:

        response = requests.post(
            FLASK_URL,
            json=data,
            timeout=0.3
        )

        return response.ok

    except requests.exceptions.RequestException:

        return False


# =========================================================
# ACTIVITY
# =========================================================

def add_activity(message):

    activity.insert(
        0,
        message
    )

    del activity[8:]


# =========================================================
# DATABASE SETUP
# =========================================================

setup_database()


print()
print("========================================")
print(" SMART DESK INSPECTOR")
print("========================================")
print("YOLO        : READY")
print("Camera      : READY")
print("QR Detector : READY")
print("Light       : READY")
print("Fan         : READY")
print("Flask       : CONNECTING")
print()
print("Press Q to quit.")
print("========================================")
print()


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    ret, frame = cap.read()

    if not ret:

        print(
            "ERROR: Could not read camera."
        )

        break


    frame_count += 1


    # =====================================================
    # GRAYSCALE
    # =====================================================

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )


    # =====================================================
    # 1. QR LOCATION
    # =====================================================

    qr_found, points, _ = \
        qr_detector.detectAndDecode(frame)


    if qr_found:

        missed_qr_frames = 0

        if qr_found != current_location:

            print(
                f"[LOCATION] Entered: {qr_found}"
            )

            current_location = qr_found

            add_activity(
                f"📍 Location: {qr_found}"
            )


    else:

        missed_qr_frames += 1

        if (
            current_location is not None
            and
            missed_qr_frames >= MISS_TOLERANCE
        ):

            print(
                f"[LOCATION] Left: {current_location}"
            )

            add_activity(
                f"📍 Left {current_location}"
            )

            current_location = None


    # =====================================================
    # 2. LIGHT DETECTION
    # =====================================================

    light_state, fixture_b, background_b, margin = \
        light_detector.update(gray)


    # =====================================================
    # 3. FAN DETECTION
    # =====================================================

    fan_state, fan_motion = \
        fan_detector.update(gray)


    # =====================================================
    # PRINT SENSOR DATA
    # =====================================================

    if frame_count % 30 == 0:

        print(
            f"[LIGHT] "
            f"Fixture={fixture_b:.1f} "
            f"Background={background_b:.1f} "
            f"Margin={margin:.1f} "
            f"Status={light_state}"
        )

        print(
            f"[FAN] "
            f"Motion={fan_motion:.2f} "
            f"Status={fan_state}"
        )


    # =====================================================
    # 4. YOLO
    # =====================================================

    results = model(
        frame,
        verbose=False,
        conf=PRODUCTION_CONFIDENCE
    )


    detections = []


    for box in results[0].boxes:

        cls_id = int(
            box.cls[0]
        )

        class_name = \
            model.names[cls_id]


        if class_name not in ALLOWED_CLASSES:

            continue


        confidence = float(
            box.conf[0]
        )


        detections.append(
            (
                class_name,
                confidence
            )
        )


    # =====================================================
    # RAW DETECTION PRINT
    # =====================================================

    if detections:

        print(
            "[YOLO]",
            detections
        )


    # =====================================================
    # 5. DECISION ENGINE
    # =====================================================

    if frame_count > STARTUP_GRACE_FRAMES:

        confirmed = engine.update(
            detections,
            current_location
        )

    else:

        confirmed = []


    # =====================================================
    # 6. CONFIRMED EVENTS
    # =====================================================

    for obj_name, location in confirmed:

        now = datetime.now()

        timestamp = now.strftime(
            "%I:%M %p"
        )


        photo_filename = (
            f"event_"
            f"{obj_name}_"
            f"{now.strftime('%H%M%S')}.jpg"
        )


        photo_path_full = os.path.join(
            PHOTO_FOLDER,
            photo_filename
        )


        cv2.imwrite(
            photo_path_full,
            frame
        )


        print(
            f"[EVENT] "
            f"{obj_name} "
            f"at "
            f"{location or 'Unknown'}"
        )


        add_activity(
            f"🚨 {obj_name} detected - "
            f"{location or 'Unknown'}"
        )


        log_event(
            obj_name,
            location,
            timestamp,
            f"photos/{photo_filename}"
        )


    # =====================================================
    # 7. DASHBOARD DETECTIONS
    # =====================================================

    icons = {

        "laptop": "💻",

        "book": "📚",

        "cell phone": "📱",

        "backpack": "🎒",

        "handbag": "👜",

        "suitcase": "🧳",

        "person": "👤",

        "bottle": "🍼"

    }


    dashboard_detections = []


    for name, confidence in detections:

        dashboard_detections.append({

            "name": name,

            "icon": icons.get(
                name,
                "📦"
            ),

            "confidence": round(
                confidence * 100,
                1
            )

        })


    # =====================================================
    # 8. SENSOR ACTIVITY
    # =====================================================

    if frame_count % 30 == 0:

        if light_state == "ON":

            add_activity(
                "💡 Classroom lights ON"
            )

        else:

            add_activity(
                "💡 Classroom lights OFF"
            )


        if fan_state == "ON":

            add_activity(
                "🌀 Classroom fans ON"
            )

        else:

            add_activity(
                "🌀 Classroom fans OFF"
            )


    # =====================================================
    # 9. SEND EVERYTHING TO FLASK
    # =====================================================

    dashboard_data = {

        "status": "Patrolling",

        "mode": "Autonomous",

        "battery": 85,

        "location":
            current_location
            or "Unknown",

        "speed": "Medium",

        "distance": 0,

        "obstacle": "Waiting for HC-SR04",

        "action": "Camera / AI Monitoring",

        "lights":
            light_state,

        "fans":
            fan_state,

        "detections":
            dashboard_detections,

        "activity":
            activity

    }


    flask_connected = \
        send_to_flask(
            dashboard_data
        )


    # =====================================================
    # 10. DISPLAY
    # =====================================================

    annotated_frame = \
        results[0].plot()


    cv2.putText(
        annotated_frame,

        f"Location: "
        f"{current_location or 'Unknown'}",

        (10, 30),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (0, 255, 0),

        2
    )


    cv2.putText(
        annotated_frame,

        f"Light: {light_state}",

        (10, 60),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (0, 255, 0),

        2
    )


    cv2.putText(
        annotated_frame,

        f"Fan: {fan_state}",

        (10, 90),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (0, 255, 0),

        2
    )


    cv2.putText(
        annotated_frame,

        f"Flask: "
        f"{'CONNECTED' if flask_connected else 'OFFLINE'}",

        (10, 120),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (0, 255, 0)
        if flask_connected
        else (0, 0, 255),

        2
    )


    cv2.imshow(
        "Smart Desk Inspector",
        annotated_frame
    )


    # =====================================================
    # QUIT
    # =====================================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# =========================================================
# CLEANUP
# =========================================================

cap.release()

cv2.destroyAllWindows()

print()
print("Smart Desk Inspector stopped.")