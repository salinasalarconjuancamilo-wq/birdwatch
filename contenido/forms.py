"""Formularios de contenido dinámico."""
from io import BytesIO

from django import forms
from django.core.files.base import ContentFile

from .models import FotoParque, LugarObservacion, MensajeContacto, Noticia, Seccion

ANCHO_MAXIMO_FOTO = 1600  # píxeles; suficiente para portadas y carrusel


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


def optimizar_foto(archivo, ancho=ANCHO_MAXIMO_FOTO, calidad=85):
    """Endereza, reduce y comprime una foto subida (JPG optimizado)."""
    if not archivo:
        return archivo
    from PIL import Image, ImageOps

    try:
        imagen = Image.open(archivo)
    except Exception:
        return archivo

    imagen = ImageOps.exif_transpose(imagen)
    if imagen.mode in ("RGBA", "LA", "P"):
        imagen = imagen.convert("RGBA")
        fondo = Image.new("RGB", imagen.size, (255, 255, 255))
        fondo.paste(imagen, mask=imagen.split()[-1])
        imagen = fondo
    else:
        imagen = imagen.convert("RGB")
    imagen.thumbnail((ancho, ancho), Image.LANCZOS)

    bufer = BytesIO()
    imagen.save(bufer, "JPEG", quality=calidad, optimize=True)
    imagen.close()
    nombre = (getattr(archivo, "name", "") or "foto.jpg").rsplit(".", 1)[0] + ".jpg"
    return ContentFile(bufer.getvalue(), name=nombre)


class LugarForm(forms.ModelForm):
    """Alta y edición de parques: datos, portada y color de su página."""

    class Meta:
        model = LugarObservacion
        fields = [
            "nombre", "slug", "tipo", "ubicacion", "eslogan", "descripcion",
            "portada", "color_acento", "latitud", "longitud", "orden", "activo",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "eslogan": forms.TextInput(attrs={"placeholder": "Ej.: Donde el bosque canta"}),
            "ubicacion": forms.TextInput(attrs={"placeholder": "Soacha, Cundinamarca"}),
            "color_acento": forms.TextInput(attrs={"type": "color"}),
            "portada": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
        help_texts = {
            "slug": "Se genera solo desde el nombre; puedes cambiarlo. Queda en /parques/<slug>/.",
            "latitud": "Deja ambos campos en blanco si la ubicación está por definir.",
            "portada": "Opcional: si no subes una, se usa la primera foto del carrusel.",
        }

    def save(self, commit=True):
        lugar = super().save(commit=False)
        if "portada" in self.files and self.files.get("portada"):
            lugar.portada = optimizar_foto(self.files["portada"])
        if commit:
            lugar.save()
        return lugar


class FotoParqueForm(forms.ModelForm):
    """Alta y edición de una foto del carrusel de un parque."""

    class Meta:
        model = FotoParque
        fields = ["imagen", "titulo", "descripcion", "orden", "activa"]
        widgets = {
            "imagen": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "titulo": forms.TextInput(attrs={"placeholder": "Ej.: Sendero del bosque de niebla"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "imagen": "JPG o PNG de hasta 10 MB. Se reduce sola para que la página cargue rápido.",
            "orden": "Número más bajo = aparece primero en el carrusel.",
            "activa": "Si la desmarcas, se guarda pero no se muestra en la página del parque.",
        }

    def clean_imagen(self):
        imagen = self.cleaned_data.get("imagen")
        if imagen and getattr(imagen, "size", 0) > 10 * 1024 * 1024:
            raise forms.ValidationError("La foto no puede pesar más de 10 MB.")
        return imagen

    def clean(self):
        datos = super().clean()
        if not self.instance.pk and not datos.get("imagen"):
            self.add_error("imagen", "Sube una foto para el carrusel del parque.")
        return datos

    def save(self, commit=True):
        foto = super().save(commit=False)
        if "imagen" in self.files and self.files.get("imagen"):
            foto.imagen = optimizar_foto(self.files["imagen"])
        if commit:
            foto.save()
        return foto


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
