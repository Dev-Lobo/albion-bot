"""Control humanizado del ratón vía pynput.

El movimiento sigue una curva de Bézier (no una línea recta) suavizada con
smoothstep, con la velocidad de cada paso ligeramente variada y una pequeña
corrección de "rebase" al final: el cursor a veces se pasa unos píxeles del
objetivo y luego se ajusta, igual que una mano humana. Los clics caen con unos
píxeles de dispersión aleatoria. Todo esto es ruido de comportamiento barato
para que el cursor no se mueva como un metrónomo.
"""
import time
import math
import random
from pynput.mouse import Controller, Button


class Input:
    def __init__(self, cfg):
        self._m = Controller()
        self.cfg = cfg

    @property
    def position(self):
        """Posición actual del cursor (x, y) en coordenadas absolutas."""
        return self._m.position

    def _scatter(self):
        """Devuelve un pequeño desplazamiento aleatorio (dx, dy) para el clic."""
        j = int(self.cfg.get("jitter", 3))
        return random.randint(-j, j), random.randint(-j, j)

    def move(self, x, y):
        """Mueve el cursor hasta (x, y) siguiendo una curva humanizada."""
        speed = max(0.05, float(self.cfg.get("move_time", 0.25)))
        humanize = bool(self.cfg.get("humanize", True))
        sx, sy = self._m.position
        dist = math.hypot(x - sx, y - sy)
        if dist < 1.5:
            self._m.position = (int(x), int(y))
            return

        steps = max(10, int(speed * 130))

        # Punto de control perpendicular a la recta origen-destino: curva la
        # trayectoria una fracción de la distancia total hacia un lado al azar.
        mx, my = (sx + x) / 2.0, (sy + y) / 2.0
        nx, ny = -(y - sy), (x - sx)
        nlen = math.hypot(nx, ny) or 1.0
        bend = random.uniform(-0.14, 0.14) * dist if humanize else 0.0
        cxp = mx + nx / nlen * bend
        cyp = my + ny / nlen * bend

        for k in range(1, steps + 1):
            e = k / steps
            e = e * e * (3 - 2 * e)  # smoothstep sobre el parámetro
            inv = 1.0 - e
            px = inv * inv * sx + 2 * inv * e * cxp + e * e * x
            py = inv * inv * sy + 2 * inv * e * cyp + e * e * y
            self._m.position = (int(px), int(py))
            factor = random.uniform(0.8, 1.2) if humanize else 1.0
            time.sleep(speed / steps * factor)

    def click(self, x, y, button=Button.left):
        """Mueve hasta (x, y) con dispersión y hace un clic con retardo humano."""
        dx, dy = self._scatter()
        tx, ty = x + dx, y + dy
        self.move(tx, ty)

        # Corrección de "rebase" ocasional: pasarse y volver, como una mano real.
        if bool(self.cfg.get("humanize", True)) and random.random() < 0.18:
            ox = tx + random.randint(-6, 6)
            oy = ty + random.randint(-6, 6)
            self._m.position = (int(ox), int(oy))
            time.sleep(random.uniform(0.01, 0.04))
            self._m.position = (int(tx), int(ty))

        time.sleep(random.uniform(0.03, 0.11))
        self._m.click(button, 1)

    def nudge(self, radius=40):
        """Micromovimiento del cursor (usado en los descansos para no quedar quieto)."""
        sx, sy = self._m.position
        self.move(sx + random.randint(-radius, radius),
                  sy + random.randint(-radius, radius))
