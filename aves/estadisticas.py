"""Cálculo centralizado de estadísticas y destacados de la comunidad.

Lo usa tanto la portada (``core.views.inicio``) como la página completa de
estadísticas (``aves.views.estadisticas``) para no duplicar consultas.
"""
from django.db.models import Count, Sum

from .models import Avistamiento


def resumen_estadisticas():
    """Devuelve los indicadores principales sobre avistamientos aprobados."""
    publicados = Avistamiento.objects.filter(aprobado=True)

    por_especie = (
        publicados.values("ave__nombre_comun", "ave__nombre_cientifico")
        .annotate(total=Count("id"))
        .order_by("-total", "ave__nombre_comun")
    )
    por_individuos = (
        publicados.values("ave__nombre_comun")
        .annotate(total=Sum("cantidad"))
        .order_by("-total", "ave__nombre_comun")
    )
    por_zona = (
        publicados.exclude(zona="")
        .values("zona")
        .annotate(total=Count("id"), especies=Count("ave", distinct=True))
        .order_by("-total")
    )

    return {
        "total_avistamientos": publicados.count(),
        "total_especies": publicados.values("ave").distinct().count(),
        "total_observadores": publicados.exclude(usuario=None).values("usuario").distinct().count(),
        "especie_mas_avistada": por_especie.first(),
        "top10": list(por_especie[:10]),
        "mas_observadas": list(por_individuos[:10]),
        "por_zona": list(por_zona),
        "casos_especiales": list(
            publicados.filter(caso_especial=True).select_related("ave", "usuario")[:8]
        ),
        "con_coordenadas": publicados.exclude(latitud=None).exclude(longitud=None).count(),
    }


def datos_mapa():
    """Devuelve los marcadores GeoJSON-like para el mapa Leaflet."""
    avistamientos = (
        Avistamiento.objects.filter(aprobado=True)
        .exclude(latitud=None)
        .exclude(longitud=None)
        .select_related("ave", "usuario")
        .order_by("-fecha")
    )
    return [
        {
            "id": a.id,
            "especie": a.ave.nombre_comun,
            "cientifico": a.ave.nombre_cientifico,
            "fecha": a.fecha.isoformat(),
            "lugar": a.lugar,
            "zona": a.get_zona_display() if a.zona else "Sin zona",
            "cantidad": a.cantidad,
            "latitud": float(a.latitud),
            "longitud": float(a.longitud),
            "notas": a.notas,
            "caso_especial": a.caso_especial,
            "validaciones": a.validaciones.count(),
            "foto": a.foto.url if a.foto else "",
            "detalle": f"/avistamientos/{a.id}/",
        }
        for a in avistamientos
    ]
