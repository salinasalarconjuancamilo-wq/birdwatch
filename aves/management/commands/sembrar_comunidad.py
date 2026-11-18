"""Siembra datos de ejemplo para la comunidad BirdWatch.

Uso: ``python manage.py sembrar_comunidad``

Crea especies, avistamientos con coordenadas (para el mapa), noticias y
preguntas frecuentes. Es idempotente: se puede ejecutar varias veces.
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from aves.models import Ave, Avistamiento
from contenido.models import Noticia, PreguntaFrecuente


ESPECIES = [
    ("Chinigüe (copetón)", "Zonotrichia capensis", "Passerellidae", "Bosque altoandino"),
    ("Buco común", "Chlorospingus flavopectus", "Passerellidae", "Bosque altoandino"),
    ("Caracara chimachima", "Milvago chimachima", "Falconidae", "Campus SENA"),
    ("Inca bronceado", "Coeligena coeligena", "Trochilidae", "Sendero ecológico"),
    ("Tucán piquiplano", "Andigena laminirostris", "Ramphastidae", "Bosque altoandino"),
    ("Candelita de frente dorada", "Myioborus ornatus", "Parulidae", "Sendero ecológico"),
    ("Tororoi coronirrufo", "Grallaria ruficapilla", "Grallariidae", "Bosque altoandino"),
    ("Pava andina", "Penelope montagnii", "Cracidae", "Bosque altoandino"),
    ("Chisga morada", "Colibri coruscans", "Trochilidae", "Zona de picnic"),
    ("Garza del ganado", "Bubulcus ibis", "Ardeidae", "Humedal y laguna"),
]

# Coordenadas base de cada zona dentro del parque.
ZONAS_COORDS = {
    "Bosque altoandino": (4.5610, -74.2960),
    "Salto del Tequendama": (4.5589, -74.2933),
    "Humedal y laguna": (4.5605, -74.2895),
    "Sendero ecológico": (4.5635, -74.2910),
    "Zona de picnic": (4.5575, -74.2905),
    "Campus SENA": (4.5550, -74.2880),
}

AVISTAMIENTOS = [
    ("Chinigüe (copetón)", "Sendero al Salto", "Sendero ecológico", 3, False,
     "Cantando al amanecer desde un arbusto de chilca."),
    ("Inca bronceado", "Jardines de la vereda", "Zona de picnic", 1, False,
     "Libando flores de dalia; se dejó fotografiar de cerca."),
    ("Caracara chimachima", "Mirador principal", "Salto del Tequendama", 2, True,
     "Planeando sobre el cañón; registro poco frecuente en el mirador."),
    ("Tucán piquiplano", "Sector de bosque conservado", "Bosque altoandino", 1, True,
     "Grupo familiar de tucanes en un aguacate silvestre."),
    ("Tororoi coronirrufo", "Quebrada La Chorrera", "Bosque altoandino", 1, False,
     "Escuchado al amanecer; visto brevemente en el sotobosque."),
    ("Pava andina", "Camino viejo del parque", "Bosque altoandino", 4, True,
     "Cuatro individuos cruzando el sendero: señal de buen estado del bosque."),
    ("Chisga morada", "Zona de descanso", "Zona de picnic", 5, False,
     "Defendiendo flores de salvia del jardín."),
    ("Garza del ganado", "Laguna del parque", "Humedal y laguna", 6, False,
     "Alimentándose junto a ganado en la orilla."),
    ("Candelita de frente dorada", "Sendero de la niebla", "Sendero ecológico", 2, False,
     "Abriendo las alas mientras buscaba insectos."),
    ("Buco común", "Borde de bosque", "Bosque altoandino", 2, False,
     "Llamadas insistentes en el borde del bosque."),
    ("Chinigüe (copetón)", "Entrada del parque", "Campus SENA", 1, False,
     "Cantando en el techo del centro de visitantes."),
    ("Caracara chimachima", "Campamento", "Zona de picnic", 1, False,
     "Observado perchado en un eucalipto."),
]

NOTICIAS = [
    (
        "BirdWatch abre su comunidad de avistamientos",
        "Ya puedes registrar tus observaciones, subir fotos y comentarlas. "
        "Cada registro ayuda a conocer mejor las aves de San Antonio del Tequendama.",
        "La plataforma incorpora un mapa interactivo con Leaflet y OpenStreetMap, "
        "estadísticas en tiempo real y un centro de ayuda para aprender a identificar aves. "
        "Toda la comunidad puede participar: los administradores revisan el contenido antes de publicarlo.",
        True,
    ),
    (
        "El bosque de niebla, protagonista de la temporada",
        "Las lluvias traen de vuelta a los colibríes y aves cantoras a los senderos del parque.",
        "Entre marzo y noviembre el bosque de niebla muestra su mayor actividad: "
        "inca bronceados, zafiros colilargos y candelitas de frente dorada frecuentan las flores. "
        "Recuerda registrarlos con coordenadas para que aparezcan en el mapa.",
        False,
    ),
    (
        "6:B Colombia se suma como aliado de BirdWatch",
        "La red de observadores acompaña el proyecto con conocimiento compartido y apoyo en la identificación.",
        "Gracias a esta alianza, la comunidad podrá acceder a guías, jornadas de observación "
        "y validación de registros. «Cada ave cuenta, cada observación importa» es el lema que nos une.",
        True,
    ),
    (
        "Cómo identificar aves por su canto en 3 pasos",
        "Graba, analiza y confirma: así funciona el identificador con inteligencia artificial.",
        "Graba entre 3 y 15 segundos, pulsa el botón de identificar y revisa el porcentaje de confianza. "
        "BirdWatch descarta voces humanas y ruidos, y exige al menos un 20 % de confianza. "
        "Confirma siempre el resultado con la foto o el comportamiento.",
        False,
    ),
]

PREGUNTAS = [
    ("¿Necesito iniciar sesión para usar BirdWatch?",
     "No. La portada, las noticias, el mapa, las estadísticas y el centro de ayuda son públicos. "
     "Inicia sesión solo para registrar avistamientos, comentar o validar información."),
    ("¿Cómo registro un avistamiento?",
     "Entra a «Avistamientos» y pulsa «Registrar avistamiento». Indica la especie, la fecha, "
     "el lugar, la zona y, si puedes, las coordenadas y una foto. Un administrador revisará el registro."),
    ("¿Para qué sirven las coordenadas?",
     "Permiten que tu avistamiento aparezca como un punto en el mapa interactivo y que se puedan "
     "calcular las especies por zona. Si no las conoces, puedes dejarlas en blanco."),
    ("¿Qué significa «validar información»?",
     "Es confirmar que un avistamiento te parece fiable. Cada registro muestra cuántas validaciones "
     "tiene; una persona solo puede validar una vez."),
    ("¿Qué hago si el identificador no reconoce un canto?",
     "Acércate lo más posible sin molestar al ave, evita ruidos de fondo y graba al menos 3 segundos. "
     "Revisa la guía para identificar aves y, si aún hay duda, escríbenos por el formulario de contacto."),
    ("¿Puedo usar las fotos que subo?",
     "Sí. Al aportar una foto a la comunidad aceptas que se muestre junto a tu avistamiento "
     "con fines educativos y de conservación. No subas fotos de terceros sin permiso."),
]


class Command(BaseCommand):
    help = "Siembra especies, avistamientos, noticias y preguntas de ejemplo (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        usuario = get_user_model().objects.filter(is_superuser=True).first()

        # 1. Especies del catálogo.
        especies = {}
        for nombre, cientifico, familia, zona in ESPECIES:
            ave, _ = Ave.objects.get_or_create(
                nombre_comun=nombre,
                defaults={
                    "nombre_cientifico": cientifico,
                    "familia": familia,
                    "zona": zona,
                    "descripcion": f"{nombre} registrado en San Antonio del Tequendama.",
                },
            )
            especies[nombre] = ave
        self.stdout.write(f"  {len(especies)} especies listas")

        # 2. Avistamientos de ejemplo con coordenadas.
        hoy = date.today()
        creados = 0
        for indice, (nombre, lugar, zona, cantidad, especial, notas) in enumerate(AVISTAMIENTOS):
            lat, lon = ZONAS_COORDS[zona]
            lat += (indice % 3) * 0.0004
            lon += (indice % 4) * 0.0005
            if Avistamiento.objects.filter(ave=especies[nombre], lugar=lugar, notas=notas).exists():
                continue
            Avistamiento.objects.create(
                ave=especies[nombre],
                usuario=usuario,
                fecha=hoy - timedelta(days=60 - indice * 4),
                lugar=lugar,
                zona=zona,
                latitud=round(lat, 6),
                longitud=round(lon, 6),
                cantidad=cantidad,
                notas=notas,
                caso_especial=especial,
                aprobado=True,
            )
            creados += 1

        # 3. Dar coordenadas y aprobación a los avistamientos del fixture inicial.
        actualizados = 0
        zonas = list(ZONAS_COORDS)
        for indice, avistamiento in enumerate(Avistamiento.objects.filter(latitud=None)):
            zona = zonas[indice % len(zonas)]
            lat, lon = ZONAS_COORDS[zona]
            avistamiento.zona = zona
            avistamiento.latitud = round(lat + 0.0002 * indice, 6)
            avistamiento.longitud = round(lon - 0.0003 * indice, 6)
            avistamiento.usuario = avistamiento.usuario or usuario
            avistamiento.aprobado = True
            avistamiento.save()
            actualizados += 1

        self.stdout.write(f"  {creados} avistamientos nuevos, {actualizados} completados")

        # 4. Noticias.
        noticias_creadas = 0
        for indice, (titulo, resumen, contenido, destacada) in enumerate(NOTICIAS):
            if Noticia.objects.filter(titulo=titulo).exists():
                continue
            Noticia.objects.create(
                titulo=titulo,
                resumen=resumen,
                contenido=contenido,
                publicada=True,
                destacada=destacada,
                publicada_en=timezone.now() - timedelta(days=20 - indice * 4),
            )
            noticias_creadas += 1

        # 5. Preguntas frecuentes.
        faqs_creadas = 0
        for indice, (pregunta, respuesta) in enumerate(PREGUNTAS):
            if PreguntaFrecuente.objects.filter(pregunta=pregunta).exists():
                continue
            PreguntaFrecuente.objects.create(pregunta=pregunta, respuesta=respuesta, orden=indice + 1)
            faqs_creadas += 1

        self.stdout.write(f"  {noticias_creadas} noticias y {faqs_creadas} preguntas nuevas")
        self.stdout.write(self.style.SUCCESS("Comunidad sembrada correctamente."))
