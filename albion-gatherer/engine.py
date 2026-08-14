"""The gathering state machine.

Runs on its own daemon thread. Loop:
  walk next waypoint -> scan screen for selected node templates ->
  click + wait on any hit (counts a gather) -> check if tools are spent ->
  if spent, walk the town route home (and optional repair route), then stop
  or resume per config.

Tool-spent is detected two ways, whichever trips first:
  * a template whose filename starts with "broken" matches on screen
  * the gather counter reaches max_gathers (hard fallback)
"""
import os
import glob
import time
import threading

import cv2

import config as C
from vision import Vision
from input_controller import Input


class BotEngine:
    def __init__(self, cfg, log, status):
        self.cfg = cfg
        self.log = log          # callable(str)
        self.status = status    # callable(str)
        self.vision = Vision()
        self.input = Input(cfg)
        self._stop = threading.Event()
        self._thread = None
        self.gathers = 0

    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running():
            return
        self._stop.clear()
        self.gathers = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    # -- helpers --------------------------------------------------------------
    def _sleep(self, seconds):
        end = time.time() + seconds
        while time.time() < end and not self._stop.is_set():
            time.sleep(0.02)

    def _templates(self, prefixes):
        out = []
        for path in sorted(glob.glob(os.path.join(C.TEMPLATE_DIR, "*.png"))):
            name = os.path.basename(path).lower()
            if any(name.startswith(p) for p in prefixes):
                img = cv2.imread(path)
                if img is not None:
                    out.append((name, img))
        return out

    def _goto(self, wp):
        self.input.click(int(wp["x"]), int(wp["y"]))

    def _tools_spent(self, broken_templates):
        if int(self.cfg["max_gathers"]) > 0 and self.gathers >= int(self.cfg["max_gathers"]):
            return True
        if broken_templates:
            screen = self.vision.grab()
            for _, tpl in broken_templates:
                if self.vision.find(screen, tpl, float(self.cfg["threshold"])):
                    return True
        return False

    def _return_home(self):
        for wp in self.cfg.get("town_route", []):
            if self._stop.is_set():
                return
            self._goto(wp)
            self._sleep(float(self.cfg["travel_delay"]))
        for wp in self.cfg.get("repair_route", []):
            if self._stop.is_set():
                return
            self._goto(wp)
            self._sleep(float(self.cfg["gather_delay"]))

    # -- main loop ------------------------------------------------------------
    def _run(self):
        try:
            prefixes = [r.lower() for r in self.cfg["resources_selected"]]
            nodes = self._templates(prefixes)
            broken = self._templates(["broken"])
            route = self.cfg["gather_route"]

            if not route:
                self.log("No gather route recorded — record one in the Routes tab first.")
                return
            if not nodes:
                self.log("No node templates for the selected resources — capture some (F8).")
                return

            self.log(f"Loaded {len(nodes)} node template(s), {len(broken)} tool template(s).")
            self.status("Farming")
            i = 0
            while not self._stop.is_set():
                self._goto(route[i % len(route)])
                self._sleep(float(self.cfg["travel_delay"]))

                screen = self.vision.grab()
                for name, tpl in nodes:
                    if self._stop.is_set():
                        break
                    hit = self.vision.find(screen, tpl, float(self.cfg["threshold"]))
                    if hit:
                        x, y, score = hit
                        self.log(f"node '{name}' {score:.2f} -> gather")
                        self.input.click(x, y)
                        self._sleep(float(self.cfg["gather_delay"]))
                        self.gathers += 1
                        self.status(f"Farming | gathers: {self.gathers}")

                if self._tools_spent(broken):
                    self.log(f"tools spent -> returning to {self.cfg['home_city']}")
                    self.status("Returning to city")
                    self._return_home()
                    if not self.cfg.get("auto_resume", False):
                        self.log("Arrived home. Refill/repair tools, then press Start.")
                        break
                    self.log("Home. Resuming loop.")
                    self.gathers = 0
                    self.status("Farming")
                i += 1
        except Exception as exc:  # noqa: BLE001 - surface any runtime fault to the log
            self.log(f"ERROR: {exc}")
        finally:
            self.status("Idle")
            self.log("Stopped.")
