from django.urls import path

from . import views

urlpatterns = [
    # Página de cada parque y selector que se abre con el logo.
    path("parques/", views.parques, name="parques"),
    path("parques/<slug:slug>/", views.parque_detalle, name="parque_detalle"),
    path("noticias/", views.noticias, name="noticias"),
    path("noticias/<slug:slug>/", views.noticia_detalle, name="noticia_detalle"),
    path("ayuda/", views.ayuda, name="ayuda"),
    path("contacto/", views.contacto, name="contacto"),
    path("conducta/", views.conducta, name="conducta"),
    # Panel de contenido (solo administradores).
    path("contenido/admin/", views.panel_contenido, name="contenido_admin"),
    path("contenido/admin/parques/", views.parques_admin, name="parques_admin"),
    path("contenido/admin/parques/<int:pk>/fotos/", views.parque_fotos, name="parque_fotos"),
    path(
        "contenido/admin/parques/<int:pk>/fotos/nueva/",
        views.parque_foto_nueva,
        name="parque_foto_nueva",
    ),
    path(
        "contenido/admin/parques/<int:pk>/fotos/<int:foto_pk>/editar/",
        views.parque_foto_editar,
        name="parque_foto_editar",
    ),
    path(
        "contenido/admin/parques/<int:pk>/fotos/<int:foto_pk>/eliminar/",
        views.parque_foto_eliminar,
        name="parque_foto_eliminar",
    ),
    path(
        "contenido/admin/parques/<int:pk>/fotos/<int:foto_pk>/alternar/",
        views.parque_foto_alternar,
        name="parque_foto_alternar",
    ),
    path(
        "contenido/admin/parques/<int:pk>/fotos/<int:foto_pk>/mover/",
        views.parque_foto_mover,
        name="parque_foto_mover",
    ),
    path("contenido/admin/lugares/nuevo/", views.lugar_nuevo, name="lugar_nuevo"),
    path("contenido/admin/lugares/<int:pk>/editar/", views.lugar_editar, name="lugar_editar"),
    path("contenido/admin/lugares/<int:pk>/eliminar/", views.lugar_eliminar, name="lugar_eliminar"),
    path("contenido/admin/lugares/<int:pk>/alternar/", views.lugar_alternar, name="lugar_alternar"),
    path("contenido/admin/secciones/nueva/", views.seccion_nueva, name="seccion_nueva"),
    path("contenido/admin/secciones/<int:pk>/editar/", views.seccion_editar, name="seccion_editar"),
    path("contenido/admin/secciones/<int:pk>/eliminar/", views.seccion_eliminar, name="seccion_eliminar"),
    path("contenido/admin/secciones/<int:pk>/alternar/", views.seccion_alternar, name="seccion_alternar"),
    path("contenido/admin/noticias/nueva/", views.noticia_nueva, name="noticia_nueva"),
    path("contenido/admin/noticias/<int:pk>/editar/", views.noticia_editar, name="noticia_editar"),
    path("contenido/admin/noticias/<int:pk>/eliminar/", views.noticia_eliminar, name="noticia_eliminar"),
    path("contenido/admin/noticias/<int:pk>/alternar/", views.noticia_alternar, name="noticia_alternar"),
]
