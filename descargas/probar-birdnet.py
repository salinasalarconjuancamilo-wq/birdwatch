"""Prueba integral del analizador BirdNET para BirdWatch.

1. Descarga un canto de ave real de Wikimedia Commons (chingolo /
   gorrión ruficollado, ave muy común en Cundinamarca).
2. Lo convierte a WAV mono de 48 kHz.
3. Espera a que el servidor BirdNET local (puerto 8080) responda.
4. Envía el WAV usando el propio cliente de Django (core.birdnet)
   y muestra las detecciones traducidas al español.
"""
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "descargas" / "prueba-ave.wav"
UA = "BirdWatch/1.0 (proyecto escolar de aves de San Antonio del Tequendama, Colombia)"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def abrir(url):
    peticion = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(peticion, timeout=90)


def buscar_audio():
    """Busca un canto de chingolo en Commons y devuelve (titulo, url, mime)."""
    consulta = 'intitle:"rufous collared sparrow" filetype:audio'
    parametros = urllib.parse.urlencode({
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": consulta,
        "gsrnamespace": "6",
        "gsrlimit": "15",
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
    })
    with abrir(f"https://commons.wikimedia.org/w/api.php?{parametros}") as respuesta:
        datos = json.loads(respuesta.read().decode("utf-8"))
    paginas = (datos.get("query") or {}).get("pages") or {}
    candidatos = sorted(paginas.values(), key=lambda p: p.get("index", 999))
    for pagina in candidatos:
        infos = pagina.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        mime = info.get("mime", "")
        if mime.startswith("audio/") and info.get("size", 99 * 1024 * 1024) < 25 * 1024 * 1024:
            return pagina.get("title", ""), info["url"], mime
    raise RuntimeError("no se encontró audio en Commons")


def convertir(datos_brutos):
    """Convierte el audio descargado a WAV mono 48 kHz."""
    import librosa
    import numpy as np
    import soundfile as sf

    audio, frecuencia = librosa.load(io.BytesIO(datos_brutos), sr=48000, mono=True)
    if len(audio) < 48000:  # al menos 1 segundo
        raise RuntimeError("el audio es demasiado corto")
    if len(audio) > 48000 * 12:  # máximo 12 segundos
        audio = audio[: 48000 * 12]
    audio = (audio / max(1e-9, np.max(np.abs(audio))) * 0.95).astype("float32")
    sf.write(str(DESTINO), audio, 48000, subtype="PCM_16")
    return len(audio) / 48000


def esperar_servidor(segundos=180):
    fin = time.time() + segundos
    while time.time() < fin:
        try:
            with abrir("http://127.0.0.1:8080/") as respuesta:
                estado = json.loads(respuesta.read().decode("utf-8"))
            print("Servidor BirdNET activo:", estado)
            return estado
        except Exception:
            time.sleep(2)
    raise RuntimeError("el servidor BirdNET no respondió en 180 segundos")


def main():
    titulo, url, mime = buscar_audio()
    print(f"Audio encontrado: {titulo} ({mime})")
    with abrir(url) as respuesta:
        datos_brutos = respuesta.read()
    print(f"Descargados {len(datos_brutos) // 1024} KB")
    duracion = convertir(datos_brutos)
    print(f"Convertido a WAV 48 kHz mono: {DESTINO} ({duracion:.1f} s)")

    esperar_servidor()

    # Usar el propio cliente de Django (prueba del stack completo).
    import os
    import sys

    RAIZ_STR = str(RAIZ)
    if RAIZ_STR not in sys.path:
        sys.path.insert(0, RAIZ_STR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "birdwatch.settings")
    import django

    django.setup()
    from core.birdnet import analizar_audio

    detecciones = analizar_audio(DESTINO.read_bytes(), "prueba-ave.wav")
    print(f"\n{len(detecciones)} detecciones devueltas por el cliente de Django:")
    for deteccion in detecciones:
        print(
            f"  {deteccion['especie_es'] or deteccion['especie_en']:40s} "
            f"({deteccion['nombre_cientifico']:24s}) "
            f"{deteccion['confianza'] * 100:5.1f}% {deteccion['tipo_sonido']}"
        )
    print("\nOK: la prueba del analizador BirdNET terminó correctamente")


if __name__ == "__main__":
    main()
