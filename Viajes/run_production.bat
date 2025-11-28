@echo off
REM Script inteligente para correr Django en modo PRODUCCION con mantenimiento automático
REM Detecta automáticamente las rutas del proyecto y entorno virtual
REM Funciona en cualquier máquina sin necesidad de cambiar rutas

REM Obtener la ruta del script actual (donde está este .bat)
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR:~0,-1%

REM Detectar el entorno virtual (busca en la carpeta padre)
cd /d "%SCRIPT_DIR%.."
set ENV_PATH=
if exist "env\Scripts\python.exe" set ENV_PATH=%CD%\env\Scripts\python.exe
if exist "venv\Scripts\python.exe" set ENV_PATH=%CD%\venv\Scripts\python.exe

REM Si no encuentra env en el padre, buscar en el directorio actual
if "%ENV_PATH%"=="" (
    cd /d "%PROJECT_ROOT%"
    if exist "env\Scripts\python.exe" set ENV_PATH=%CD%\env\Scripts\python.exe
    if exist "env311\Scripts\python.exe" set ENV_PATH=%CD%\env311\Scripts\python.exe
    if exist "venv\Scripts\python.exe" set ENV_PATH=%CD%\venv\Scripts\python.exe
)

REM Si aún no encuentra, usar python del sistema
if "%ENV_PATH%"=="" (
    echo [!] ADVERTENCIA: No se encontro entorno virtual, usando Python del sistema
    set ENV_PATH=python
) else (
    echo [OK] Entorno virtual detectado: %ENV_PATH%
)

REM Volver al directorio del proyecto
cd /d "%PROJECT_ROOT%"

:START
cls
echo.
echo ========================================
echo   SERVIDOR DE PRODUCCION - INM VIAJES
echo ========================================
echo.
echo [*] Directorio: %PROJECT_ROOT%
echo [*] Python: %ENV_PATH%
echo.
echo [*] Verificando si hay servidor de mantenimiento activo...

REM Matar cualquier servidor de mantenimiento previo
for /f "tokens=2" %%a in ('tasklist /FI "WINDOWTITLE eq Servidor de Mantenimiento*" /NH 2^>nul') do (
    if not "%%a"=="" (
        echo [*] Deteniendo servidor de mantenimiento...
        taskkill /F /FI "WINDOWTITLE eq Servidor de Mantenimiento*" >nul 2>&1
    )
)

echo [*] Iniciando Django en modo PRODUCCION (Puerto 8002)...
echo [!] Presiona Ctrl+C para detener el servidor
echo.
set DJANGO_SETTINGS_MODULE=Viajes.settings.production

REM Ejecutar Django con la ruta detectada
"%ENV_PATH%" manage.py runserver 0.0.0.0:8002

REM Cuando Django se detiene (por Ctrl+C o error), llegar aquí
echo.
echo ========================================
echo   DJANGO DETENIDO
echo ========================================
echo.
echo [*] Levantando servidor de mantenimiento automáticamente...
echo.

REM Iniciar servidor de mantenimiento en una nueva ventana con rutas relativas
start "Servidor de Mantenimiento" cmd /c "title Servidor de Mantenimiento - INM && cd /d "%PROJECT_ROOT%" && "%ENV_PATH%" maintenance_server.py"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   MODO MANTENIMIENTO ACTIVO
echo ========================================
echo.
echo [OK] Servidor de mantenimiento corriendo en puerto 8002
echo.
echo Opciones:
echo   [R] Reiniciar servidor de produccion
echo   [M] Ejecutar migraciones y reiniciar
echo   [S] Recolectar archivos estaticos (collectstatic) y reiniciar
echo   [A] Migraciones + Collectstatic + Reiniciar (TODO)
echo   [X] Salir (mantenimiento seguira activo)
echo.

choice /C RMSAX /N /M "Selecciona una opcion (R/M/S/A/X): "

if errorlevel 5 goto EXIT
if errorlevel 4 goto ALL
if errorlevel 3 goto COLLECTSTATIC
if errorlevel 2 goto MIGRATE
if errorlevel 1 goto RESTART

:MIGRATE
echo.
echo [*] Ejecutando migraciones...
set DJANGO_SETTINGS_MODULE=Viajes.settings.production
"%ENV_PATH%" manage.py migrate
echo.
echo [OK] Migraciones completadas
timeout /t 3 /nobreak >nul
goto RESTART

:COLLECTSTATIC
echo.
echo [*] Recolectando archivos estaticos...
set DJANGO_SETTINGS_MODULE=Viajes.settings.production
"%ENV_PATH%" manage.py collectstatic --noinput
echo.
echo [OK] Archivos estaticos recolectados
timeout /t 3 /nobreak >nul
goto RESTART

:ALL
echo.
echo ========================================
echo   EJECUTANDO TODO
echo ========================================
echo.
echo [1/2] Ejecutando migraciones...
set DJANGO_SETTINGS_MODULE=Viajes.settings.production
"%ENV_PATH%" manage.py migrate
echo.
echo [2/2] Recolectando archivos estaticos...
"%ENV_PATH%" manage.py collectstatic --noinput
echo.
echo [OK] Todas las tareas completadas
timeout /t 3 /nobreak >nul
goto RESTART

:RESTART
echo.
echo [*] Preparando reinicio del servidor de produccion...
timeout /t 2 /nobreak >nul
goto START

:EXIT
echo.
echo [!] Saliendo... El servidor de mantenimiento seguira activo
echo [!] Para detenerlo, cierra la ventana "Servidor de Mantenimiento"
echo.
pause
exit