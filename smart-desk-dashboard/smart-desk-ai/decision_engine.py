import time

class DecisionEngine:
    def __init__(self, confirm_frames=5, min_confidence=0.5, cooldown_seconds=600):
        self.confirm_frames = confirm_frames
        self.min_confidence = min_confidence
        self.cooldown_seconds = cooldown_seconds  # don't re-alert same (object, location) within this window
        self.streaks = {}
        self.last_alert_time = {}  # key: (object, location) -> last alert timestamp

    def update(self, detections, location):
        """
        detections: list of (class_name, confidence) for this frame
        location: current known location string, or None
        Returns: list of (class_name, location) newly confirmed AND not in cooldown
        """
        seen_this_frame = set()
        newly_confirmed = []
        loc_key = location or "Unknown Location"

        for class_name, confidence in detections:
            if confidence < self.min_confidence:
                continue

            seen_this_frame.add(class_name)
            self.streaks[class_name] = self.streaks.get(class_name, 0) + 1

            if self.streaks[class_name] == self.confirm_frames:
                key = (class_name, loc_key)
                last_time = self.last_alert_time.get(key, 0)
                if time.time() - last_time >= self.cooldown_seconds:
                    self.last_alert_time[key] = time.time()
                    newly_confirmed.append((class_name, loc_key))
                # else: real detection, but suppressed — already alerted for this object+location recently

        for class_name in list(self.streaks.keys()):
            if class_name not in seen_this_frame:
                self.streaks[class_name] = 0

        return newly_confirmed