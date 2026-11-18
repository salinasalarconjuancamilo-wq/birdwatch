"""Modelos del catálogo y de la comunidad de avistamientos.

Un *avistamiento* es la observación de un ave en un lugar y una fecha. Los
avistamientos pueden llevar coordenadas (para el mapa Leaflet), foto, notas y
un marcador de «caso especial». Un administrador aprueba el contenido antes de
que sea público; los usuarios pueden comentar y validar la información.
"""
from django.conf import settings
from django.db import models


ZONAS_PARQUE = [
    ("Bosque altoandino", "Bosque altoandino"),
    ("Salto del Tequendama", "Salto del Tequendama"),
    ("Humedal y laguna", "Humedal y laguna"),
    ("Sendero ecológico", "Sendero ecológico"),
    ("Zona de picnic", "Zona de picnic y campamento"),
    ("Campus SENA", "Campus SENA / centro de visitantes"),
]


class Ave(models.Model):
    """Catálogo de aves que se pueden observar."""

    nombre_comun = models.CharField("nombre común", max_length=100, unique=True)
    nombre_cientifico = models.CharField("nombre científico", max_length=100, blank=True, default="")
    familia = models.CharField(max_length=100, blank=True, default="")
    color = models.CharField(max_length=100, blank=True, default="")
    tamano = models.CharField("tamaño", max_length=50, blank=True, default="")
    foto_url = models.URLField("foto (URL)", blank=True, default="")
    descripcion = models.TextField("descripción", blank=True, default="")
    zona = models.CharField(
        "zona habitual", max_length=60, blank=True, default="", choices=ZONAS_PARQUE
    )

    class Meta:
        verbose_name = "ave del catálogo"
        verbose_name_plural = "aves del catálogo"
        ordering = ["nombre_comun"]

    def __str__(self):
        if self.nombre_cientifico:
            return f"{self.nombre_comun} ({self.nombre_cientifico})"
        return self.nombre_comun


class Avistamiento(models.Model):
    """Registro de un avistamiento reportado por un observador."""

    ave = models.ForeignKey(
        Ave,
        on_delete=models.CASCADE,
        related_name="avistamientos",
        verbose_name="especie",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avistamientos",
        verbose_name="registrado por",
    )
    fecha = models.DateField("fecha de la observación")
    lugar = models.CharField("lugar", max_length=120)
    zona = models.CharField("zona del parque", max_length=60, blank=True, default="", choices=ZONAS_PARQUE)
    latitud = models.DecimalField("latitud", max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField("longitud", max_digits=9, decimal_places=6, null=True, blank=True)
    cantidad = models.PositiveIntegerField("cantidad de aves", default=1)
    foto = models.ImageField("foto", upload_to="avistamientos/", blank=True, null=True)
    notas = models.TextField("notas", blank=True, default="")
    caso_especial = models.BooleanField(
        "caso especial",
        default=False,
        help_text="Marca avistamientos relevantes: especie rara, anidación, comportamiento inusual, etc.",
    )
    aprobado = models.BooleanField("aprobado por el administrador", default=False)
    creado_en = models.DateTimeField("registrado en", auto_now_add=True)

    class Meta:
        verbose_name = "avistamiento"
        verbose_name_plural = "avistamientos"
        ordering = ["-fecha", "-creado_en"]

    def __str__(self):
        return f"{self.cantidad} × {self.ave.nombre_comun} en {self.lugar} ({self.fecha})"

    @property
    def tiene_coordenadas(self):
        return self.latitud is not None and self.longitud is not None


class Comentario(models.Model):
    """Comentario de un usuario sobre un avistamiento."""

    avistamiento = models.ForeignKey(
        Avistamiento, on_delete=models.CASCADE, related_name="comentarios"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios"
    )
    texto = models.TextField("comentario")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "comentario"
        verbose_name_plural = "comentarios"
        ordering = ["creado_en"]

    def __str__(self):
        return f"{self.usuario}: {self.texto[:40]}"


class Validacion(models.Model):
    """Voto de un usuario que confirma que el avistamiento es fiable."""

    avistamiento = models.ForeignKey(
        Avistamiento, on_delete=models.CASCADE, related_name="validaciones"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="validaciones"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "validación"
        verbose_name_plural = "validaciones"
        ordering = ["-creado_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["avistamiento", "usuario"], name="validacion_unica_por_usuario"
            )
        ]

    def __str__(self):
        return f"{self.usuario} validó {self.avistamiento_id}"
