"""Formularios de la comunidad de avistamientos."""
import re

from django import forms
from django.utils import timezone

from .models import Avistamiento, Comentario

# Límites acordados con QA: textos acotados y geocerca del área de cobertura.
MAX_LUGAR = 100
MAX_NOTAS = 1000
MAX_COMENTARIO = 1000
LATITUD_MINIMA, LATITUD_MAXIMA = 4.0, 5.2
LONGITUD_MINIMA, LONGITUD_MAXIMA = -75.0, -73.5

_ETIQUETA_HTML = re.compile(r"<\s*/?\s*[A-Za-z!][^>]*>")


def validar_texto(valor, etiqueta, maximo, exige_letras=False):
    """Rechaza HTML, cadenas de solo símbolos y textos demasiado largos."""
    texto = (valor or "").strip()
    if not texto:
        return texto
    if _ETIQUETA_HTML.search(texto):
        raise forms.ValidationError(
            f"{etiqueta} no puede contener etiquetas HTML ni código incrustado."
        )
    if not any(caracter.isalnum() for caracter in texto):
        raise forms.ValidationError(
            f"{etiqueta} debe contener texto; no se aceptan solo símbolos."
        )
    if exige_letras and not any(caracter.isalpha() for caracter in texto):
        raise forms.ValidationError(f"{etiqueta} debe contener al menos una letra.")
    if len(texto) > maximo:
        raise forms.ValidationError(
            f"{etiqueta} no puede superar los {maximo} caracteres."
        )
    return texto


class AvistamientoForm(forms.ModelForm):
    """Formulario validado para registrar o editar una observación."""

    lugar = forms.CharField(max_length=MAX_LUGAR, strip=True)
    notas = forms.CharField(
        max_length=MAX_NOTAS, required=False, strip=True, widget=forms.Textarea
    )

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
            "fecha": forms.DateInput(attrs={"type": "date", "required": True}),
            "notas": forms.Textarea(
                attrs={
                    "rows": 4,
                    "maxlength": str(MAX_NOTAS),
                    "placeholder": "¿Qué viste, cómo estaba el clima, qué hacía el ave…?",
                }
            ),
            "lugar": forms.TextInput(
                attrs={
                    "placeholder": "Ej. sendero al Salto del Tequendama",
                    "minlength": "3",
                    "maxlength": str(MAX_LUGAR),
                    "required": True,
                }
            ),
            "latitud": forms.NumberInput(
                attrs={
                    "step": "any",
                    "min": str(LATITUD_MINIMA),
                    "max": str(LATITUD_MAXIMA),
                    "placeholder": "4.558900",
                }
            ),
            "longitud": forms.NumberInput(
                attrs={
                    "step": "any",
                    "min": str(LONGITUD_MINIMA),
                    "max": str(LONGITUD_MAXIMA),
                    "placeholder": "-74.293300",
                }
            ),
            "cantidad": forms.NumberInput(attrs={"min": "1"}),
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
            "lugar": f"Entre 3 y {MAX_LUGAR} caracteres. Sin etiquetas HTML.",
            "fecha": "No se permiten fechas futuras.",
            "latitud": "Si conoces las coordenadas, aparecerás en el mapa. Ej. 4.558900",
            "longitud": "Ej. -74.293300 (el signo menos es importante).",
            "notas": f"Máximo {MAX_NOTAS} caracteres.",
            "caso_especial": "Especie rara, anidación, crianza o cualquier conducta destacable.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La fecha máxima se calcula al crear el formulario, nunca al importar.
        self.fields["fecha"].widget.attrs["max"] = timezone.localdate().isoformat()

    def clean_fecha(self):
        fecha = self.cleaned_data.get("fecha")
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError(
                "La fecha de la observación no puede ser futura."
            )
        return fecha

    def clean_lugar(self):
        return validar_texto(
            self.cleaned_data.get("lugar"), "El lugar", MAX_LUGAR, exige_letras=True
        )

    def clean_notas(self):
        return validar_texto(
            self.cleaned_data.get("notas"), "Las notas", MAX_NOTAS
        )

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
        if latitud is not None and longitud is not None:
            lat, lon = float(latitud), float(longitud)
            if not (
                LATITUD_MINIMA <= lat <= LATITUD_MAXIMA
                and LONGITUD_MINIMA <= lon <= LONGITUD_MAXIMA
            ):
                raise forms.ValidationError(
                    "Las coordenadas están fuera del área de cobertura del Parque "
                    "Ecológico San Antonio del Tequendama (latitud 4.0 a 5.2, "
                    "longitud -75.0 a -73.5)."
                )
        return cleaned


class ComentarioForm(forms.ModelForm):
    """Comentario acotado a 1000 caracteres (BUG-04)."""

    texto = forms.CharField(
        label="Tu comentario",
        max_length=MAX_COMENTARIO,
        strip=True,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "maxlength": str(MAX_COMENTARIO),
                "placeholder": "Comparte tu observación con la comunidad…",
            }
        ),
    )

    class Meta:
        model = Comentario
        fields = ["texto"]

    def clean_texto(self):
        texto = self.cleaned_data.get("texto", "").strip()
        if not texto:
            raise forms.ValidationError("Escribe un comentario antes de publicar.")
        return texto
