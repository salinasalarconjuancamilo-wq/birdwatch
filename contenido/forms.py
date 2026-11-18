"""Formularios de contenido dinámico."""
from django import forms

from .models import MensajeContacto


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
