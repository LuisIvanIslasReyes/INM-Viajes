"""
Configuración para correr tests sin MySQL ni .env (SQLite en memoria).

    python manage.py test apps.empleados --settings=Viajes.settings.test
"""
import os

# base.py exige estas variables vía decouple; en tests no hay .env.
for _var, _valor in {
    'SECRET_KEY': 'django-insecure-solo-para-tests',
    'DB_NAME': 'test', 'DB_USER': 'test', 'DB_PASSWORD': 'test',
}.items():
    os.environ.setdefault(_var, _valor)

from .base import *  # noqa: E402,F401,F403

DEBUG = False
ALLOWED_HOSTS = ['testserver', 'localhost']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
