import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .birdnet import analizar_audio, comprobar_servicio
from .models import Deteccion

# Confianza mínima para guardar una detección en la base de datos.
CONFIANZA_MINIMA = 0.05


def inicio(request):
    """Portada: carrusel de aves del municipio, visión y misión."""
    from .models import Ave

    return render(request, "inicio.html", {"aves": Ave.objects.all()})


def entrar(request):
    """Ingreso de usuarios (superusuario inicial: user / 1234)."""
    if request.user.is_authenticated:
        return redirect("identificar")

    error = None
    if request.method == "POST":
        usuario = authenticate(
            request,
            username=request.POST.get("usuario", "").strip(),
            password=request.POST.get("contrasena", ""),
        )
        if usuario is not None:
            login(request, usuario)
            messages.success(request, f"¡Hola de nuevo, {usuario.username}!")
            siguiente = request.POST.get("siguiente") or request.GET.get("siguiente")
            if siguiente and siguiente.startswith("/"):
                return redirect(siguiente)
            return redirect("inicio")
        error = "Usuario o contraseña incorrectos."
    return render(request, "login.html", {"error": error})


def salir(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect("inicio")


@login_required
@ensure_csrf_cookie
def identificar(request):
    """Identificador de aves por sonido con el micrófono y BirdNET."""
    return render(request, "identificar.html")


@login_required
@require_POST
def analizar(request):
    """Recibe la grabación del navegador y la envía a la API BirdNET."""
    archivo = request.FILES.get("audio")
    if archivo is None:
        return JsonResponse({"error": "No se recibió ninguna grabación."}, status=400)
    if archivo.size > 25 * 1024 * 1024:
        return JsonResponse({"error": "La grabación es demasiado grande (máximo 25 MB)."}, status=400)
    if archivo.size < 1000:
        return JsonResponse({"error": "La grabación es demasiado corta."}, status=400)

    try:
        resultados = analizar_audio(archivo.read(), archivo.name or "grabacion.wav")
    except RuntimeError as error:
        return JsonResponse({"error": str(error)}, status=502)
    except (ValueError, TypeError) as error:
        return JsonResponse({"error": f"Respuesta inesperada de BirdNET: {error}"}, status=502)

    guardadas = []
    for resultado in resultados:
        if resultado["confianza"] < CONFIANZA_MINIMA:
            continue
        guardadas.append(Deteccion.objects.create(usuario=request.user, **resultado))

    return JsonResponse(
        {
            "resultados": [
                {
                    "id": d.id,
                    "especie_en": d.especie_en,
                    "especie_es": d.especie_es,
                    "nombre_cientifico": d.nombre_cientifico,
                    "tipo_sonido": d.tipo_sonido,
                    "confianza": d.confianza,
                    "creado_en": d.creado_en.isoformat(),
                }
                for d in guardadas
            ]
        }
    )


@login_required
def historial(request):
    """Historial de detecciones del usuario autenticado."""
    detecciones = request.user.detecciones.all()[:50]
    return JsonResponse(
        {
            "detecciones": [
                {
                    "id": d.id,
                    "especie_en": d.especie_en,
                    "especie_es": d.especie_es,
                    "nombre_cientifico": d.nombre_cientifico,
                    "tipo_sonido": d.tipo_sonido,
                    "confianza": d.confianza,
                    "creado_en": d.creado_en.isoformat(),
                }
                for d in detecciones
            ]
        }
    )


def estado(request):
    """Estado de los servicios para el panel de la página de identificación."""
    return JsonResponse({"postgres": True, "birdnet": comprobar_servicio()})


def service_worker(request):
    """Sirve el service worker (PWA) desde la raíz del sitio."""
    archivo = Path(settings.BASE_DIR) / "estaticos" / "js" / "sw.js"
    return FileResponse(archivo.open("rb"), content_type="application/javascript")
