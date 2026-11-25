"""Pruebas del control de intentos de inicio de sesión."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import ControlAcceso


class BloqueoAccesoTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="prueba",
            first_name="Prueba",
            email="prueba@birdwatch.local",
            password="ClaveSegura123!",
        )
        self.datos = {"correo": self.usuario.email}

    def _intentar(self, contrasena):
        return self.client.post("/entrar/", {**self.datos, "contrasena": contrasena})

    def _errores(self, respuesta):
        return " ".join(respuesta.context["form"].non_field_errors())

    def test_tres_fallos_bloquean_la_cuenta(self):
        self.assertIn("Te quedan 2 intentos", self._errores(self._intentar("mala1")))
        self.assertIn("Te queda 1 intento", self._errores(self._intentar("mala2")))
        respuesta = self._intentar("mala3")
        self.assertIn("bloqueada durante 15 minutos", self._errores(respuesta))

        control = ControlAcceso.objects.get(usuario=self.usuario)
        self.assertEqual(control.intentos_fallidos, 3)
        self.assertIsNotNone(control.bloqueado_hasta)
        self.assertTrue(control.esta_bloqueado())

        # Ni la contraseña correcta permite entrar mientras esté bloqueada.
        self.assertIn("bloqueada temporalmente", self._errores(self._intentar("ClaveSegura123!")))

    def test_el_bloqueo_vence_y_la_clave_correcta_entra(self):
        for intento in range(3):
            self._intentar(f"mala{intento}")
        control = ControlAcceso.objects.get(usuario=self.usuario)
        control.bloqueado_hasta = timezone.now() - timedelta(minutes=1)
        control.save(update_fields=["bloqueado_hasta"])

        respuesta = self._intentar("ClaveSegura123!")
        self.assertEqual(respuesta.status_code, 302)
        control.refresh_from_db()
        self.assertEqual(control.intentos_fallidos, 0)
        self.assertIsNone(control.bloqueado_hasta)

    def test_un_acierto_reinicia_los_intentos(self):
        self._intentar("mala1")
        self._intentar("mala2")
        respuesta = self._intentar("ClaveSegura123!")
        self.assertEqual(respuesta.status_code, 302)

        control = ControlAcceso.objects.get(usuario=self.usuario)
        self.assertEqual(control.intentos_fallidos, 0)
        self.assertIsNone(control.bloqueado_hasta)


class CuentaTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="maria-jose",
            first_name="María José",
            email="maria@example.com",
            password="ClaveSegura123!",
        )
        self.client.force_login(self.usuario)

    def test_registro_usa_nombre_como_username(self):
        self.client.logout()
        respuesta = self.client.post(
            "/registrarse/",
            {
                "nombre": "Juan Pérez",
                "correo": "juan@example.com",
                "contrasena1": "ClaveSegura123!",
                "contrasena2": "ClaveSegura123!",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        creado = get_user_model().objects.get(email="juan@example.com")
        self.assertEqual(creado.username, "juan-perez")
        self.assertEqual(creado.first_name, "Juan Pérez")

    def test_username_unico_para_nombres_repetidos(self):
        get_user_model().objects.create_user(
            username="juan-perez",
            first_name="Juan Pérez",
            email="otro@example.com",
            password="ClaveSegura123!",
        )
        self.client.logout()
        self.client.post(
            "/registrarse/",
            {
                "nombre": "Juan Pérez",
                "correo": "juan2@example.com",
                "contrasena1": "ClaveSegura123!",
                "contrasena2": "ClaveSegura123!",
            },
        )
        self.assertEqual(
            get_user_model().objects.get(email="juan2@example.com").username,
            "juan-perez-2",
        )

    def test_cambiar_correo_y_nombre_actualiza_username(self):
        respuesta = self.client.post(
            "/cuenta/",
            {
                "nombre": "Ana María",
                "correo": "nueva@example.com",
                "contrasena_actual": "ClaveSegura123!",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "nueva@example.com")
        self.assertEqual(self.usuario.first_name, "Ana María")
        self.assertEqual(self.usuario.username, "ana-maria")

        self.client.logout()
        entrada = self.client.post(
            "/entrar/", {"correo": "nueva@example.com", "contrasena": "ClaveSegura123!"}
        )
        self.assertEqual(entrada.status_code, 302)

    def test_cambiar_correo_requiere_clave_actual_correcta(self):
        respuesta = self.client.post(
            "/cuenta/",
            {
                "nombre": "María José",
                "correo": "nueva@example.com",
                "contrasena_actual": "incorrecta",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("La contraseña actual no es correcta.", respuesta.content.decode())
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "maria@example.com")
