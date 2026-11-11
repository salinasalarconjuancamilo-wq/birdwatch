"""Cliente de la API de identificación BirdNET (Cornell Lab of Ornithology).

BIRDWATCH graba el audio en el navegador, lo envía a este backend Django y
este lo reenvía al servidor HTTP de BirdNET Analyzer (paquete de Python
`birdnet_analyzer`, ejecutado con INICIAR-BIRDWATCH.bat o el servicio que
el proyecto tenga configurado en la variable BIRDNET_URL).
"""
import datetime
import json
import os
import urllib.error
import urllib.request

from .traducciones import TRADUCCIONES

# URL del servicio BirdNET Analyzer (servidor HTTP del paquete birdnet_analyzer).
BIRDNET_URL = os.environ.get("BIRDNET_URL", "http://localhost:8080")

# Coordenadas de San Antonio del Tequendama, Cundinamarca, Colombia.
LATITUD = 4.6267
LONGITUD = -74.3300

TIPOS_SONIDO = {
    "Song and call": "Canto y llamado",
    "Song": "Canto",
    "Call": "Llamado",
}

INSTRUCCIONES = (
    "No fue posible conectar con el servicio de identificación BirdNET. "
    "Inicia el analizador ejecutando el archivo INICIAR-BIRDWATCH.bat "
    "(o el comando: python -m birdnet_analyzer.server --host 127.0.0.1 --port 8080) "
    "y vuelve a intentarlo."
)


def comprobar_servicio(tiempo_fuera=3):
    """Indica si el servicio BirdNET está activo (True) o no (False)."""
    try:
        urllib.request.urlopen(BIRDNET_URL, timeout=tiempo_fuera)
        return True
    except urllib.error.HTTPError:
        # Respondió con un código HTTP (p. ej. 404): el servicio está activo.
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _semana_del_ano():
    """Semana del año (1-48) según el formato de semana de BirdNET."""
    hoy = datetime.date.today()
    semana = (hoy.month - 1) * 4 + min(4, hoy.day // 7 + 1)
    return max(1, min(48, semana))


def _interpretar_etiqueta(etiqueta, confianza):
    """Convierte la etiqueta de BirdNET en un diccionario normalizado.

    Las etiquetas de BirdNET llegan como "Nombre cientifico_Nombre comun"
    (o "Nombre cientifico_Nombre comun_Song and call" en versiones viejas).
    """
    partes = str(etiqueta).split("_")
    if len(partes) >= 3 and partes[-1] in TIPOS_SONIDO:
        cientifico, comun, tipo = partes[0], "_".join(partes[1:-1]), partes[-1]
    elif len(partes) >= 2:
        cientifico, comun, tipo = partes[0], "_".join(partes[1:]), ""
    else:
        cientifico, comun, tipo = "", str(etiqueta), ""
    return {
        "especie_en": comun,
        "especie_es": TRADUCCIONES.get(comun, ""),
        "nombre_cientifico": cientifico,
        "tipo_sonido": TIPOS_SONIDO.get(tipo, tipo),
        "confianza": round(float(confianza), 4),
    }


def analizar_audio(datos_wav, nombre="grabacion.wav"):
    """Envía el audio (bytes WAV) a BirdNET y devuelve la lista de detecciones.

    La petición usa multipart/form-data con los campos que espera el
    servidor de BirdNET Analyzer: "audio" (archivo) y "meta" (JSON con
    la ubicación y parámetros del análisis).

    Lanza RuntimeError cuando el servicio no está disponible.
    """
    meta = {
        "filename": nombre,
        "lat": LATITUD,
        "lon": LONGITUD,
        "week": _semana_del_ano(),
        "sf_thresh": 0.03,
        "sensitivity": 1.0,
        "overlap": 0.0,
        "pmode": "avg",
        "num_results": 10,
        "save": False,
    }

    frontera = "BirdWatchPythonCliente"
    inicio = (
        f"--{frontera}\r\n"
        f'Content-Disposition: form-data; name="meta"\r\n\r\n'
        f"{json.dumps(meta)}\r\n"
        f"--{frontera}\r\n"
        f'Content-Disposition: form-data; name="audio"; filename="{nombre}"\r\n'
        f"Content-Type: audio/wav\r\n\r\n"
    ).encode("utf-8")
    cierre = f"\r\n--{frontera}--\r\n".encode("utf-8")

    peticion = urllib.request.Request(
        BIRDNET_URL.rstrip("/") + "/analyze",
        data=inicio + datos_wav + cierre,
        headers={"Content-Type": f"multipart/form-data; boundary={frontera}"},
    )

    try:
        with urllib.request.urlopen(peticion, timeout=300) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", "ignore")[:300]
        raise RuntimeError(
            f"BirdNET respondió con un error HTTP {error.code}. {detalle}"
        ) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RuntimeError(INSTRUCCIONES) from error

    if isinstance(datos, dict):
        if datos.get("msg") not in (None, "success"):
            raise RuntimeError(f"BirdNET respondió: {datos.get('msg')}")
        resultados = datos.get("results", [])
    else:
        resultados = datos

    return [
        _interpretar_etiqueta(etiqueta, confianza)
        for etiqueta, confianza in resultados
    ]
