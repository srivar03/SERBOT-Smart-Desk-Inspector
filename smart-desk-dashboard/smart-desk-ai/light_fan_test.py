import cv2
import numpy as np

cap = cv2.VideoCapture(0)
prev_gray = None

BRIGHTNESS_THRESHOLD = 100
MOTION_THRESHOLD = 3  # lowered significantly for distant, subtle motion

# Define a region of interest (ROI) where the fan is in the frame
# Adjust these numbers based on where the fan appears in YOUR video window
# Format: [y_start:y_end, x_start:x_end]
ROI_Y_START, ROI_Y_END = 0, 150      # top portion of frame
ROI_X_START, ROI_X_END = 200, 450    # adjust based on fan's horizontal position

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Crop to just the fan region
    fan_region = gray[ROI_Y_START:ROI_Y_END, ROI_X_START:ROI_X_END]

    brightness = np.mean(gray)
    light_status = "ON" if brightness > BRIGHTNESS_THRESHOLD else "OFF"

    fan_status = "UNKNOWN"
    if prev_gray is not None:
        prev_fan_region = prev_gray[ROI_Y_START:ROI_Y_END, ROI_X_START:ROI_X_END]
        diff = cv2.absdiff(fan_region, prev_fan_region)
        motion_level = np.mean(diff)
        fan_status = f"ON (moving) [{motion_level:.2f}]" if motion_level > MOTION_THRESHOLD else f"OFF (still) [{motion_level:.2f}]"

    prev_gray = gray

    display_frame = frame.copy()
    # Draw a rectangle showing the ROI being checked, for visual confirmation
    cv2.rectangle(display_frame, (ROI_X_START, ROI_Y_START), (ROI_X_END, ROI_Y_END), (0, 255, 255), 2)
    cv2.putText(display_frame, f"Brightness: {brightness:.1f} -> Light: {light_status}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(display_frame, f"Fan ROI Motion: {fan_status}",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow('Light/Fan Detection Test', display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()