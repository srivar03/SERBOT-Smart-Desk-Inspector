import numpy as np

class LightDetector:
    """
    Detects whether a classroom's artificial light fixture is ON, by
    comparing brightness INSIDE a fixture region against the
    background around it — not the whole-frame average.

    Sunlight raises the whole frame evenly, so the fixture-vs-background
    MARGIN stays small even when absolute brightness is high. A real lit
    fixture creates a strong local margin. This isn't perfect (see
    testing notes) but is meaningfully more robust than global brightness.
    """

    def __init__(self, fixture_roi=None, margin_threshold=25, stable_frames=8):
        # fixture_roi: (y1, y2, x1, x2). Set this to your actual light
        # fixture's position once you calibrate it — see testing section.
        self.fixture_roi = fixture_roi
        self.margin_threshold = margin_threshold
        self.stable_frames = stable_frames
        self.on_streak = 0
        self.off_streak = 0
        self.state = "OFF"

    def _get_roi(self, height, width):
        if self.fixture_roi:
            return self.fixture_roi
        # Default guess: upper-center box, until calibrated per room
        return (0, height // 4, width // 3, 2 * width // 3)

    def update(self, gray_frame):
        height, width = gray_frame.shape
        y1, y2, x1, x2 = self._get_roi(height, width)

        fixture_region = gray_frame[y1:y2, x1:x2]
        fixture_brightness = float(np.mean(fixture_region))

        mask = np.ones_like(gray_frame, dtype=bool)
        mask[y1:y2, x1:x2] = False
        background_brightness = float(np.mean(gray_frame[mask]))

        margin = fixture_brightness - background_brightness

        if margin > self.margin_threshold:
            self.on_streak += 1
            self.off_streak = 0
        else:
            self.off_streak += 1
            self.on_streak = 0

        if self.on_streak >= self.stable_frames:
            self.state = "ON"
        elif self.off_streak >= self.stable_frames:
            self.state = "OFF"
        # else: not enough consecutive evidence yet — keep previous state

        return self.state, fixture_brightness, background_brightness, margin