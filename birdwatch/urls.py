"""URLs principales del proyecto BIRDWATCH."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from aves import views as aves_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Portada alterna de la app aves (se conserva por compatibilidad).
    path("portada/", aves_views.home, name="home"),
    # Comunidad: avistamientos, comentarios, validaciones y aprobación.
    path("avistamientos/", include("aves.urls")),
    # Mapa interactivo y estadísticas (rutas cortas de acceso público).
    path("mapa/", aves_views.mapa, name="mapa"),
    path("mapa/datos/", aves_views.avistamientos_json, name="avistamientos_json"),
    path("estadisticas/", aves_views.estadisticas, name="estadisticas"),
    # Contenido dinámico: noticias, ayuda, contacto y código de conducta.
    path("", include("contenido.urls")),
    # App principal (inicio, login, identificador BirdNET, historial...).
    path("", include("core.urls")),
]

# Servir las fotos subidas en desarrollo (DEBUG=True).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
