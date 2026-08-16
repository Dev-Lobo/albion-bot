"""Grabador de atajos globales para puntos de ruta e imágenes de nodos/herramientas.

Mientras está armado (el escuchador está en marcha), en cualquier parte de la pantalla:
  F7  -> añade la posición actual del cursor a la ruta activa
  F8  -> guarda una imagen de 64x64 alrededor del cursor como plantilla

La ruta activa (recolección / ciudad / reparación), el tipo de punto
(minimapa / pantalla) y el nombre de la plantilla se fijan desde la interfaz
antes de apuntar y pulsar.
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
        self.tpl_name = "mineral"

    def set_target(self, name):
        self.target = name
        self.log(f"grabando en: {name}")

    def set_type(self, name):
        self.wp_type = name

    def set_tpl_name(self, name):
        self.tpl_name = (name or "nodo").strip().lower().replace(" ", "_")

    def armed(self):
        return self._listener is not None

    def start(self):
        if self._listener:
            return
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()
        self.log("grabador ARMADO — F7 = añadir punto, F8 = capturar plantilla")

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
            self.log("grabador apagado")

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
            self.log(f"error del grabador: {exc}")

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
        self.log(f"plantilla guardada: {os.path.basename(path)}")
