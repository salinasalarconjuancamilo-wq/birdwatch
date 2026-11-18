"""Vistas públicas y panel de administración de contenido."""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permisos import es_administrador, solo_administrador

from .forms import LugarForm, MensajeContactoForm, NoticiaPanelForm, SeccionForm
from .models import LugarObservacion, Noticia, PreguntaFrecuente, Seccion, secciones_activas


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
    forma = formulario(request.POST or None, instance=instancia)
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
    lugar.delete()
    messages.success(request, f"Se eliminó el lugar «{nombre}».")
    return redirect("contenido_admin")


@solo_administrador
@require_POST
def lugar_alternar(request, pk):
    lugar = get_object_or_404(LugarObservacion, pk=pk)
    lugar.activo = not lugar.activo
    lugar.save(update_fields=["activo"])
    messages.success(request, f"«{lugar.nombre}» {'se muestra' if lugar.activo else 'se ocultó'} en el mapa.")
    return redirect("contenido_admin")


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
