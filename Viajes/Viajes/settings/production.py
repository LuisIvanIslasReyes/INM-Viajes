"""
Configuración para producción
"""
from .base import *
from decouple import config, Csv

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# NO incluir django_browser_reload en producción
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django_browser_reload']
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'browser_reload' not in mw]

# ============================================
# CONFIGURACIÓN PARA SUB-RUTA /viajes/
# ============================================

# NO usar FORCE_SCRIPT_NAME - Django manejará las URLs tal como vienen de Nginx

# Nombres ÚNICOS de cookies (evita conflictos con FaceID)
SESSION_COOKIE_NAME = 'inmviajes_sessionid'
CSRF_COOKIE_NAME = 'inmviajes_csrftoken'

# Ruta de las cookies (solo válidas en /viajes/)
SESSION_COOKIE_PATH = '/viajes/'
CSRF_COOKIE_PATH = '/viajes/'

# ============================================
# SEGURIDAD HTTPS/SSL
# ============================================

# Django detrás de proxy Nginx con HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies seguras en producción
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Seguridad adicional
SECURE_SSL_REDIRECT = False  # Nginx maneja el redirect HTTP->HTTPS
SECURE_HSTS_SECONDS = 31536000  # HSTS por 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ============================================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ============================================

# SIN prefijo /viajes/ - Nginx lo quita con rewrite antes de llegar aquí
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise para servir archivos estáticos en producción
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================
# URLs DE AUTENTICACIÓN
# ============================================

# SIN prefijo /viajes/ - Nginx lo quita con rewrite antes de llegar aquí
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'