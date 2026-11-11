@echo off
rem BirdWatch - Servidor del analizador BirdNET (Cornell Lab)
rem Escucha en http://127.0.0.1:8080 y analiza los WAV que envia Django.
cd /d "%~dp0"
if not exist "descargas\birdnet-subidas" mkdir "descargas\birdnet-subidas"
title BirdNET - analizador de cantos de aves
"herramientas\python\python.exe" servidor_birdnet.py --host 127.0.0.1 --port 8080 --spath "descargas\birdnet-subidas" > "descargas\birdnet-servidor.log" 2>&1
if errorlevel 1 (
    echo.
    echo El analizador BirdNET se detuvo con un error.
    echo Revisa el archivo descargas\birdnet-servidor.log
    pause
)
