"""Punto de entrada WSGI del proyecto BIRDWATCH."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "birdwatch.settings")

application = get_wsgi_application()
