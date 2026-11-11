"""Prueba end-to-end de la aplicación web BirdWatch.

Simula lo que hace el navegador de un usuario real:
1. Abre la portada y comprueba el carrusel.
2. Entra con user/1234 (con el token CSRF).
3. Abre la página del identificador.
4. Consulta el estado de los servicios.
5. Envía una grabación WAV a /analizar/ (multipart + CSRF).
6. Lee el historial de detecciones.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
WAV = RAIZ / "descargas" / "prueba-ave.wav"
BASE = "http://127.0.0.1:3000"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests  # viene con birdnet_analyzer[server]

sesion = requests.Session()
fallos = 0


def comprobar(nombre, condicion, detalle=""):
    global fallos
    marca = "OK " if condicion else "FALLO"
    if not condicion:
        fallos += 1
    print(f"[{marca}] {nombre} {detalle}")


# 1. Portada
respuesta = sesion.get(BASE + "/", timeout=30)
comprobar("Portada responde 200", respuesta.status_code == 200, f"(codigo {respuesta.status_code})")
comprobar("Portada trae 9 aves", respuesta.text.count('class="diapositiva"') == 9)
comprobar("Portada tiene vision y mision", "Visión" in respuesta.text and "Misión" in respuesta.text)

# 2. Login con CSRF
respuesta = sesion.get(BASE + "/entrar/", timeout=30)
token = sesion.cookies.get("csrftoken", "")
comprobar("Pagina de entrada responde", respuesta.status_code == 200 and "usuario" in respuesta.text.lower())
comprobar("Token CSRF presente", bool(token))

respuesta = sesion.post(
    BASE + "/entrar/",
    data={"usuario": "user", "contrasena": "1234", "csrfmiddlewaretoken": token},
    headers={"Referer": BASE + "/entrar/"},
    timeout=30,
    allow_redirects=False,
)
comprobar("Login user/1234 aceptado", respuesta.status_code == 302, f"(codigo {respuesta.status_code})")
comprobar("Sesion iniciada", "sessionid" in sesion.cookies)

# 3. Identificador
respuesta = sesion.get(BASE + "/identificar/", timeout=30)
comprobar("Identificador responde", respuesta.status_code == 200)
comprobar("Boton de grabar presente", 'id="boton-grabar"' in respuesta.text)

# 4. Estado de servicios
respuesta = sesion.get(BASE + "/estado/", timeout=30)
estado = respuesta.json()
comprobar("Estado: BirdNET activo", estado.get("birdnet") is True, str(estado))

# 5. Analizar el WAV (lo mismo que hace el navegador)
token = sesion.cookies.get("csrftoken", token)
respuesta = sesion.post(
    BASE + "/analizar/",
    files={"audio": ("grabacion-birdwatch.wav", WAV.read_bytes(), "audio/wav")},
    headers={"X-CSRFToken": token, "Referer": BASE + "/identificar/"},
    timeout=300,
)
cuerpo = respuesta.json() if respuesta.headers.get("content-type", "").startswith("application/json") else {}
comprobar("Analisis responde 200", respuesta.status_code == 200, f"(codigo {respuesta.status_code})")
resultados = cuerpo.get("resultados", [])
comprobar("Hay detecciones en la respuesta", len(resultados) > 0, f"({len(resultados)} resultados)")
for resultado in resultados[:5]:
    print(f"       - {resultado.get('especie_es') or resultado.get('especie_en')}"
          f" ({resultado.get('nombre_cientifico')}) {resultado.get('confianza')}")

# 6. Historial
respuesta = sesion.get(BASE + "/historial/", timeout=30)
detecciones = respuesta.json().get("detecciones", [])
comprobar("Historial devuelve las detecciones", len(detecciones) >= len(resultados) - 1, f"({len(detecciones)} filas)")

# 7. Peticiones sin sesion deben redirigir a /entrar/
sin_sesion = requests.Session()
respuesta = sin_sesion.get(BASE + "/identificar/", timeout=30, allow_redirects=False)
comprobar("Sin sesion redirige al login", respuesta.status_code == 302, f"(codigo {respuesta.status_code})")

print()
if fallos:
    print(f"FIN: {fallos} comprobaciones fallaron")
    sys.exit(1)
print("FIN: la prueba end-to-end de la aplicacion web paso por completo")
