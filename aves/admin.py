from django.contrib import admin

from .models import Ave, Avistamiento


@admin.register(Ave)
class AveAdmin(admin.ModelAdmin):
    list_display = ("nombre_comun", "nombre_cientifico", "familia", "tamano")
    search_fields = ("nombre_comun", "nombre_cientifico")


@admin.register(Avistamiento)
class AvistamientoAdmin(admin.ModelAdmin):
    list_display = ("ave", "fecha", "lugar", "cantidad")
    list_filter = ("fecha", "lugar")
    date_hierarchy = "fecha"
