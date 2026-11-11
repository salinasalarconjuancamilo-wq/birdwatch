# BirdWatch · San Antonio del Tequendama

Aplicativo web **híbrido (celular y computador)** para identificar las aves de
San Antonio del Tequendama (Cundinamarca, Colombia) **por su canto**, usando la
inteligencia artificial **BirdNET** del Laboratorio de Ornitología de Cornell.
Todo el sistema funciona en la carpeta del proyecto, sin instalaciones previas
ni permisos de administrador.

## Qué incluye

- **Inicio**: carrusel con las 9 aves representativas del municipio (condor
  andino, colibríes, tucán piquiplano, tororoi, candelita y pava andina) y las
  secciones de **visión y misión** del proyecto.
- **Botón con el logo del ave** (un colibrí) que abre la página de
  identificación: pide permiso del micrófono, graba entre 3 y 15 segundos y
  envía el audio a BirdNET con la ubicación del municipio (4.6267, -74.3300).
- **Detecciones guardadas en PostgreSQL** con su nombre en español,
  nombre científico y porcentaje de confianza; se consultan en "Mis últimas
  detecciones" y en el administrador de Django (`/admin/`).
- **Aplicación web progresiva (PWA)**: se puede instalar en el celular desde
  el navegador.
- Interfaz en **español**, con paleta **verde de bosque andino de niebla**.

## Cómo se usa

### 1. Iniciar

Haz doble clic en **`INICIAR-BIRDWATCH.bat`**. El archivo:

1. Arranca **PostgreSQL** en el puerto 5433 (si no estaba corriendo).
2. Arranca el **analizador BirdNET** en el puerto 8080.
3. Arranca la **aplicación web Django** en el puerto 3000.
4. Abre el navegador en <http://localhost:3000>.

> La primera vez, BirdNET tarda unos 15 segundos en cargar el modelo (224 MB).

### 2. Entrar

Por el momento el acceso es solo del superusuario:

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

Haz doble clic en **`DETENER-BIRDWATCH.bat`** (detiene la web, BirdNET y
PostgreSQL) o cierra las ventanas minimizadas "BirdNET" y "Django BirdWatch".

## Uso desde el celular

1. En el celular, conectado a la **misma red Wi-Fi**, abre
   `http://IP-DEL-COMPUTADOR:3000` (la IP se ve con `ipconfig`).
2. **Importante**: los navegadores solo permiten el micrófono en **HTTPS** o
   en `localhost`. Para grabar desde el celular hay que servir la aplicación
   con HTTPS (por ejemplo con un certificado y `runserver --nostatic` tras
   habilitar SSL, o un proxy como Caddy). En el computador, con
   `http://localhost:3000` funciona sin problema.
3. El diseño es responsivo: el carrusel, el login y el identificador se
   adaptan a la pantalla del teléfono.

## Estructura del proyecto

```
INICIAR-BIRDWATCH.bat      Arranca todo (PostgreSQL + BirdNET + web)
INICIAR-BIRDNET.bat        Arranca solo el analizador BirdNET (puerto 8080)
DETENER-BIRDWATCH.bat      Detiene todos los servicios
manage.py                  Utilidades de Django
birdwatch/                 Configuración del proyecto Django (settings, urls)
core/                      Aplicación principal: modelos, vistas, cliente
                           BirdNET, traducciones ES y datos de las aves
aves/                      Aplicación original del repositorio: catálogo de
                           aves y registro de avistamientos (ver abajo)
plantillas/                Páginas HTML (base, inicio, login, identificar)
estaticos/                 CSS, JavaScript, manifest PWA, logo y fotos de aves
servidor_birdnet.py        Servidor HTTP del analizador BirdNET (bottle)
herramientas/python/       Python 3.12 portátil con todas las librerías
herramientas/postgres/     PostgreSQL 16 portátil (puerto 5433)
herramientas/pgdatos/      Clúster de datos de PostgreSQL
descargas/                 Instaladores, registros y scripts de prueba
requirements.txt           Dependencias de Python del proyecto
```

## App `aves`: catálogo y avistamientos (versión original del repositorio)

La primera versión del proyecto traía la aplicación `aves`, que conserva un
**catálogo de aves** (nombre común y científico, familia, color, tamaño y foto)
y el **registro de avistamientos** (ave, fecha, lugar, cantidad y notas). Sigue
instalada y se administra desde el panel de Django:

1. Entra a <http://localhost:3000/admin/> con `user` / `1234`.
2. En la sección **AVES** están **Aves** (catálogo) y **Avistamientos**.

Sus datos iniciales (`aves/fixtures/datos_iniciales.json`) se cargan en la base
de datos PostgreSQL junto con las tablas de la app principal `core`:

```
herramientas\python\python.exe manage.py loaddata aves/fixtures/datos_iniciales.json
```

## Servicios y puertos

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Web Django | 3000 | Aplicación (todas las páginas) |
| BirdNET | 8080 | Analizador de cantos (`servidor_birdnet.py`) |
| PostgreSQL | 5433 | Base de datos `birdwatch` (usuario `birdwatch`) |

## Configuración avanzada

Todo se puede cambiar con variables de entorno antes de iniciar:

- `DATABASE_URL`: cadena de conexión PostgreSQL, por ejemplo
  `postgres://usuario:clave@servidor:5432/birdwatch`.
- `BIRDNET_URL`: URL del analizador BirdNET (por defecto
  `http://localhost:8080`).
- `DJANGO_CSRF_ORIGINS`: orígenes adicionales confiables para el formulario
  de análisis, separados por comas (útil al servir con HTTPS).
- `DJANGO_SECRET_KEY` y `DJANGO_DEBUG=0`: para un despliegue real.

### Comandos útiles de Django

```
herramientas\python\python.exe manage.py runserver 0.0.0.0:3000 --noreload
herramientas\python\python.exe manage.py sembrar          (recarga las aves)
herramientas\python\python.exe manage.py createsuperuser --username user
```

### PostgreSQL manual

```
herramientas\postgres\bin\pg_ctl.exe -D "herramientas\pgdatos" -o "-p 5433" -l "descargas\pg-servidor.log" start
herramientas\postgres\bin\pg_ctl.exe -D "herramientas\pgdatos" -l "descargas\pg-servidor.log" stop
```

Contraseña del usuario `birdwatch`: `birdwatch` (misma base de datos:
`birdwatch`).

## Pruebas incluidas

- `descargas/probar-birdnet.py` — descarga un canto real de Commons y comprueba
  el analizador BirdNET de punta a punta (identificó correctamente el chingolo
  *Zonotrichia capensis*).
- `descargas/probar-django.py` — prueba completa de la web: portada, login
  `user`/`1234`, identificador, análisis de audio, historial y protección por
  sesión.

## Notas técnicas

- El paquete `birdnet_analyzer` 2.4 de PyPI ya no incluye su módulo `server`;
  por eso `servidor_birdnet.py` implementa la misma API (multipart
  `audio`+`meta` → JSON de resultados) usando la biblioteca interna del
  analizador.
- Los binarios de PostgreSQL y TensorFlow requieren las DLLs del runtime de
  Visual C++; ya están incluidas en las carpetas `herramientas\` (copiadas de
  los propios paquetes de Python), así que **no hace falta instalar nada en el
  sistema**.
- El servidor BirdNET usa un solo hilo (la configuración global del analizador
  no es segura entre hilos), igual que el servidor original.

## Créditos

- **BirdNET** y el modelo BirdNET GLOBAL 6K V2.4: Laboratorio de Ornitología
  de Cornell e Institut für Vogelforschung (licencia CC BY-NC-SA 4.0).
- **Fotos de las aves**: Wikimedia Commons — Michael Gäbler (CC BY 3.0),
  Joseph C. Boone (CC BY-SA 4.0), Charles J. Sharp (CC BY-SA 4.0), Mike's
  Birds (CC BY-SA 2.0) y Félix Uribe (CC BY 2.0).
- **Canto de prueba**: *Zonotrichia capensis* vía xeno-canto (XC243300) /
  Wikimedia Commons.
- **PostgreSQL**, **Django**, **Python**, **bottle**: software libre de sus
  respectivos autores.
