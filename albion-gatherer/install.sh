#!/usr/bin/env bash
# ============================================================================
#  Albion Gatherer — instalador de un solo comando (Linux / X11)
#  Ejecútalo desde dentro del repo:   bash install.sh
#  Después:                           albion-gatherer
#
#  Crea un venv aislado junto al código fuente, instala las dependencias y deja
#  un lanzador (~/.local/bin/albion-gatherer) + una entrada .desktop.
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

c_green ">> Instalador de Albion Gatherer"

# --- 1. comprobaciones: python3 + venv + tkinter -----------------------------
if ! command -v python3 >/dev/null 2>&1; then
  c_red "No se encontró python3. Instálalo: sudo apt install python3 python3-venv python3-tk"
  exit 1
fi
PYV=$(python3 -c 'import sys;print("%d%d"%sys.version_info[:2])')
if [ "$PYV" -lt 39 ]; then
  c_red "Se requiere Python 3.9+ (se encontró $(python3 -V))."; exit 1
fi

if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
  c_dim "falta tkinter — intentando: sudo apt install -y python3-tk"
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get install -y python3-tk python3-venv || true
  fi
  python3 -c 'import tkinter' >/dev/null 2>&1 || {
    c_red "tkinter sigue faltando. Instala el paquete python3-tk (o tk) de tu distro y reintenta."
    exit 1
  }
fi

if [ "${XDG_SESSION_TYPE:-}" = "wayland" ]; then
  c_red "!! Estás en una sesión Wayland. La inyección de ratón/teclado necesita X11."
  c_dim "   Cierra sesión y elige 'Xorg' / 'X11' en la pantalla de inicio para una entrada fiable."
fi

# --- 2. copiar el código fuente a APP_DIR ------------------------------------
c_green ">> instalando archivos en $APP_DIR"
mkdir -p "$APP_DIR" "$BIN_DIR" "$(dirname "$DESKTOP")"
for f in config.py vision.py input_controller.py engine.py recorder.py app.py requirements.txt README.txt; do
  cp -f "$SRC_DIR/$f" "$APP_DIR/$f"
done

# --- 3. crear venv + instalar dependencias -----------------------------------
c_green ">> creando entorno virtual"
python3 -m venv "$VENV"
c_green ">> instalando dependencias (esto tarda un minuto)"
"$VENV/bin/pip" install --upgrade pip >/dev/null
"$VENV/bin/pip" install -r "$APP_DIR/requirements.txt"

# --- 4. lanzador + entrada de escritorio -------------------------------------
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
Comment=Bot de recolección por visión de pantalla para Albion Online
Exec=$BIN_DIR/albion-gatherer
Terminal=false
Categories=Game;Utility;
DESK

c_green ">> listo."
echo
c_dim "Lánzalo:   albion-gatherer"
c_dim "Si no lo encuentra, añade ~/.local/bin al PATH:"
c_dim '   echo '"'"'export PATH="$HOME/.local/bin:$PATH"'"'"' >> ~/.bashrc && source ~/.bashrc'
echo
c_dim "El primer uso necesita una calibración de 5 min — ver README.txt"
