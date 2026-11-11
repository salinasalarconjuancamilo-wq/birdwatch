# -*- coding: utf-8 -*-
"""Genera MANUAL-BIRDWATCH.docx: la guía completa de cómo está hecha la app.

Uso:
    herramientas\\python\\python.exe descargas\\generar-manual.py

El documento explica qué es BIRDWATCH, cómo funciona por dentro, cómo
arrancarla, cómo se recorre su código y cómo modificarla paso a paso.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

VERDE_OSCURO = RGBColor(0x1B, 0x43, 0x2B)
VERDE_MEDIO = RGBColor(0x2E, 0x7D, 0x46)


# ----------------------------------------------------------------- utilidades
def con_estilo(doc):
    """Ajusta fuentes y colores base del documento."""
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    for nivel, color, tam in ((1, VERDE_OSCURO, 16), (2, VERDE_MEDIO, 13), (3, VERDE_OSCURO, 11.5)):
        estilo = doc.styles[f"Heading {nivel}"]
        estilo.font.name = "Calibri"
        estilo.font.size = Pt(tam)
        estilo.font.color.rgb = color
        estilo.font.bold = True


def p(doc, texto, negrita=False, cursiva=False):
    parrafo = doc.add_paragraph()
    partes = texto.split("**")  # **negrita** dentro del texto
    for i, parte in enumerate(partes):
        if not parte:
            continue
        trozo = parrafo.add_run(parte)
        trozo.bold = negrita or i % 2 == 1
        trozo.italic = cursiva
    return parrafo


def vinetas(doc, items):
    for item in items:
        p(doc, item).style = doc.styles["List Bullet"]


def pasos(doc, items):
    for item in items:
        p(doc, item).style = doc.styles["List Number"]


def codigo(doc, lineas, titulo=None):
    """Bloque de código: fuente monoespaciada y fondo gris claro."""
    if titulo:
        t = p(doc, titulo, negrita=True)
        t.paragraph_format.space_before = Pt(8)
    for linea in lineas:
        parrafo = doc.add_paragraph()
        run = parrafo.add_run(linea)
        run.font.name = "Consolas"
        run.font.size = Pt(9)
        parrafo.paragraph_format.left_indent = Cm(0.7)
        parrafo.paragraph_format.space_after = Pt(0)
        parrafo.paragraph_format.space_before = Pt(0)


def tabla(doc, encabezados, filas):
    t = doc.add_table(rows=1, cols=len(encabezados))
    try:
        t.style = doc.styles["Light Grid Accent 6"]
    except KeyError:
        t.style = doc.styles["Table Grid"]
    for celda, texto in zip(t.rows[0].cells, encabezados):
        celda.text = texto
        for run in celda.paragraphs[0].runs:
            run.bold = True
    for fila in filas:
        celdas = t.add_row().cells
        for celda, texto in zip(celdas, fila):
            celda.text = texto
    doc.add_paragraph()  # aire después de la tabla
    return t


def nota(doc, texto):
    parrafo = p(doc, texto, cursiva=True)
    parrafo.paragraph_format.left_indent = Cm(0.7)
    return parrafo


# ------------------------------------------------------------------ documento
doc = Document()
con_estilo(doc)

# Propiedades del archivo.
doc.core_properties.title = "Manual de BIRDWATCH"
doc.core_properties.author = "Proyecto BIRDWATCH · San Antonio del Tequendama"
doc.core_properties.language = "es-CO"

# ----------------------------------------------------------------- portada
titulo = doc.add_heading("BIRDWATCH", level=0)
titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub = p(doc, "Manual de construcción, arranque y modificación de la aplicación", negrita=True)
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub2a = p(doc, "Identificación de aves por su canto con inteligencia artificial", cursiva=True)
sub2a.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub2b = p(doc, "San Antonio del Tequendama · Cundinamarca · Colombia", cursiva=True)
sub2b.alignment = WD_ALIGN_PARAGRAPH.CENTER
fecha = p(doc, "Noviembre de 2026 · versión 1.0", cursiva=True)
fecha.alignment = WD_ALIGN_PARAGRAPH.CENTER

p(
    doc,
    "Este manual explica **cómo está programada** la aplicación BIRDWATCH, **cómo se "
    "arranca** cada día y **cómo se modifica** sin necesidad de ser programador "
    "experto. Está escrito en español y pensado para aprender: cada sección se puede "
    "seguir paso a paso sobre la carpeta del proyecto.",
)

# ------------------------------------------------------------- 1. qué es
doc.add_heading("1. ¿Qué es BIRDWATCH?", level=1)
p(
    doc,
    "BIRDWATCH es un **aplicativo web híbrido** (funciona igual en el celular y en el "
    "computador) que identifica **aves por su canto**. El usuario pulsa un botón con el "
    "logo de un ave, el navegador graba unos segundos de audio con el micrófono y una "
    "**inteligencia artificial llamada BirdNET** (creada por el Laboratorio de "
    "Ornitología de Cornell, EE. UU.) dice qué especie está cantando y con qué "
    "confianza.",
)
p(
    doc,
    "La app fue construida para San Antonio del Tequendama, un municipio del bosque "
    "andino de niebla en Cundinamarca. Su portada muestra un **carrusel con 9 aves "
    "representativas del municipio**, la **visión y la misión** del proyecto, y lleva "
    "un historial de detecciones guardado en una base de datos **PostgreSQL**.",
)
p(doc, "Características principales:")
vinetas(
    doc,
    [
        "Identificación por el **canto del ave** con BirdNET (más de 6.000 especies del mundo conocidas por el modelo).",
        "**Por ahora la app identifica solo al chinigüe (copetón)** (*Zonotrichia capensis*), el ave insignia de esta versión (ver receta 8.2 para ampliar).",
        "Interfaz **100 % en español** con paleta **verde de bosque andino**.",
        "**Híbrida**: el mismo diseño se adapta a celular, tableta y computador.",
        "**PWA**: se puede instalar en el celular desde el navegador.",
        "Todo el sistema (Python, PostgreSQL, librerías, modelo de IA) vive dentro de la carpeta del proyecto: **no hay que instalar nada** ni tener permisos de administrador.",
        "Acceso protegido con usuario y contraseña (superusuario inicial **user / 1234**).",
    ],
)

# ------------------------------------------------------------- 2. requisitos
doc.add_heading("2. ¿Qué necesito para que funcione?", level=1)
p(
    doc,
    "Solo una computadora con **Windows 10 u 11**, unos **6 GB de espacio libre** y "
    "**4 GB de RAM** (recomendado). Todo lo demás ya viene incluido dentro de la "
    "carpeta del proyecto:",
)
tabla(
    doc,
    ["Qué", "Dónde está", "Para qué sirve"],
    [
        ["Python 3.12 portátil", "herramientas\\python\\", "Ejecutar toda la app y la IA (no se instala)"],
        ["PostgreSQL 16 portátil", "herramientas\\postgres\\", "Base de datos, en el puerto 5433"],
        ["Librerías de Python", "herramientas\\python\\Lib\\site-packages\\", "Django, BirdNET, TensorFlow, bottle, etc."],
        ["Modelo BirdNET GLOBAL 6K V2.4", "herramientas\\python\\Lib\\site-packages\\", "La IA que reconoce los cantos (224 MB)"],
        ["Fotos y logos", "estaticos\\img\\", "Carrusel y botón del ave"],
        ["Canto de prueba", "descargas\\prueba-ave.wav", "Probar el identificador sin ave cerca"],
    ],
)
nota(doc, "Nota: los requisitos completos de dependencias están listados en requirements.txt, por si algún día se quiere reproducir la instalación en otro equipo.")

# ------------------------------------------------------------- 3. cómo funciona
doc.add_heading("3. Cómo funciona por dentro (la idea general)", level=1)
p(
    doc,
    "BIRDWATCH es en realidad **cuatro programas trabajando juntos**. Entender este "
    "esquema es entender toda la app:",
)
tabla(
    doc,
    ["Programa", "Puerto", "Qué hace"],
    [
        ["1. El navegador (celular o PC)", "—", "Muestra las páginas y graba el micrófono"],
        ["2. Django (la web)", "3000", "Sirve las páginas, recibe el audio y guarda los resultados"],
        ["3. BirdNET (la IA)", "8080", "Analiza el audio y dice qué ave es (servidor_birdnet.py)"],
        ["4. PostgreSQL (los datos)", "5433", "Guarda aves del carrusel, detecciones y usuarios"],
    ],
)
p(
    doc,
    "**Django** es un “marco de trabajo” (framework) de Python muy popular para "
    "construir webs: cada página que ve el usuario la dibuja una **plantilla HTML**, "
    "la prepara una **vista** (una función de Python) y los datos viven en **modelos** "
    "que PostgreSQL convierte en tablas. **BirdNET** es un programa aparte que "
    "funciona como un servicio: Django le envía el audio por HTTP y le devuelve un "
    "JSON con las especies reconocidas.",
)

doc.add_heading("3.1 El viaje de un canto (paso a paso)", level=2)
p(doc, "Esto es lo que ocurre cada vez que alguien identifica un ave:")
pasos(
    doc,
    [
        "El usuario inicia sesión y pulsa el botón grande con el logo del ave.",
        "El navegador pide **permiso del micrófono** y el usuario lo acepta.",
        "El JavaScript de la página (estaticos\\js\\identificar.js) graba entre 3 y 15 segundos.",
        "El navegador convierte la grabación a un archivo de sonido **WAV** (mono, 16 bits, 48 kHz).",
        "El navegador envía ese WAV al servidor Django con una petición **POST a /analizar/**.",
        "La vista analizar() de core\\views.py recibe el audio y llama a core\\birdnet.py.",
        "core\\birdnet.py reenvía el audio al servicio BirdNET (puerto 8080) junto con la **lista de especies permitidas** (por ahora solo el chinigüe).",
        "servidor_birdnet.py pasa el audio por la **red neuronal BirdNET** y devuelve, por ejemplo: “Zonotrichia capensis, 42 %”.",
        "Django traduce el nombre al español, guarda la **detección en PostgreSQL** y responde en JSON.",
        "El navegador pinta la tarjeta del resultado (“Chinigüe (copetón) · 42 %”) y actualiza el historial.",
    ],
)
nota(doc, "La confianza es el porcentaje con el que la IA está segura: cuanto más limpio y cercano sea el canto, más alto sale.")

# ------------------------------------------------------------- 4. estructura
doc.add_heading("4. Estructura de carpetas del proyecto", level=1)
codigo(
    doc,
    [
        "BirdWatch (carpeta del proyecto)",
        "|",
        "|-- INICIAR-BIRDWATCH.bat      Arranca TODO (doble clic y listo)",
        "|-- INICIAR-BIRDNET.bat        Arranca solo la IA BirdNET",
        "|-- DETENER-BIRDWATCH.bat      Detiene todos los servicios",
        "|-- manage.py                  Utilidades de Django (migraciones, servidor...)",
        "|-- requirements.txt           Lista de librerías de Python",
        "|-- servidor_birdnet.py        El servicio de la IA (puerto 8080)",
        "|",
        "|-- birdwatch\\                 Configuración global del proyecto Django",
        "|     |-- settings.py          Puertos, base de datos, idioma, apps",
        "|     |-- urls.py              Rutas principales (reparte a cada app)",
        "|     |-- wsgi.py              Enlace para servidores de producción",
        "|",
        "|-- core\\                      APP PRINCIPAL (identificador de aves)",
        "|     |-- models.py            Tablas: Ave y Deteccion",
        "|     |-- views.py             Vistas: inicio, entrar, identificar, analizar...",
        "|     |-- urls.py              Rutas de la app core",
        "|     |-- birdnet.py           Cliente de la IA + ESPECIES_PERMITIDAS",
        "|     |-- traducciones.py      Nombres de aves en español (Colombia)",
        "|     |-- admin.py             Configura el panel /admin/",
        "|     |-- data\\aves.json       Las 9 aves del carrusel",
        "|     +-- management\\commands\\sembrar.py  Carga datos iniciales",
        "|",
        "|-- aves\\                      APP ORIGINAL del repositorio (catálogo",
        "|     |                         y avistamientos, se edita en /admin/)",
        "|     |-- models.py, views.py, admin.py, fixtures\\...",
        "|",
        "|-- plantillas\\                Las páginas HTML",
        "|     |-- base.html            Esqueleto común (encabezado y pie)",
        "|     |-- inicio.html          Portada: carrusel + visión y misión",
        "|     |-- login.html           Página de entrada (usuario/contraseña)",
        "|     +-- identificar.html     El identificador con el botón de grabar",
        "|",
        "|-- estaticos\\                 Lo que el navegador descarga",
        "|     |-- css\\estilos.css      TODOS los colores y estilos",
        "|     |-- js\\identificar.js   Grabación de micrófono y resultados",
        "|     |-- js\\carrusel.js       Movimiento del carrusel",
        "|     |-- js\\comun.js, login.js, sw.js   Utilidades y PWA",
        "|     +-- img\\logo.svg, img\\aves\\*.jpg   Logo y fotos",
        "|",
        "|-- descargas\\                 Instaladores, pruebas y registros",
        "|     |-- prueba-ave.wav        Canto real de chinigüe para pruebas",
        "|     |-- probar-birdnet.py     Prueba de la IA por separado",
        "|     |-- probar-django.py     Prueba completa de la web",
        "|     +-- generar-manual.py     Generó este documento",
        "|",
        "+-- herramientas\\              TODO el software portátil (Python,",
        "                               PostgreSQL, clúster de datos pgdatos)",
    ],
    titulo="Mapa de carpetas",
)

# ------------------------------------------------------------- 5. arranque
doc.add_heading("5. Arranque paso a paso (cómo hacer que funcione)", level=1)
doc.add_heading("5.1 Iniciar la aplicación", level=2)
pasos(
    doc,
    [
        "Abre la carpeta del proyecto en el Explorador de Windows.",
        "Haz **doble clic en INICIAR-BIRDWATCH.bat**.",
        "Aparece una ventana negra que va mostrando: [1/3] PostgreSQL, [2/3] BirdNET, [3/3] web.",
        "Espera: la **primera vez** BirdNET tarda unos 15 segundos en cargar su modelo (224 MB).",
        "El navegador se abre solo en http://localhost:3000 (si no, ábrelo manualmente).",
        "Entra con **user / 1234**.",
    ],
)
p(
    doc,
    "El archivo .bat deja dos ventanas minimizadas (**BirdNET** y **Django BirdWatch**): "
    "son los servicios. No las cierres mientras uses la app. Si uno de los servicios ya "
    "estaba corriendo, el .bat lo detecta y no lo duplica.",
)
doc.add_heading("5.2 Qué hace el arranque, por dentro", level=2)
p(
    doc,
    "INICIAR-BIRDWATCH.bat ejecuta tres órdenes, en orden. Si algún día algo falla, "
    "puedes correr cada orden a mano y ver el error con detalle:",
)
codigo(
    doc,
    [
        'rem 1. Base de datos PostgreSQL (puerto 5433):',
        '"herramientas\\postgres\\bin\\pg_ctl.exe" -D "herramientas\\pgdatos" -o "-p 5433" -l "descargas\\pg-servidor.log" start',
        "",
        'rem 2. Inteligencia artificial BirdNET (puerto 8080):',
        '"herramientas\\python\\python.exe" servidor_birdnet.py --host 127.0.0.1 --port 8080 --spath "descargas\\birdnet-subidas"',
        "",
        'rem 3. Aplicacion web Django (puerto 3000):',
        '"herramientas\\python\\python.exe" manage.py runserver 0.0.0.0:3000 --noreload',
    ],
)
doc.add_heading("5.3 Detener la aplicación", level=2)
p(doc, "Doble clic en **DETENER-BIRDWATCH.bat**, o cierra las dos ventanas minimizadas y ejecuta:")
codigo(doc, ['"herramientas\\postgres\\bin\\pg_ctl.exe" -D "herramientas\\pgdatos" stop'])
doc.add_heading("5.4 Usarla desde el celular", level=2)
pasos(
    doc,
    [
        "El celular debe estar en la **misma red Wi-Fi** que el computador.",
        "En el celular abre http://IP-DEL-COMPUTADOR:3000 (la IP se ve con el comando ipconfig).",
        "Para **grabar el micrófono** el navegador exige HTTPS o localhost; en el celular se necesita servir la app con HTTPS (ver solución de problemas 10).",
        "El diseño se adapta solo: carrusel, login e identificador son responsivos.",
    ],
)

# ------------------------------------------------------------- 6. uso diario
doc.add_heading("6. Uso diario: identificar el chinigüe (copetón)", level=1)
pasos(
    doc,
    [
        "Entra en http://localhost:3000 e inicia sesión (user / 1234).",
        "Pulsa el botón grande **“Identificar un ave por su canto”** (el del logo del ave).",
        "En la página del identificador pulsa **Grabar** y acepta el permiso del micrófono.",
        "Acerca el equipo al canto y espera entre **3 y 15 segundos** (a los 15 se detiene solo).",
        "Pulsa **Detener**: en unos segundos aparece la tarjeta con la especie y su **porcentaje de confianza**.",
        "La detección queda guardada: abajo está **“Mis últimas detecciones”** y en /admin/ se pueden ver todas.",
    ],
)
p(
    doc,
    "**Por ahora el identificador solo reconoce al chinigüe (copetón)** "
    "(*Zonotrichia capensis*). Si grabas otro canto, la app dirá que no identificó el "
    "chinigüe con suficiente confianza: es el comportamiento esperado de esta versión. "
    "Para probar sin un ave cerca, existe un canto real en descargas\\prueba-ave.wav "
    "(de un chingolo grabado en Commons) que se puede reproducir por los parlantes y "
    "grabarlo con el micrófono.",
)

# ------------------------------------------------------------- 7. recorrido por el código
doc.add_heading("7. Recorrido por el código: ¿dónde está cada cosa?", level=1)
p(
    doc,
    "Esta sección es la “radiografía” de la app. Sirve para saber **qué archivo "
    "abrir** antes de hacer cualquier cambio.",
)

doc.add_heading("7.1 birdwatch\\settings.py — la configuración general", level=2)
vinetas(
    doc,
    [
        "INSTALLED_APPS: la lista de aplicaciones instaladas. Aquí están **core** (la nueva) y **aves** (la original del repositorio).",
        "DATABASES: la conexión a PostgreSQL. Por defecto: postgres://birdwatch:birdwatch@localhost:5433/birdwatch (se puede cambiar con la variable de entorno DATABASE_URL).",
        "LANGUAGE_CODE = “es-co” y TIME_ZONE = “America/Bogota”: todo en español y hora colombiana.",
        "STATIC_URL y STATICFILES_DIRS: dónde viven las fotos, CSS y JavaScript (la carpeta estaticos\\).",
        "TEMPLATES DIRS: dónde viven las páginas HTML (la carpeta plantillas\\).",
    ],
)
doc.add_heading("7.2 Las rutas (URLs): quién responde a cada dirección", level=2)
p(doc, "birdwatch\\urls.py reparte el tráfico a la app core; core\\urls.py asigna cada dirección a una vista:")
tabla(
    doc,
    ["Dirección", "Vista (core\\views.py)", "Qué hace"],
    [
        ["/", "inicio", "Portada con el carrusel de aves, visión y misión"],
        ["/entrar/", "entrar", "Formulario de inicio de sesión"],
        ["/salir/", "salir", "Cierra la sesión"],
        ["/identificar/", "identificar", "Página del identificador (requiere sesión)"],
        ["/analizar/", "analizar", "Recibe el WAV del micrófono y llama a BirdNET"],
        ["/historial/", "historial", "Últimas 50 detecciones del usuario (JSON)"],
        ["/estado/", "estado", "Panel: ¿está activa la base y la IA?"],
        ["/admin/", "(Django)", "Panel de administración de datos"],
    ],
)
doc.add_heading("7.3 core\\models.py — los datos", level=2)
vinetas(
    doc,
    [
        "**Ave**: nombre_comun, nombre_cientifico, descripcion, imagen, orden. Son las 9 aves del carrusel; se cargan con el comando sembrar.",
        "**Deteccion**: usuario, especie_en, especie_es, nombre_cientifico, tipo_sonido, confianza, creado_en. Cada identificación guardada es una fila de esta tabla.",
        "Cada modelo se convierte en una tabla real con el comando migrate (ver glosario).",
    ],
)
doc.add_heading("7.4 core\\views.py — el cerebro del servidor", level=2)
p(
    doc,
    "Cada vista es una función que recibe la petición del navegador y responde. Las "
    "más importantes: **analizar()** valida el audio (tamaño entre 25 MB y 1 KB), "
    "llama a la IA, descarta resultados con confianza menor a 0.05 y guarda cada "
    "detección con Deteccion.objects.create(...). **entrar()** revisa usuario y "
    "contraseña con el sistema de usuarios de Django.",
)
doc.add_heading("7.5 core\\birdnet.py — el puente hacia la IA", level=2)
vinetas(
    doc,
    [
        "BIRDNET_URL: dirección del servicio BirdNET (http://localhost:8080, cambiable con la variable de entorno BIRDNET_URL).",
        "LATITUD y LONGITUD: coordenadas de San Antonio del Tequendama (4.6267, -74.3300).",
        "ESPECIES_PERMITIDAS: **la lista que restringe la identificación al chinigüe** (ver receta 8.2).",
        "analizar_audio(): arma la petición multipart/form-data con el audio y el “meta” (ubicación, semana, lista de especies) y la envía al puerto 8080.",
        "_interpretar_etiqueta(): separa la respuesta de BirdNET (“Zonotrichia capensis_Rufous-collared Sparrow”) en nombre científico, nombre común y tipo de sonido.",
    ],
)
doc.add_heading("7.6 servidor_birdnet.py — el servicio de la IA", level=2)
p(
    doc,
    "El paquete oficial birdnet_analyzer 2.4 ya no trae su propio servidor web, así "
    "que este archivo implementa uno equivalente (con la librería bottle) que expone "
    "POST /analyze: recibe el audio + un JSON “meta”, ajusta la configuración del "
    "analizador (incluida la lista de especies permitidas, campo **slist**), pasa el "
    "audio por la red neuronal y devuelve un JSON con las especies y sus confianzas. "
    "Usa un solo hilo a la vez, igual que el servidor original.",
)
doc.add_heading("7.7 plantillas\\ y estaticos\\ — lo que ve el usuario", level=2)
vinetas(
    doc,
    [
        "base.html: encabezado, pie y enlaces comunes a todas las páginas.",
        "inicio.html: portada, carrusel ({% for ave in aves %}) y las tarjetas de visión y misión.",
        "identificar.html: botón de grabar, cronómetro, medidor de nivel y zona de resultados.",
        "login.html: formulario de acceso.",
        "estaticos\\js\\identificar.js: pide el micrófono (getUserMedia), graba con AudioWorklet, construye el WAV y lo envía con el token CSRF.",
        "estaticos\\css\\estilos.css: colores, tamaños y disposición de TODO el sitio (ver receta 8.4).",
    ],
)
doc.add_heading("7.8 La app aves (versión original del repositorio)", level=2)
p(
    doc,
    "El proyecto nació de un repositorio que ya tenía la app **aves**: un catálogo "
    "de aves y un registro de avistamientos. Se conservó y se administra en "
    "/admin/ (sección AVES: Aves y Avistamientos). Sus datos iniciales están en "
    "aves\\fixtures\\datos_iniciales.json y ya están cargados en PostgreSQL.",
)

# ------------------------------------------------------------- 8. recetas
doc.add_heading("8. Recetas de modificación (hazlo tú mismo)", level=1)
p(doc, "Consejos generales antes de empezar: haz siempre una copia del archivo que vas a tocar, cambia una sola cosa a la vez, y después de guardar reinicia la web (DETENER-BIRDWATCH.bat y luego INICIAR-BIRDWATCH.bat).")

doc.add_heading("8.1 Cambiar los textos de las páginas", level=2)
pasos(
    doc,
    [
        "Abre el archivo de plantillas\\ correspondiente (por ejemplo plantillas\\inicio.html para la portada).",
        "Busca el texto que quieres cambiar (Ctrl+B en el editor para buscar).",
        "Cuidado con lo que está entre {% y %}: son órdenes del sistema, no texto visible.",
        "Guarda el archivo y recarga la página en el navegador (F5).",
    ],
)
nota(doc, "Los archivos .html aceptan tildes y eñes sin problema; están guardados en UTF-8. Para ventanas de comandos (.bat) es mejor evitar tildes.")

doc.add_heading("8.2 Cambiar qué aves puede identificar (ESPECIES_PERMITIDAS)", level=2)
p(
    doc,
    "La restricción “solo chinigüe” vive en **core\\birdnet.py**, en la lista "
    "ESPECIES_PERMITIDAS. Cada etiqueta tiene el formato "
    "“NombreCientifico_NombreComunEnIngles” (BirdNET usa nombres en inglés):",
)
codigo(
    doc,
    [
        "ESPECIES_PERMITIDAS = [",
        '    "Zonotrichia capensis_Rufous-collared Sparrow",  # chinigüe (copetón)',
        "]",
    ],
)
p(doc, "Para agregar otra ave, añade su etiqueta a la lista:")
codigo(
    doc,
    [
        "ESPECIES_PERMITIDAS = [",
        '    "Zonotrichia capensis_Rufous-collared Sparrow",  # chinigüe (copetón)',
        '    "Colibri coruscans_Sparkling Violetear",          # chisga morada',
        '    "Turdus fuscater_Great Thrush",                   # mirla lugubris',
        "]",
    ],
)
vinetas(
    doc,
    [
        "Para quitar la restricción y dejar que la IA devuelva cualquier ave de la región, cambia la lista a [] (vacía).",
        "La lista completa de etiquetas vive en el archivo labels.txt del paquete birdnet_analyzer (dentro de herramientas\\python\\Lib\\site-packages\\).",
        "También conviene añadir el nombre en español de la especie nueva en core\\traducciones.py, para que el resultado no salga en inglés.",
        "Tras guardar, reinicia la web y el analizador (DETENER + INICIAR) para que el cambio surta efecto.",
    ],
)

doc.add_heading("8.3 Agregar o cambiar aves del carrusel", level=2)
p(doc, "Hay dos caminos. El rápido, desde el panel de administración:")
pasos(
    doc,
    [
        "Entra a http://localhost:3000/admin/ con user / 1234.",
        "En la sección CORE elige **Aves**: ahí puedes editar o agregar aves (nombre, descripción y ruta de la foto).",
        "Guarda y recarga la portada: el carrusel se arma solo con lo que haya en la tabla.",
    ],
)
p(doc, "El camino permanente, editando el archivo de datos:")
pasos(
    doc,
    [
        "Abre core\\data\\aves.json: es la lista de las 9 aves con su información.",
        "Copia un bloque completo, cambia sus campos y coloca la foto nueva en estaticos\\img\\aves\\.",
        "Ejecuta: herramientas\\python\\python.exe manage.py sembrar",
        "Ese comando vuelve a crear el superusuario y recarga las aves del JSON en PostgreSQL.",
    ],
)

doc.add_heading("8.4 Cambiar los colores del sitio", level=2)
p(
    doc,
    "Todos los colores están en **estaticos\\css\\estilos.css**, al principio, como "
    "variables CSS (paleta verde de bosque andino):",
)
codigo(
    doc,
    [
        ":root {",
        "    --verde-noche:  #081c15;   /* el verde mas oscuro (pie) */",
        "    --verde-bosque: #1b4332;   /* encabezados y fondos fuertes */",
        "    --verde-medio:  #2d6a4f;   /* botones y acentos */",
        "    --verde-hoja:   #40916c;   /* acentos de hoja */",
        "    --verde-claro:  #52b788;   /* detalles vivos */",
        "    --verde-menta:  #b7e4c7;   /* fondos suaves */",
        "    --verde-niebla: #d8f3dc;   /* fondos claros */",
        "    --crema: #fffaf0;  --sol: #ffd166;  --naranja: #f48c06;",
        "    --fruto: #ef476f;  --cielo: #5fa8d3;",
        "}",
    ],
)
p(doc, "Cambia los códigos hexadecimales (#1b432b, etc.) por los que quieras, guarda y recarga la página. Todo el sitio usa esas variables, así que el cambio se aplica a la vez en celular y computador.")

doc.add_heading("8.5 Cambiar la contraseña del superusuario", level=2)
codigo(
    doc,
    [
        'herramientas\\python\\python.exe manage.py changepassword user',
        "",
        "rem (o tambien se puede desde /admin/ : Usuarios > user)",
    ],
)
nota(doc, "El comando sembrar restablece la clave a 1234; si cambias la contraseña, no ejecutes sembrar o cámbiala de nuevo después.")

doc.add_heading("8.6 Cambiar las coordenadas del municipio", level=2)
p(doc, "En core\\birdnet.py, líneas LATITUD y LONGITUD:")
codigo(doc, ["LATITUD = 4.6267", "LONGITUD = -74.3300"])
p(doc, "La IA usa esas coordenadas para elegir qué aves son verosímiles en la zona; si la app se lleva a otro municipio, hay que poner las coordenadas de ese lugar (Google Maps: clic derecho > coordenadas).")

doc.add_heading("8.7 Cambiar el logo del ave", level=2)
pasos(
    doc,
    [
        "Dibuja o descarga un logo (SVG o PNG).",
        "Guárdalo como estaticos\\img\\logo.svg (o cambia el nombre en las plantillas).",
        "Recarga la página: el logo aparece en el encabezado, el botón de la portada y el botón de grabar.",
    ],
)

doc.add_heading("8.8 Crear más usuarios", level=2)
codigo(
    doc,
    [
        'herramientas\\python\\python.exe manage.py createsuperuser --username nuevo_usuario',
        "(el comando pide la clave dos veces)",
    ],
)

# ------------------------------------------------------------- 9. comandos
doc.add_heading("9. Comandos útiles", level=1)
tabla(
    doc,
    ["Comando", "Para qué sirve"],
    [
        ["INICIAR-BIRDWATCH.bat", "Arranca todo (base de datos + IA + web)"],
        ["DETENER-BIRDWATCH.bat", "Detiene todo"],
        ["INICIAR-BIRDNET.bat", "Arranca solo la IA (puerto 8080)"],
        ["manage.py runserver 0.0.0.0:3000 --noreload", "Web a mano (ver errores en pantalla)"],
        ["manage.py migrate", "Crea/actualiza tablas en PostgreSQL"],
        ["manage.py sembrar", "Recarga superusuario user/1234 y las 9 aves"],
        ["manage.py createsuperuser --username X", "Crear otro usuario"],
        ["manage.py changepassword user", "Cambiar la contraseña"],
        ["manage.py loaddata aves/fixtures/datos_iniciales.json", "Cargar datos de la app aves"],
        ["pg_ctl ... start / stop", "Encender/apagar PostgreSQL a mano"],
        ["descargas\\probar-django.py", "Prueba completa de la web (15 comprobaciones)"],
        ["descargas\\probar-birdnet.py", "Prueba de la IA con un canto real"],
        ["descargas\\generar-manual.py", "Regenera este documento Word"],
    ],
)
p(doc, "Todos los comandos de manage.py se ejecutan con el Python del proyecto:")
codigo(doc, ['herramientas\\python\\python.exe manage.py ...'])

# ------------------------------------------------------------- 10. problemas
doc.add_heading("10. Solución de problemas", level=1)
tabla(
    doc,
    ["Problema", "Causa probable", "Solución"],
    [
        ["“No se detecta el analizador BirdNET”", "La IA no está corriendo", "Ejecuta INICIAR-BIRDWATCH.bat y espera a que cargue (15 s la primera vez)"],
        ["La página no abre (localhost:3000)", "Otro programa usa el puerto 3000", "Ciérralo o corre la web en otro puerto: manage.py runserver 0.0.0.0:3001 --noreload"],
        ["Error de conexión a la base de datos", "PostgreSQL detenido", "pg_ctl start (ver sección 5.2) y revisar descargas\\pg-servidor.log"],
        ["El micrófono no funciona", "El navegador exige HTTPS o localhost", "Abre http://localhost:3000 en el mismo computador, o monta HTTPS para el celular"],
        ["“No se identificó el chinigüe”", "Canto lejano o ruido de fondo", "Acércate, graba entre 5 y 15 s, evita lluvia y motores"],
        ["Aparecen avisos raros de TensorFlow (oneDNN)", "Mensajes informativos del motor de IA", "Ignorarlos: no son errores"],
        ["Falta una DLL (vcruntime/msvcp)", "Runtime de Visual C++ ausente", "Ya están incluidas en herramientas\\; si se copia el proyecto a otro PC, copiar la carpeta completa"],
        ["Resultados con otra ave distinta", "La lista ESPECIES_PERMITIDAS quedó vacía", "Revisar core\\birdnet.py y reiniciar los servicios"],
        ["Todo muy lento al analizar", "Primera carga del modelo o CPU ocupada", "Cerrar programas pesados; la primera carga siempre tarda más"],
        ["La app en el celular no graba", "HTTPS pendiente", "Servir con HTTPS (p. ej. Caddy) o probar el identificador en el PC"],
    ],
)

# ------------------------------------------------------------- 11. glosario
doc.add_heading("11. Glosario para principiantes", level=1)
tabla(
    doc,
    ["Término", "Significado"],
    [
        ["Aplicación (app) Django", "Un “módulo” del proyecto con sus páginas, datos y URLs (core y aves)"],
        ["Vista", "Función de Python que recibe una petición del navegador y responde una página o un JSON"],
        ["Plantilla", "El archivo HTML con el diseño de la página; Django le “rellena” los datos"],
        ["Modelo", "Descripción de una tabla de datos en Python (Ave, Deteccion)"],
        ["Migración", "El ajuste que Django hace en la base de datos cuando cambia un modelo"],
        ["URL / ruta", "La dirección web (/identificar/, /analizar/)"],
        ["JSON", "Formato de texto para intercambiar datos entre programas"],
        ["API", "Servicio que un programa ofrece a otro (BirdNET expone /analyze)"],
        ["BirdNET", "La IA del Laboratorio de Ornitología de Cornell que reconoce cantos"],
        ["Red neuronal", "Modelo matemático entrenado con miles de grabaciones de aves"],
        ["WAV", "Archivo de audio sin compresión; el que produce el micrófono de la web"],
        ["48 kHz / 16 bits", "Calidad del audio: 48.000 muestras por segundo, cada una de 16 bits"],
        ["Confianza", "Porcentaje de seguridad de la IA (42 % = bastante segura)"],
        ["PostgreSQL", "Sistema de base de datos donde se guardan aves, detecciones y usuarios"],
        ["Puerto", "“Ventanilla” donde escucha cada programa (3000 web, 8080 IA, 5433 datos)"],
        ["localhost", "Dirección que significa “este mismo computador”"],
        ["CSRF", "Protección de Django contra envíos falsos de formularios"],
        ["Sesión", "Estado “conectado” del usuario tras iniciar sesión"],
        ["Superusuario", "Usuario administrador que puede entrar a /admin/"],
        ["PWA", "Aplicación web progresiva: se instala en el celular desde el navegador"],
        [".bat", "Archivo de órdenes de Windows; se ejecuta con doble clic"],
        ["Variable de entorno", "Valor de configuración que se puede fijar antes de arrancar (DATABASE_URL, BIRDNET_URL)"],
    ],
)

# ------------------------------------------------------------- 12. créditos
doc.add_heading("12. Créditos y licencias", level=1)
vinetas(
    doc,
    [
        "BirdNET y el modelo BirdNET GLOBAL 6K V2.4: Laboratorio de Ornitología de Cornell e Institut für Vogelforschung (CC BY-NC-SA 4.0).",
        "Fotos de las aves: Wikimedia Commons (Michael Gäbler, Joseph C. Boone, Charles J. Sharp, Mike's Birds, Félix Uribe).",
        "Canto de prueba: Zonotrichia capensis vía xeno-canto (XC243300) / Wikimedia Commons.",
        "Software: Python, Django, PostgreSQL, TensorFlow, bottle, python-docx (libres y gratuitos).",
        "Proyecto educativo de San Antonio del Tequendama, Cundinamarca, Colombia.",
    ],
)

# ------------------------------------------------------------------ guardar
destino = RAIZ / "MANUAL-BIRDWATCH.docx"
doc.save(destino)
print(f"Manual generado: {destino}")
print(f"Tamaño: {destino.stat().st_size / 1024:.0f} KB")
