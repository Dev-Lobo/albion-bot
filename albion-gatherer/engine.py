"""La máquina de estados de recolección (el "cerebro" del bot).

Corre en su propio hilo demonio. Bucle:
  ir al siguiente punto de ruta -> escanear la pantalla buscando las plantillas
  de los recursos elegidos -> clicar y recolectar los nodos hallados ->
  comprobar si las herramientas están gastadas -> si lo están, recorrer la ruta
  de vuelta a la ciudad (y la de reparación opcional), y luego parar o reanudar
  según la configuración.

INTELIGENCIA (todo opcional desde Ajustes):
  * smart_scan .......... ve TODOS los nodos visibles y farmea varios por parada,
                          empezando por el más cercano al cursor.
  * adaptive_gather ..... espera hasta que el nodo DESAPARECE (recolección real)
                          en vez de dormir un tiempo fijo -> más rápido y fiable.
  * adaptive_threshold .. baja la confianza si lleva rato sin ver nada y la sube
                          de nuevo al acertar -> se autocalibra en marcha.
  * humanize ............ ruido gaussiano en los tiempos + descansos tipo humano
                          cada cierto número aleatorio de recolecciones.

Herramienta gastada se detecta de dos formas, la que salte primero:
  * una plantilla cuyo nombre empieza por "broken" coincide en pantalla
  * el contador de recolecciones llega a max_gathers (tope de seguridad)
"""
import os
import glob
import math
import time
import random
import threading

import cv2

import config as C
from vision import Vision
from input_controller import Input


class BotEngine:
    def __init__(self, cfg, log, status):
        self.cfg = cfg
        self.log = log          # invocable(str)
        self.status = status    # invocable(str)
        self.vision = Vision()
        self.input = Input(cfg)
        self._stop = threading.Event()
        self._thread = None
        self.gathers = 0
        # estado de la inteligencia (se reinicia en cada arranque)
        self._thr = float(cfg["threshold"])   # confianza efectiva (puede autoajustarse)
        self._miss_streak = 0                 # paradas seguidas sin ver ningún nodo
        self._next_break_at = 0               # nº de recolecciones en el que toca descansar
        self._t0 = 0.0                        # marca de tiempo del inicio de sesión

    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running():
            return
        self._stop.clear()
        self.gathers = 0
        self._thr = float(self.cfg["threshold"])
        self._miss_streak = 0
        self._t0 = time.time()
        self._schedule_break()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    # -- utilidades -----------------------------------------------------------
    def _sleep(self, seconds):
        """Duerme respetando la señal de parada (comprueba cada 20 ms)."""
        end = time.time() + max(0.0, seconds)
        while time.time() < end and not self._stop.is_set():
            time.sleep(0.02)

    def _h(self, base):
        """Aplica ruido gaussiano a un tiempo base si la humanización está activa."""
        if not self.cfg.get("humanize", True):
            return float(base)
        return max(0.05, random.gauss(float(base), float(base) * 0.15))

    def _templates(self, prefixes):
        """Carga las plantillas .png cuyo nombre empieza por alguno de los prefijos."""
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

    # -- inteligencia ---------------------------------------------------------
    def _schedule_break(self):
        """Fija dentro de cuántas recolecciones tocará el próximo descanso humano."""
        lo = int(self.cfg.get("break_every_min", 25))
        hi = max(lo, int(self.cfg.get("break_every_max", 45)))
        self._next_break_at = self.gathers + random.randint(lo, hi)

    def _maybe_break(self):
        """Si toca, hace una pausa larga tipo humano con algún micromovimiento."""
        if not self.cfg.get("humanize", True):
            return
        if self.gathers < self._next_break_at:
            return
        dur = random.uniform(float(self.cfg.get("break_short", 8.0)),
                             float(self.cfg.get("break_long", 35.0)))
        self.log(f"descanso humano ~{dur:.0f}s (tras {self.gathers} recolecciones)")
        self.status(C.STATUS_RESTING)
        end = time.time() + dur
        while time.time() < end and not self._stop.is_set():
            # de vez en cuando muevo un poco el ratón para no quedar congelado
            if random.random() < 0.25:
                try:
                    self.input.nudge()
                except Exception:
                    pass
            self._sleep(random.uniform(0.6, 1.4))
        self._schedule_break()
        self.status(f"{C.STATUS_FARMING} | recolectadas: {self.gathers}")

    def _scan_nodes(self, nodes):
        """Devuelve todos los nodos visibles como (x, y, score, name, tpl).

        Con smart_scan usa find_all (todas las coincidencias); si no, se queda
        con la mejor por plantilla, replicando el comportamiento clásico.
        """
        screen = self.vision.grab()
        found = []
        smart = self.cfg.get("smart_scan", True)
        cap = max(1, int(self.cfg.get("max_scan_nodes", 4)))
        for name, tpl in nodes:
            if self._stop.is_set():
                break
            if smart:
                for x, y, score in self.vision.find_all(screen, tpl, self._thr, max_hits=cap * 2):
                    found.append((x, y, score, name, tpl))
            else:
                hit = self.vision.find(screen, tpl, self._thr)
                if hit:
                    x, y, score = hit
                    found.append((x, y, score, name, tpl))
        return found

    def _order_by_distance(self, found):
        """Ordena los nodos por cercanía al cursor (menos viaje = más humano y rápido)."""
        cx, cy = self.input.position
        return sorted(found, key=lambda n: math.hypot(n[0] - cx, n[1] - cy))

    def _gather_one(self, x, y, tpl):
        """Clica un nodo y espera a que termine la recolección.

        Con adaptive_gather sondea la zona del nodo: en cuanto la plantilla deja
        de coincidir ahí (nodo agotado) da por hecha la recolección, con el
        gather_delay como techo. Si no, simplemente espera el gather_delay.
        """
        self.input.click(x, y)
        ceiling = float(self.cfg["gather_delay"])
        if not self.cfg.get("adaptive_gather", True):
            self._sleep(self._h(ceiling))
            return
        # deja arrancar la animación antes de empezar a vigilar
        self._sleep(min(0.5, ceiling * 0.3))
        deadline = time.time() + ceiling
        while time.time() < deadline and not self._stop.is_set():
            try:
                still_there = self.vision.present_at((x, y), tpl, self._thr)
            except Exception:
                still_there = True
            if not still_there:
                return  # nodo agotado -> recolección terminada antes de tiempo
            self._sleep(0.25)

    def _reward_hit(self):
        """Tras recolectar: reinicia la racha de fallos y devuelve la confianza a su base."""
        self._miss_streak = 0
        base = float(self.cfg["threshold"])
        if self.cfg.get("adaptive_threshold", True) and self._thr < base:
            self._thr = min(base, self._thr + 0.01)

    def _register_miss(self):
        """Tras una parada sin nodos: si se repite, baja la confianza dentro del límite."""
        self._miss_streak += 1
        if not self.cfg.get("adaptive_threshold", True):
            return
        floor = float(self.cfg.get("thr_floor", 0.60))
        if self._miss_streak >= 3 and self._thr > floor:
            self._thr = max(floor, self._thr - 0.02)
            self._miss_streak = 0
            self.log(f"sin nodos varias veces -> bajo confianza a {self._thr:.2f}")

    def _tools_spent(self, broken_templates):
        if int(self.cfg["max_gathers"]) > 0 and self.gathers >= int(self.cfg["max_gathers"]):
            return True
        if broken_templates:
            screen = self.vision.grab()
            for _, tpl in broken_templates:
                if self.vision.find(screen, tpl, self._thr):
                    return True
        return False

    def _return_home(self):
        for wp in self.cfg.get("town_route", []):
            if self._stop.is_set():
                return
            self._goto(wp)
            self._sleep(self._h(self.cfg["travel_delay"]))
        for wp in self.cfg.get("repair_route", []):
            if self._stop.is_set():
                return
            self._goto(wp)
            self._sleep(self._h(self.cfg["gather_delay"]))

    def _rate(self):
        """Recolecciones por hora estimadas para el registro."""
        elapsed = max(1.0, time.time() - self._t0)
        return self.gathers / elapsed * 3600.0

    # -- bucle principal ------------------------------------------------------
    def _run(self):
        try:
            prefixes = [r.lower() for r in self.cfg["resources_selected"]]
            nodes = self._templates(prefixes)
            broken = self._templates(["broken"])
            route = self.cfg["gather_route"]

            if not route:
                self.log("No hay ruta de recolección grabada — graba una en la pestaña Rutas primero.")
                return
            if not nodes:
                self.log("No hay plantillas de nodos para los recursos elegidos — captura algunas (F8).")
                return

            modo = "inteligente" if self.cfg.get("smart_scan", True) else "clásico"
            self.log(f"Cargadas {len(nodes)} plantilla(s) de nodo y {len(broken)} de herramienta. Modo: {modo}.")
            self.status(C.STATUS_FARMING)
            i = 0
            while not self._stop.is_set():
                self._goto(route[i % len(route)])
                self._sleep(self._h(self.cfg["travel_delay"]))

                found = self._scan_nodes(nodes)
                if found:
                    ordered = self._order_by_distance(found)
                    cap = max(1, int(self.cfg.get("max_scan_nodes", 4)))
                    if not self.cfg.get("smart_scan", True):
                        cap = 1
                    for x, y, score, name, tpl in ordered[:cap]:
                        if self._stop.is_set():
                            break
                        self.log(f"nodo '{name}' {score:.2f} -> recolectar")
                        self._gather_one(x, y, tpl)
                        self.gathers += 1
                        self._reward_hit()
                        self.status(f"{C.STATUS_FARMING} | recolectadas: {self.gathers} "
                                    f"| ~{self._rate():.0f}/h | conf {self._thr:.2f}")
                        self._maybe_break()
                        if self._stop.is_set():
                            break
                else:
                    self._register_miss()

                if self._tools_spent(broken):
                    self.log(f"herramientas gastadas -> volviendo a {self.cfg['home_city']}")
                    self.status(C.STATUS_RETURNING)
                    self._return_home()
                    if not self.cfg.get("auto_resume", False):
                        self.log("En casa. Repara/recarga las herramientas y pulsa Iniciar.")
                        break
                    self.log("En casa. Reanudando el bucle.")
                    self.gathers = 0
                    self._schedule_break()
                    self.status(C.STATUS_FARMING)
                i += 1
        except Exception as exc:  # noqa: BLE001 - lleva cualquier fallo en marcha al registro
            self.log(f"ERROR: {exc}")
        finally:
            self.status(C.STATUS_IDLE)
            self.log(f"Detenido. Total recolectadas: {self.gathers} (~{self._rate():.0f}/h).")
