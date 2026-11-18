"""Rutas de la comunidad de avistamientos (se montan en /avistamientos/)."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.lista_avistamientos, name="avistamientos"),
    path("nuevo/", views.crear_avistamiento, name="avistamiento_nuevo"),
    path("pendientes/", views.pendientes, name="avistamientos_pendientes"),
    path("<int:pk>/", views.detalle_avistamiento, name="avistamiento_detalle"),
    path("<int:pk>/comentar/", views.comentar, name="avistamiento_comentar"),
    path("<int:pk>/validar/", views.validar, name="avistamiento_validar"),
    path("<int:pk>/aprobar/", views.aprobar, name="avistamiento_aprobar"),
    path("<int:pk>/eliminar/", views.eliminar, name="avistamiento_eliminar"),
]
