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
