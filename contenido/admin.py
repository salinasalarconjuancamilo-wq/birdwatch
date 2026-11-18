from django.contrib import admin

from .models import MensajeContacto, Noticia, PreguntaFrecuente


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "publicada", "destacada", "publicada_en")
    list_editable = ("publicada", "destacada")
    list_filter = ("publicada", "destacada")
    search_fields = ("titulo", "resumen", "contenido")
    prepopulated_fields = {"slug": ("titulo",)}
    date_hierarchy = "publicada_en"


@admin.register(PreguntaFrecuente)
class PreguntaFrecuenteAdmin(admin.ModelAdmin):
    list_display = ("pregunta", "orden", "activa")
    list_editable = ("orden", "activa")


@admin.register(MensajeContacto)
class MensajeContactoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "correo", "asunto", "creado_en", "respondido")
    list_editable = ("respondido",)
    list_filter = ("respondido",)
    search_fields = ("nombre", "correo", "asunto")
    readonly_fields = ("nombre", "correo", "asunto", "mensaje", "creado_en")
