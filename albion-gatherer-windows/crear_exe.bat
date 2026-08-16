@echo off
REM ============================================================
REM  Albion Gatherer - crear un .EXE independiente (Windows)
REM  Doble clic aqui. Genera  dist\AlbionGatherer.exe , un
REM  unico archivo que se abre con doble clic, sin terminal.
REM  (Necesita Python instalado SOLO para construirlo; el .exe
REM   resultante ya funciona por si solo.)
REM ============================================================
setlocal
cd /d "%~dp0"
title Crear AlbionGatherer.exe

echo ============================================
echo   Creando AlbionGatherer.exe
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No se encontro Python.
  echo Instalalo desde https://www.python.org/downloads/
  echo y marca "Add python.exe to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Preparando entorno virtual...
  python -m venv .venv
)

echo [2/3] Instalando dependencias + PyInstaller...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
  echo [ERROR] Fallo la instalacion de dependencias.
  pause
  exit /b 1
)

echo [3/3] Empaquetando el .exe (esto tarda unos minutos)...
".venv\Scripts\pyinstaller.exe" --noconfirm --onefile --windowed ^
  --name AlbionGatherer ^
  --collect-all customtkinter ^
  app.py
if errorlevel 1 (
  echo [ERROR] PyInstaller no pudo generar el .exe.
  pause
  exit /b 1
)

echo.
echo ============================================
echo   LISTO.
echo ============================================
echo.
echo   Tu programa esta en:   dist\AlbionGatherer.exe
echo   Doble clic ahi para abrir el bot sin terminal.
echo.
echo   Nota: Windows puede mostrar un aviso de SmartScreen
echo   porque el .exe no esta firmado. Pulsa "Mas informacion"
echo   y luego "Ejecutar de todas formas".
echo.
pause
endlocal
