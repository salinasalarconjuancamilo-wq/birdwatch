@echo off
rem ============================================================
rem  BirdWatch - San Antonio del Tequendama, Cundinamarca
rem  Inicia todo el aplicativo:
rem    1. PostgreSQL local del equipo (servicio del sistema, puerto 5432)
rem    2. Analizador BirdNET (puerto 8080)
rem    3. Aplicacion web Django (puerto 3000)
rem  Uso: hacer doble clic en este archivo.
rem  Nota: usa el entorno virtual .venv del proyecto (requerimientos
rem  ya instalados con: .venv\Scripts\python.exe -m pip install -r requirements.txt)
rem ============================================================
title BirdWatch - arranque
cd /d "%~dp0"
echo.
echo  === BirdWatch - San Antonio del Tequendama ===
echo.

rem ---------- 1. PostgreSQL (servicio local del sistema) ----------
echo [1/3] Verificando PostgreSQL local...
netstat -ano | findstr ":5432 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo       El PostgreSQL local no esta corriendo.
    echo       Inicia el servicio "postgresql-x64-18" desde la app
    echo       de Servicios de Windows y vuelve a ejecutar este archivo.
) else (
    echo       PostgreSQL local listo (puerto 5432).
)

rem ---------- 2. Analizador BirdNET ----------
echo [2/3] Arrancando el analizador BirdNET...
netstat -ano | findstr ":8080 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    start "BirdNET" /min ".venv\Scripts\python.exe" servidor_birdnet.py --host 127.0.0.1 --port 8080 --spath "%TEMP%\birdwatch-subidas"
    echo       BirdNET arrancando en el puerto 8080 (tarda unos segundos).
) else (
    echo       BirdNET ya estaba corriendo en el puerto 8080.
)

rem ---------- 3. Aplicacion web ----------
echo [3/3] Arrancando la aplicacion web...
netstat -ano | findstr ":3000 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    start "Django BirdWatch" /min ".venv\Scripts\python.exe" manage.py runserver 0.0.0.0:3000 --noreload
    echo       Aplicacion web arrancando en el puerto 3000.
) else (
    echo       La aplicacion web ya estaba corriendo en el puerto 3000.
)

echo.
echo  Listo. Abriendo http://localhost:3000 en el navegador...
echo.
echo  Usuario: user   -   Clave: 1234
echo.
echo  En el celular (misma red wifi): http://IP-DE-ESTE-EQUIPO:3000
echo  Ojo: el microfono del navegador solo funciona en HTTPS
echo  o en localhost; en el celular usa una direccion https.
echo.
echo  Para detener todo: ejecuta DETENER-BIRDWATCH.bat
echo  o cierra las ventanas minimizadas "BirdNET" y "Django BirdWatch".
echo.
timeout /t 6 /nobreak >nul
start "" "http://localhost:3000"
exit /b 0
