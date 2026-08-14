"""Configuración persistente de Albion Gatherer.

Se guarda como JSON en ~/.config/albion-gatherer/config.json. Las plantillas
(imágenes de nodos y de herramienta gastada) viven en templates/, capturadas
desde el grabador de la propia app.

NOTA: los identificadores del código (nombres de variables y claves del JSON)
se mantienen en inglés a propósito, porque son la "API interna" del programa y
renombrarlos rompería configuraciones ya guardadas. Todo lo que lee o ve una
persona —interfaz, registros, comentarios y esta documentación— está en español.
"""
import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/albion-gatherer")
TEMPLATE_DIR = os.path.join(CONFIG_DIR, "templates")
ROUTE_DIR = os.path.join(CONFIG_DIR, "routes")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Textos de estado compartidos entre el motor y la interfaz (deben coincidir).
STATUS_IDLE = "Inactivo"
STATUS_FARMING = "Recolectando"
STATUS_RETURNING = "Volviendo a la ciudad"
STATUS_RESTING = "Descanso humano"

DEFAULT = {
    "home_city": "Martlock",
    "resources_all": ["Mineral", "Piedra", "Fibra", "Cuero", "Madera", "Pescado"],
    "resources_selected": ["Mineral"],
    # Cada punto de ruta: {"x": int, "y": int, "type": "minimap" | "screen"}
    "gather_route": [],   # el bucle de recolección
    "town_route": [],     # clics que te llevan a casa cuando se rompen las herramientas
    "repair_route": [],   # clics en el vendedor/banco ya en la ciudad (opcional)
    "threshold": 0.75,    # confianza de coincidencia de plantilla (0..1)
    "travel_delay": 1.4,  # segundos de espera tras una orden de movimiento
    "gather_delay": 2.6,  # TECHO de segundos por recolección (con modo adaptativo es el máximo)
    "move_time": 0.25,    # segundos que dura un movimiento humanizado del cursor
    "jitter": 3,          # píxeles de dispersión aleatoria del clic
    "max_gathers": 40,    # tope de seguridad: volver a casa tras N recolecciones
    "auto_resume": False, # reanudar el bucle tras llegar a casa
    # ----------------------------------------------------------------------
    # Inteligencia del bot (todo activable/desactivable desde la pestaña Ajustes)
    # ----------------------------------------------------------------------
    "smart_scan": True,        # escanea TODOS los nodos visibles y farmea varios por parada
    "adaptive_gather": True,   # detecta cuándo el nodo desaparece en vez de esperar un tiempo fijo
    "adaptive_threshold": True,  # autoajusta la confianza según aciertos y fallos
    "humanize": True,          # ruido gaussiano en los tiempos + descansos tipo humano
    "max_scan_nodes": 4,       # cuántos nodos farmear como máximo por parada antes de avanzar
    "break_every_min": 25,     # tomar un descanso tras un número aleatorio de recolecciones (mínimo)
    "break_every_max": 45,     # ...(máximo)
    "break_short": 8.0,        # duración mínima del descanso humano (s)
    "break_long": 35.0,        # duración máxima del descanso humano (s)
    "thr_floor": 0.60,         # límite inferior al que el autoajuste puede bajar la confianza
}


def ensure_dirs():
    """Crea las carpetas de configuración, plantillas y rutas si no existen."""
    for d in (CONFIG_DIR, TEMPLATE_DIR, ROUTE_DIR):
        os.makedirs(d, exist_ok=True)


def load():
    """Carga la configuración del disco fusionándola con los valores por defecto."""
    ensure_dirs()
    cfg = dict(DEFAULT)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                cfg.update(json.load(fh))
        except (json.JSONDecodeError, OSError):
            pass
    # conserva las claves nuevas si el archivo en disco es anterior a ellas
    for k, v in DEFAULT.items():
        cfg.setdefault(k, v)
    return cfg


def save(cfg):
    """Guarda la configuración de forma atómica (escribe .tmp y luego reemplaza)."""
    ensure_dirs()
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG_FILE)
