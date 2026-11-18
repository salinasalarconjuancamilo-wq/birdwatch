"""Datos de identidad disponibles en todas las plantillas."""
from django.conf import settings


def datos_sitio(request):
    return {
        "frase_inspiradora": getattr(settings, "FRASE_INSPIRADORA", ""),
        "aliado": getattr(settings, "ALIADO", ""),
        "nombre_parque": getattr(settings, "NOMBRE_PARQUE", ""),
        "redes_sociales": getattr(settings, "REDES_SOCIALES", []),
    }
