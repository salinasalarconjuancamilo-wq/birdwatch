@echo off
setlocal EnableDelayedExpansion
rem ============================================================
rem  BirdWatch - San Antonio del Tequendama, Cundinamarca
rem  Arranca todo con un solo comando:
rem    python manage.py runserver
rem  Ese comando inicia la web (puerto 3000) y el analizador
rem  BirdNET (puerto 8080) automaticamente.
rem
rem  Requisitos (una sola vez):
rem    python -m venv env --system-site-packages
rem    env\Scripts\python.exe -m pip install -r requirements.txt
rem    env\Scripts\python.exe manage.py preparar
rem ============================================================
title BirdWatch - arranque
cd /d "%~dp0"

rem ---------- Modo desarrollo ----------
rem  Por seguridad DJANGO_DEBUG es False por defecto; este arranque local lo
rem  activa para poder ver los archivos estaticos sin collectstatic.
set "DJANGO_DEBUG=1"

echo.
echo  === BirdWatch - San Antonio del Tequendama ===
echo.

rem ---------- IntÃ©rprete de Python ----------
set "PY="
if exist "env\Scripts\python.exe" set "PY=env\Scripts\python.exe"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY (
    echo [1/3] Creando el entorno virtual "env" e instalando dependencias...
    python -m venv env --system-site-packages
    set "PY=env\Scripts\python.exe"
    "!PY!" -m pip install -r requirements.txt
) else (
    echo [1/3] Entorno virtual listo: !PY!
)

rem ---------- Base de datos ----------
rem  Se usa PostgreSQL si esta activo y acepta las credenciales de
rem  settings.py (o DATABASE_URL). Si no, se usa el SQLite local.
set "DB_ENGINE="
netstat -ano | findstr ":5432 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    "!PY!" manage.py shell -c "from django.db import connection; connection.ensure_connection()" >nul 2>&1
    if errorlevel 1 (
        echo       PostgreSQL no acepta las credenciales actuales.
        echo       Se usa SQLite local ^(db.sqlite3^).
        set "DB_ENGINE=sqlite"
    ) else (
        echo       PostgreSQL local listo ^(puerto 5432^).
    )
) else (
    echo       PostgreSQL no esta activo; se usa SQLite local ^(db.sqlite3^).
    set "DB_ENGINE=sqlite"
)

rem ---------- Migraciones y datos iniciales ----------
echo [2/3] Preparando base de datos...
"!PY!" manage.py preparar

echo.
echo [3/3] Arrancando BirdWatch (web en 3000 + BirdNET en 8080)...
echo  Para detener todo: ejecuta DETENER-BIRDWATCH.bat
echo.
start "Django BirdWatch" /min cmd /c ""!PY!" manage.py runserver 0.0.0.0:3000"
timeout /t 6 /nobreak >nul
start "" "http://localhost:3000"
exit /b 0
