@echo off
REM ============================================================
REM  Actualizacion manual de PRODUCCION con el servicio INMViajes.
REM  Reemplaza el menu de run_production.bat:
REM    1) Detiene el servicio y levanta la pagina de mantenimiento (8002)
REM    2) Tu actualizas el codigo y eliges: migrate / collectstatic / ambos
REM    3) Quita el mantenimiento y vuelve a arrancar el servicio
REM
REM  Ejecutar como ADMINISTRADOR.
REM ============================================================
setlocal

set "NSSM=C:\Users\usuariobc\Documents\nssm-2.24\win64\nssm.exe"
set "SERVICE=INMViajes"
set "PORT=8002"
set "DJANGO_SETTINGS_MODULE=Viajes.settings.production"

net session >nul 2>&1
if errorlevel 1 (
    echo [X] Este script debe ejecutarse como Administrador.
    pause
    exit /b 1
)

REM --- Rutas (carpeta de este .bat = carpeta con manage.py) ---
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
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"

echo.
echo [*] Deteniendo servicio %SERVICE%...
"%NSSM%" stop "%SERVICE%"
call :LIBERAR_PUERTO

echo [*] Levantando pagina de mantenimiento en puerto %PORT%...
start "Servidor de Mantenimiento - INM" /min "%PYTHON_EXE%" maintenance_server.py
timeout /t 2 /nobreak >nul

:MENU
cls
echo.
echo ========================================
echo   MODO MANTENIMIENTO ACTIVO - INM VIAJES
echo ========================================
echo.
echo  Servicio %SERVICE% DETENIDO. Los usuarios ven la pagina de mantenimiento.
echo  Actualiza el codigo ahora (copiar archivos / git pull) y luego elige:
echo.
echo   [M] Migraciones y levantar servicio
echo   [S] Collectstatic y levantar servicio
echo   [A] Migraciones + Collectstatic y levantar servicio
echo   [R] Solo levantar servicio
echo   [X] Salir dejando el mantenimiento activo (servicio detenido)
echo.
choice /C MSARX /N /M "Selecciona una opcion (M/S/A/R/X): "

if errorlevel 5 goto SALIR
if errorlevel 4 goto LEVANTAR
if errorlevel 3 goto TODO
if errorlevel 2 goto STATIC
if errorlevel 1 goto MIGRAR

:MIGRAR
call :RUN_MIGRATE
if errorlevel 1 goto FALLO
goto LEVANTAR

:STATIC
call :RUN_STATIC
if errorlevel 1 goto FALLO
goto LEVANTAR

:TODO
call :RUN_MIGRATE
if errorlevel 1 goto FALLO
call :RUN_STATIC
if errorlevel 1 goto FALLO
goto LEVANTAR

:FALLO
echo.
echo [X] El comando fallo. El servicio sigue DETENIDO y el mantenimiento activo.
echo     Corrige el problema y vuelve a elegir, o usa [R] para levantar igual.
pause
goto MENU

:LEVANTAR
echo.
echo [*] Quitando pagina de mantenimiento...
call :LIBERAR_PUERTO
echo [*] Iniciando servicio %SERVICE%...
"%NSSM%" start "%SERVICE%"
timeout /t 3 /nobreak >nul
"%NSSM%" status "%SERVICE%"
echo.
echo [OK] Revisa que la app responda. Log: %PROJECT_DIR%\logs\servicio.log
pause
exit /b 0

:SALIR
echo.
echo [!] Mantenimiento ACTIVO y servicio DETENIDO.
echo     Para volver a produccion ejecuta este script otra vez y elige [R].
pause
exit /b 0

REM ---------------- Subrutinas ----------------

:RUN_MIGRATE
echo.
echo [*] python manage.py migrate
"%PYTHON_EXE%" manage.py migrate
exit /b %errorlevel%

:RUN_STATIC
echo.
echo [*] python manage.py collectstatic --noinput
"%PYTHON_EXE%" manage.py collectstatic --noinput
exit /b %errorlevel%

:LIBERAR_PUERTO
REM Mata lo que escuche en el puerto (el servidor de mantenimiento).
REM Solo se llama con el servicio ya detenido.
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do taskkill /F /PID %%p >nul 2>&1
timeout /t 1 /nobreak >nul
exit /b 0
