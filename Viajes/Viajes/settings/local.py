"""
Configuración para desarrollo local
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Django Browser Reload para desarrollo
INSTALLED_APPS += ['django_browser_reload']
MIDDLEWARE += ['django_browser_reload.middleware.BrowserReloadMiddleware']

# ============================================
# DESARROLLO SIN PREFIJO
# ============================================
# En local no usamos /viajes/ porque no hay Nginx
# Usamos las URLs directamente como están en urls.py
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
LOGIN_URL = '/accounts/login/'
# Fase 25: el dispatcher por rol decide dónde aterriza cada usuario tras login.
LOGIN_REDIRECT_URL = '/inicio/'
LOGOUT_REDIRECT_URL = '/accounts/login/'