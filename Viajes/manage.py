import os
import sys
from decouple import config


def main():
    """Run administrative tasks."""
    # Lee el entorno desde .env (local o production)
    environment = config('DJANGO_ENV', default='local')
    
    if environment == 'production':
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Viajes.settings.production')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Viajes.settings.local')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()