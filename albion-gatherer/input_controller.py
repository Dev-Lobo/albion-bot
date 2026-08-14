"""Humanized mouse control via pynput.

Movement follows a smoothstep-eased path in many small steps instead of a
teleport, and clicks land with a few pixels of random scatter — cheap
behavioral noise so the cursor doesn't move like a metronome.
"""
import time
import random
from pynput.mouse import Controller, Button


class Input:
    def __init__(self, cfg):
        self._m = Controller()
        self.cfg = cfg

    def _scatter(self):
        j = int(self.cfg.get("jitter", 3))
        return random.randint(-j, j), random.randint(-j, j)

    def move(self, x, y):
        speed = max(0.05, float(self.cfg.get("move_time", 0.25)))
        sx, sy = self._m.position
        steps = max(8, int(speed * 120))
        for k in range(1, steps + 1):
            t = k / steps
            ease = t * t * (3 - 2 * t)  # smoothstep
            self._m.position = (
                int(sx + (x - sx) * ease),
                int(sy + (y - sy) * ease),
            )
            time.sleep(speed / steps)

    def click(self, x, y, button=Button.left):
        dx, dy = self._scatter()
        self.move(x + dx, y + dy)
        time.sleep(random.uniform(0.03, 0.09))
        self._m.click(button, 1)
