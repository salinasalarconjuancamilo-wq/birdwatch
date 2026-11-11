@echo off
rem ============================================================
rem  BirdWatch - Detiene la aplicacion:
rem    - La aplicacion web Django (puerto 3000)
rem    - El analizador BirdNET (puerto 8080)
rem    - PostgreSQL (puerto 5433)
rem ============================================================
title BirdWatch - detencion
cd /d "%~dp0"
echo.
echo  === Deteniendo BirdWatch ===
echo.

echo [1/3] Deteniendo la aplicacion web (puerto 3000)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000 " ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>&1

echo [2/3] Deteniendo el analizador BirdNET (puerto 8080)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8080 " ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>&1

echo [3/3] Deteniendo PostgreSQL...
"herramientas\postgres\bin\pg_ctl.exe" -D "herramientas\pgdatos" -l "descargas\pg-servidor.log" stop

echo.
echo  BirdWatch detenido por completo.
echo.
pause
