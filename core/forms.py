"""Formularios del panel de administración del carrusel."""
from pathlib import Path

from django import forms
from django.conf import settings
from django.utils.text import slugify

from .models import Ave

# Formatos y tamaño máximo aceptados para las fotos del carrusel.
TAMANO_MAXIMO_FOTO = 10 * 1024 * 1024  # 10 MB
ANCHO_MAXIMO_FOTO = 1280  # píxeles; suficiente para la tarjeta y liviano


def _carpeta_fotos():
    carpeta = Path(settings.BASE_DIR) / "estaticos" / "img" / "aves"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def _nombre_archivo(nombre_cientifico, carpeta, imagen_actual=""):
    """Nombre único para la foto, a partir del nombre científico."""
    base = slugify(nombre_cientifico) or "ave"
    candidato = f"{base}.jpg"
    if imagen_actual == f"img/aves/{candidato}":
        return candidato  # al editar, se reemplaza la propia foto
    contador = 2
    while (carpeta / candidato).exists():
        candidato = f"{base}-{contador}.jpg"
        contador += 1
    return candidato


def guardar_foto(archivo, nombre_cientifico, imagen_actual=""):
    """Guarda la foto subida en estaticos/img/aves y devuelve su ruta.

    La imagen se endereza según el EXIF, se reduce a un máximo de 1280 px de
    ancho y se guarda como JPG optimizado (así el carrusel carga rápido).
    """
    from PIL import Image, ImageOps

    carpeta = _carpeta_fotos()
    nombre = _nombre_archivo(nombre_cientifico, carpeta, imagen_actual)
    destino = carpeta / nombre

    imagen = Image.open(archivo)
    imagen = ImageOps.exif_transpose(imagen)
    if imagen.mode in ("RGBA", "LA", "P"):
        imagen = imagen.convert("RGBA")
        fondo = Image.new("RGB", imagen.size, (255, 255, 255))
        fondo.paste(imagen, mask=imagen.split()[-1])
        imagen = fondo
    else:
        imagen = imagen.convert("RGB")
    imagen.thumbnail((ANCHO_MAXIMO_FOTO, ANCHO_MAXIMO_FOTO), Image.LANCZOS)
    imagen.save(destino, "JPEG", quality=85, optimize=True)
    imagen.close()

    return f"img/aves/{nombre}"


class AveForm(forms.ModelForm):
    """Formulario para añadir o editar un ave del carrusel."""

    foto = forms.ImageField(
        label="Foto del ave",
        required=False,
        help_text="JPG o PNG de hasta 10 MB. Se ajusta sola al marco del carrusel.",
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
    )

    class Meta:
        model = Ave
        fields = ["nombre_comun", "nombre_cientifico", "descripcion", "orden", "activo"]
        widgets = {
            "descripcion": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Dónde vive, cómo es, por qué es especial…",
                }
            ),
            "nombre_comun": forms.TextInput(attrs={"placeholder": "Ej.: Mirla lugubris"}),
            "nombre_cientifico": forms.TextInput(attrs={"placeholder": "Ej.: Turdus fuscater"}),
        }
        help_texts = {
            "nombre_cientifico": "No puede repetirse: identifica el ave en la base de datos.",
            "orden": "Número más bajo = aparece primero en el carrusel.",
            "activo": "Si lo desmarcas, el ave se guarda pero no se muestra en la portada.",
        }

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and foto.size > TAMANO_MAXIMO_FOTO:
            raise forms.ValidationError("La foto no puede pesar más de 10 MB.")
        return foto

    def clean(self):
        datos = super().clean()
        if not self.instance.pk and not datos.get("foto"):
            self.add_error("foto", "Sube una foto para el carrusel.")
        return datos

    def save(self, commit=True):
        ave = super().save(commit=False)
        foto = self.cleaned_data.get("foto")
        if foto:
            ave.imagen = guardar_foto(foto, ave.nombre_cientifico, ave.imagen)
        if commit:
            ave.save()
        return ave
