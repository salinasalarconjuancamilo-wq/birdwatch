"""Páginas de error propias, sin exponer información técnica del servidor."""
from django.http import HttpResponse
from django.template.loader import render_to_string


def _pagina_error(request, plantilla, estado, titulo, mensaje):
    # Se renderiza sin RequestContext: así una plantilla de error nunca depende
    # de consultas a la base de datos ni de context processors.
    html = render_to_string(
        plantilla, {"titulo": titulo, "mensaje": mensaje}
    )
    return HttpResponse(html, status=estado)


def error400(request, exception=None):
    return _pagina_error(
        request,
        "400.html",
        400,
        "Solicitud no válida",
        "No pudimos procesar la solicitud porque era demasiado grande o tenía "
        "un formato inesperado. Vuelve a intentarlo con un texto más corto.",
    )


def error403(request, exception=None):
    return _pagina_error(
        request,
        "403.html",
        403,
        "Acceso no permitido",
        "No tienes permiso para ver esta página o realizar esta acción.",
    )


def error404(request, exception=None):
    return _pagina_error(
        request,
        "404.html",
        404,
        "Página no encontrada",
        "La página que buscas no existe o cambió de dirección.",
    )


def error500(request):
    return _pagina_error(
        request,
        "500.html",
        500,
        "Error temporal del servidor",
        "Ocurrió un problema inesperado. Inténtalo de nuevo en unos minutos.",
    )
