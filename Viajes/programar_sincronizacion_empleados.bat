@echo off
REM ============================================================
REM  Crea (o reemplaza) las tareas programadas de Windows que
REM  sincronizan el catalogo de empleados con la Estancia:
REM    - cada 15 minutos, incremental (solo lo que cambio);
REM    - cada noche, completa (todo el catalogo; marca inactivos
REM      a los que ya no vengan, p. ej. borrados en la Estancia).
REM  Corren como SYSTEM: no dependen de que alguien tenga sesion
REM  iniciada y sobreviven a reinicios y apagones.
REM
REM  Ejecutar como ADMINISTRADOR. Se puede volver a ejecutar.
REM ============================================================
setlocal

set "TAREA=INMViajes\SincronizarEmpleados"
set "MINUTOS=15"
set "TAREA_COMPLETA=INMViajes\SincronizarEmpleadosCompleta"
set "HORA_COMPLETA=03:00"

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

schtasks /Create /TN "%TAREA_COMPLETA%" /TR "\"%BAT%\" --completa" /SC DAILY /ST %HORA_COMPLETA% /RU SYSTEM /RL HIGHEST /F
if errorlevel 1 (
    echo [X] No se pudo crear la tarea nocturna.
    pause
    exit /b 1
)

echo.
echo [*] Tarea "%TAREA%" creada: cada %MINUTOS% minutos ^(incremental^).
echo [*] Tarea "%TAREA_COMPLETA%" creada: diario a las %HORA_COMPLETA% ^(completa^).
echo [*] Corriendo una sincronizacion de prueba...
schtasks /Run /TN "%TAREA%"
echo [*] Revisa el resultado en: %~dp0logs\sincronizar_empleados.log
echo     y en Viajes ^> Empleados ("Ultima actualizacion desde la Estancia").
echo.
echo  Para quitarlas:  schtasks /Delete /TN "%TAREA%" /F
echo                  schtasks /Delete /TN "%TAREA_COMPLETA%" /F
pause
