"""URLs principales del proyecto BIRDWATCH."""
from django.contrib import admin
from django.urls import path, include

from aves import views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Portada del proyecto (vista home de la app aves)
    path("portada/", views.home, name="home"),
    # App principal (inicio, login, identificador BirdNET, historial...)
    path("", include("core.urls")),
]
