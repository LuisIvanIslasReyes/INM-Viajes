@echo off
REM Script para correr Django en modo PRODUCCION
echo Corriendo Django en modo PRODUCCION...
set DJANGO_SETTINGS_MODULE=Viajes.settings.production
python manage.py runserver 0.0.0.0:8001
