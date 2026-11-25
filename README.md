# BirdWatch · San Antonio del Tequendama

> **«Cada ave cuenta, cada observación importa»**

Aplicativo web **híbrido (celular y computador)** para identificar las aves de
San Antonio del Tequendama (Cundinamarca, Colombia) **por su canto** y construir
una **comunidad de observación ciudadana**.

- Identificación con **BirdNET** (Laboratorio de Ornitología de Cornell).
- Registro de **avistamientos** con ubicación, especie, foto y notas.
- **Mapa interactivo** con **Leaflet + OpenStreetMap** (gratis, ligero, sin APIs de pago) que muestra
  únicamente **Parque Nacional Natural Chicaque**, **Zoológico Santa Cruz** y **Reserva Natural Kendama**.
- **Centro de ayuda**, **contacto** y **código de conducta**. Estadísticas, noticias y la sección del
  aliado permanecen **desactivadas** hasta que haya información real.
- El convenio con **6:B Colombia — red de observadores** todavía no existe; no se muestra públicamente.

---

## 1. Roles

| Rol | Qué puede hacer |
|-----|-----------------|
| **Acceso público** | Ver la portada informativa, el selector y las páginas de los parques, el mapa, los avistamientos aprobados, la ayuda y la conducta. No requiere login. Las secciones desactivadas no son públicas. |
| **Usuario** | Todo lo anterior + registrar avistamientos, comentar y validar información. Puede crear su cuenta en `/registrarse/`. |
| **Administrador** (`is_staff`/`is_superuser`) | Todo lo anterior + aprobar contenido, controlar registros y gestionar lugares, secciones y noticias desde `/contenido/admin/` y `/admin/`. |
| **Superadministrador** (`is_superuser`) | Todo lo anterior + editar el **carrusel de aves** (`/carrusel/`) y el **carrusel de fotos de cada parque** (`/contenido/admin/parques/`). |

El acceso se hace con **correo electrónico y contraseña**. Después de sembrar, el superadministrador
usa el correo `user@birdwatch.local`; la clave inicial se toma de `BIRDWATCH_ADMIN_PASSWORD`
(valor por defecto solo para el entorno local).

---

## 2. Módulos

| Módulo | Ruta | Descripción |
|--------|------|-------------|
| Portada | `/` | Portada informativa pública, carrusel de aves, visión y misión. Las demás secciones aparecen solo si están activas. |
| **Parques** | `/parques/` | **Selector de parques: es la página que se abre al pulsar el logo.** |
| **Página de un parque** | `/parques/<slug>/` | Página personalizada: portada, eslogan, descripción, carrusel de fotos y avistamientos del lugar. |
| Portada alterna | `/portada/` | Vista histórica de la app `aves` (se conserva por compatibilidad). |
| Identificador | `/identificar/` | Micrófono → WAV → BirdNET → especies con % de confianza. |
| Avistamientos | `/avistamientos/` | Listado con filtros por zona, especie y texto. |
| Registrar | `/avistamientos/nuevo/` | Formulario sencillo con especie, fecha, lugar, zona, coordenadas, foto y notas. |
| Ficha | `/avistamientos/<id>/` | Detalle, comentarios y validaciones. |
| Por aprobar | `/avistamientos/pendientes/` | Cola de revisión del administrador. |
| Mapa | `/mapa/` | Leaflet + OpenStreetMap solo con los 3 lugares de observación. |
| Datos del mapa | `/mapa/datos/` | JSON con los lugares (útil para integraciones). |
| Estadísticas | `/estadisticas/` | Desactivada por defecto; el administrador puede activarla desde el panel de contenido. |
| Noticias | `/noticias/` | Desactivada por defecto; no hay contenido publicado aún. |
| Ayuda | `/ayuda/` | Preguntas frecuentes + guía para identificar aves. |
| Contacto | `/contacto/` | Formulario de mensajes; los guarda en la base de datos. |
| Conducta | `/conducta/` | Normas para respetar a las aves y su hábitat. |
| Registrarse | `/registrarse/` | Alta pública de usuarios con correo y contraseña. |
| Recuperar clave | `/recuperar/` | Envía un código de 6 dígitos por correo y permite crear una nueva clave. |
| Panel de contenido | `/contenido/admin/` | Agregar/editar/eliminar parques, secciones y noticias; activar o desactivar secciones. |
| **Carrusel de parques** | `/contenido/admin/parques/` | **Solo superadministrador:** fotos de cada parque (subir, ordenar, ocultar, eliminar). |
| Carrusel de aves | `/carrusel/` | Solo superadministrador: edita el carrusel de la portada. |
| Admin | `/admin/` | Usuarios, contenido y registros. |

---

## 3. Inicio rápido (tres comandos)

Requisitos: **Python 3.12 o superior** y **PostgreSQL** (servicio local en el puerto 5432).
Si no quieres usar PostgreSQL, define `DB_ENGINE=sqlite` y se empleará `db.sqlite3`.

```bat
python -m venv env --system-site-packages
env\Scripts\python.exe -m pip install -r requirements.txt
env\Scripts\python.exe manage.py preparar
env\Scripts\python.exe manage.py runserver
```

> En este equipo el entorno virtual se llama `env`. El script `INICIAR-BIRDWATCH.bat`
> detecta `env` o `.venv` y usa SQLite automáticamente si PostgreSQL no autentica.

La aplicación queda en <http://localhost:3000>.

- `preparar` aplica las migraciones y siembra los datos iniciales (usuarios, aves,
  parques del mapa, secciones, noticias y preguntas). Es **idempotente**.
- `runserver` inicia **Django en el puerto 3000 y BirdNET en el 8080 automáticamente**.
  La primera vez BirdNET tarda unos 15 segundos en cargar el modelo (224 MB).
  Si quieres arrancar solo la web: `python manage.py runserver --sin-birdnet`.

### Base de datos PostgreSQL

La conexión por defecto es `postgres://birdwatch:birdwatch@localhost:5432/birdwatch`.
Si es la primera vez en el equipo, crea el usuario y la base desde `psql` como superusuario:

```sql
CREATE ROLE birdwatch LOGIN PASSWORD 'birdwatch';
CREATE DATABASE birdwatch OWNER birdwatch;
```

Para usar otra base o servidor:

```bat
set DATABASE_URL=postgres://usuario:clave@servidor:5432/basedatos
```

> También existe el modo SQLite (`set DB_ENGINE=sqlite`) solo para pruebas rápidas
> sin PostgreSQL; no se usa en producción.

Los datos que siembra `preparar`:

- `sembrar`: superusuario, usuario de prueba y 9 aves del carrusel (acceso por correo).
- `loaddata`: catálogo de aves de la comunidad.
- `sembrar_comunidad`: especies, avistamientos, los 3 lugares del mapa, 5 secciones
  (solo «mapa» y «ayuda» activas), noticias y preguntas frecuentes.

---

## 4. Cómo se usa

### 4.1 Iniciar

- **Opción recomendada:** `python manage.py runserver` (levanta web + BirdNET).
- **Atajo en Windows:** doble clic en **`INICIAR-BIRDWATCH.bat`**.

> El atajo usa el entorno `env` (o `.venv`) y comprueba PostgreSQL antes de arrancar:
> si no está activo o las credenciales fallan, se inicia con `DB_ENGINE=sqlite`.

La web queda en <http://localhost:3000> y BirdNET en el puerto 8080.
Para detener todo: `DETENER-BIRDWATCH.bat` o `Ctrl+C` en la consola de `runserver`.

> Si prefieres arrancar los servicios por separado:
>
> ```
> .venv\Scripts\python.exe servidor_birdnet.py --host 127.0.0.1 --port 8080
> .venv\Scripts\python.exe manage.py runserver 0.0.0.0:3000 --noreload
> ```

### 4.2 Entrar, registrarse y recuperar la clave

- **Iniciar sesión** (`/entrar/`): campos **Correo electrónico** y **Contraseña**.
  El correo es el identificador de acceso; el `username` interno se genera desde el nombre.
- **¿No tienes cuenta?** → `/registrarse/` crea un Usuario (no administrador).
- **¿Ya tienes cuenta?** → `/entrar/` desde el formulario de registro.
- **Cambiar nombre o correo** → `/cuenta/` (pide la contraseña actual). El `username`
  se recalcula a partir del nombre; el correo se puede cambiar sin perder la sesión.
- **¿Olvidaste tu contraseña?** → `/recuperar/` envía un código de 6 dígitos al correo,
  se valida en `/recuperar/verificar/` y se guarda la nueva clave en `/recuperar/nueva-clave/`.

En desarrollo el correo se imprime en la consola de Django (`EMAIL_BACKEND=console`). Para enviarlo
de verdad configura estas variables antes de iniciar:

```
set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
set EMAIL_HOST=smtp.tuservidor.com
set EMAIL_PORT=587
set EMAIL_HOST_USER=tu-usuario
set EMAIL_HOST_PASSWORD=tu-clave
set EMAIL_FROM=BirdWatch <no-reply@birdwatch.local>
set CODIGO_RECUPERACION_MINUTOS=15
```

### 4.3 Identificar un ave

1. Pulsa el botón **«Identificar un ave por su canto»** (o entra a `/identificar/`).
2. Pulsa **Grabar** y acepta el permiso del micrófono.
3. Acerca el equipo al canto y graba entre 3 y 15 segundos.
4. Aparecen las especies probables con su confianza y se guarda la detección.

BirdNET descarta voces humanas, motores e insectos y exige **≥ 20 % de confianza**.

### 4.4 Participar en la comunidad

1. Entra a **Avistamientos** → **Registrar avistamiento**.
2. Elige la especie, la fecha, el lugar y la zona del parque.
3. Añade coordenadas (opcional) y una foto. El **mapa público ya no muestra avistamientos**:
   solo los lugares de observación gestionados por el administrador.
4. Un administrador aprueba el registro; después puede comentarse y validarse.

### 4.5 Detener

Doble clic en **`DETENER-BIRDWATCH.bat`** o cierra las ventanas "BirdNET" y "Django BirdWatch".

---

## 5. Desde el celular

1. Conectado a la misma Wi-Fi, abre `http://IP-DEL-COMPUTADOR:3000` (`ipconfig`).
2. El navegador solo permite el micrófono en **HTTPS** o en `localhost`; para grabar
   desde el celular hay que servir con HTTPS.
3. El diseño es responsivo: menú, carrusel, formularios, mapa y tablas se adaptan al teléfono.

---

## 6. Estructura del proyecto

```
birdwatch/                 Configuración (settings, urls, context processors)
  settings.py              Apps, BD, correo/SMTP, idioma, MEDIA, redes
  urls.py                  Todas las rutas del sitio
  context_processors.py    Frase, redes y secciones activas en las plantillas
core/                      Identificación por canto, acceso y carrusel de aves
  birdnet.py               Cliente BirdNET, umbral 20 %, filtros anti-ruido
  traducciones.py          Inglés → español
  models.py                Ave, Deteccion y CodigoRecuperacion
  forms.py / views.py      Login, registro, recuperación, identificar, analizar
  urls.py                  Rutas de acceso y del carrusel
  permisos.py              Decoradores de roles (Usuario / Administrador / Superadmin)
  data/aves.json           Aves del carrusel
  management/commands/     sembrar, preparar y runserver (arranca BirdNET solo)
aves/                      Catálogo y comunidad de avistamientos
  models.py                Ave, Avistamiento, Comentario, Validación
  forms.py / views.py / urls.py / admin.py
  estadisticas.py          Cálculo centralizado de destacados (el mapa ya no los usa)
  management/commands/sembrar_comunidad.py
contenido/                 Contenido dinámico, parques y panel de administración
  models.py                Noticia, PreguntaFrecuente, MensajeContacto,
                           LugarObservacion (página del parque) y FotoParque (carrusel)
  views.py / urls.py / forms.py / admin.py
plantillas/                TODAS las páginas HTML en un solo lugar
  base.html, inicio.html, login.html, registrarse.html, identificar.html…
  aves/                    Listado, formulario, ficha, mapa, estadísticas…
  contenido/               Noticias, ayuda, contacto, conducta, panel_admin,
                           parques.html, parque_detalle.html y el panel de fotos
  carrusel_admin.html      Panel del carrusel de aves
  carrusel_form.html       Alta y edición de aves del carrusel
estaticos/                 TODOS los archivos estáticos en un solo lugar
  css/estilos.css          Diseño principal (incluye parques)
  css/comunidad.css        Estilos de los módulos de comunidad
  js/mapa.js               Marcadores de lugares Leaflet desde JSON
  js/identificar.js        Micrófono y envío de audio
  js/carrusel.js           Carruseles de la portada y de cada parque
  img/logo.png             Logo redondo
medios/                    Fotos subidas (parques, avistamientos, noticias); no va a git
servidor_birdnet.py        Servidor HTTP del analizador (bottle, puerto 8080)
INICIAR-BIRDWATCH.bat      Atajo de arranque para Windows
DETENER-BIRDWATCH.bat      Detención de servicios
```

---

## 7. Mapa (Leaflet + OpenStreetMap)

No hay que pagar nada ni registrar API keys:

- CSS: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css`
- JS: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`
- Teselas: `https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}` (Esri World Street Map, sin API key).
  No se usa CARTO: su endpoint público devuelve una imagen que dice «API KEY REQUIRED».

Los lugares se gestionan en `contenido/models.py::LugarObservacion` y se inyectan en la
plantilla con `json_script`. El administrador puede agregar, editar, eliminar, ocultar y
dar coordenadas a cada lugar desde `/contenido/admin/`.

Los **únicos** lugares sembrados son:

| Lugar | Ubicación | Coordenadas |
|-------|-----------|-------------|
| Parque Nacional Natural Chicaque | Soacha, Cundinamarca | 4.606944, -74.302778 |
| Zoológico Santa Cruz | San Andrés de Antonio | 4.583569, -74.332948 |
| Reserva Natural Kendama | Ubicación por definir | **sin coordenadas** (no se inventan) |

El mapa **ya no muestra avistamientos de aves**. Kendama se lista como «Ubicación por definir»
hasta que se confirme oficialmente. No se inventan parques adicionales.

---

## 8. Identificación por canto (detalles)

`ESPECIES_PERMITIDAS = []` → BirdNET identifica cualquier ave (~6.500 especies).
Para limitarlo a unas pocas, edita `core/birdnet.py`:

```python
ESPECIES_PERMITIDAS = [
    "Zonotrichia capensis_Rufous-collared Sparrow",  # chinigüe (copetón)
]
```

`FILTRAR_POR_REGION = False` → se consideran todas las especies. Si se activa,
BirdNET usa las coordenadas de San Antonio del Tequendama y reduce a ~480 especies.

Filtros anti-falsos-positivos:

1. `ETIQUETAS_NO_AVE`: descarta siempre humano, perro, motor, ruido, sirena, insectos, etc.
2. `CONFIANZA_MINIMA = 0.20`: solo se muestran coincidencias ≥ 20 %.

`core/traducciones.py` traduce al español las especies más comunes de Colombia.

---

## 9. Administrar el carrusel de la portada

Solo el superadministrador. Entra a `/carrusel/` (enlace **Carrusel** en la cabecera).

- **Añadir un ave** con foto (JPG/PNG ≤ 10 MB; se reduce a 1280 px).
- **Editar**, **ordenar** (▲ ▼), **ocultar/mostrar** y **eliminar**.
- Los cambios se ven al instante en `/`.

También se puede gestionar desde `/admin/`, pero el panel Carrusel es el recomendado.

---

## 10. Parques: página propia y carrusel de fotos

Cada parque registrado tiene una página personalizada y su propio carrusel.

### 10.1 Cómo entra el visitante

1. El **logo** de la cabecera abre el **selector de parques** (`/parques/`).
2. También hay un enlace **Parques** en el menú principal.
3. Al elegir un parque se abre su página: `/parques/<slug>/` con portada, eslogan,
   descripción, carrusel de fotos y los avistamientos aprobados en ese lugar.

El carrusel se pausa al pasar el mouse, responde a las flechas del teclado y se puede
deslizar con el dedo en el celular.

### 10.2 Registrar un parque (Administrador)

En `/contenido/admin/` → **+ Agregar parque o lugar**. Los campos de la página son:

| Campo | Para qué sirve |
|-------|----------------|
| Nombre | Título de la página y base del `slug`. |
| Slug | Dirección `/parques/<slug>/`. Se genera solo; puedes cambiarlo. |
| Tipo | Parque natural, zoológico, reserva u otro. |
| Ubicación | Texto visible, p. ej. «Soacha, Cundinamarca». |
| Eslogan | Frase corta bajo el nombre. |
| Descripción | Texto de la página del parque. |
| Foto de portada | Imagen principal (opcional). Si no hay, se usa la primera foto del carrusel. |
| Color de acento | Color de la página en hexadecimal (selector de color). |
| Coordenadas | Para que aparezca en el mapa (opcional). |

Las fotos se reducen y comprimen solas (máximo 1600 px, JPG optimizado).

### 10.3 Editar el carrusel de un parque (solo superadministrador)

Entra a `/contenido/admin/parques/` (enlace **Parques admin** en la cabecera) y pulsa
**Fotos** en el parque que quieras. Desde ahí puedes:

- **Añadir foto** (JPG/PNG ≤ 10 MB) con título, descripción y posición.
- **Editar** los datos de la foto.
- **Ordenar** con ▲ ▼.
- **Ocultar/mostrar** una foto sin borrarla.
- **Eliminar** la foto (también borra el archivo de `medios/parques/`).

Los cambios se ven de inmediato en la página pública del parque. El panel de fotos
también es accesible desde el botón **Editar carrusel** en la propia página del parque.

> Solo el superadministrador ve y usa estos botones; el resto de usuarios y los
> visitantes anónimos solo pueden ver las páginas.

---

## 11. Configuración avanzada

| Variable | Uso |
|----------|-----|
| `DB_ENGINE=sqlite` | Base local `db.sqlite3` (sin PostgreSQL). |
| `DATABASE_URL` | Cadena PostgreSQL, p. ej. `postgres://usuario:clave@servidor:5432/birdwatch`. |
| `BIRDNET_URL` | URL del analizador (por defecto `http://localhost:8080`). |
| `DJANGO_CSRF_ORIGINS` | Orígenes adicionales para HTTPS. |
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` | Para un despliegue real. |

Las redes sociales y la frase inspiradora se editan en un solo lugar:
`birdwatch/settings.py` (`REDES_SOCIALES`, `FRASE_INSPIRADORA`, `ALIADO`).

Comandos útiles:

```
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py preparar
.venv\Scripts\python.exe manage.py runserver
```

---

## 12. Notas técnicas

- `birdnet_analyzer` 2.4 ya no trae su módulo `server`; `servidor_birdnet.py`
  reimplementa la API con `bottle`.
- Si faltan los archivos V2.4 en `checkpoints/`, se descargan de un espejo público en
  Hugging Face; el dominio original (`tuc.cloud`) no siempre resuelve.
- El servidor BirdNET usa un solo hilo (configuración global no segura entre hilos).
- Las grabaciones del analizador van a `%TEMP%\birdwatch-subidas`.
- Las fotos subidas van a `medios/` (`avistamientos/`, `noticias/`, `parques/`).
- Leaflet y OpenStreetMap se cargan por CDN; no hay dependencias de pago.

---

## 13. Créditos

- **BirdNET** y el modelo GLOBAL 6K V2.4: Cornell Lab of Ornithology e
  Institut für Vogelforschung (CC BY-NC-SA 4.0).
- **Fotos de las aves**: Wikimedia Commons — Michael Gäbler (CC BY 3.0),
  Joseph C. Boone (CC BY-SA 4.0), Charles J. Sharp (CC BY-SA 4.0), Mike's
  Birds (CC BY-SA 2.0) y Félix Uribe (CC BY 2.0).
- **OpenStreetMap** y sus colaboradores (ODbL); **Leaflet** (BSD 2-Clause).
- **Django**, **Python**, **bottle**, **Pillow**, **PostgreSQL**: software libre.
