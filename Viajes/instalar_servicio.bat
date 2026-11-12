@echo off
REM ============================================================
REM  Instala INM Viajes (Django, puerto 8002) como servicio de
REM  Windows con NSSM, para que arranque solo tras un reinicio
REM  o un apagon y se reinicie si el proceso se cae.
REM
REM  Ejecutar como ADMINISTRADOR (clic derecho > Ejecutar como
REM  administrador). Se puede volver a ejecutar: si el servicio
REM  ya existe, lo reinstala con esta configuracion.
REM ============================================================
setlocal

set "NSSM=C:\Users\usuariobc\Documents\nssm-2.24\win64\nssm.exe"
set "SERVICE=INMViajes"
set "PORT=8002"

REM --- Verificar permisos de administrador ---
net session >nul 2>&1
if errorlevel 1 (
    echo [X] Este script debe ejecutarse como Administrador.
    pause
    exit /b 1
)

if not exist "%NSSM%" (
    echo [X] No se encontro nssm.exe en: %NSSM%
    pause
    exit /b 1
)

REM --- Rutas del proyecto (carpeta donde esta este .bat = carpeta con manage.py) ---
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
for %%I in ("%PROJECT_DIR%\..") do set "ROOT_DIR=%%~fI"

REM --- Detectar el python del entorno virtual (igual que run_production.bat) ---
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

if not exist "%ROOT_DIR%\.env" (
    echo [!] ADVERTENCIA: no existe %ROOT_DIR%\.env
    echo     Django no arrancara sin SECRET_KEY, DB_* y ALLOWED_HOSTS.
    pause
)

echo.
echo [*] Proyecto : %PROJECT_DIR%
echo [*] Python   : %PYTHON_EXE%
echo [*] Servicio : %SERVICE% (puerto %PORT%)
echo.

REM --- Si ya existe el servicio, detenerlo y quitarlo para reinstalar ---
sc query "%SERVICE%" >nul 2>&1
if not errorlevel 1 (
    echo [*] El servicio ya existe, se reinstalara...
    "%NSSM%" stop "%SERVICE%" >nul 2>&1
    "%NSSM%" remove "%SERVICE%" confirm
)

REM --- Avisar si algo ya ocupa el puerto (run_production.bat o mantenimiento) ---
netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul
if not errorlevel 1 (
    echo [!] El puerto %PORT% ya esta en uso. Cierra run_production.bat y la
    echo     ventana "Servidor de Mantenimiento" antes de continuar.
    pause
)

if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

REM --- Instalar ---
REM --noreload: sin el autoreloader, runserver es UN solo proceso, asi NSSM
REM lo puede detener/reiniciar sin dejar procesos huerfanos ocupando el puerto.
"%NSSM%" install "%SERVICE%" "%PYTHON_EXE%" manage.py runserver 0.0.0.0:%PORT% --noreload
if errorlevel 1 (
    echo [X] Fallo la instalacion del servicio.
    pause
    exit /b 1
)

"%NSSM%" set "%SERVICE%" AppDirectory "%PROJECT_DIR%"
"%NSSM%" set "%SERVICE%" AppEnvironmentExtra DJANGO_SETTINGS_MODULE=Viajes.settings.production PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
"%NSSM%" set "%SERVICE%" DisplayName "INM Viajes (Django)"
"%NSSM%" set "%SERVICE%" Description "Sistema de Gestion de Viajes INM - Django en puerto %PORT%"

REM Arranque automatico (retrasado: da tiempo a red y MySQL tras un apagon)
"%NSSM%" set "%SERVICE%" Start SERVICE_DELAYED_AUTO_START

REM Si el proceso termina por cualquier motivo, reiniciarlo a los 5 segundos
"%NSSM%" set "%SERVICE%" AppExit Default Restart
"%NSSM%" set "%SERVICE%" AppRestartDelay 5000

REM Logs (rotan al llegar a 10 MB)
"%NSSM%" set "%SERVICE%" AppStdout "%PROJECT_DIR%\logs\servicio.log"
"%NSSM%" set "%SERVICE%" AppStderr "%PROJECT_DIR%\logs\servicio.log"
"%NSSM%" set "%SERVICE%" AppRotateFiles 1
"%NSSM%" set "%SERVICE%" AppRotateOnline 1
"%NSSM%" set "%SERVICE%" AppRotateBytes 10485760

REM --- Si MySQL corre en esta maquina como servicio, esperar a que arranque ---
set "MYSQL_SVC="
for %%S in (MySQL80 MySQL84 MySQL57 MySQL) do (
    sc query %%S >nul 2>&1 && if not defined MYSQL_SVC set "MYSQL_SVC=%%S"
)
if defined MYSQL_SVC (
    echo [*] Dependencia agregada: servicio %MYSQL_SVC%
    "%NSSM%" set "%SERVICE%" DependOnService %MYSQL_SVC%
) else (
    echo [!] No se detecto el servicio de MySQL; no se agrego dependencia.
    echo     Si NSSM arranca antes que MySQL, reintentara cada 5 segundos.
)

REM --- Iniciar ---
echo.
"%NSSM%" start "%SERVICE%"
timeout /t 3 /nobreak >nul
"%NSSM%" status "%SERVICE%"

echo.
echo ============================================================
echo  Listo. Comandos utiles:
echo    "%NSSM%" status  %SERVICE%
echo    "%NSSM%" restart %SERVICE%
echo    "%NSSM%" stop    %SERVICE%
echo  Log: %PROJECT_DIR%\logs\servicio.log
echo ============================================================
pause
endlocal
