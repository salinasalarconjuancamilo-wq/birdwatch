"""Descarga fotos de aves de Wikimedia Commons para el carrusel de BirdWatch.

Busca cada nombre científico en Commons, toma la primera foto JPEG que
aparezca y la guarda en estaticos/img/aves/ con el nombre que usa
core/data/aves.json. Los créditos se guardan en descargas/creditos-aves.json.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "estaticos" / "img" / "aves"
DESTINO.mkdir(parents=True, exist_ok=True)

AVES = [
    ("Vultur gryphus", "condor-andino.jpg"),
    ("Coeligena coeligena", "inca-bronceado.jpg"),
    ("Aglaiocercus kingii", "zafiro-colilargo.jpg"),
    ("Lesbia victoriae", "colibri-colinegro.jpg"),
    ("Colibri coruscans", "chisga-morada.jpg"),
    ("Andigena laminirostris", "tucan-piquiplano.jpg"),
    ("Grallaria ruficapilla", "tororoi-coronirrufo.jpg"),
    ("Myioborus ornatus", "candelita-frente-dorada.jpg"),
    ("Penelope montagnii", "pava-andina.jpg"),
]

UA = "BirdWatch/1.0 (proyecto escolar de aves de San Antonio del Tequendama, Colombia)"


def abrir(url):
    peticion = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(peticion, timeout=60)


def buscar(nombre):
    consulta = f'"{nombre}" filetype:bitmap'
    parametros = urllib.parse.urlencode({
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": consulta,
        "gsrnamespace": "6",
        "gsrlimit": "20",
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": "1200",
    })
    with abrir(f"https://commons.wikimedia.org/w/api.php?{parametros}") as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def elegir(datos):
    paginas = (datos.get("query") or {}).get("pages") or {}
    candidatos = sorted(paginas.values(), key=lambda p: p.get("index", 999))
    # Preferir fotos JPEG (la mayoría de fotos de aves en Commons).
    for pagina in candidatos:
        infos = pagina.get("imageinfo") or []
        if infos and infos[0].get("mime") == "image/jpeg" and infos[0].get("thumburl"):
            return pagina, infos[0]
    for pagina in candidatos:
        infos = pagina.get("imageinfo") or []
        if infos and infos[0].get("thumburl"):
            return pagina, infos[0]
    return None, None


def limpiar(texto):
    return unescape(re.sub(r"<[^>]+>", "", texto or "")).strip()


creditos = []
for nombre, archivo in AVES:
    destino = DESTINO / archivo
    try:
        pagina, info = elegir(buscar(nombre))
        if not info:
            print(f"SIN RESULTADO: {nombre}")
            creditos.append({"archivo": archivo, "ave": nombre, "error": "sin resultados"})
            continue
        with abrir(info["thumburl"]) as respuesta, open(destino, "wb") as salida:
            salida.write(respuesta.read())
        meta = info.get("extmetadata") or {}
        creditos.append({
            "archivo": archivo,
            "ave": nombre,
            "titulo": pagina.get("title", ""),
            "autor": limpiar(meta.get("Artist", {}).get("value", "")),
            "licencia": limpiar(meta.get("LicenseShortName", {}).get("value", "")),
            "pagina": info.get("descriptionurl", ""),
            "tamano_kb": round(destino.stat().st_size / 1024, 1),
        })
        print(f"OK {archivo} ({destino.stat().st_size // 1024} KB) - {pagina.get('title')}")
    except Exception as error:  # noqa: BLE001
        print(f"ERROR {nombre}: {error}")
        creditos.append({"archivo": archivo, "ave": nombre, "error": str(error)})
    time.sleep(1)

salida_creditos = RAIZ / "descargas" / "creditos-aves.json"
salida_creditos.write_text(json.dumps(creditos, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Creditos guardados en {salida_creditos}")
