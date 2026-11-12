@echo off
title BirdWatch - SQLite local
cd /d "%~dp0"
set DB_ENGINE=sqlite

if not exist "env\Scripts\python.exe" (
    echo No se encontro el entorno virtual "env".
    echo Crea uno con: python -m venv env --system-site-packages
    pause
    exit /b 1
)

echo Aplicando migraciones...
env\Scripts\python.exe manage.py migrate

echo.
echo BirdWatch corriendo en:  http://localhost:3000
echo Usuario: user   Contrasena: 1234
echo Para detenerlo: cierra esta ventana o pulsa Ctrl+C.
echo.
env\Scripts\python.exe manage.py runserver 0.0.0.0:3000
pause
