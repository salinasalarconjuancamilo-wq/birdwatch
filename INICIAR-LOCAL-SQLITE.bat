@echo off
rem ============================================================
rem  BirdWatch - SQLite local (sin PostgreSQL)
rem  Prepara la base, siembra datos, arranca BirdNET y la web.
rem ============================================================
title BirdWatch - SQLite local
cd /d "%~dp0"
set DB_ENGINE=sqlite

if not exist ".venv\Scripts\python.exe" (
    echo No se encontro el entorno virtual ".venv".
    echo Crea uno con: python -m venv .venv --system-site-packages
    echo Luego: .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

set PY=.venv\Scripts\python.exe

echo.
echo === BirdWatch - San Antonio del Tequendama (SQLite) ===
echo.

echo [1/4] Aplicando migraciones...
%PY% manage.py migrate

echo [2/4] Cargando datos iniciales...
%PY% manage.py sembrar
%PY% manage.py loaddata aves/fixtures/datos_iniciales.json
%PY% manage.py sembrar_comunidad

echo [3/4] Arrancando el analizador BirdNET (puerto 8080)...
start "BirdNET" /MIN %PY% servidor_birdnet.py --host 127.0.0.1 --port 8080

echo [4/4] BirdWatch corriendo en:  http://localhost:3000
echo Usuario: user   Contrasena: 1234
echo Para detenerlo: cierra esta ventana o pulsa Ctrl+C.
echo.
%PY% manage.py runserver 0.0.0.0:3000 --noreload
pause
