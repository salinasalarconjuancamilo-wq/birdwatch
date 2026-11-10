# Birdwatch 🐦

Base de datos para el registro de avistamientos de aves, hecha con **Django**.

## Estructura de la base de datos

La app **`aves`** tiene dos tablas:

| Tabla | Descripción | Campos |
|---|---|---|
| `Ave` | Catálogo de aves | nombre común, nombre científico, familia, color, tamaño, foto (URL) |
| `Avistamiento` | Registro de un avistamiento | ave (relación), fecha, lugar, cantidad, notas |

Un `Avistamiento` está relacionado a un `Ave` (una ave puede tener muchos avistamientos).

## Cómo ejecutar el proyecto

1. Crear el entorno virtual (aprovecha el Django instalado en el equipo):

   ```
   python -m venv env --system-site-packages
   ```

   Si tienes acceso a internet también puedes usar `python -m venv env` y luego `env\Scripts\pip install django`.

2. Activar el entorno:

   ```
   .\env\Scripts\activate
   ```

3. Aplicar las migraciones (esto crea la base de datos `db.sqlite3`):

   ```
   python manage.py migrate
   ```

4. (Opcional) Cargar los datos de ejemplo (5 aves y 5 avistamientos):

   ```
   python manage.py loaddata datos_iniciales
   ```

5. Crear tu usuario administrador:

   ```
   python manage.py createsuperuser
   ```

6. Encender el servidor:

   ```
   python manage.py runserver
   ```

   y abrir http://127.0.0.1:8000/admin/ en el navegador.

## Flujo de trabajo en equipo ⚠️

Para que **los cambios de tu compañero y los tuyos aparezcan en el repositorio**, sigue este orden:

1. **Antes de empezar a trabajar**, baja lo que haya subido el otro:

   ```
   git pull origin main
   ```

2. **Trabaja**: crea o modifica archivos, registra aves en el admin, etc.

3. **Guarda tus cambios**:

   ```
   git add .
   git commit -m "Descripción de lo que hiciste"
   ```

4. **Súbelos a GitHub**:

   ```
   git push origin main
   ```

5. Si el `push` falla porque el otro ya subió cambios, ejecuta primero:

   ```
   git pull origin main --no-rebase
   ```

   Git intentará fusionar todo. Si marca **conflicto** en un archivo, ábrelo en un editor de código, deja las dos versiones como mejor convenga, guarda, y luego:

   ```
   git add .
   git commit -m "Fusion de cambios"
   git push origin main
   ```

### Cómo compartir los datos que registres

La base de datos local (`db.sqlite3`) **no se sube a GitHub** (cada uno genera la suya). Para compartir los registros del admin, expórtalos como fixture:

```
python manage.py dumpdata aves --indent 2 -o aves/fixtures/mis_registros.json
git add . && git commit -m "Mis registros de avistamientos" && git push origin main
```

Y el compañero los carga con:

```
python manage.py loaddata mis_registros
```
