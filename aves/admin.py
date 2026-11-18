from django.contrib import admin

from .models import Ave, Avistamiento, Comentario, Validacion


@admin.register(Ave)
class AveAdmin(admin.ModelAdmin):
    list_display = ("nombre_comun", "nombre_cientifico", "familia", "zona", "tamano")
    list_filter = ("familia", "zona")
    search_fields = ("nombre_comun", "nombre_cientifico")


@admin.register(Avistamiento)
class AvistamientoAdmin(admin.ModelAdmin):
    list_display = (
        "ave",
        "fecha",
        "lugar",
        "zona",
        "cantidad",
        "usuario",
        "aprobado",
        "caso_especial",
    )
    list_editable = ("aprobado", "caso_especial")
    list_filter = ("aprobado", "caso_especial", "zona", "fecha")
    search_fields = ("ave__nombre_comun", "lugar", "notas")
    date_hierarchy = "fecha"
    readonly_fields = ("creado_en",)


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "avistamiento", "creado_en")
    search_fields = ("texto", "usuario__username")


@admin.register(Validacion)
class ValidacionAdmin(admin.ModelAdmin):
    list_display = ("usuario", "avistamiento", "creado_en")
