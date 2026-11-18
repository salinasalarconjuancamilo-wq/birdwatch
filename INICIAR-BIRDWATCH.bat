@echo off
rem ============================================================
rem  BirdWatch - San Antonio del Tequendama, Cundinamarca
rem  Arranca todo con un solo comando:
rem    python manage.py runserver
rem  Ese comando inicia la web (puerto 3000) y el analizador
rem  BirdNET (puerto 8080) automaticamente.
rem
rem  Requisitos (una sola vez):
rem    python -m venv .venv
rem    .venv\Scripts\python.exe -m pip install -r requirements.txt
rem    .venv\Scripts\python.exe manage.py preparar
rem ============================================================
title BirdWatch - arranque
cd /d "%~dp0"
echo.
echo  === BirdWatch - San Antonio del Tequendama ===
echo.

rem ---------- PostgreSQL (servicio local del sistema) ----------
echo [1/2] Verificando PostgreSQL local...
netstat -ano | findstr ":5432 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo       El PostgreSQL local no esta corriendo.
    echo       Inicia el servicio "postgresql-x64-18" desde la app
    echo       de Servicios de Windows y vuelve a ejecutar este archivo.
    pause
    exit /b 1
)
echo       PostgreSQL local listo ^(puerto 5432^).

rem ---------- Entorno virtual ----------
if not exist ".venv\Scripts\python.exe" (
    echo [2/2] Creando el entorno virtual e instalando dependencias...
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo [2/2] Entorno virtual listo.
)

echo.
echo  Arrancando BirdWatch ^(web en 3000 + BirdNET en 8080^)...
echo  Para detener todo: ejecuta DETENER-BIRDWATCH.bat
echo.
start "Django BirdWatch" /min ".venv\Scripts\python.exe" manage.py runserver
timeout /t 6 /nobreak >nul
start "" "http://localhost:3000"
exit /b 0
