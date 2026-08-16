@echo off
REM ============================================================
REM  Albion Gatherer - instalador facil para Windows
REM  Doble clic en este archivo. Crea un entorno aislado e
REM  instala todo lo necesario. (Sin acentos a proposito para
REM  que la consola de Windows no muestre simbolos raros.)
REM ============================================================
setlocal
cd /d "%~dp0"
title Instalador de Albion Gatherer

echo ============================================
echo   Instalador de Albion Gatherer (Windows)
echo ============================================
echo.

REM --- 1. comprobar que Python esta instalado ---------------
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No se encontro Python.
  echo.
  echo Instalalo desde: https://www.python.org/downloads/
  echo IMPORTANTE: durante la instalacion marca la casilla
  echo             "Add python.exe to PATH".
  echo.
  echo Cuando lo tengas, vuelve a ejecutar este instalador.
  echo.
  pause
  exit /b 1
)

echo [1/3] Creando entorno virtual (.venv)...
python -m venv .venv
if errorlevel 1 (
  echo [ERROR] No se pudo crear el entorno virtual.
  pause
  exit /b 1
)

echo [2/3] Actualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip

echo [3/3] Instalando dependencias (tarda un par de minutos)...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Fallo la instalacion de dependencias.
  pause
  exit /b 1
)

echo.
echo ============================================
echo   LISTO. Instalacion completada.
echo ============================================
echo.
echo   Para ABRIR el bot:      doble clic en  ejecutar.bat
echo   Para crear un .EXE:     doble clic en  crear_exe.bat
echo.
pause
endlocal
