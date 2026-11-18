# BirdWatch · San Antonio del Tequendama

> **«Cada ave cuenta, cada observación importa»**

Aplicativo web **híbrido (celular y computador)** para identificar las aves de
San Antonio del Tequendama (Cundinamarca, Colombia) **por su canto** y construir
una **comunidad de observación ciudadana**.

- Identificación con **BirdNET** (Laboratorio de Ornitología de Cornell).
- Registro de **avistamientos** con ubicación, especie, foto y notas.
- **Mapa interactivo** con **Leaflet + OpenStreetMap** (gratis, ligero, sin APIs de pago).
- **Noticias**, **estadísticas**, **centro de ayuda**, **contacto** y **código de conducta**.
- Aliado: **6:B Colombia — red de observadores**.

---

## 1. Roles

| Rol | Qué puede hacer |
|-----|-----------------|
| **Acceso público** | Ver la portada, noticias, avistamientos aprobados, mapa, estadísticas, ayuda y conducta. No requiere login. |
| **Usuario** | Todo lo anterior + registrar avistamientos, comentar y validar información. |
| **Administrador** (`is_staff`/`is_superuser`) | Todo lo anterior + aprobar contenido, controlar registros, gestionar usuarios y noticias desde `/admin/`. |

El usuario inicial es `user` / `1234` (superadministrador).

---

## 2. Módulos

| Módulo | Ruta | Descripción |
|--------|------|-------------|
| Portada | `/` | Carrusel de aves, destacados en vivo y últimas noticias. |
| Portada alterna | `/portada/` | Vista histórica de la app `aves` (se conserva por compatibilidad). |
| Identificador | `/identificar/` | Micrófono → WAV → BirdNET → especies con % de confianza. |
| Avistamientos | `/avistamientos/` | Listado con filtros por zona, especie y texto. |
| Registrar | `/avistamientos/nuevo/` | Formulario sencillo con especie, fecha, lugar, zona, coordenadas, foto y notas. |
| Ficha | `/avistamientos/<id>/` | Detalle, comentarios y validaciones. |
| Por aprobar | `/avistamientos/pendientes/` | Cola de revisión del administrador. |
| Mapa | `/mapa/` | Leaflet + OpenStreetMap con los avistamientos georreferenciados. |
| Datos del mapa | `/mapa/datos/` | JSON con los marcadores (útil para integraciones). |
| Estadísticas | `/estadisticas/` | Especie más avistada, Top 10, más observadas, especies por zona, casos especiales e info del parque. |
| Noticias | `/noticias/` | Novedades dinámicas del proyecto y del parque. |
| Ayuda | `/ayuda/` | Preguntas frecuentes + guía para identificar aves. |
| Contacto | `/contacto/` | Formulario de mensajes; los guarda en la base de datos. |
| Conducta | `/conducta/` | Normas para respetar a las aves y su hábitat. |
| Carrusel | `/carrusel/` | Panel del superadministrador para editar la portada. |
| Admin | `/admin/` | Usuarios, contenido y registros. |

---

## 3. Requisitos del equipo (una sola vez)

- **Python 3.12 o superior**.
- **PostgreSQL** opcional: con `DB_ENGINE=sqlite` no se necesita nada más.
  Si se usa PostgreSQL (servicio de Windows, puerto 5432):

  ```sql
  CREATE ROLE birdwatch LOGIN PASSWORD 'birdwatch';
  CREATE DATABASE birdwatch OWNER birdwatch;
  ```

- Entorno virtual e dependencias:

  ```
  python -m venv .venv --system-site-packages
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  ```

- Tablas y datos de ejemplo:

  ```
  set DB_ENGINE=sqlite
  .venv\Scripts\python.exe manage.py migrate
  .venv\Scripts\python.exe manage.py sembrar
  .venv\Scripts\python.exe manage.py loaddata aves/fixtures/datos_iniciales.json
  .venv\Scripts\python.exe manage.py sembrar_comunidad
  ```

  - `sembrar`: superusuario (`user` / `1234`) y 9 aves del carrusel.
  - `sembrar_comunidad`: especies, avistamientos con coordenadas, 4 noticias y 6 preguntas frecuentes. Es **idempotente**.

---

## 4. Cómo se usa

### 4.1 Iniciar

- **Con PostgreSQL**: doble clic en **`INICIAR-BIRDWATCH.bat`**.
- **Sin PostgreSQL**: doble clic en **`INICIAR-LOCAL-SQLITE.bat`** (usa `DB_ENGINE=sqlite`).

Ambos dejan la web en <http://localhost:3000>. El analizador BirdNET arranca en el
puerto 8080. La primera vez tarda unos 15 segundos en cargar el modelo (224 MB).

> Si el `.bat` no arranca en tu intérprete de comandos, ejecuta manualmente:
>
> ```
> set DB_ENGINE=sqlite
> .venv\Scripts\python.exe servidor_birdnet.py --host 127.0.0.1 --port 8080
> .venv\Scripts\python.exe manage.py runserver 0.0.0.0:3000 --noreload
> ```

### 4.2 Entrar

Usuario `user` · contraseña `1234`.

### 4.3 Identificar un ave

1. Pulsa el botón **«Identificar un ave por su canto»** (o entra a `/identificar/`).
2. Pulsa **Grabar** y acepta el permiso del micrófono.
3. Acerca el equipo al canto y graba entre 3 y 15 segundos.
4. Aparecen las especies probables con su confianza y se guarda la detección.

BirdNET descarta voces humanas, motores e insectos y exige **≥ 20 % de confianza**.

### 4.4 Participar en la comunidad

1. Entra a **Avistamientos** → **Registrar avistamiento**.
2. Elige la especie, la fecha, el lugar y la zona del parque.
3. Añade coordenadas (opcional) para que aparezca en el **mapa**, y una foto.
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
  settings.py              Apps, BD (PostgreSQL/SQLite), idioma, MEDIA, redes
  urls.py                  Todas las rutas del sitio
  context_processors.py    Frase, aliado y redes en todas las plantillas
core/                      Identificación por canto (BirdNET) y carrusel
  birdnet.py               Cliente BirdNET, umbral 20 %, filtros anti-ruido
  traducciones.py          Inglés → español
  views.py / urls.py       Portada, login, identificar, analizar, carrusel
  permisos.py              Decoradores de roles (Usuario / Administrador)
  data/aves.json           Aves del carrusel
aves/                      Catálogo y comunidad de avistamientos
  models.py                Ave, Avistamiento, Comentario, Validación
  forms.py / views.py / urls.py / admin.py
  estadisticas.py          Cálculo centralizado de destacados y marcadores
  management/commands/sembrar_comunidad.py
  templates/aves/          Listado, formulario, ficha, mapa, estadísticas…
contenido/                 Contenido dinámico
  models.py                Noticia, PreguntaFrecuente, MensajeContacto
  views.py / urls.py / forms.py / admin.py
  templates/contenido/     Noticias, ayuda, contacto, conducta
plantillas/                base.html, inicio.html, login, identificar, carrusel
estaticos/
  css/estilos.css          Diseño principal
  css/comunidad.css        Estilos de los módulos de comunidad
  js/mapa.js               Marcadores Leaflet desde JSON
  js/identificar.js        Micrófono y envío de audio
  js/carrusel.js           Carrusel de la portada
  img/logo.png             Logo redondo
servidor_birdnet.py        Servidor HTTP del analizador (bottle, puerto 8080)
INICIAR-BIRDWATCH.bat      Arranque con PostgreSQL
INICIAR-LOCAL-SQLITE.bat   Arranque sin PostgreSQL
DETENER-BIRDWATCH.bat      Detención de servicios
```

---

## 7. Mapa (Leaflet + OpenStreetMap)

No hay que pagar nada ni registrar API keys:

- CSS: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css`
- JS: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`
- Teselas: `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`

Los marcadores se generan en `aves/estadisticas.py::datos_mapa()` y se inyectan
en la plantilla con `json_script`. Un avistamiento aparece en el mapa solo si está
**aprobado** y tiene **latitud y longitud**. Los casos especiales se marcan con ★.

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

## 10. Configuración avanzada

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
.venv\Scripts\python.exe manage.py sembrar_comunidad
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:3000 --noreload
```

---

## 11. Notas técnicas

- `birdnet_analyzer` 2.4 ya no trae su módulo `server`; `servidor_birdnet.py`
  reimplementa la API con `bottle`.
- El servidor BirdNET usa un solo hilo (configuración global no segura entre hilos).
- Las grabaciones del analizador van a `%TEMP%\birdwatch-subidas`.
- Las fotos subidas van a `medios/avistamientos/` y `medios/noticias/` (configurable con `MEDIA_ROOT`).
- Leaflet y OpenStreetMap se cargan por CDN; no hay dependencias de pago.

---

## 12. Créditos

- **BirdNET** y el modelo GLOBAL 6K V2.4: Cornell Lab of Ornithology e
  Institut für Vogelforschung (CC BY-NC-SA 4.0).
- **Fotos de las aves**: Wikimedia Commons — Michael Gäbler (CC BY 3.0),
  Joseph C. Boone (CC BY-SA 4.0), Charles J. Sharp (CC BY-SA 4.0), Mike's
  Birds (CC BY-SA 2.0) y Félix Uribe (CC BY 2.0).
- **OpenStreetMap** y sus colaboradores (ODbL); **Leaflet** (BSD 2-Clause).
- **Django**, **Python**, **bottle**, **Pillow**, **PostgreSQL**: software libre.
