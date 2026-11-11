@echo off
rem ============================================================
rem  BirdWatch - Detiene la aplicacion:
rem    - La aplicacion web Django (puerto 3000)
rem    - El analizador BirdNET (puerto 8080)
rem  El PostgreSQL local del equipo (servicio del sistema,
rem  puerto 5432) NO se detiene: es compartido con el sistema.
rem ============================================================
title BirdWatch - detencion
cd /d "%~dp0"
echo.
echo  === Deteniendo BirdWatch ===
echo.

echo [1/2] Deteniendo la aplicacion web (puerto 3000)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000 " ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>&1

echo [2/2] Deteniendo el analizador BirdNET (puerto 8080)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8080 " ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>&1

echo       PostgreSQL local (servicio del sistema) sigue corriendo.
echo.
echo  BirdWatch detenido por completo.
echo.
pause
