@echo off
REM Script para ejecutar el servidor de mantenimiento
REM Úsalo cuando necesites detener el servidor principal para hacer cambios

echo.
echo ========================================
echo   SERVIDOR DE MANTENIMIENTO - INM
echo ========================================
echo.
echo Ejecutando servidor de mantenimiento en puerto 8002...
echo.

cd /d "%~dp0"
C:\Users\alberto\Documents\GitHub\INM-Viajes\env\Scripts\python.exe maintenance_server.py

pause
