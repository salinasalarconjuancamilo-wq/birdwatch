"""Vistas públicas y panel de administración de contenido."""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from aves.models import Avistamiento
from core.permisos import es_administrador, solo_administrador, solo_superadmin

from .forms import (
    FotoParqueForm,
    LugarForm,
    MensajeContactoForm,
    NoticiaPanelForm,
    SeccionForm,
)
from .models import (
    FotoParque,
    LugarObservacion,
    Noticia,
    PreguntaFrecuente,
    Seccion,
    secciones_activas,
)


def _exigir_seccion(request, clave):
    """Una sección desactivada no es pública; el administrador sí puede verla."""
    if clave not in secciones_activas() and not es_administrador(request.user):
        raise Http404("Esta sección todavía no está disponible.")


def noticias(request):
    """Listado de novedades del proyecto y del parque."""
    _exigir_seccion(request, "noticias")
    lista = Noticia.objects.filter(publicada=True)
    return render(request, "contenido/noticias.html", {"noticias": lista})


def noticia_detalle(request, slug):
    """Una noticia concreta (solo si está publicada, salvo administradores)."""
    _exigir_seccion(request, "noticias")
    consulta = Noticia.objects.all()
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        consulta = consulta.filter(publicada=True)
    noticia = get_object_or_404(consulta, slug=slug)
    return render(request, "contenido/noticia_detalle.html", {"noticia": noticia})


def ayuda(request):
    """Centro de ayuda: preguntas frecuentes y guía para identificar aves."""
    preguntas = PreguntaFrecuente.objects.filter(activa=True)
    return render(request, "contenido/ayuda.html", {"preguntas": preguntas})


def contacto(request):
    """Formulario de mensajes; guarda el mensaje y confirma al usuario."""
    enviado = False
    if request.method == "POST":
        formulario = MensajeContactoForm(request.POST)
        if formulario.is_valid():
            formulario.save()
            messages.success(
                request,
                "¡Mensaje enviado! Gracias por escribirnos; te responderemos pronto.",
            )
            enviado = True
            formulario = MensajeContactoForm()
    else:
        formulario = MensajeContactoForm()
    return render(
        request,
        "contenido/contacto.html",
        {"formulario": formulario, "enviado": enviado},
    )


def conducta(request):
    """Código de conducta para la observación responsable de aves."""
    return render(request, "contenido/conducta.html")


# ------------------------------------------------------ Páginas de los parques


def parques(request):
    """Selector de parques: es la página que se abre al pulsar el logo."""
    consulta = LugarObservacion.objects.all()
    if not es_administrador(request.user):
        consulta = consulta.filter(activo=True)
    lugares = consulta.prefetch_related("fotos").order_by("orden", "nombre")
    return render(request, "contenido/parques.html", {"lugares": lugares})


def parque_detalle(request, slug):
    """Página personalizada de un parque: portada, carrusel y avistamientos."""
    lugar = get_object_or_404(LugarObservacion, slug=slug)
    if not lugar.activo and not es_administrador(request.user):
        raise Http404("Este parque todavía no está publicado.")

    fotos = lugar.fotos.filter(activa=True)
    avistamientos = Avistamiento.objects.filter(
        aprobado=True, lugar__iexact=lugar.nombre
    ).select_related("ave")[:6]
    return render(
        request,
        "contenido/parque_detalle.html",
        {
            "lugar": lugar,
            "fotos": fotos,
            "avistamientos": avistamientos,
            "total_avistamientos": Avistamiento.objects.filter(
                aprobado=True, lugar__iexact=lugar.nombre
            ).count(),
            "puede_editar": request.user.is_superuser,
        },
    )


# ------------------------------------------------ Panel de administración


@solo_administrador
def panel_contenido(request):
    """Centro único para gestionar lugares, secciones y noticias."""
    return render(
        request,
        "contenido/panel_admin.html",
        {
            "lugares": LugarObservacion.objects.all(),
            "secciones": Seccion.objects.all(),
            "noticias": Noticia.objects.all()[:20],
        },
    )


def _editar(request, formulario, instancia, titulo, volver, mensaje):
    """Lógica compartida por los formularios del panel."""
    forma = formulario(request.POST or None, request.FILES or None, instance=instancia)
    if request.method == "POST" and forma.is_valid():
        forma.save()
        messages.success(request, mensaje)
        return redirect(volver)
    return render(
        request,
        "contenido/formulario_admin.html",
        {"form": forma, "titulo": titulo, "volver": volver},
    )


@solo_administrador
def lugar_nuevo(request):
    return _editar(
        request, LugarForm, None, "Agregar lugar de observación",
        "contenido_admin", "Lugar agregado al mapa.",
    )


@solo_administrador
def lugar_editar(request, pk):
    lugar = get_object_or_404(LugarObservacion, pk=pk)
    return _editar(
        request, LugarForm, lugar, f"Editar {lugar.nombre}",
        "contenido_admin", "Lugar actualizado.",
    )


@solo_administrador
@require_POST
def lugar_eliminar(request, pk):
    lugar = get_object_or_404(LugarObservacion, pk=pk)
    nombre = lugar.nombre
    if lugar.portada:
        lugar.portada.delete(save=False)
    for foto in lugar.fotos.all():
        if foto.imagen:
            foto.imagen.delete(save=False)
    lugar.delete()
    messages.success(request, f"Se eliminó el lugar «{nombre}».")
    return redirect("contenido_admin")


@solo_administrador
@require_POST
def lugar_alternar(request, pk):
    lugar = get_object_or_404(LugarObservacion, pk=pk)
    lugar.activo = not lugar.activo
    lugar.save(update_fields=["activo"])
    messages.success(
        request,
        f"«{lugar.nombre}» {'se muestra' if lugar.activo else 'se ocultó'} en el sitio.",
    )
    return redirect("contenido_admin")


# ---------------------------------------- Carrusel de fotos de cada parque


@solo_superadmin
def parques_admin(request):
    """Listado de parques para administrar su carrusel de fotos."""
    lugares = (
        LugarObservacion.objects.prefetch_related("fotos")
        .order_by("orden", "nombre")
    )
    return render(request, "contenido/parques_admin.html", {"lugares": lugares})


@solo_superadmin
def parque_fotos(request, pk):
    """Carrusel de fotos de un parque."""
    lugar = get_object_or_404(LugarObservacion, pk=pk)
    return render(
        request,
        "contenido/parque_fotos.html",
        {"lugar": lugar, "fotos": lugar.fotos.all()},
    )


@solo_superadmin
def parque_foto_nueva(request, pk):
    lugar = get_object_or_404(LugarObservacion, pk=pk)
    if request.method == "POST":
        formulario = FotoParqueForm(request.POST, request.FILES)
        if formulario.is_valid():
            foto = formulario.save(commit=False)
            foto.lugar = lugar
            foto.save()
            messages.success(request, f"Se añadió una foto a «{lugar.nombre}».")
            return redirect("parque_fotos", pk=lugar.pk)
    else:
        ultimo = (
            lugar.fotos.order_by("-orden").values_list("orden", flat=True).first() or 0
        )
        formulario = FotoParqueForm(initial={"orden": ultimo + 1, "activa": True})
    return render(
        request,
        "contenido/parque_foto_form.html",
        {
            "formulario": formulario,
            "lugar": lugar,
            "titulo": f"Añadir foto a «{lugar.nombre}»",
        },
    )


@solo_superadmin
def parque_foto_editar(request, pk, foto_pk):
    lugar = get_object_or_404(LugarObservacion, pk=pk)
    foto = get_object_or_404(FotoParque, pk=foto_pk, lugar=lugar)
    if request.method == "POST":
        formulario = FotoParqueForm(request.POST, request.FILES, instance=foto)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "La foto se actualizó.")
            return redirect("parque_fotos", pk=lugar.pk)
    else:
        formulario = FotoParqueForm(instance=foto)
    return render(
        request,
        "contenido/parque_foto_form.html",
        {
            "formulario": formulario,
            "lugar": lugar,
            "foto": foto,
            "titulo": f"Editar foto de «{lugar.nombre}»",
        },
    )


@solo_superadmin
@require_POST
def parque_foto_eliminar(request, pk, foto_pk):
    lugar = get_object_or_404(LugarObservacion, pk=pk)
    foto = get_object_or_404(FotoParque, pk=foto_pk, lugar=lugar)
    if foto.imagen:
        foto.imagen.delete(save=False)
    foto.delete()
    messages.success(request, f"Se eliminó una foto de «{lugar.nombre}».")
    return redirect("parque_fotos", pk=lugar.pk)


@solo_superadmin
@require_POST
def parque_foto_alternar(request, pk, foto_pk):
    lugar = get_object_or_404(LugarObservacion, pk=pk)
    foto = get_object_or_404(FotoParque, pk=foto_pk, lugar=lugar)
    foto.activa = not foto.activa
    foto.save(update_fields=["activa"])
    estado = "se muestra" if foto.activa else "se ocultó"
    messages.success(request, f"La foto {estado} en el carrusel de «{lugar.nombre}».")
    return redirect("parque_fotos", pk=lugar.pk)


@solo_superadmin
@require_POST
def parque_foto_mover(request, pk, foto_pk):
    lugar = get_object_or_404(LugarObservacion, pk=pk)
    foto = get_object_or_404(FotoParque, pk=foto_pk, lugar=lugar)
    direccion = request.POST.get("direccion")
    fotos = list(lugar.fotos.order_by("orden", "id"))
    indice = next((i for i, otra in enumerate(fotos) if otra.pk == foto.pk), None)
    destino = indice + (-1 if direccion == "subir" else 1) if indice is not None else None
    if destino is None or not 0 <= destino < len(fotos):
        return redirect("parque_fotos", pk=lugar.pk)

    for posicion, otra in enumerate(fotos, start=1):
        if otra.orden != posicion:
            otra.orden = posicion
            otra.save(update_fields=["orden"])
    vecina = fotos[destino]
    foto.orden, vecina.orden = vecina.orden, foto.orden
    foto.save(update_fields=["orden"])
    vecina.save(update_fields=["orden"])

    messages.success(request, "La foto cambió de posición.")
    return redirect("parque_fotos", pk=lugar.pk)


@solo_administrador
def seccion_nueva(request):
    return _editar(
        request, SeccionForm, None, "Agregar sección",
        "contenido_admin", "Sección creada. Puedes activarla cuando esté lista.",
    )


@solo_administrador
def seccion_editar(request, pk):
    seccion = get_object_or_404(Seccion, pk=pk)
    return _editar(
        request, SeccionForm, seccion, f"Editar sección «{seccion.nombre}»",
        "contenido_admin", "Sección actualizada.",
    )


@solo_administrador
@require_POST
def seccion_eliminar(request, pk):
    seccion = get_object_or_404(Seccion, pk=pk)
    nombre = seccion.nombre
    seccion.delete()
    messages.success(request, f"Se eliminó la sección «{nombre}».")
    return redirect("contenido_admin")


@solo_administrador
@require_POST
def seccion_alternar(request, pk):
    seccion = get_object_or_404(Seccion, pk=pk)
    seccion.activa = not seccion.activa
    seccion.save(update_fields=["activa"])
    messages.success(request, f"Sección «{seccion.nombre}» {'activada' if seccion.activa else 'desactivada'}.")
    return redirect("contenido_admin")


@solo_administrador
def noticia_nueva(request):
    return _editar(
        request, NoticiaPanelForm, None, "Agregar noticia",
        "contenido_admin", "Noticia guardada.",
    )


@solo_administrador
def noticia_editar(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    return _editar(
        request, NoticiaPanelForm, noticia, f"Editar noticia «{noticia.titulo}»",
        "contenido_admin", "Noticia actualizada.",
    )


@solo_administrador
@require_POST
def noticia_eliminar(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    titulo = noticia.titulo
    noticia.delete()
    messages.success(request, f"Se eliminó la noticia «{titulo}».")
    return redirect("contenido_admin")


@solo_administrador
@require_POST
def noticia_alternar(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    noticia.publicada = not noticia.publicada
    noticia.save(update_fields=["publicada"])
    messages.success(request, f"Noticia {'publicada' if noticia.publicada else 'despublicada'}.")
    return redirect("contenido_admin")
