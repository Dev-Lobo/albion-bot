"""Global-hotkey recorder for waypoints and node/tool templates.

While armed (listener running), anywhere on screen:
  F7  -> append the current cursor position to the active route
  F8  -> save a 64x64 image around the cursor as a template

The active route (gather / town / repair), waypoint type (minimap / screen),
and template name are set from the GUI before you point-and-press.
"""
import os

import mss
import numpy as np
import cv2
from pynput import keyboard, mouse

import config as C


class Recorder:
    def __init__(self, cfg, log):
        self.cfg = cfg
        self.log = log
        self._mouse = mouse.Controller()
        self._listener = None
        self._sct = mss.mss()
        self.target = "gather_route"
        self.wp_type = "minimap"
        self.tpl_name = "ore"

    def set_target(self, name):
        self.target = name
        self.log(f"recording into: {name}")

    def set_type(self, name):
        self.wp_type = name

    def set_tpl_name(self, name):
        self.tpl_name = (name or "node").strip().lower().replace(" ", "_")

    def armed(self):
        return self._listener is not None

    def start(self):
        if self._listener:
            return
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()
        self.log("recorder ARMED — F7 = add waypoint, F8 = capture template")

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
            self.log("recorder off")

    def _on_press(self, key):
        try:
            if key == keyboard.Key.f7:
                x, y = self._mouse.position
                self.cfg[self.target].append(
                    {"x": int(x), "y": int(y), "type": self.wp_type}
                )
                C.save(self.cfg)
                self.log(f"+ {self.target} ({int(x)},{int(y)}) "
                         f"[{len(self.cfg[self.target])}]")
            elif key == keyboard.Key.f8:
                self._capture()
        except Exception as exc:  # noqa: BLE001
            self.log(f"recorder error: {exc}")

    def _capture(self, size=64):
        x, y = self._mouse.position
        region = {"left": int(x - size // 2), "top": int(y - size // 2),
                  "width": size, "height": size}
        raw = np.array(self._sct.grab(region))
        img = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
        idx = 1
        while os.path.exists(os.path.join(C.TEMPLATE_DIR, f"{self.tpl_name}_{idx}.png")):
            idx += 1
        path = os.path.join(C.TEMPLATE_DIR, f"{self.tpl_name}_{idx}.png")
        cv2.imwrite(path, img)
        self.log(f"template saved: {os.path.basename(path)}")
