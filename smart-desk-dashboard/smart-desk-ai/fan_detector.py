import numpy as np
import cv2

class FanDetector:
    """
    Detects fan ON/OFF within a FIXED, manually-calibrated ROI.

    Robustness against false positives (people, shadows, curtains,
    camera shake) comes from requiring SUSTAINED motion across many
    consecutive frames before declaring ON, and sustained stillness
    before declaring OFF — a brief disturbance doesn't have the same
    continuous frame-to-frame rhythm that spinning blades do.

    NOTE: COCO (YOLO's default 80 classes) has no "fan" class, so this
    cannot auto-locate the fan. fan_roi must be set manually per camera
    position. A custom-trained "fan" class would remove this limitation
    later, per the original project plan's fallback option.
    """

    def __init__(self, fan_roi, motion_threshold=3, on_frames=10, off_frames=15):
        self.fan_roi = fan_roi  # (y1, y2, x1, x2)
        self.motion_threshold = motion_threshold
        self.on_frames = on_frames
        self.off_frames = off_frames
        self.prev_region = None
        self.motion_streak = 0
        self.still_streak = 0
        self.state = "OFF"

    def update(self, gray_frame):
        y1, y2, x1, x2 = self.fan_roi
        region = gray_frame[y1:y2, x1:x2]

        motion_level = 0.0
        if self.prev_region is not None:
            diff = cv2.absdiff(region, self.prev_region)
            motion_level = float(np.mean(diff))

            if motion_level > self.motion_threshold:
                self.motion_streak += 1
                self.still_streak = 0
            else:
                self.still_streak += 1
                self.motion_streak = 0

            if self.motion_streak >= self.on_frames:
                self.state = "ON"
            elif self.still_streak >= self.off_frames:
                self.state = "OFF"

        self.prev_region = region
        return self.state, motion_level