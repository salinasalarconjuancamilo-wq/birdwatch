from django.urls import path

from . import views

urlpatterns = [
    path("noticias/", views.noticias, name="noticias"),
    path("noticias/<slug:slug>/", views.noticia_detalle, name="noticia_detalle"),
    path("ayuda/", views.ayuda, name="ayuda"),
    path("contacto/", views.contacto, name="contacto"),
    path("conducta/", views.conducta, name="conducta"),
]
