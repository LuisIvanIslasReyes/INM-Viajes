@echo off
REM Detiene y elimina el servicio de Windows INMViajes. Ejecutar como Administrador.
setlocal
set "NSSM=C:\Users\usuariobc\Documents\nssm-2.24\win64\nssm.exe"
set "SERVICE=INMViajes"

net session >nul 2>&1
if errorlevel 1 (
    echo [X] Este script debe ejecutarse como Administrador.
    pause
    exit /b 1
)

"%NSSM%" stop "%SERVICE%"
"%NSSM%" remove "%SERVICE%" confirm
pause
endlocal
