@echo off
REM ============================================================
REM  Crea (o reemplaza) la tarea programada de Windows que
REM  sincroniza el catalogo de empleados con la Estancia cada
REM  15 minutos. Corre como SYSTEM: no depende de que alguien
REM  tenga sesion iniciada y sobrevive a reinicios y apagones.
REM
REM  Ejecutar como ADMINISTRADOR. Se puede volver a ejecutar.
REM ============================================================
setlocal

set "TAREA=INMViajes\SincronizarEmpleados"
set "MINUTOS=15"

net session >nul 2>&1
if errorlevel 1 (
    echo [X] Este script debe ejecutarse como Administrador.
    pause
    exit /b 1
)

set "BAT=%~dp0sincronizar_empleados.bat"
if not exist "%BAT%" (
    echo [X] No se encontro %BAT%
    pause
    exit /b 1
)

schtasks /Create /TN "%TAREA%" /TR "\"%BAT%\"" /SC MINUTE /MO %MINUTOS% /RU SYSTEM /RL HIGHEST /F
if errorlevel 1 (
    echo [X] No se pudo crear la tarea.
    pause
    exit /b 1
)

echo.
echo [*] Tarea "%TAREA%" creada: cada %MINUTOS% minutos.
echo [*] Corriendo una sincronizacion de prueba...
schtasks /Run /TN "%TAREA%"
echo [*] Revisa el resultado en: %~dp0logs\sincronizar_empleados.log
echo     y en Viajes ^> Empleados ("Ultima actualizacion desde la Estancia").
echo.
echo  Para quitarla:  schtasks /Delete /TN "%TAREA%" /F
pause
