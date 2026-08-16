"""Captura de pantalla + coincidencia de plantillas.

grab()       -> fotograma BGR del monitor completo vía mss (rápido, sin pasar por PIL).
find()       -> centro de la MEJOR coincidencia en coordenadas de pantalla absolutas, o None.
find_all()   -> TODAS las coincidencias por encima del umbral, con supresión de no-máximos
                (para que el modo inteligente vea cada nodo en pantalla, no solo el mejor).
present_at() -> True si una plantilla aún coincide cerca de un punto (para detectar
                cuándo un nodo se agota mientras se recolecta).

Las coordenadas absolutas incluyen el desplazamiento izquierda/arriba del monitor,
así que el punto devuelto se le puede pasar directo al controlador del ratón.
"""
import mss
import numpy as np
import cv2


class Vision:
    def __init__(self):
        self._sct = mss.mss()
        # monitors[0] es la unión virtual de todas las pantallas; [1] es la principal.
        self.mon = self._sct.monitors[1]

    def grab(self):
        """Devuelve un fotograma BGR del monitor principal."""
        raw = np.array(self._sct.grab(self.mon))
        return cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)

    def find(self, screen, template, threshold):
        """Centro absoluto de la mejor coincidencia, o None si nada supera el umbral."""
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

    def find_all(self, screen, template, threshold, max_hits=12):
        """Todas las coincidencias sobre el umbral, ordenadas por confianza descendente.

        Aplica supresión de no-máximos: descarta detecciones que se solapan con
        una mejor ya aceptada, para no clicar dos veces el mismo nodo.
        Devuelve una lista de (cx, cy, score) en coordenadas absolutas.
        """
        th, tw = template.shape[:2]
        if th > screen.shape[0] or tw > screen.shape[1]:
            return []
        res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(res >= threshold)
        if len(xs) == 0:
            return []
        candidates = sorted(
            zip(xs.tolist(), ys.tolist(), res[ys, xs].tolist()),
            key=lambda c: c[2], reverse=True,
        )
        min_dx, min_dy = tw * 0.6, th * 0.6
        hits = []
        for x, y, score in candidates:
            cx = x + tw // 2 + self.mon["left"]
            cy = y + th // 2 + self.mon["top"]
            if all(abs(cx - hx) > min_dx or abs(cy - hy) > min_dy
                   for hx, hy, _ in hits):
                hits.append((cx, cy, float(score)))
                if len(hits) >= max_hits:
                    break
        return hits

    def present_at(self, point, template, threshold, pad=6):
        """¿Sigue la plantilla coincidiendo alrededor de 'point' (coords absolutas)?

        Recorta una ventana pequeña alrededor del punto y busca la plantilla solo
        ahí. Se usa para saber si un nodo aún existe (todavía recolectando) o ya
        desapareció (recolección terminada) sin escanear la pantalla entera.
        """
        th, tw = template.shape[:2]
        half_w, half_h = tw // 2 + pad, th // 2 + pad
        left = point[0] - half_w
        top = point[1] - half_h
        region = {
            "left": int(left),
            "top": int(top),
            "width": int(tw + pad * 2),
            "height": int(th + pad * 2),
        }
        if region["width"] < tw or region["height"] < th:
            return False
        try:
            raw = np.array(self._sct.grab(region))
        except Exception:
            return False
        patch = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
        if patch.shape[0] < th or patch.shape[1] < tw:
            return False
        res = cv2.matchTemplate(patch, template, cv2.TM_CCOEFF_NORMED)
        return float(res.max()) >= threshold
