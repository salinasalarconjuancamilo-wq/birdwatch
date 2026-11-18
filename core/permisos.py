"""Decoradores de permisos compartidos por todas las apps de BirdWatch.

Roles del proyecto
------------------
* **Acceso público**: cualquier visitante sin iniciar sesión. Puede leer.
* **Usuario**: persona con sesión iniciada. Puede registrar avistamientos,
  comentar y validar información.
* **Administrador**: ``is_staff`` o ``is_superuser``. Además puede aprobar
  contenido, gestionar usuarios y controlar los registros.
* **Superadministrador**: ``is_superuser``. Además edita el carrusel de aves y
  el carrusel de fotos de cada parque.
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def es_administrador(user):
    """Devuelve True si el usuario tiene el rol Administrador."""
    return bool(user.is_authenticated and (user.is_staff or user.is_superuser))


def _redirigir_a_login(request):
    """Manda al login conservando la página que se quería visitar."""
    return redirect(f"{reverse('entrar')}?siguiente={request.path}")


def solo_usuario(vista):
    """Exige sesión iniciada (Usuario o Administrador)."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirigir_a_login(request)
        return vista(request, *args, **kwargs)

    return envoltura


def solo_administrador(vista):
    """Exige sesión iniciada y rol Administrador."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirigir_a_login(request)
        if not es_administrador(request.user):
            messages.error(request, "Esta acción es solo para administradores.")
            return redirect("avistamientos")
        return vista(request, *args, **kwargs)

    return envoltura


def solo_superadmin(vista):
    """Permite el acceso únicamente al superadministrador."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirigir_a_login(request)
        if not request.user.is_superuser:
            messages.error(
                request, "Solo el superadministrador puede modificar el carrusel."
            )
            return redirect("inicio")
        return vista(request, *args, **kwargs)

    return envoltura
