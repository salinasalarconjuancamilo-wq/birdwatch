"""Carga los datos iniciales de BIRDWATCH: superusuario y aves del municipio."""
import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import Ave

ARCHIVO = Path(__file__).resolve().parents[2] / "data" / "aves.json"


class Command(BaseCommand):
    help = "Crea el superusuario inicial (user / 1234) y las aves representativas de San Antonio del Tequendama."

    def handle(self, *args, **options):
        usuario, creado = User.objects.get_or_create(
            username="user",
            defaults={
                "first_name": "Superusuario",
                "email": "user@birdwatch.local",
            },
        )
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.set_password("1234")
        usuario.save()
        if creado:
            self.stdout.write(self.style.SUCCESS("Superusuario 'user' creado (clave: 1234)."))
        else:
            self.stdout.write(self.style.SUCCESS("Superusuario 'user' actualizado (clave: 1234)."))

        datos = json.loads(ARCHIVO.read_text(encoding="utf-8"))
        for dato in datos:
            Ave.objects.update_or_create(
                nombre_cientifico=dato["nombre_cientifico"],
                defaults={
                    "nombre_comun": dato["nombre_comun"],
                    "descripcion": dato["descripcion"],
                    "imagen": dato["imagen"],
                    "orden": dato["orden"],
                },
            )
        self.stdout.write(self.style.SUCCESS(f"{len(datos)} aves cargadas en la base de datos."))
