from ultralytics import YOLO
import cv2
from decision_engine import DecisionEngine

model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture(0)
engine = DecisionEngine(confirm_frames=5, min_confidence=0.4)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, verbose=False, conf=0.1)

    detections = []
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        class_name = model.names[cls_id]
        confidence = float(box.conf[0])
        detections.append((class_name, confidence))

    confirmed = engine.update(detections)
    for obj in confirmed:
        print(f"🚨 CONFIRMED EVENT: {obj}")

    annotated_frame = results[0].plot()
    cv2.imshow('Smart Desk Inspector - YOLO Test', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()