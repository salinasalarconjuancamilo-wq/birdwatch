"""Pruebas de regresión de los defectos del informe QA v4.0."""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .forms import AvistamientoForm, ComentarioForm, MAX_COMENTARIO
from .models import Avistamiento, Ave, Comentario, Validacion


class AvistamientoFormTests(TestCase):
    def setUp(self):
        self.ave = Ave.objects.create(nombre_comun="Colibrí inca")
        self.datos = {
            "ave": self.ave.pk,
            "fecha": timezone.localdate().isoformat(),
            "lugar": "Sendero El Roble",
            "zona": "Bosque altoandino",
            "latitud": "4.606944",
            "longitud": "-74.302778",
            "cantidad": 1,
        }

    def test_formulario_valido(self):
        self.assertTrue(AvistamientoForm(self.datos).is_valid())

    def test_fecha_futura_rechazada(self):
        datos = {**self.datos, "fecha": (timezone.localdate() + timedelta(days=1)).isoformat()}
        formulario = AvistamientoForm(datos)
        self.assertFalse(formulario.is_valid())
        self.assertIn("no puede ser futura", str(formulario.errors["fecha"]))

    def test_etiquetas_html_y_simbolos_rechazados(self):
        formulario = AvistamientoForm({
            **self.datos,
            "lugar": "<h1>Texto gigante</h1>",
            "notas": "!@#$%^&*()_+-=[]{}",
        })
        self.assertFalse(formulario.is_valid())
        self.assertIn("HTML", str(formulario.errors["lugar"]))
        self.assertIn("símbolos", str(formulario.errors["notas"]))

    def test_longitud_maxima_rechazada(self):
        formulario = AvistamientoForm({**self.datos, "lugar": "A" * 101, "notas": "B" * 1001})
        self.assertFalse(formulario.is_valid())
        self.assertIn("lugar", formulario.errors)
        self.assertIn("notas", formulario.errors)

    def test_geocerca_regional_rechaza_coordenadas_oceanicas(self):
        formulario = AvistamientoForm({**self.datos, "latitud": "3.000000", "longitud": "-1.000000"})
        self.assertFalse(formulario.is_valid())
        self.assertIn("fuera del área", str(formulario.non_field_errors()))

    def test_fecha_maxima_es_dinamica_en_el_widget(self):
        formulario = AvistamientoForm()
        self.assertEqual(
            formulario.fields["fecha"].widget.attrs["max"],
            timezone.localdate().isoformat(),
        )


class ComentarioTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="observador", email="observador@example.com", password="ClaveSegura123!"
        )
        self.ave = Ave.objects.create(nombre_comun="Buco común")
        self.avistamiento = Avistamiento.objects.create(
            ave=self.ave,
            usuario=self.usuario,
            fecha=timezone.localdate(),
            lugar="Sendero El Roble",
            aprobado=True,
        )
        self.client.force_login(self.usuario)
        self.url = f"/avistamientos/{self.avistamiento.pk}/comentar/"

    def test_formulario_limita_el_comentario(self):
        self.assertTrue(ComentarioForm({"texto": "A" * MAX_COMENTARIO}).is_valid())
        self.assertFalse(ComentarioForm({"texto": "A" * (MAX_COMENTARIO + 1)}).is_valid())

    def test_carga_masiva_no_rompe_la_aplicacion(self):
        respuesta = self.client.post(self.url, {"texto": "x" * (settings.DATA_UPLOAD_MAX_MEMORY_SIZE + 100)})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Comentario.objects.count(), 0)
        detalle = self.client.get(f"/avistamientos/{self.avistamiento.pk}/")
        self.assertContains(detalle, "El comentario es demasiado grande")

    def test_comentario_largo_se_guarda_y_se_escape(self):
        respuesta = self.client.post(self.url, {"texto": "<script>alert('QA')</script>"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Comentario.objects.count(), 1)
        detalle = self.client.get(f"/avistamientos/{self.avistamiento.pk}/")
        self.assertContains(detalle, "&lt;script&gt;", html=False)
        self.assertNotContains(detalle, "<script>alert('QA')</script>", html=False)


class ValidacionComunitariaTests(TestCase):
    def setUp(self):
        self.autor = get_user_model().objects.create_user(
            username="autor", email="autor@example.com", password="ClaveSegura123!"
        )
        self.otro = get_user_model().objects.create_user(
            username="otro", email="otro@example.com", password="ClaveSegura123!"
        )
        self.ave = Ave.objects.create(nombre_comun="Turpial")
        self.avistamiento = Avistamiento.objects.create(
            ave=self.ave,
            usuario=self.autor,
            fecha=timezone.localdate(),
            lugar="Campus SENA",
            aprobado=True,
        )
        self.url = f"/avistamientos/{self.avistamiento.pk}/validar/"

    def test_el_autor_no_puede_validar_su_propio_registro(self):
        self.client.force_login(self.autor)
        respuesta = self.client.post(self.url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Validacion.objects.count(), 0)
        detalle = self.client.get(f"/avistamientos/{self.avistamiento.pk}/")
        self.assertNotContains(detalle, "Validar información")

    def test_otro_usuario_si_puede_validar(self):
        self.client.force_login(self.otro)
        respuesta = self.client.post(self.url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Validacion.objects.count(), 1)
        detalle = self.client.get(f"/avistamientos/{self.avistamiento.pk}/")
        self.assertContains(detalle, "Validado por ti")
