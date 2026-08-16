@echo off
REM ============================================================
REM  Albion Gatherer - abrir el bot (Windows)
REM  Doble clic aqui despues de haber ejecutado instalar.bat
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
  echo No parece estar instalado todavia.
  echo Ejecuta primero  instalar.bat
  echo.
  pause
  exit /b 1
)

REM pythonw = sin ventana negra de consola detras de la app
start "" ".venv\Scripts\pythonw.exe" "app.py"
