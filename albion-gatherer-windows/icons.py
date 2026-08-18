"""Iconos de recursos dibujados por código (sin archivos ni assets externos).

Cada icono es un glifo simple en oro, generado con PIL al arrancar y envuelto en
un CTkImage. Son originales: no se copia arte de ningún juego ni de terceros, así
que se pueden distribuir sin problemas de licencia. Estética a juego con la
interfaz (oro sobre fondo oscuro).
"""
from PIL import Image, ImageDraw
import customtkinter as ctk

GOLD = (255, 215, 0, 255)
GOLD_DK = (150, 116, 12, 255)
DARK = (27, 26, 33, 255)   # color del panel, para "huecos" (ojo del pez, anillos)

SS = 4          # supermuestreo para bordes suaves
SIZE = 22       # tamaño final del icono en px


def _canvas(n):
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _pts(n, coords):
    return [(x * n, y * n) for x, y in coords]


def _mineral(d, n):
    # gema facetada
    body = [(0.30, 0.26), (0.70, 0.26), (0.87, 0.46), (0.50, 0.90), (0.13, 0.46)]
    d.polygon(_pts(n, body), fill=GOLD)
    d.line(_pts(n, [(0.13, 0.46), (0.87, 0.46)]), fill=GOLD_DK, width=max(1, n // 40))
    d.line(_pts(n, [(0.30, 0.26), (0.50, 0.46)]), fill=GOLD_DK, width=max(1, n // 40))
    d.line(_pts(n, [(0.70, 0.26), (0.50, 0.46)]), fill=GOLD_DK, width=max(1, n // 40))
    d.line(_pts(n, [(0.50, 0.46), (0.50, 0.90)]), fill=GOLD_DK, width=max(1, n // 40))


def _piedra(d, n):
    # dos rocas
    d.ellipse(_pts(n, [(0.10, 0.42), (0.66, 0.86)]), fill=GOLD)
    d.ellipse(_pts(n, [(0.48, 0.30), (0.90, 0.66)]), fill=GOLD_DK)
    d.ellipse(_pts(n, [(0.50, 0.32), (0.88, 0.64)]), fill=GOLD)


def _fibra(d, n):
    # planta: tallo + hojas
    w = max(1, n // 22)
    d.line(_pts(n, [(0.50, 0.92), (0.50, 0.24)]), fill=GOLD, width=w * 2)
    leaves = [
        [(0.50, 0.34), (0.30, 0.24), (0.32, 0.42)],
        [(0.50, 0.34), (0.70, 0.24), (0.68, 0.42)],
        [(0.50, 0.52), (0.26, 0.46), (0.32, 0.62)],
        [(0.50, 0.52), (0.74, 0.46), (0.68, 0.62)],
    ]
    for lf in leaves:
        d.polygon(_pts(n, lf), fill=GOLD)
    d.ellipse(_pts(n, [(0.44, 0.16), (0.56, 0.30)]), fill=GOLD)


def _cuero(d, n):
    # piel/pellejo estirado (blob irregular)
    hide = [(0.50, 0.14), (0.70, 0.24), (0.86, 0.44), (0.76, 0.60),
            (0.86, 0.82), (0.62, 0.74), (0.50, 0.86), (0.38, 0.74),
            (0.14, 0.82), (0.24, 0.60), (0.14, 0.44), (0.30, 0.24)]
    d.polygon(_pts(n, hide), fill=GOLD)


def _madera(d, n):
    # tronco con anillos en la punta
    d.rounded_rectangle(_pts(n, [(0.24, 0.36), (0.86, 0.64)]),
                        radius=n * 0.14, fill=GOLD)
    d.ellipse(_pts(n, [(0.12, 0.34), (0.36, 0.66)]), fill=GOLD)
    d.ellipse(_pts(n, [(0.17, 0.42), (0.31, 0.58)]), fill=GOLD_DK)
    d.ellipse(_pts(n, [(0.21, 0.47), (0.27, 0.53)]), fill=GOLD)


def _pescado(d, n):
    # cuerpo + cola + ojo
    d.ellipse(_pts(n, [(0.12, 0.34), (0.72, 0.70)]), fill=GOLD)
    d.polygon(_pts(n, [(0.66, 0.52), (0.92, 0.34), (0.92, 0.70)]), fill=GOLD)
    d.ellipse(_pts(n, [(0.26, 0.46), (0.34, 0.54)]), fill=DARK)


_DRAW = {
    "Mineral": _mineral,
    "Piedra": _piedra,
    "Fibra": _fibra,
    "Cuero": _cuero,
    "Madera": _madera,
    "Pescado": _pescado,
}


def build(size=SIZE):
    """Devuelve {nombre_recurso: CTkImage}. Silencioso si algo falla."""
    out = {}
    n = size * SS
    for name, fn in _DRAW.items():
        try:
            img, d = _canvas(n)
            fn(d, n)
            img = img.resize((size, size), Image.LANCZOS)
            out[name] = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
        except Exception:
            pass
    return out
