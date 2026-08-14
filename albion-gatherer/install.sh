#!/usr/bin/env bash
# ============================================================================
#  Albion Gatherer — one-command installer (Linux / X11)
#  Run from inside the repo:   bash install.sh
#  Then:                       albion-gatherer
#
#  Builds an isolated venv next to the source, installs deps, and drops a
#  launcher (~/.local/bin/albion-gatherer) + a .desktop entry.
# ============================================================================
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${ALBION_BOT_DIR:-$HOME/.local/share/albion-gatherer}"
BIN_DIR="$HOME/.local/bin"
VENV="$APP_DIR/.venv"
DESKTOP="$HOME/.local/share/applications/albion-gatherer.desktop"

c_green() { printf '\033[1;32m%s\033[0m\n' "$1"; }
c_red()   { printf '\033[1;31m%s\033[0m\n' "$1"; }
c_dim()   { printf '\033[2m%s\033[0m\n' "$1"; }

c_green ">> Albion Gatherer installer"

# --- 1. sanity: python3 + venv + tkinter -------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  c_red "python3 not found. Install it: sudo apt install python3 python3-venv python3-tk"
  exit 1
fi
PYV=$(python3 -c 'import sys;print("%d%d"%sys.version_info[:2])')
if [ "$PYV" -lt 39 ]; then
  c_red "Python 3.9+ required (found $(python3 -V))."; exit 1
fi

if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
  c_dim "tkinter missing — attempting: sudo apt install -y python3-tk"
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get install -y python3-tk python3-venv || true
  fi
  python3 -c 'import tkinter' >/dev/null 2>&1 || {
    c_red "tkinter still missing. Install your distro's python3-tk (or tk) package, then re-run."
    exit 1
  }
fi

if [ "${XDG_SESSION_TYPE:-}" = "wayland" ]; then
  c_red "!! You are on a Wayland session. Mouse/keyboard injection needs X11."
  c_dim "   Log out and pick 'Xorg' / 'X11' at the login screen for reliable input."
fi

# --- 2. copy source into APP_DIR ---------------------------------------------
c_green ">> installing files to $APP_DIR"
mkdir -p "$APP_DIR" "$BIN_DIR" "$(dirname "$DESKTOP")"
for f in config.py vision.py input_controller.py engine.py recorder.py app.py requirements.txt README.txt; do
  cp -f "$SRC_DIR/$f" "$APP_DIR/$f"
done

# --- 3. build venv + install deps --------------------------------------------
c_green ">> creating virtualenv"
python3 -m venv "$VENV"
c_green ">> installing dependencies (this takes a minute)"
"$VENV/bin/pip" install --upgrade pip >/dev/null
"$VENV/bin/pip" install -r "$APP_DIR/requirements.txt"

# --- 4. launcher + desktop entry ---------------------------------------------
cat > "$BIN_DIR/albion-gatherer" <<LAUNCH
#!/usr/bin/env bash
cd "$APP_DIR"
exec "$VENV/bin/python" "$APP_DIR/app.py" "\$@"
LAUNCH
chmod +x "$BIN_DIR/albion-gatherer"

cat > "$DESKTOP" <<DESK
[Desktop Entry]
Type=Application
Name=Albion Gatherer
Comment=Screen-vision gathering bot for Albion Online
Exec=$BIN_DIR/albion-gatherer
Terminal=false
Categories=Game;Utility;
DESK

c_green ">> done."
echo
c_dim "Launch it:   albion-gatherer"
c_dim "If not found, add ~/.local/bin to PATH:"
c_dim '   echo '"'"'export PATH="$HOME/.local/bin:$PATH"'"'"' >> ~/.bashrc && source ~/.bashrc'
echo
c_dim "First run needs a 5-min calibration — see README.txt"
