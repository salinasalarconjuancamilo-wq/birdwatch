"""Middleware de protección frente a cargas excesivas de datos."""
from django.core.exceptions import RequestDataTooBig
from django.http import HttpResponseBadRequest


class LimiteCargaMiddleware:
    """Evita que RequestDataTooBig llegue como excepción no controlada.

    Las vistas que esperan texto del usuario (por ejemplo la publicación de
    comentarios) capturan la excepción por sí mismas para mostrar un aviso y
    redirigir. Este middleware cubre cualquier otro endpoint y garantiza una
    respuesta 400 genérica, sin trazas internas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except RequestDataTooBig:
            return HttpResponseBadRequest(
                "La solicitud es demasiado grande. Reduce el tamaño del texto o "
                "de los archivos e inténtalo de nuevo."
            )
