"""Formularios del carrusel y del acceso a BirdWatch."""
from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.text import slugify

from .models import Ave
from .usuarios import username_desde_nombre

# Formatos y tamaño máximo aceptados para las fotos del carrusel.
TAMANO_MAXIMO_FOTO = 10 * 1024 * 1024  # 10 MB
ANCHO_MAXIMO_FOTO = 1280  # píxeles; suficiente para la tarjeta y liviano


def validar_nombre(valor):
    """Nombre de 2 a 50 letras (con acentos, ñ y espacios)."""
    nombre = valor.strip()
    if not nombre.replace(" ", "").isalpha():
        raise ValidationError(
            "El nombre solo puede contener letras y espacios; no se permiten números ni caracteres especiales."
        )
    return nombre


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


# ------------------------------------------------------------------- Acceso


class IngresoForm(forms.Form):
    """Ingreso con correo electrónico (admite el usuario antiguo por compatibilidad)."""

    correo = forms.CharField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "tu@correo.com", "autocomplete": "email"}),
    )
    contrasena = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    siguiente = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_correo(self):
        valor = self.cleaned_data["correo"].strip()
        if "@" in valor:
            try:
                validate_email(valor)
            except ValidationError:
                raise ValidationError("Escribe un correo electrónico válido.")
        return valor


class RegistroForm(forms.Form):
    """Creación de una cuenta de Usuario (nunca administrador)."""

    nombre = forms.CharField(
        label="Nombre",
        max_length=50,
        min_length=2,
        required=True,
        error_messages={
            "required": "Escribe tu nombre.",
            "min_length": "El nombre debe tener al menos 2 letras.",
            "max_length": "El nombre no puede tener más de 50 caracteres.",
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej.: María José",
                "autocomplete": "given-name",
                "minlength": "2",
                "pattern": r"[A-Za-záéíóúüñÁÉÍÓÚÜÑ ]+",
                "title": "Solo letras y espacios; mínimo 2 caracteres.",
            }
        ),
    )
    correo = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "tu@correo.com", "autocomplete": "email"}),
    )
    contrasena1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    contrasena2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_nombre(self):
        # isalpha() acepta letras con acentos y ñ; se permiten espacios entre palabras.
        return validar_nombre(self.cleaned_data["nombre"])

    def clean_correo(self):
        correo = self.cleaned_data["correo"].strip().lower()
        usuarios = get_user_model().objects
        if usuarios.filter(email__iexact=correo).exists() or usuarios.filter(username__iexact=correo).exists():
            raise ValidationError("Ya existe una cuenta con ese correo electrónico. Inicia sesión.")
        if len(correo) > 150:
            raise ValidationError("El correo electrónico es demasiado largo.")
        return correo

    def clean(self):
        datos = super().clean()
        clave = datos.get("contrasena1")
        if clave and clave != datos.get("contrasena2"):
            self.add_error("contrasena2", "Las contraseñas no coinciden.")
        if clave:
            nombre = datos.get("nombre", "")
            candidato = get_user_model()(
                username=username_desde_nombre(nombre), email=datos.get("correo", ""),
                first_name=nombre,
            )
            try:
                validate_password(clave, user=candidato)
            except ValidationError as errores:
                self.add_error("contrasena1", errores.messages[0])
        return datos


# ------------------------------------------------------------------- Mi cuenta


class CuentaForm(forms.Form):
    """Editar nombre y correo; el username se recalcula desde el nombre."""

    nombre = forms.CharField(
        label="Nombre",
        max_length=50,
        min_length=2,
        required=True,
        error_messages={
            "required": "Escribe tu nombre.",
            "min_length": "El nombre debe tener al menos 2 letras.",
            "max_length": "El nombre no puede tener más de 50 caracteres.",
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej.: María José",
                "autocomplete": "given-name",
                "minlength": "2",
                "pattern": r"[A-Za-záéíóúüñÁÉÍÓÚÜÑ ]+",
                "title": "Solo letras y espacios; mínimo 2 caracteres.",
            }
        ),
    )
    correo = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "tu@correo.com", "autocomplete": "email"}),
    )
    contrasena_actual = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
        error_messages={"required": "Escribe tu contraseña actual para confirmar el cambio."},
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        if usuario is not None:
            self.fields["nombre"].initial = usuario.first_name
            self.fields["correo"].initial = usuario.email

    def clean_nombre(self):
        return validar_nombre(self.cleaned_data["nombre"])

    def clean_correo(self):
        correo = self.cleaned_data["correo"].strip().lower()
        if len(correo) > 150:
            raise ValidationError("El correo electrónico es demasiado largo.")
        consulta = get_user_model().objects.filter(email__iexact=correo)
        if self.usuario is not None:
            consulta = consulta.exclude(pk=self.usuario.pk)
        if consulta.exists():
            raise ValidationError("Ya existe una cuenta con ese correo electrónico.")
        return correo

    def clean(self):
        datos = super().clean()
        clave = datos.get("contrasena_actual")
        if self.usuario is not None and clave and not self.usuario.check_password(clave):
            self.add_error("contrasena_actual", "La contraseña actual no es correcta.")
        return datos

    def save(self):
        self.usuario.first_name = self.cleaned_data["nombre"]
        self.usuario.username = username_desde_nombre(
            self.cleaned_data["nombre"], excluir_pk=self.usuario.pk
        )
        self.usuario.email = self.cleaned_data["correo"]
        self.usuario.save(update_fields=["first_name", "username", "email"])
        return self.usuario


class RecuperarForm(forms.Form):
    """Solicita el código de verificación para un correo registrado."""

    correo = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "tu@correo.com", "autocomplete": "email"}),
    )


class VerificarCodigoForm(forms.Form):
    """Valida el código de 6 dígitos enviado al correo."""

    correo = forms.EmailField(label="Correo electrónico")
    codigo = forms.CharField(
        label="Código de verificación",
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={"placeholder": "000000", "inputmode": "numeric"}),
    )

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].strip()
        if not codigo.isdigit():
            raise ValidationError("El código debe tener 6 dígitos.")
        return codigo


class NuevaClaveForm(forms.Form):
    """Establece la nueva contraseña tras validar el código."""

    contrasena1 = forms.CharField(
        label="Nueva contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )
    contrasena2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean(self):
        datos = super().clean()
        clave = datos.get("contrasena1")
        if clave and clave != datos.get("contrasena2"):
            self.add_error("contrasena2", "Las contraseñas no coinciden.")
        if clave:
            usuario = getattr(self, "usuario", None)
            try:
                validate_password(clave, user=usuario)
            except ValidationError as errores:
                self.add_error("contrasena1", errores.messages[0])
        return datos
