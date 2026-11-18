"""Vistas del catálogo, los avistamientos, el mapa y las estadísticas."""
from django.contrib import messages
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from contenido.models import LugarObservacion, secciones_activas

from core.permisos import es_administrador, solo_administrador, solo_usuario

from .estadisticas import resumen_estadisticas
from .forms import AvistamientoForm, ComentarioForm
from .models import Avistamiento, Ave, Validacion, ZONAS_PARQUE


def home(request):
    """Portada alterna ``/portada/`` (se conserva por compatibilidad)."""
    return render(request, "aves/home.html")


def _consulta_visible(request):
    """Avistamientos que el visitante actual tiene permiso para ver."""
    consulta = Avistamiento.objects.select_related("ave", "usuario")
    if es_administrador(request.user):
        return consulta
    if request.user.is_authenticated:
        return consulta.filter(Q(aprobado=True) | Q(usuario=request.user))
    return consulta.filter(aprobado=True)


def _puede_ver(request, avistamiento):
    if avistamiento.aprobado or es_administrador(request.user):
        return True
    return request.user.is_authenticated and avistamiento.usuario_id == request.user.id


def _destino_seguro(request, por_defecto):
    """Evita redirecciones externas enviadas en el campo 'siguiente'."""
    destino = request.POST.get("siguiente", "")
    if destino.startswith("/") and not destino.startswith("//"):
        return destino
    return por_defecto


def lista_avistamientos(request):
    """Listado público de avistamientos, con filtros por zona y especie."""
    avistamientos = _consulta_visible(request)

    zona = request.GET.get("zona", "").strip()
    especie = request.GET.get("especie", "").strip()
    buscar = request.GET.get("q", "").strip()

    if zona:
        avistamientos = avistamientos.filter(zona=zona)
    if especie:
        avistamientos = avistamientos.filter(ave_id=especie)
    if buscar:
        avistamientos = avistamientos.filter(
            Q(ave__nombre_comun__icontains=buscar)
            | Q(ave__nombre_cientifico__icontains=buscar)
            | Q(lugar__icontains=buscar)
            | Q(notas__icontains=buscar)
        )

    return render(
        request,
        "aves/lista_avistamientos.html",
        {
            "avistamientos": avistamientos,
            "zonas": ZONAS_PARQUE,
            "especies": Ave.objects.all(),
            "filtros": {"zona": zona, "especie": especie, "q": buscar},
            "pendientes": Avistamiento.objects.filter(aprobado=False).count()
            if es_administrador(request.user)
            else 0,
        },
    )


@solo_usuario
def crear_avistamiento(request):
    """Registro de una nueva observación (rol Usuario)."""
    if request.method == "POST":
        formulario = AvistamientoForm(request.POST, request.FILES)
        if formulario.is_valid():
            avistamiento = formulario.save(commit=False)
            avistamiento.usuario = request.user
            # El administrador aprueba automáticamente lo que él mismo registra.
            avistamiento.aprobado = es_administrador(request.user)
            avistamiento.save()
            messages.success(
                request,
                "Avistamiento registrado. "
                + (
                    "Ya es público."
                    if avistamiento.aprobado
                    else "Un administrador lo revisará antes de publicarlo."
                ),
            )
            return redirect("avistamiento_detalle", pk=avistamiento.pk)
    else:
        formulario = AvistamientoForm()

    return render(
        request,
        "aves/avistamiento_form.html",
        {"formulario": formulario, "zonas": ZONAS_PARQUE},
    )


@solo_usuario
def editar_avistamiento(request, pk):
    """Edita un avistamiento propio (los administradores editan cualquiera)."""
    avistamiento = get_object_or_404(Avistamiento, pk=pk)
    if not (es_administrador(request.user) or avistamiento.usuario_id == request.user.id):
        messages.error(request, "Solo puedes editar tus propios avistamientos.")
        return redirect("avistamiento_detalle", pk=pk)

    if request.method == "POST":
        formulario = AvistamientoForm(
            request.POST, request.FILES, instance=avistamiento
        )
        if formulario.is_valid():
            avistamiento = formulario.save()
            messages.success(request, "Avistamiento actualizado.")
            return redirect("avistamiento_detalle", pk=avistamiento.pk)
    else:
        formulario = AvistamientoForm(instance=avistamiento)

    return render(
        request,
        "aves/avistamiento_form.html",
        {
            "formulario": formulario,
            "zonas": ZONAS_PARQUE,
            "avistamiento": avistamiento,
        },
    )


def detalle_avistamiento(request, pk):
    """Ficha de un avistamiento con comentarios y validaciones."""
    avistamiento = get_object_or_404(Avistamiento.objects.select_related("ave", "usuario"), pk=pk)
    if not _puede_ver(request, avistamiento):
        messages.error(request, "Ese avistamiento todavía no está publicado.")
        return redirect("avistamientos")

    comentarios = avistamiento.comentarios.select_related("usuario")
    validado = False
    if request.user.is_authenticated:
        validado = Validacion.objects.filter(
            avistamiento=avistamiento, usuario=request.user
        ).exists()

    return render(
        request,
        "aves/avistamiento_detalle.html",
        {
            "avistamiento": avistamiento,
            "comentarios": comentarios,
            "formulario_comentario": ComentarioForm(),
            "validado": validado,
            "total_validaciones": avistamiento.validaciones.count(),
        },
    )


@solo_usuario
@require_POST
def comentar(request, pk):
    """Añade un comentario a un avistamiento publicado."""
    avistamiento = get_object_or_404(Avistamiento, pk=pk)
    if not _puede_ver(request, avistamiento):
        messages.error(request, "No puedes comentar ese avistamiento.")
        return redirect("avistamientos")
    formulario = ComentarioForm(request.POST)
    if formulario.is_valid():
        comentario = formulario.save(commit=False)
        comentario.avistamiento = avistamiento
        comentario.usuario = request.user
        comentario.save()
        messages.success(request, "Comentario publicado.")
    else:
        messages.error(request, "El comentario no puede estar vacío.")
    return redirect("avistamiento_detalle", pk=pk)


@solo_usuario
@require_POST
def validar(request, pk):
    """Confirma (o retira la confirmación) de un avistamiento."""
    avistamiento = get_object_or_404(Avistamiento, pk=pk)
    if not _puede_ver(request, avistamiento):
        messages.error(request, "No puedes validar ese avistamiento.")
        return redirect("avistamientos")
    validacion = Validacion.objects.filter(avistamiento=avistamiento, usuario=request.user).first()
    if validacion:
        validacion.delete()
        messages.info(request, "Quitaste tu validación.")
    else:
        Validacion.objects.create(avistamiento=avistamiento, usuario=request.user)
        messages.success(request, "¡Gracias! Validaste este avistamiento.")
    return redirect("avistamiento_detalle", pk=pk)


@solo_administrador
def pendientes(request):
    """Cola de contenido por aprobar (rol Administrador)."""
    return render(
        request,
        "aves/pendientes.html",
        {"pendientes": Avistamiento.objects.filter(aprobado=False).select_related("ave", "usuario")},
    )


@solo_administrador
@require_POST
def aprobar(request, pk):
    """Aprueba un avistamiento para que sea público."""
    avistamiento = get_object_or_404(Avistamiento, pk=pk)
    avistamiento.aprobado = True
    avistamiento.save(update_fields=["aprobado"])
    messages.success(request, f"Aprobado el avistamiento de {avistamiento.ave.nombre_comun}.")
    return redirect(_destino_seguro(request, "avistamientos_pendientes"))


@solo_administrador
@require_POST
def eliminar(request, pk):
    """Elimina un registro (control de registros del administrador)."""
    avistamiento = get_object_or_404(Avistamiento, pk=pk)
    nombre = avistamiento.ave.nombre_comun
    avistamiento.delete()
    messages.success(request, f"Se eliminó el avistamiento de {nombre}.")
    return redirect(_destino_seguro(request, "avistamientos"))


def _lugares_mapa():
    """Lugares activos; los que no tienen coordenadas se listan aparte."""
    lugares = LugarObservacion.objects.filter(activo=True)
    return [lugar.datos_mapa() for lugar in lugares]


def mapa(request):
    """Mapa de lugares para observar aves (Leaflet + OpenStreetMap)."""
    lugares = _lugares_mapa()
    return render(
        request,
        "aves/mapa.html",
        {
            "lugares": lugares,
            "con_coordenadas": [l for l in lugares if l["latitud"] is not None],
        },
    )


def lugares_json(request):
    """JSON público con los lugares del mapa (sin avistamientos)."""
    return JsonResponse({"lugares": _lugares_mapa()}, safe=False)


def estadisticas(request):
    """Panel de estadísticas y destacados de la comunidad."""
    if "estadisticas" not in secciones_activas() and not es_administrador(request.user):
        raise Http404("Esta sección todavía no está disponible.")
    contexto = resumen_estadisticas()
    contexto["zonas"] = ZONAS_PARQUE
    return render(request, "aves/estadisticas.html", contexto)
