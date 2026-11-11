"""
Configuración del proyecto BIRDWATCH.
Aves de San Antonio del Tequendama, Cundinamarca, Colombia.
"""
from pathlib import Path
import os
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

# Nota de seguridad: en un despliegue real nunca uses SECRET_KEY por defecto.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-birdwatch-san-antonio-del-tequendama-cambiar-en-produccion",
)

# True solo para desarrollo local. En producción usar DEBUG=False y un servidor WSGI.
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["*"]

# Orígenes adicionales confiables para CSRF, separados por comas en la
# variable de entorno DJANGO_CSRF_ORIGINS (por ejemplo
# "https://birdwatch.example.com,http://192.168.1.20:3000").
CSRF_TRUSTED_ORIGINS = [
    origen.strip()
    for origen in os.environ.get("DJANGO_CSRF_ORIGINS", "").split(",")
    if origen.strip()
]

# ------------------------------------------------------------------ Aplicaciones
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # App principal: identificador por canto (BirdNET) y detecciones.
    "core",
    # App original del repositorio: catalogo y avistamientos de aves
    # (se administra desde /admin/).
    "aves",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "birdwatch.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "plantillas"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "birdwatch.wsgi.application"

# ------------------------------------------------------------------ Base de datos
# Por defecto apunta al PostgreSQL local del equipo (servicio del sistema,
# puerto 5432). Antes usaba el PostgreSQL portátil del proyecto en 5433.
# Se puede sobreescribir con la variable de entorno DATABASE_URL, por ejemplo:
#   set DATABASE_URL=postgres://usuario:clave@servidor:5432/basedatos
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgres://birdwatch:birdwatch@localhost:5432/birdwatch"
)

_u = urlparse(DATABASE_URL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _u.path.lstrip("/") or "birdwatch",
        "USER": _u.username or "birdwatch",
        "PASSWORD": _u.password or "birdwatch",
        "HOST": _u.hostname or "localhost",
        "PORT": _u.port or 5432,
        "CONN_MAX_AGE": 60,
    }
}

# ------------------------------------------------------------------ Autenticación
LOGIN_URL = "/entrar/"
LOGIN_REDIRECT_URL = "/identificar/"
LOGOUT_REDIRECT_URL = "/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------ Internacionalización
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------ Archivos estáticos
STATIC_URL = "/estaticos/"
STATICFILES_DIRS = [BASE_DIR / "estaticos"]
STATIC_ROOT = BASE_DIR / "estaticos-compilados"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
