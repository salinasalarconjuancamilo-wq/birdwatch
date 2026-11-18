"""Modelos de contenido dinámico: noticias, preguntas frecuentes y contacto."""
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Noticia(models.Model):
    """Novedad del proyecto o del parque, mostrada en la portada."""

    titulo = models.CharField("título", max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    resumen = models.TextField("resumen", blank=True, default="")
    contenido = models.TextField("contenido")
    imagen = models.ImageField("imagen", upload_to="noticias/", blank=True, null=True)
    publicada = models.BooleanField("publicada", default=True)
    destacada = models.BooleanField("destacada en la portada", default=False)
    publicada_en = models.DateTimeField("fecha de publicación", default=timezone.now)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "noticia"
        verbose_name_plural = "noticias"
        ordering = ["-destacada", "-publicada_en"]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo) or "noticia"
            slug = base
            numero = 2
            while Noticia.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{numero}"
                numero += 1
            self.slug = slug
        super().save(*args, **kwargs)


class PreguntaFrecuente(models.Model):
    """Pregunta del centro de ayuda."""

    pregunta = models.CharField(max_length=250)
    respuesta = models.TextField()
    orden = models.PositiveSmallIntegerField("orden", default=0)
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "pregunta frecuente"
        verbose_name_plural = "preguntas frecuentes"
        ordering = ["orden", "id"]

    def __str__(self):
        return self.pregunta


class MensajeContacto(models.Model):
    """Mensaje enviado por el formulario de contacto."""

    nombre = models.CharField(max_length=120)
    correo = models.EmailField("correo electrónico")
    asunto = models.CharField(max_length=180, blank=True, default="")
    mensaje = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)
    respondido = models.BooleanField(default=False)

    class Meta:
        verbose_name = "mensaje de contacto"
        verbose_name_plural = "mensajes de contacto"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.nombre} — {self.asunto or self.correo}"


class LugarObservacion(models.Model):
    """Lugar de interés para observar aves, mostrado en el mapa."""

    TIPOS = [
        ("parque", "Parque natural"),
        ("zoologico", "Zoológico"),
        ("reserva", "Reserva natural"),
        ("otro", "Otro lugar"),
    ]

    nombre = models.CharField(max_length=180)
    tipo = models.CharField(max_length=20, choices=TIPOS, default="parque")
    ubicacion = models.CharField(
        "ubicación",
        max_length=180,
        help_text="Texto visible para los visitantes, p. ej. «Soacha, Cundinamarca».",
    )
    descripcion = models.TextField(blank=True, default="")
    latitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Dejar en blanco si la ubicación está por definir; el lugar no se dibujará en el mapa.",
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Dejar en blanco si la ubicación está por definir.",
    )
    orden = models.PositiveSmallIntegerField("orden de presentación", default=0)
    activo = models.BooleanField("mostrar en el mapa", default=True)

    class Meta:
        verbose_name = "lugar de observación"
        verbose_name_plural = "lugares de observación"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return f"{self.nombre} — {self.ubicacion}"

    @property
    def tiene_coordenadas(self):
        return self.latitud is not None and self.longitud is not None

    def datos_mapa(self):
        """Dict serializable para Leaflet; sin coordenadas si están por definir."""
        return {
            "id": self.pk,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "tipo_texto": self.get_tipo_display(),
            "ubicacion": self.ubicacion,
            "descripcion": self.descripcion,
            "latitud": float(self.latitud) if self.tiene_coordenadas else None,
            "longitud": float(self.longitud) if self.tiene_coordenadas else None,
        }


class Seccion(models.Model):
    """Sección activable del sitio (estadísticas, noticias, aliado, etc.)."""

    CLAVES = [
        ("estadisticas", "Tu comunidad en números"),
        ("noticias", "Noticias y novedades"),
        ("aliado", "Aliado de Colombia — Red de Observadores"),
        ("mapa", "Mapa de lugares"),
        ("ayuda", "Centro de ayuda"),
    ]

    clave = models.SlugField(unique=True, help_text="Identificador usado por el sitio, p. ej. «noticias».")
    nombre = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True, default="")
    activa = models.BooleanField(default=False)

    class Meta:
        verbose_name = "sección"
        verbose_name_plural = "secciones"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({'activa' if self.activa else 'inactiva'})"

    @classmethod
    def activas(cls):
        return {s.clave: s for s in cls.objects.filter(activa=True)}


def secciones_activas():
    """Devuelve las secciones publicadas; tolera una base recién clonada."""
    try:
        return Seccion.activas()
    except Exception:  # tabla aún no migrada o base no disponible
        return {}
