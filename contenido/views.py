"""Vistas públicas de noticias, centro de ayuda, contacto y conducta."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, render

from .forms import MensajeContactoForm
from .models import Noticia, PreguntaFrecuente


def noticias(request):
    """Listado de novedades del proyecto y del parque."""
    lista = Noticia.objects.filter(publicada=True)
    return render(request, "contenido/noticias.html", {"noticias": lista})


def noticia_detalle(request, slug):
    """Una noticia concreta (solo si está publicada, salvo administradores)."""
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
