"""Página propia de cada parque: slug, eslogan, portada y carrusel de fotos."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contenido", "0002_lugarobservacion_seccion"),
    ]

    operations = [
        migrations.AddField(
            model_name="lugarobservacion",
            name="slug",
            field=models.SlugField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="lugarobservacion",
            name="eslogan",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Frase corta que aparece bajo el nombre en la página del parque.",
                max_length=200,
                verbose_name="eslogan",
            ),
        ),
        migrations.AddField(
            model_name="lugarobservacion",
            name="portada",
            field=models.ImageField(
                blank=True,
                help_text="Imagen grande de la página del parque (opcional).",
                null=True,
                upload_to="parques/portadas/",
                verbose_name="foto de portada",
            ),
        ),
        migrations.AddField(
            model_name="lugarobservacion",
            name="color_acento",
            field=models.CharField(
                default="#40916c",
                help_text="Color de la página del parque en formato hexadecimal, p. ej. #40916c.",
                max_length=7,
                verbose_name="color de acento",
            ),
        ),
        migrations.CreateModel(
            name="FotoParque",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(blank=True, default="", max_length=140, verbose_name="título")),
                ("descripcion", models.TextField(blank=True, default="", verbose_name="descripción")),
                ("imagen", models.ImageField(upload_to="parques/fotos/", verbose_name="foto")),
                ("orden", models.PositiveSmallIntegerField(default=0, verbose_name="orden de presentación")),
                ("activa", models.BooleanField(default=True, verbose_name="mostrar en el carrusel")),
                ("creada_en", models.DateTimeField(auto_now_add=True, verbose_name="creada en")),
                (
                    "lugar",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fotos",
                        to="contenido.lugarobservacion",
                        verbose_name="parque",
                    ),
                ),
            ],
            options={
                "verbose_name": "foto de parque",
                "verbose_name_plural": "fotos de parques",
                "ordering": ["orden", "id"],
            },
        ),
    ]
