"""Rellena el slug de los parques existentes y lo hace único."""
from django.db import migrations, models
from django.utils.text import slugify


def poblar_slugs(apps, schema_editor):
    LugarObservacion = apps.get_model("contenido", "LugarObservacion")
    usados = set()
    for lugar in LugarObservacion.objects.all().order_by("pk"):
        base = slugify(lugar.nombre) or "parque"
        slug = base
        numero = 2
        while slug in usados or LugarObservacion.objects.filter(slug=slug).exclude(pk=lugar.pk).exists():
            slug = f"{base}-{numero}"
            numero += 1
        usados.add(slug)
        LugarObservacion.objects.filter(pk=lugar.pk).update(slug=slug)


class Migration(migrations.Migration):

    dependencies = [
        ("contenido", "0003_lugarobservacion_pagina_fotos"),
    ]

    operations = [
        migrations.RunPython(poblar_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="lugarobservacion",
            name="slug",
            field=models.SlugField(
                blank=True,
                help_text="Dirección de la página del parque: /parques/<slug>/",
                max_length=200,
                unique=True,
            ),
        ),
    ]
