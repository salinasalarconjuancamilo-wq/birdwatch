# BirdWatch · San Antonio del Tequendama

Aplicativo web **híbrido (celular y computador)** para identificar las aves de
San Antonio del Tequendama (Cundinamarca, Colombia) **por su canto**, usando la
inteligencia artificial **BirdNET** del Laboratorio de Ornitología de Cornell.

## Qué incluye

- **Inicio**: carrusel con las 9 aves representativas del municipio (cóndor
  andino, colibríes, tucán piquiplano, tororoi, candelita y pava andina) y las
  secciones de **visión y misión** del proyecto.
- **Botón con el logo del ave** (un colibrí) que abre la página de
  identificación: pide permiso del micrófono, graba entre 3 y 15 segundos y
  envía el audio a BirdNET con la ubicación del municipio (4.6267, -74.3300).
- **Por ahora el identificador reconoce solo al chinigüe (copetón)**
  (*Zonotrichia capensis*), el ave insignia de esta primera versión. Ver
  la sección ["Especie identificada"](#especie-identificada-chinigüe-copetón).
- **Detecciones guardadas en PostgreSQL** con su nombre en español,
  nombre científico y porcentaje de confianza; se consultan en "Mis últimas
  detecciones" y en el administrador de Django (`/admin/`).
- **Aplicación web progresiva (PWA)**: se puede instalar en el celular desde
  el navegador.
- Interfaz en **español**, con paleta **verde de bosque andino de niebla**.

## Requisitos del equipo (una sola vez)

- **Python 3.12 o superior** en el sistema.
- **PostgreSQL** instalado como servicio de Windows (cualquier versión
  reciente) con la base de datos del proyecto:

  ```sql
  CREATE ROLE birdwatch LOGIN PASSWORD 'birdwatch';
  CREATE DATABASE birdwatch OWNER birdwatch;
  ```

- Preparar el entorno virtual del proyecto (descarga ~600 MB de TensorFlow,
  tarda varios minutos):

  ```
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  ```

  Luego crear las tablas y cargar los datos iniciales:

  ```
  .venv\Scripts\python.exe manage.py migrate
  .venv\Scripts\python.exe manage.py sembrar
  .venv\Scripts\python.exe manage.py loaddata aves/fixtures/datos_iniciales.json
  ```

  El comando `sembrar` crea el superusuario (`user` / `1234`) y las 9 aves.

## Cómo se usa

### 1. Iniciar

Haz doble clic en **`INICIAR-BIRDWATCH.bat`**. El archivo:

1. Verifica el **PostgreSQL del equipo** (servicio del sistema, puerto 5432).
2. Arranca el **analizador BirdNET** en el puerto 8080.
3. Arranca la **aplicación web Django** en el puerto 3000.
4. Abre el navegador en <http://localhost:3000>.

> La primera vez, BirdNET tarda unos 15 segundos en cargar el modelo (224 MB).

### 2. Entrar

- **Usuario**: `user`
- **Contraseña**: `1234`

### 3. Identificar un ave

1. En la portada pulsa el botón grande **"Identificar un ave por su canto"**
   (el del colibrí).
2. En la página del identificador pulsa **Grabar** y acepta el permiso del
   micrófono.
3. Acerca el equipo al canto del ave y espera entre 3 y 15 segundos; pulsa
   **Detener** (o espera a que se detenga solo a los 15 segundos).
4. En segundos aparecen las especies más probables con su porcentaje de
   confianza, y la detección queda guardada en la base de datos.

### 4. Detener

Haz doble clic en **`DETENER-BIRDWATCH.bat`** (detiene la web y BirdNET; el
servicio PostgreSQL del equipo sigue corriendo, porque es compartido) o cierra
las ventanas minimizadas "BirdNET" y "Django BirdWatch".

## Uso desde el celular

1. En el celular, conectado a la **misma red Wi-Fi**, abre
   `http://IP-DEL-COMPUTADOR:3000` (la IP se ve con `ipconfig`).
2. **Importante**: los navegadores solo permiten el micrófono en **HTTPS** o
   en `localhost`. Para grabar desde el celular hay que servir la aplicación
   con HTTPS. En el computador, con `http://localhost:3000` funciona sin
   problema.
3. El diseño es responsivo: el carrusel, el login y el identificador se
   adaptan a la pantalla del teléfono.

## Estructura del proyecto

```
INICIAR-BIRDWATCH.bat      Arranca todo (BirdNET + web)
DETENER-BIRDWATCH.bat      Detiene los servicios de la app
manage.py                  Utilidades de Django
requirements.txt           Dependencias de Python del proyecto
.venv/                     Entorno virtual (no se sube a git)
birdwatch/                 Configuración del proyecto Django (settings, urls)
core/                      Aplicación principal: modelos, vistas, cliente
                           BirdNET, traducciones ES y datos de las aves
aves/                      Catálogo de aves y registro de avistamientos
                           (se administra en /admin/)
plantillas/                Páginas HTML (base, inicio, login, identificar)
estaticos/                 CSS, JavaScript, manifest PWA, logo y fotos de aves
servidor_birdnet.py        Servidor HTTP del analizador BirdNET (bottle)
```

## App `aves`: catálogo y avistamientos

Conserva un **catálogo de aves** (nombre común y científico, familia, color,
tamaño y foto) y el **registro de avistamientos** (ave, fecha, lugar, cantidad
y notas). Se administra desde el panel de Django:

1. Entra a <http://localhost:3000/admin/> con `user` / `1234`.
2. En la sección **AVES** están **Aves** (catálogo) y **Avistamientos**.

Sus datos iniciales viven en `aves/fixtures/datos_iniciales.json`.

## Servicios y puertos

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Web Django | 3000 | Aplicación (todas las páginas) |
| BirdNET | 8080 | Analizador de cantos (`servidor_birdnet.py`) |
| PostgreSQL | 5432 | Base de datos `birdwatch` (servicio del equipo) |

## Especie identificada: chinigüe (copetón)

Por decisión del proyecto, en esta primera versión la app **solo identifica al
chinigüe (copetón)** (*Zonotrichia capensis*), aunque BirdNET conozca más de
6.000 aves del mundo. Así el resultado siempre es claro y controlado.

La lista de especies permitidas vive en `core/birdnet.py`, en la constante
`ESPECIES_PERMITIDAS`:

```python
ESPECIES_PERMITIDAS = [
    "Zonotrichia capensis_Rufous-collared Sparrow",  # chinigüe (copetón)
]
```

Cada etiqueta tiene el formato `"NombreCientifico_NombreComunEnIngles"`.
Para agregar otra ave, añade su etiqueta a la lista; para dejar que BirdNET
devuelva cualquier ave de la región, cambia la lista a `[]` (vacía). Después
de editar, reinicia la web y el analizador con `DETENER-BIRDWATCH.bat` y
`INICIAR-BIRDWATCH.bat`.

## Configuración avanzada

Todo se puede cambiar con variables de entorno antes de iniciar:

- `DATABASE_URL`: cadena de conexión PostgreSQL, por ejemplo
  `postgres://usuario:clave@servidor:5432/birdwatch`
  (por defecto `postgres://birdwatch:birdwatch@localhost:5432/birdwatch`).
- `BIRDNET_URL`: URL del analizador BirdNET (por defecto
  `http://localhost:8080`).
- `DJANGO_CSRF_ORIGINS`: orígenes adicionales confiables para el formulario
  de análisis, separados por comas (útil al servir con HTTPS).
- `DJANGO_SECRET_KEY` y `DJANGO_DEBUG=0`: para un despliegue real.

### Comandos útiles de Django

```
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:3000 --noreload
.venv\Scripts\python.exe manage.py sembrar          (recarga las aves)
.venv\Scripts\python.exe manage.py createsuperuser --username user
```

## Notas técnicas

- El paquete `birdnet_analyzer` 2.4 de PyPI ya no incluye su módulo `server`;
  por eso `servidor_birdnet.py` implementa la misma API (multipart
  `audio`+`meta` → JSON de resultados) usando la biblioteca interna del
  analizador.
- El servidor BirdNET usa un solo hilo (la configuración global del analizador
  no es segura entre hilos), igual que el servidor original.
- Las grabaciones que el analizador conserva (si se pide `save` en el meta)
  van a la carpeta temporal de Windows (`%TEMP%\birdwatch-subidas`).

## Créditos

- **BirdNET** y el modelo BirdNET GLOBAL 6K V2.4: Laboratorio de Ornitología
  de Cornell e Institut für Vogelforschung (licencia CC BY-NC-SA 4.0).
- **Fotos de las aves**: Wikimedia Commons — Michael Gäbler (CC BY 3.0),
  Joseph C. Boone (CC BY-SA 4.0), Charles J. Sharp (CC BY-SA 4.0), Mike's
  Birds (CC BY-SA 2.0) y Félix Uribe (CC BY 2.0).
- **PostgreSQL**, **Django**, **Python**, **bottle**: software libre de sus
  respectivos autores.
