from django.contrib import admin

from .models import (
    FotoParque,
    LugarObservacion,
    MensajeContacto,
    Noticia,
    PreguntaFrecuente,
    Seccion,
)


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


class FotoParqueInline(admin.TabularInline):
    model = FotoParque
    extra = 0
    fields = ("imagen", "titulo", "orden", "activa")
    ordering = ("orden", "id")


@admin.register(LugarObservacion)
class LugarObservacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "ubicacion", "activo", "orden")
    list_editable = ("activo", "orden")
    list_filter = ("tipo", "activo")
    search_fields = ("nombre", "ubicacion", "descripcion")
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [FotoParqueInline]


@admin.register(FotoParque)
class FotoParqueAdmin(admin.ModelAdmin):
    list_display = ("lugar", "titulo", "orden", "activa")
    list_editable = ("orden", "activa")
    list_filter = ("activa", "lugar")
    search_fields = ("titulo", "descripcion", "lugar__nombre")


@admin.register(Seccion)
class SeccionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "clave", "activa")
    list_editable = ("activa",)
    list_filter = ("activa",)
    search_fields = ("nombre", "clave")
