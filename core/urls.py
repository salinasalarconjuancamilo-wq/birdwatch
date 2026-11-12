from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("entrar/", views.entrar, name="entrar"),
    path("salir/", views.salir, name="salir"),
    path("identificar/", views.identificar, name="identificar"),
    path("analizar/", views.analizar, name="analizar"),
    path("historial/", views.historial, name="historial"),
    path("estado/", views.estado, name="estado"),
    path("sw.js", views.service_worker, name="service_worker"),
    # Administración del carrusel (solo superadministrador).
    path("carrusel/", views.carrusel_admin, name="carrusel_admin"),
    path("carrusel/nueva/", views.carrusel_nueva, name="carrusel_nueva"),
    path("carrusel/<int:pk>/editar/", views.carrusel_editar, name="carrusel_editar"),
    path("carrusel/<int:pk>/eliminar/", views.carrusel_eliminar, name="carrusel_eliminar"),
    path("carrusel/<int:pk>/alternar/", views.carrusel_alternar, name="carrusel_alternar"),
    path("carrusel/<int:pk>/mover/", views.carrusel_mover, name="carrusel_mover"),
]
