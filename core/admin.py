from django.contrib import admin

from .models import Ave, Deteccion


@admin.register(Ave)
class AveAdmin(admin.ModelAdmin):
    list_display = ("orden", "nombre_comun", "nombre_cientifico", "activo")
    list_display_links = ("nombre_comun",)
    list_editable = ("orden", "activo")
    search_fields = ("nombre_comun", "nombre_cientifico")


@admin.register(Deteccion)
class DeteccionAdmin(admin.ModelAdmin):
    list_display = ("especie_es", "especie_en", "confianza", "usuario", "creado_en")
    list_filter = ("usuario",)
    search_fields = ("especie_es", "especie_en", "nombre_cientifico")
    readonly_fields = [campo.name for campo in Deteccion._meta.fields]
