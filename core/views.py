import json
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .birdnet import CONFIANZA_MINIMA, analizar_audio, comprobar_servicio
from .forms import AveForm
from .models import Ave, Deteccion


def solo_superadmin(vista):
    """Permite el acceso únicamente al superadministrador."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('entrar')}?siguiente={request.path}")
        if not request.user.is_superuser:
            messages.error(
                request, "Solo el superadministrador puede modificar el carrusel."
            )
            return redirect("inicio")
        return vista(request, *args, **kwargs)

    return envoltura


def inicio(request):
    """Portada: carrusel de aves del municipio, visión y misión."""
    return render(request, "inicio.html", {"aves": Ave.objects.filter(activo=True)})


@solo_superadmin
def carrusel_admin(request):
    """Panel para administrar las aves del carrusel de la portada."""
    aves = Ave.objects.all()
    return render(
        request,
        "carrusel_admin.html",
        {"aves": aves, "aves_visibles": aves.filter(activo=True).count()},
    )


@solo_superadmin
def carrusel_nueva(request):
    """Añade un ave al carrusel (con subida de foto)."""
    if request.method == "POST":
        formulario = AveForm(request.POST, request.FILES)
        if formulario.is_valid():
            ave = formulario.save()
            messages.success(request, f"«{ave.nombre_comun}» se añadió al carrusel.")
            return redirect("carrusel_admin")
    else:
        ultimo = Ave.objects.order_by("-orden").values_list("orden", flat=True).first()
        formulario = AveForm(initial={"orden": (ultimo or 0) + 1, "activo": True})
    return render(
        request,
        "carrusel_form.html",
        {"formulario": formulario, "titulo": "Añadir ave al carrusel"},
    )


@solo_superadmin
def carrusel_editar(request, pk):
    """Edita la ficha o la foto de un ave del carrusel."""
    ave = get_object_or_404(Ave, pk=pk)
    if request.method == "POST":
        formulario = AveForm(request.POST, request.FILES, instance=ave)
        if formulario.is_valid():
            ave = formulario.save()
            messages.success(request, f"«{ave.nombre_comun}» se actualizó.")
            return redirect("carrusel_admin")
    else:
        formulario = AveForm(instance=ave)
    return render(
        request,
        "carrusel_form.html",
        {
            "formulario": formulario,
            "ave": ave,
            "titulo": f"Editar «{ave.nombre_comun}»",
        },
    )


@solo_superadmin
@require_POST
def carrusel_eliminar(request, pk):
    """Elimina un ave del carrusel y su foto si no la usa otra ave."""
    ave = get_object_or_404(Ave, pk=pk)
    nombre = ave.nombre_comun
    ruta_foto = Path(settings.BASE_DIR) / "estaticos" / ave.imagen
    if (
        ave.imagen.startswith("img/aves/")
        and not Ave.objects.filter(imagen=ave.imagen).exclude(pk=ave.pk).exists()
        and ruta_foto.is_file()
    ):
        ruta_foto.unlink()
    ave.delete()
    messages.success(request, f"«{nombre}» se eliminó del carrusel.")
    return redirect("carrusel_admin")


@solo_superadmin
@require_POST
def carrusel_alternar(request, pk):
    """Muestra u oculta un ave del carrusel sin borrarla."""
    ave = get_object_or_404(Ave, pk=pk)
    ave.activo = not ave.activo
    ave.save(update_fields=["activo"])
    estado = "se muestra" if ave.activo else "se ocultó"
    messages.success(request, f"«{ave.nombre_comun}» {estado} en el carrusel.")
    return redirect("carrusel_admin")


@solo_superadmin
@require_POST
def carrusel_mover(request, pk):
    """Sube o baja un ave una posición en el carrusel."""
    ave = get_object_or_404(Ave, pk=pk)
    direccion = request.POST.get("direccion")
    aves = list(Ave.objects.order_by("orden", "nombre_comun"))
    indice = next((i for i, otra in enumerate(aves) if otra.pk == ave.pk), None)
    destino = indice + (-1 if direccion == "subir" else 1) if indice is not None else None
    if destino is None or not 0 <= destino < len(aves):
        return redirect("carrusel_admin")

    # Normaliza el orden (1, 2, 3…) para que el intercambio siempre funcione.
    for posicion, otra in enumerate(aves, start=1):
        if otra.orden != posicion:
            otra.orden = posicion
            otra.save(update_fields=["orden"])
    vecina = aves[destino]
    ave.orden, vecina.orden = vecina.orden, ave.orden
    ave.save(update_fields=["orden"])
    vecina.save(update_fields=["orden"])

    messages.success(request, f"«{ave.nombre_comun}» cambió de posición.")
    return redirect("carrusel_admin")


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
