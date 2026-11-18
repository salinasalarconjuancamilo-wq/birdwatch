"""Datos de identidad disponibles en todas las plantillas."""
from django.conf import settings

from contenido.models import secciones_activas


def datos_sitio(request):
    activas = secciones_activas()
    return {
        "frase_inspiradora": getattr(settings, "FRASE_INSPIRADORA", ""),
        "aliado": getattr(settings, "ALIADO", ""),
        "nombre_parque": getattr(settings, "NOMBRE_PARQUE", ""),
        "redes_sociales": getattr(settings, "REDES_SOCIALES", []),
        "secciones_activas": activas,
    }
