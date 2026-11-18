"""Prepara PostgreSQL y los datos iniciales en un solo paso.

Uso:

    python manage.py preparar

Aplica las migraciones y siembra usuarios, aves, lugares, noticias y preguntas.
Es idempotente: se puede ejecutar varias veces sin duplicar datos.
"""
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import OperationalError, connection

AYUDA_POSTGRES = """
No se pudo conectar a PostgreSQL con la configuración actual.

1) Verifica que el servicio esté corriendo (Windows: servicio «postgresql-x64-18»).
2) Crea la base y el usuario una sola vez, desde psql como superusuario:

     CREATE ROLE birdwatch LOGIN PASSWORD 'birdwatch';
     CREATE DATABASE birdwatch OWNER birdwatch;

3) Si usas otros datos, define la variable DATABASE_URL antes de arrancar:

     set DATABASE_URL=postgres://usuario:clave@localhost:5432/birdwatch
"""


class Command(BaseCommand):
    help = "Crea las tablas en PostgreSQL y carga los datos iniciales de BirdWatch."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sin-datos",
            action="store_true",
            help="Solo aplica migraciones (no siembra usuarios ni contenido).",
        )

    def handle(self, *args, **options):
        motor = connection.settings_dict["ENGINE"].rsplit(".", 1)[-1]
        base = connection.settings_dict["NAME"]
        self.stdout.write(f"Base de datos: {motor} · {base}")

        try:
            connection.ensure_connection()
        except OperationalError as error:
            self.stderr.write(self.style.ERROR(str(error)))
            self.stderr.write(AYUDA_POSTGRES)
            raise SystemExit(1)

        self.stdout.write("Aplicando migraciones…")
        call_command("migrate", interactive=False, verbosity=1)

        if options["sin_datos"]:
            self.stdout.write(self.style.SUCCESS("Migraciones listas."))
            return

        self.stdout.write("Sembrando usuarios y aves del carrusel…")
        call_command("sembrar")

        fixture = Path(settings.BASE_DIR) / "aves" / "fixtures" / "datos_iniciales.json"
        if fixture.is_file():
            self.stdout.write("Cargando catálogo de aves…")
            call_command("loaddata", str(fixture))

        self.stdout.write("Sembrando comunidad, mapa y contenido…")
        call_command("sembrar_comunidad")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("BirdWatch quedó listo."))
        self.stdout.write("Inicia la aplicación con:")
        self.stdout.write("    python manage.py runserver")
        self.stdout.write("")
        self.stdout.write("Acceso del superadministrador:")
        self.stdout.write("    correo: user@birdwatch.local    contraseña: 1234")
