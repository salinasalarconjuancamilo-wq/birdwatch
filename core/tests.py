"""Pruebas del control de intentos de inicio de sesión."""
import io
import re
from contextlib import redirect_stdout
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import CodigoRecuperacion, ControlAcceso
from .usuarios import username_desde_nombre


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


class ValidacionCuentaTests(TestCase):
    """BUG-11 y BUG-12: dominios enrutables y nombres no reservados."""

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="maria-jose",
            first_name="María José",
            email="maria@example.com",
            password="ClaveSegura123!",
        )
        self.client.force_login(self.usuario)

    def _cambiar(self, nombre="María José", correo="nueva@example.com"):
        return self.client.post(
            "/cuenta/",
            {
                "nombre": nombre,
                "correo": correo,
                "contrasena_actual": "ClaveSegura123!",
            },
        )

    def test_correo_localhost_rechazado(self):
        respuesta = self._cambiar(correo="test@localhost")
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "dominios locales o no enrutables")
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "maria@example.com")

    def test_correo_publico_aceptado(self):
        self.assertEqual(self._cambiar(correo="nueva@example.com").status_code, 302)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "nueva@example.com")

    def test_nombre_reservado_rechazado(self):
        respuesta = self._cambiar(nombre="admin")
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "reservado por el sistema")
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, "María José")
        self.assertEqual(self.usuario.username, "maria-jose")

    def test_username_generado_nunca_es_reservado(self):
        self.assertEqual(username_desde_nombre("Admin"), "observador-admin")
        self.assertEqual(username_desde_nombre("Administrador"), "observador-administrador")

    def test_registro_rechaza_nombre_reservado_y_correo_local(self):
        self.client.logout()
        respuesta = self.client.post(
            "/registrarse/",
            {
                "nombre": "Admin",
                "correo": "nuevo@localhost",
                "contrasena1": "ClaveSegura123!",
                "contrasena2": "ClaveSegura123!",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "reservado por el sistema")
        self.assertContains(respuesta, "dominios locales o no enrutables")
        self.assertFalse(get_user_model().objects.filter(email="nuevo@localhost").exists())

    @override_settings(DEBUG=False)
    def test_pagina_404_es_propia_y_sin_trazas(self):
        respuesta = self.client.get("/esta-pagina-no-existe/")
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, "Página no encontrada", status_code=404)
        self.assertNotContains(respuesta, "Traceback", status_code=404)


class RecuperarContrasenaTests(TestCase):
    """El flujo de recuperación funciona con correo real y sin SMTP."""

    LOCAL = "django.core.mail.backends.locmem.EmailBackend"
    CONSOLA = "django.core.mail.backends.console.EmailBackend"

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="recuperar",
            email="recuperar@example.com",
            password="ClaveAntigua123!",
        )
        mail.outbox = []

    def _codigo_del_correo(self):
        return re.search(r"\b(\d{6})\b", mail.outbox[0].body).group(1)

    @override_settings(EMAIL_BACKEND=LOCAL)
    def test_flujo_completo_cambia_la_clave_y_permite_entrar(self):
        respuesta = self.client.post("/recuperar/", {"correo": self.usuario.email})
        self.assertRedirects(respuesta, "/recuperar/verificar/")
        self.assertEqual(len(mail.outbox), 1)

        codigo = self._codigo_del_correo()
        respuesta = self.client.post(
            "/recuperar/verificar/", {"correo": self.usuario.email, "codigo": codigo}
        )
        self.assertRedirects(respuesta, "/recuperar/nueva-clave/")

        respuesta = self.client.post(
            "/recuperar/nueva-clave/",
            {"contrasena1": "ClaveNueva456!", "contrasena2": "ClaveNueva456!"},
        )
        self.assertRedirects(respuesta, "/entrar/")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("ClaveNueva456!"))
        self.assertEqual(
            self.client.post(
                "/entrar/",
                {"correo": self.usuario.email, "contrasena": "ClaveNueva456!"},
            ).status_code,
            302,
        )

    @override_settings(EMAIL_BACKEND=LOCAL)
    def test_codigo_incorrecto_no_permite_cambiar_la_clave(self):
        self.client.post("/recuperar/", {"correo": self.usuario.email})
        respuesta = self.client.post(
            "/recuperar/verificar/", {"correo": self.usuario.email, "codigo": "000000"}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "El código no es válido o ya venció")
        self.assertNotIn("recuperar_usuario_id", self.client.session)

    @override_settings(EMAIL_BACKEND=LOCAL)
    def test_codigo_ya_usado_no_se_puede_reutilizar(self):
        self.client.post("/recuperar/", {"correo": self.usuario.email})
        codigo = self._codigo_del_correo()
        self.client.post(
            "/recuperar/verificar/", {"correo": self.usuario.email, "codigo": codigo}
        )
        self.client.post(
            "/recuperar/nueva-clave/",
            {"contrasena1": "ClaveNueva456!", "contrasena2": "ClaveNueva456!"},
        )
        respuesta = self.client.post(
            "/recuperar/verificar/", {"correo": self.usuario.email, "codigo": codigo}
        )
        self.assertContains(respuesta, "El código no es válido o ya venció")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("ClaveNueva456!"))

    @override_settings(EMAIL_BACKEND=CONSOLA, DEBUG=False)
    def test_sin_smtp_el_codigo_se_muestra_en_la_pagina(self):
        with redirect_stdout(io.StringIO()):
            respuesta = self.client.post("/recuperar/", {"correo": self.usuario.email})
        self.assertRedirects(respuesta, "/recuperar/verificar/")
        pagina = self.client.get("/recuperar/verificar/")
        codigo = self.client.session["recuperar_codigo_local"]
        self.assertContains(pagina, "Modo local")
        self.assertContains(pagina, codigo)

        respuesta = self.client.post(
            "/recuperar/verificar/", {"correo": self.usuario.email, "codigo": codigo}
        )
        self.assertRedirects(respuesta, "/recuperar/nueva-clave/")
        self.assertNotIn("recuperar_codigo_local", self.client.session)

    @override_settings(EMAIL_BACKEND=LOCAL)
    def test_correo_desconocido_no_revela_si_esta_registrado(self):
        respuesta = self.client.post("/recuperar/", {"correo": "nadie@example.com"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta["Location"], "/recuperar/verificar/")
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(
            self.client.get("/recuperar/verificar/"),
            "Si el correo está registrado",
        )
        self.assertFalse(CodigoRecuperacion.objects.exists())

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        DEBUG=False,
        EMAIL_HOST="localhost",
        EMAIL_PORT=1,
    )
    def test_fallo_smtp_no_envia_a_la_pantalla_de_verificacion(self):
        respuesta = self.client.post("/recuperar/", {"correo": self.usuario.email})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "No se pudo enviar el correo")
        self.assertNotIn("recuperar_correo", self.client.session)
