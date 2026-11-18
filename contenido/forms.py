"""Formularios de contenido dinámico."""
from django import forms

from .models import LugarObservacion, MensajeContacto, Noticia, Seccion


class MensajeContactoForm(forms.ModelForm):
    """Formulario público de contacto."""

    class Meta:
        model = MensajeContacto
        fields = ["nombre", "correo", "asunto", "mensaje"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Tu nombre"}),
            "correo": forms.EmailInput(attrs={"placeholder": "tu@correo.com"}),
            "asunto": forms.TextInput(attrs={"placeholder": "Asunto (opcional)"}),
            "mensaje": forms.Textarea(
                attrs={"rows": 6, "placeholder": "Cuéntanos tu duda, sugerencia o reporte…"}
            ),
        }
        labels = {
            "nombre": "Nombre",
            "correo": "Correo electrónico",
            "asunto": "Asunto",
            "mensaje": "Mensaje",
        }


# --------------------------------------------------- Panel de administración


class LugarForm(forms.ModelForm):
    """Alta y edición de lugares que aparecen en el mapa."""

    class Meta:
        model = LugarObservacion
        fields = [
            "nombre", "tipo", "ubicacion", "descripcion",
            "latitud", "longitud", "orden", "activo",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "ubicacion": forms.TextInput(attrs={"placeholder": "Soacha, Cundinamarca"}),
        }
        help_texts = {
            "latitud": "Deja ambos campos en blanco si la ubicación está por definir.",
        }


class SeccionForm(forms.ModelForm):
    """Activación y edición de secciones del sitio."""

    class Meta:
        model = Seccion
        fields = ["clave", "nombre", "descripcion", "activa"]
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}


class NoticiaPanelForm(forms.ModelForm):
    """Contenido editorial publicado desde el panel (sin imagen)."""

    class Meta:
        model = Noticia
        fields = ["titulo", "resumen", "contenido", "publicada", "destacada", "publicada_en"]
        widgets = {
            "resumen": forms.Textarea(attrs={"rows": 3}),
            "contenido": forms.Textarea(attrs={"rows": 8}),
        }
