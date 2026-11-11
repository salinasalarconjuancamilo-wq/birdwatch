from django.db import models


class Ave(models.Model):
    """Catálogo de aves que se pueden observar."""
    nombre_comun = models.CharField(max_length=100, unique=True)
    nombre_cientifico = models.CharField(max_length=100, blank=True, default="")
    familia = models.CharField(max_length=100, blank=True, default="")
    color = models.CharField(max_length=100, blank=True, default="")
    tamano = models.CharField(max_length=50, blank=True, default="")
    foto_url = models.URLField(blank=True, default="")

    def __str__(self):
        return f"{self.nombre_comun} ({self.nombre_cientifico})" if self.nombre_cientifico else self.nombre_comun


class Avistamiento(models.Model):
    """Registro de un avistamiento de un ave en un lugar y fecha."""
    ave = models.ForeignKey(Ave, on_delete=models.CASCADE, related_name="avistamientos")
    fecha = models.DateField()
    lugar = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField(default=1)
    notas = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.cantidad} {self.ave.nombre_comun} en {self.lugar} el {self.fecha}"
