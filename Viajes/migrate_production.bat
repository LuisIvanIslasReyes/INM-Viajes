@echo off
REM Script para aplicar migraciones en PRODUCCION
echo Aplicando migraciones en modo PRODUCCION...
set DJANGO_SETTINGS_MODULE=Viajes.settings.production
python manage.py migrate
pause
