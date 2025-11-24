@echo off
REM Script para correr Django en modo DESARROLLO
echo Corriendo Django en modo DESARROLLO...
set DJANGO_SETTINGS_MODULE=Viajes.settings.local
python manage.py runserver
