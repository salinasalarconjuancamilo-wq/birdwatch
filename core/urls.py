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
]
