import json
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from aves.estadisticas import resumen_estadisticas
from contenido.models import Noticia, secciones_activas

from .birdnet import CONFIANZA_MINIMA, analizar_audio, comprobar_servicio
from .forms import (
    AveForm,
    IngresoForm,
    NuevaClaveForm,
    RecuperarForm,
    RegistroForm,
    VerificarCodigoForm,
)
from .models import Ave, CodigoRecuperacion, Deteccion


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
    """Portada: carrusel, visión y misión; las demás secciones son opcionales."""
    activas = secciones_activas()
    contexto = {
        "aves": Ave.objects.filter(activo=True),
        "noticias": Noticia.objects.filter(publicada=True)[:3] if "noticias" in activas else [],
    }
    if "estadisticas" in activas:
        contexto.update(resumen_estadisticas())
    return render(request, "inicio.html", contexto)


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


def _siguiente_seguro(request, form):
    destino = (form.cleaned_data.get("siguiente") or request.GET.get("siguiente") or "").strip()
    return destino if destino.startswith("/") and not destino.startswith("//") else ""


def entrar(request):
    """Ingreso con correo electrónico y contraseña."""
    if request.user.is_authenticated:
        return redirect("identificar")

    inicial = {"siguiente": request.GET.get("siguiente", "")}
    if request.method == "POST":
        datos = request.POST.copy()
        # Compatibilidad con scripts y usuarios antiguos que enviaban «usuario».
        if not datos.get("correo") and datos.get("usuario"):
            datos["correo"] = datos["usuario"]
        form = IngresoForm(datos)
        if form.is_valid():
            identificador = form.cleaned_data["correo"]
            usuarios = get_user_model().objects
            if "@" in identificador:
                usuario = usuarios.filter(email__iexact=identificador).first() or usuarios.filter(
                    username__iexact=identificador
                ).first()
            else:
                usuario = usuarios.filter(username__iexact=identificador).first()
            autenticado = None
            if usuario is not None and usuario.is_active:
                autenticado = authenticate(
                    request, username=usuario.username, password=form.cleaned_data["contrasena"]
                )
            if autenticado is not None:
                login(request, autenticado)
                messages.success(request, f"¡Hola de nuevo, {autenticado.first_name or autenticado.username}!")
                destino = _siguiente_seguro(request, form)
                return redirect(destino or "inicio")
            form.add_error(None, "Correo electrónico o contraseña incorrectos.")
    else:
        form = IngresoForm(initial=inicial)
    return render(request, "login.html", {"form": form})


def registrarse(request):
    """Alta pública de usuarios: nunca crea privilegios de administración."""
    if request.user.is_authenticated:
        return redirect("inicio")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        usuario = get_user_model().objects.create_user(
            username=datos["correo"],
            email=datos["correo"],
            first_name=datos["nombre"].strip(),
            password=datos["contrasena1"],
        )
        login(request, usuario)
        messages.success(request, "¡Bienvenido a BirdWatch! Tu cuenta ya está lista.")
        return redirect("inicio")
    return render(request, "registrarse.html", {"form": form})


def recuperar(request):
    """Envía un código de 6 dígitos al correo registrado."""
    form = RecuperarForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        correo = form.cleaned_data["correo"].strip()
        enviados = 0
        for usuario in get_user_model().objects.filter(email__iexact=correo):
            registro = CodigoRecuperacion.crear(usuario)
            minutos = getattr(settings, "CODIGO_RECUPERACION_MINUTOS", 15)
            try:
                send_mail(
                    "Tu código de recuperación de BirdWatch",
                    (
                        f"Hola {usuario.first_name or usuario.username}:\n\n"
                        f"Tu código de verificación es {registro.codigo}.\n"
                        f"Válido durante {minutos} minutos.\n\n"
                        "Si no solicitaste este cambio, ignora este mensaje.\n\n"
                        "Equipo BirdWatch"
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.email],
                    fail_silently=False,
                )
                enviados += 1
            except Exception:
                messages.error(
                    request,
                    "No se pudo enviar el correo. Revisa la configuración SMTP e inténtalo de nuevo.",
                )
        request.session["recuperar_correo"] = correo
        if enviados:
            messages.info(request, "Enviamos un código de verificación a tu correo electrónico.")
        return redirect("recuperar_verificar")
    return render(request, "recuperar.html", {"form": form})


def recuperar_verificar(request):
    """Comprueba el código recibido y habilita el cambio de contraseña."""
    correo_inicial = request.session.get("recuperar_correo", "")
    form = VerificarCodigoForm(
        request.POST or None,
        initial={"correo": correo_inicial} if correo_inicial else None,
    )
    if request.method == "POST" and form.is_valid():
        correo = form.cleaned_data["correo"].strip()
        codigo = form.cleaned_data["codigo"]
        registro_valido = None
        for usuario in get_user_model().objects.filter(email__iexact=correo):
            candidato = (
                CodigoRecuperacion.objects.filter(usuario=usuario, codigo=codigo)
                .order_by("-creado_en")
                .first()
            )
            if candidato and candidato.vigente():
                registro_valido = candidato
                break
        if registro_valido is None:
            form.add_error("codigo", "El código no es válido o ya venció. Solicita uno nuevo.")
        else:
            request.session["recuperar_usuario_id"] = registro_valido.usuario_id
            request.session["recuperar_codigo_id"] = registro_valido.pk
            return redirect("recuperar_nueva_clave")
    return render(request, "recuperar_verificar.html", {"form": form})


def recuperar_nueva_clave(request):
    """Guarda la nueva contraseña y cancela el código utilizado."""
    usuario_id = request.session.get("recuperar_usuario_id")
    codigo_id = request.session.get("recuperar_codigo_id")
    registro = CodigoRecuperacion.objects.filter(pk=codigo_id, usuario_id=usuario_id).first()
    if registro is None or not registro.vigente():
        messages.error(request, "El código venció o no es válido. Solicita uno nuevo.")
        return redirect("recuperar")

    usuario = registro.usuario
    form = NuevaClaveForm(request.POST or None)
    form.usuario = usuario
    if request.method == "POST" and form.is_valid():
        usuario.set_password(form.cleaned_data["contrasena1"])
        usuario.save(update_fields=["password"])
        registro.usado_en = timezone.now()
        registro.save(update_fields=["usado_en"])
        for clave in ("recuperar_correo", "recuperar_usuario_id", "recuperar_codigo_id"):
            request.session.pop(clave, None)
        messages.success(request, "Contraseña actualizada. Ya puedes iniciar sesión.")
        return redirect("entrar")
    return render(request, "recuperar_nueva_clave.html", {"form": form, "usuario": usuario})


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
    motor = (
        "sqlite"
        if settings.DATABASES["default"]["ENGINE"].endswith("sqlite3")
        else "postgres"
    )
    return JsonResponse(
        {
            "motor": motor,
            "postgres": motor == "postgres",
            "birdnet": comprobar_servicio(),
        }
    )


def service_worker(request):
    """Sirve el service worker (PWA) desde la raíz del sitio."""
    archivo = Path(settings.BASE_DIR) / "estaticos" / "js" / "sw.js"
    return FileResponse(archivo.open("rb"), content_type="application/javascript")
