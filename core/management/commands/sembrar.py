"""Carga los datos iniciales de BIRDWATCH: usuarios y aves del municipio."""
import json
import os
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import Ave

ARCHIVO = Path(__file__).resolve().parents[2] / "data" / "aves.json"


class Command(BaseCommand):
    help = "Crea el superusuario, un usuario de prueba y las aves representativas del municipio."

    def handle(self, *args, **options):
        clave_admin = os.environ.get("BIRDWATCH_ADMIN_PASSWORD", "1234")
        clave_usuario = os.environ.get("BIRDWATCH_USUARIO_PASSWORD", "clave1234")

        administrador, _ = User.objects.get_or_create(
            username="user",
            defaults={
                "first_name": "Superusuario",
                "email": "user@birdwatch.local",
            },
        )
        administrador.first_name = "Superusuario"
        administrador.email = "user@birdwatch.local"
        administrador.is_staff = True
        administrador.is_superuser = True
        administrador.set_password(clave_admin)
        administrador.save()
        self.stdout.write(self.style.SUCCESS("Superusuario listo (acceso por correo electrónico)."))

        observador, _ = User.objects.get_or_create(
            username="observador",
            defaults={
                "first_name": "Observador",
                "email": "observador@birdwatch.local",
            },
        )
        observador.first_name = "Observador"
        observador.email = "observador@birdwatch.local"
        observador.is_staff = False
        observador.is_superuser = False
        observador.set_password(clave_usuario)
        observador.save()
        self.stdout.write(self.style.SUCCESS("Usuario de prueba listo (acceso por correo electrónico)."))

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
