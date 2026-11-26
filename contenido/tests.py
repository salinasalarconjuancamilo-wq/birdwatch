"""Pruebas de regresión del panel de carrusel de parques."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import FotoParque, LugarObservacion


class EliminarParqueTests(TestCase):
    def setUp(self):
        self.superusuario = get_user_model().objects.create_superuser(
            username="admin-carrusel",
            email="admin@example.com",
            password="ClaveSegura123!",
        )
        self.parque = LugarObservacion.objects.create(
            nombre="Parque de pruebas",
            slug="parque-de-pruebas",
            ubicacion="Soacha, Cundinamarca",
        )

    def test_boton_eliminar_parque_aparece_en_el_carrusel(self):
        self.client.force_login(self.superusuario)
        respuesta = self.client.get(reverse("parques_admin"))
        self.assertContains(respuesta, "Eliminar parque")
        self.assertContains(
            respuesta,
            reverse("lugar_eliminar", args=[self.parque.pk]),
        )

    def test_boton_eliminar_parque_aparece_en_las_fotos(self):
        self.client.force_login(self.superusuario)
        respuesta = self.client.get(reverse("parque_fotos", args=[self.parque.pk]))
        self.assertContains(respuesta, "Eliminar parque")

    def test_eliminar_parque_desde_el_carrusel(self):
        self.client.force_login(self.superusuario)
        foto = FotoParque.objects.create(lugar=self.parque, titulo="Sendero")
        respuesta = self.client.post(
            reverse("lugar_eliminar", args=[self.parque.pk]),
            {"volver": "parques_admin"},
        )
        self.assertRedirects(respuesta, reverse("parques_admin"))
        self.assertFalse(LugarObservacion.objects.filter(pk=self.parque.pk).exists())
        self.assertFalse(FotoParque.objects.filter(pk=foto.pk).exists())

    def test_eliminar_parque_vuelve_al_panel_de_contenido_por_defecto(self):
        self.client.force_login(self.superusuario)
        respuesta = self.client.post(reverse("lugar_eliminar", args=[self.parque.pk]))
        self.assertRedirects(respuesta, reverse("contenido_admin"))

    def test_visitante_no_puede_eliminar_parque(self):
        respuesta = self.client.post(reverse("lugar_eliminar", args=[self.parque.pk]))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("entrar"), respuesta["Location"])
        self.assertTrue(LugarObservacion.objects.filter(pk=self.parque.pk).exists())
