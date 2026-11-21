@echo off
REM ============================================================
REM  Sincroniza el catalogo de empleados con la Estancia.
REM  Lo ejecuta la tarea programada "INMViajes\SincronizarEmpleados"
REM  (ver programar_sincronizacion_empleados.bat). Tambien se puede
REM  correr a mano para probar. Log: logs\sincronizar_empleados.log
REM ============================================================
setlocal

set "DJANGO_SETTINGS_MODULE=Viajes.settings.production"

set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
for %%I in ("%PROJECT_DIR%\..") do set "ROOT_DIR=%%~fI"

set "PYTHON_EXE="
if exist "%ROOT_DIR%\env\Scripts\python.exe"     set "PYTHON_EXE=%ROOT_DIR%\env\Scripts\python.exe"
if exist "%ROOT_DIR%\venv\Scripts\python.exe"    set "PYTHON_EXE=%ROOT_DIR%\venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%PROJECT_DIR%\env\Scripts\python.exe"    set "PYTHON_EXE=%PROJECT_DIR%\env\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%PROJECT_DIR%\env311\Scripts\python.exe" set "PYTHON_EXE=%PROJECT_DIR%\env311\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%PROJECT_DIR%\venv\Scripts\python.exe"   set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe"
if not defined PYTHON_EXE (
    echo [X] No se encontro el entorno virtual ^(env\Scripts\python.exe^).
    exit /b 1
)

if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"
cd /d "%PROJECT_DIR%"

echo [%date% %time%] >> "%PROJECT_DIR%\logs\sincronizar_empleados.log"
"%PYTHON_EXE%" manage.py sincronizar_empleados >> "%PROJECT_DIR%\logs\sincronizar_empleados.log" 2>&1
exit /b %errorlevel%
