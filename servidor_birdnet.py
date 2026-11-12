"""Servidor HTTP de análisis BirdNET para BirdWatch.

El paquete birdnet_analyzer 2.4.0 de PyPI ya no incluye el módulo server,
así que este archivo implementa un servicio equivalente con bottle: recibe
un WAV por multipart/form-data junto con un JSON "meta" y devuelve los
resultados en el mismo formato del servidor original de BirdNET.

    POST /analyze  ->  {"msg": "success", "results": [["Scientific_Common", 0.87], ...]}

Campos aceptados en "meta":
    filename     nombre del archivo recibido
    lat, lon     coordenadas (San Antonio del Tequendama en el cliente)
    week         semana del año (1-48) o -1 para todo el año
    sf_thresh    umbral del filtro por ubicación (por defecto 0.03)
    sensitivity  sensibilidad de detección (por defecto 1.0)
    overlap      traslape entre fragmentos de 3 s (por defecto 0)
    pmode        "avg" (promedio) o "max" para combinar fragmentos
    num_results  cantidad máxima de especies a devolver (10)
    slist        lista de etiquetas BirdNET permitidas; si viene, el análisis
                 SOLO puede devolver esas especies (por ejemplo, el chinigüe)
    save         true para conservar el archivo recibido en --spath

Uso:
    python servidor_birdnet.py [--host 127.0.0.1] [--port 8080] [--spath CARPETA]
"""
import argparse
import json
import os
import tempfile
import time
import uuid

from bottle import Bottle, request, run

import birdnet_analyzer.config as cfg
from birdnet_analyzer.analyze.utils import iterate_audio_chunks, load_codes
from birdnet_analyzer.species.utils import get_species_list
from birdnet_analyzer.utils import ensure_model_exists, read_lines

aplicacion = Bottle()

# Carpeta para conservar las grabaciones (se llena con --spath).
CARPETA_GUARDADO = ""

EXTENSIONES = (".wav", ".flac", ".mp3", ".ogg", ".m4a", ".wma", ".aiff", ".aif")


def preparar_configuracion(meta):
    """Ajusta la configuración global de birdnet_analyzer según "meta"."""
    ensure_model_exists()

    # Modelo BirdNET V2.4 y sus etiquetas.
    cfg.MODEL_PATH = cfg.BIRDNET_MODEL_PATH
    cfg.LABELS_FILE = cfg.BIRDNET_LABELS_FILE
    cfg.SAMPLE_RATE = cfg.BIRDNET_SAMPLE_RATE
    cfg.SIG_LENGTH = cfg.BIRDNET_SIG_LENGTH
    cfg.LABELS = read_lines(cfg.LABELS_FILE)
    cfg.TRANSLATED_LABELS = cfg.LABELS
    cfg.CODES = load_codes()

    # Parámetros del análisis.
    cfg.CUSTOM_CLASSIFIER = None
    cfg.USE_PERCH = False
    cfg.APPLY_SIGMOID = True
    cfg.SIGMOID_SENSITIVITY = float(meta.get("sensitivity", 1.0))
    cfg.SIG_OVERLAP = min(2.9, max(0.0, float(meta.get("overlap", 0.0))))
    cfg.SIG_MINLEN = 1.0
    cfg.BANDPASS_FMIN = 0
    cfg.BANDPASS_FMAX = 15000
    cfg.AUDIO_SPEED = 1.0
    cfg.BATCH_SIZE = 1
    cfg.CPU_THREADS = 1
    cfg.MIN_CONFIDENCE = float(meta.get("min_conf", 0.01))
    cfg.MERGE_CONSECUTIVE = 1
    cfg.TOP_N = None
    cfg.FILE_SPLITTING_DURATION = 600
    cfg.SKIP_EXISTING_RESULTS = False

    # Ubicación y filtro de especies.
    lat = float(meta.get("lat", -1))
    lon = float(meta.get("lon", -1))
    semana = int(meta.get("week", -1))
    cfg.LATITUDE, cfg.LONGITUDE, cfg.WEEK = lat, lon, semana
    umbral = float(meta.get("sf_thresh", 0.03))
    cfg.LOCATION_FILTER_THRESHOLD = umbral
    cfg.SPECIES_LIST_FILE = None

    # Lista de especies permitidas por el cliente (etiquetas BirdNET
    # "NombreCientifico_NombreComun"). Si viene, tiene prioridad sobre la
    # lista de la ubicación: así la app puede identificar, por ejemplo,
    # solo el chinigüe (copetón).
    permitidas = [
        str(etiqueta).strip()
        for etiqueta in (meta.get("slist") or [])
        if str(etiqueta).strip()
    ]
    if permitidas:
        cfg.SPECIES_LIST = permitidas
    elif lat != -1 and lon != -1:
        cfg.SPECIES_LIST = get_species_list(lat, lon, semana, umbral)
    else:
        cfg.SPECIES_LIST = None


def analizar_archivo(ruta, modo):
    """Analiza el audio y devuelve la lista [(etiqueta, confianza), ...]."""
    puntajes = {}
    for _, _, pred in iterate_audio_chunks(ruta):
        for etiqueta, puntaje in zip(cfg.LABELS, pred):
            puntajes.setdefault(etiqueta, []).append(float(puntaje))

    # Filtrar por la lista de especies de la ubicación.
    if cfg.SPECIES_LIST:
        puntajes = {e: p for e, p in puntajes.items() if e in cfg.SPECIES_LIST}

    resultados = []
    for etiqueta, valores in puntajes.items():
        if modo == "max":
            confianza = max(valores)
        else:  # "avg": promedio entre fragmentos
            confianza = sum(valores) / len(valores)
        if confianza >= cfg.MIN_CONFIDENCE:
            resultados.append((etiqueta, round(confianza, 4)))
    resultados.sort(key=lambda par: par[1], reverse=True)
    return resultados


@aplicacion.get("/")
def raiz():
    return {
        "msg": "Servidor BirdNET para BirdWatch activo",
        "modelo": cfg.MODEL_VERSION,
    }


@aplicacion.post("/analyze")
def analizar():
    subida = request.files.get("audio")
    if subida is None:
        request.response.status = 400
        return {"msg": "No se recibió el campo 'audio'."}

    try:
        meta = json.loads(request.forms.get("meta") or "{}")
    except ValueError:
        meta = {}

    preparar_configuracion(meta)

    limite = max(1, int(meta.get("num_results", 10) or 10))
    modo = str(meta.get("pmode", "avg")).lower()
    guardar = bool(meta.get("save", False))

    # Nombre de archivo seguro y único.
    nombre = os.path.basename(str(meta.get("filename") or "grabacion.wav"))
    if not nombre.lower().endswith(EXTENSIONES):
        nombre += ".wav"
    nombre = f"{uuid.uuid4().hex[:8]}-{nombre}"

    carpeta = CARPETA_GUARDADO if (guardar and CARPETA_GUARDADO) else tempfile.mkdtemp(prefix="birdwatch-")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    subida.save(ruta, overwrite=True)

    try:
        resultados = analizar_archivo(ruta, modo)[:limite]
    except Exception as error:  # noqa: BLE001
        request.response.status = 500
        return {"msg": f"No se pudo analizar el audio: {error}"}
    finally:
        if not (guardar and CARPETA_GUARDADO):
            for _ in range(5):
                try:
                    os.remove(ruta)
                    break
                except OSError:
                    time.sleep(0.2)

    return {"msg": "success", "results": [list(par) for par in resultados]}


def main():
    global CARPETA_GUARDADO

    analizador = argparse.ArgumentParser(description="Servidor BirdNET para BirdWatch")
    analizador.add_argument("--host", default="127.0.0.1")
    analizador.add_argument("--port", type=int, default=8080)
    analizador.add_argument("--spath", default="", help="Carpeta donde conservar las grabaciones recibidas")
    argumentos = analizador.parse_args()

    CARPETA_GUARDADO = argumentos.spath
    if CARPETA_GUARDADO:
        os.makedirs(CARPETA_GUARDADO, exist_ok=True)

    print(f"Servidor BirdNET para BirdWatch en http://{argumentos.host}:{argumentos.port}")
    run(aplicacion, host=argumentos.host, port=argumentos.port, quiet=False)


if __name__ == "__main__":
    main()
