import cv2
from pyzbar.pyzbar import decode

cap = cv2.VideoCapture(0)
last_seen = None
missed_frames = 0
MISS_TOLERANCE = 10  # allow up to 10 frames of no-detection before declaring "left"

while True:
    ret, frame = cap.read()
    if not ret:
        break

    decoded_objects = decode(frame)

    current_qr = None
    for obj in decoded_objects:
        current_qr = obj.data.decode('utf-8')

        points = obj.polygon
        if len(points) == 4:
            pts = [(p.x, p.y) for p in points]
            for i in range(4):
                cv2.line(frame, pts[i], pts[(i+1) % 4], (0, 255, 0), 3)

        cv2.putText(frame, current_qr, (obj.rect.left, obj.rect.top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    if current_qr:
        missed_frames = 0  # reset, since we just saw it
        if current_qr != last_seen:
            print(f"Entered location: {current_qr}")
            last_seen = current_qr
    else:
        missed_frames += 1
        if last_seen is not None and missed_frames >= MISS_TOLERANCE:
            print(f"Left location: {last_seen}")
            last_seen = None

    cv2.imshow('QR Code Decode Test', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()