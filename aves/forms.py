"""Formularios de la comunidad de avistamientos."""
from django import forms

from .models import Avistamiento, Comentario


class AvistamientoForm(forms.ModelForm):
    """Formulario sencillo para registrar una observación."""

    class Meta:
        model = Avistamiento
        fields = [
            "ave",
            "fecha",
            "lugar",
            "zona",
            "latitud",
            "longitud",
            "cantidad",
            "foto",
            "notas",
            "caso_especial",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "notas": forms.Textarea(attrs={"rows": 4, "placeholder": "¿Qué viste, cómo estaba el clima, qué hacía el ave…?"}),
            "lugar": forms.TextInput(attrs={"placeholder": "Ej. sendero al Salto del Tequendama"}),
            "latitud": forms.NumberInput(attrs={"step": "any", "placeholder": "4.558900"}),
            "longitud": forms.NumberInput(attrs={"step": "any", "placeholder": "-74.293300"}),
        }
        labels = {
            "ave": "Especie",
            "fecha": "Fecha de la observación",
            "lugar": "Lugar",
            "zona": "Zona del parque",
            "latitud": "Latitud (opcional)",
            "longitud": "Longitud (opcional)",
            "cantidad": "Cantidad de aves",
            "foto": "Foto (opcional)",
            "notas": "Notas",
            "caso_especial": "Es un caso especial",
        }
        help_texts = {
            "latitud": "Si conoces las coordenadas, aparecerás en el mapa. Ej. 4.558900",
            "longitud": "Ej. -74.293300 (el signo menos es importante).",
            "caso_especial": "Especie rara, anidación, crianza o cualquier conducta destacable.",
        }

    def clean(self):
        cleaned = super().clean()
        latitud = cleaned.get("latitud")
        longitud = cleaned.get("longitud")
        if (latitud is None) != (longitud is None):
            raise forms.ValidationError(
                "Indica la latitud y la longitud juntas, o deja ambas en blanco."
            )
        if latitud is not None and not (-90 <= float(latitud) <= 90):
            raise forms.ValidationError("La latitud debe estar entre -90 y 90.")
        if longitud is not None and not (-180 <= float(longitud) <= 180):
            raise forms.ValidationError("La longitud debe estar entre -180 y 180.")
        return cleaned


class ComentarioForm(forms.ModelForm):
    """Formulario breve para comentar un avistamiento."""

    class Meta:
        model = Comentario
        fields = ["texto"]
        widgets = {
            "texto": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Comparte tu observación con la comunidad…"}
            )
        }
        labels = {"texto": "Tu comentario"}
