"""Persistent configuration for Albion Gatherer.

Stored as JSON at ~/.config/albion-gatherer/config.json. Templates (node and
worn-tool images) live in templates/, captured through the in-app recorder.
"""
import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/albion-gatherer")
TEMPLATE_DIR = os.path.join(CONFIG_DIR, "templates")
ROUTE_DIR = os.path.join(CONFIG_DIR, "routes")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT = {
    "home_city": "Martlock",
    "resources_all": ["Ore", "Stone", "Fiber", "Hide", "Wood", "Fish"],
    "resources_selected": ["Ore"],
    # Each waypoint: {"x": int, "y": int, "type": "minimap" | "screen"}
    "gather_route": [],   # the farming loop
    "town_route": [],     # clicks that walk you home when tools break
    "repair_route": [],   # clicks at the vendor/bank once home (optional)
    "threshold": 0.75,    # template-match confidence (0..1)
    "travel_delay": 1.4,  # seconds to wait after a move order
    "gather_delay": 2.6,  # seconds a gather animation takes
    "move_time": 0.25,    # seconds a humanized cursor move takes
    "jitter": 3,          # pixels of random click scatter
    "max_gathers": 40,    # hard fallback: return home after N gathers
    "auto_resume": False, # re-run the loop after arriving home
}


def ensure_dirs():
    for d in (CONFIG_DIR, TEMPLATE_DIR, ROUTE_DIR):
        os.makedirs(d, exist_ok=True)


def load():
    ensure_dirs()
    cfg = dict(DEFAULT)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                cfg.update(json.load(fh))
        except (json.JSONDecodeError, OSError):
            pass
    # keep new default keys if the on-disk file predates them
    for k, v in DEFAULT.items():
        cfg.setdefault(k, v)
    return cfg


def save(cfg):
    ensure_dirs()
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    os.replace(tmp, CONFIG_FILE)
