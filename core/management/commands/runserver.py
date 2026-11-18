"""``runserver`` que también inicia el analizador BirdNET.

Con esto basta un solo comando para tener la aplicación completa:

    python manage.py runserver

- Django queda en http://localhost:3000
- BirdNET queda en http://127.0.0.1:8080 (se inicia solo, si no estaba activo)

Para usar solo la web (sin analizador):

    python manage.py runserver --sin-birdnet
    # o: set BIRDWATCH_SIN_BIRDNET=1
"""
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import (
    Command as RunserverCommand,
)

HOST_BIRDNET = "127.0.0.1"
PUERTO_BIRDNET = 8080


def _puerto_abierto(host, puerto, tiempo=0.4):
    """True si algo ya está escuchando en host:puerto."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conexion:
        conexion.settimeout(tiempo)
        return conexion.connect_ex((host, puerto)) == 0


class Command(RunserverCommand):
    help = "Inicia Django y, si hace falta, el analizador BirdNET (puerto 8080)."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--sin-birdnet",
            action="store_true",
            help="No inicia el analizador BirdNET (solo la web).",
        )

    def handle(self, *args, **options):
        self.sin_birdnet = (
            options.pop("sin_birdnet", False)
            or os.environ.get("BIRDWATCH_SIN_BIRDNET", "") == "1"
        )
        self._proceso_birdnet = None
        self._registro = None

        # Por comodidad, el puerto por defecto es el 3000 (el de la documentación).
        if not options.get("addrport"):
            options["addrport"] = "0.0.0.0:3000"

        # Con el recargador automático, solo el proceso padre arranca BirdNET.
        if os.environ.get("RUN_MAIN") != "true":
            self._iniciar_birdnet()

        try:
            super().handle(*args, **options)
        finally:
            self._detener_birdnet()

    # ------------------------------------------------------------- BirdNET

    def _iniciar_birdnet(self):
        if self.sin_birdnet:
            self.stdout.write("BirdNET desactivado (--sin-birdnet).")
            return
        if _puerto_abierto(HOST_BIRDNET, PUERTO_BIRDNET):
            self.stdout.write(
                self.style.SUCCESS(
                    f"BirdNET ya está activo en http://{HOST_BIRDNET}:{PUERTO_BIRDNET}"
                )
            )
            return

        script = Path(settings.BASE_DIR) / "servidor_birdnet.py"
        if not script.is_file():
            self.stderr.write(
                "No se encontró servidor_birdnet.py; la web arranca sin analizador."
            )
            return

        carpeta_subidas = Path(tempfile.gettempdir()) / "birdwatch-subidas"
        carpeta_subidas.mkdir(parents=True, exist_ok=True)
        ruta_registro = Path(tempfile.gettempdir()) / "birdwatch-birdnet.log"
        self._registro = ruta_registro.open("a", encoding="utf-8", errors="replace")

        entorno = os.environ.copy()
        entorno.setdefault("PYTHONIOENCODING", "utf-8")
        comando = [
            sys.executable,
            str(script),
            "--host", HOST_BIRDNET,
            "--port", str(PUERTO_BIRDNET),
            "--spath", str(carpeta_subidas),
        ]
        try:
            self._proceso_birdnet = subprocess.Popen(
                comando,
                cwd=str(settings.BASE_DIR),
                stdout=self._registro,
                stderr=subprocess.STDOUT,
                env=entorno,
            )
        except OSError as error:
            self.stderr.write(f"No se pudo iniciar BirdNET: {error}")
            self._registro.close()
            self._registro = None
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"BirdNET iniciado (PID {self._proceso_birdnet.pid}); "
                f"tarda unos segundos en cargar el modelo."
            )
        )
        self.stdout.write(f"  Registro: {ruta_registro}")

    def _detener_birdnet(self):
        if self._proceso_birdnet and self._proceso_birdnet.poll() is None:
            self._proceso_birdnet.terminate()
            try:
                self._proceso_birdnet.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self._proceso_birdnet.kill()
        if self._registro:
            self._registro.close()
            self._registro = None
