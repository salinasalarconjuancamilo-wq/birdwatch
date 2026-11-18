from django.conf import settings
from django.db import models
from django.utils import timezone


class Ave(models.Model):
    """Ave representativa de San Antonio del Tequendama, Cundinamarca."""

    nombre_comun = models.CharField("nombre común", max_length=120)
    nombre_cientifico = models.CharField("nombre científico", max_length=120, unique=True)
    descripcion = models.TextField("descripción")
    imagen = models.CharField(
        "imagen",
        max_length=255,
        help_text="Ruta de la imagen dentro de los estáticos, p. ej. img/aves/condor-andino.jpg",
    )
    orden = models.PositiveSmallIntegerField("orden de presentación", default=0)
    activo = models.BooleanField("mostrar en el carrusel", default=True)

    class Meta:
        verbose_name = "ave"
        verbose_name_plural = "aves"
        ordering = ["orden", "nombre_comun"]

    def __str__(self):
        return f"{self.nombre_comun} ({self.nombre_cientifico})"


class Deteccion(models.Model):
    """Identificación de un ave por su canto, hecha con BirdNET por un usuario."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="detecciones",
        verbose_name="usuario",
    )
    especie_en = models.CharField("especie (inglés)", max_length=150)
    especie_es = models.CharField("especie (español)", max_length=150, blank=True, default="")
    nombre_cientifico = models.CharField("nombre científico", max_length=150, blank=True, default="")
    tipo_sonido = models.CharField("tipo de sonido", max_length=60, blank=True, default="")
    confianza = models.FloatField("confianza")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "detección"
        verbose_name_plural = "detecciones"
        ordering = ["-creado_en"]

    def __str__(self):
        nombre = self.especie_es or self.especie_en
        return f"{nombre} ({self.confianza:.0%}) por {self.usuario}"


class CodigoRecuperacion(models.Model):
    """Código temporal enviado por correo para restablecer una contraseña."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="codigos_recuperacion",
        verbose_name="usuario",
    )
    codigo = models.CharField("código", max_length=6)
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    usado_en = models.DateTimeField("usado en", null=True, blank=True)

    class Meta:
        verbose_name = "código de recuperación"
        verbose_name_plural = "códigos de recuperación"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Código para {self.usuario}"

    def vigente(self):
        minutos = getattr(settings, "CODIGO_RECUPERACION_MINUTOS", 15)
        return self.usado_en is None and (timezone.now() - self.creado_en).total_seconds() < minutos * 60

    @classmethod
    def crear(cls, usuario):
        """Invalida los códigos anteriores y devuelve uno nuevo de 6 dígitos."""
        import secrets

        cls.objects.filter(usuario=usuario, usado_en__isnull=True).update(usado_en=timezone.now())
        return cls.objects.create(usuario=usuario, codigo=f"{secrets.randbelow(1000000):06d}")
