"""Screen capture + template matching.

grab() -> full-monitor BGR frame via mss (fast, no PIL round-trip).
find() -> center of the single best match in *absolute* screen coords, or None.
Absolute coords include the monitor's left/top offset so the returned point can
be fed straight to the mouse controller.
"""
import mss
import numpy as np
import cv2


class Vision:
    def __init__(self):
        self._sct = mss.mss()
        # monitors[0] is the virtual union of all screens; [1] is the primary.
        self.mon = self._sct.monitors[1]

    def grab(self):
        raw = np.array(self._sct.grab(self.mon))
        return cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)

    def find(self, screen, template, threshold):
        th, tw = template.shape[:2]
        if th > screen.shape[0] or tw > screen.shape[1]:
            return None
        res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val < threshold:
            return None
        cx = max_loc[0] + tw // 2 + self.mon["left"]
        cy = max_loc[1] + th // 2 + self.mon["top"]
        return (cx, cy, float(max_val))
