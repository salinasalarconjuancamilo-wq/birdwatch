"""Utilidades para derivar el ``username`` del nombre del usuario.

El correo es el identificador de acceso, pero no el ``username`` interno:
este se genera a partir del nombre para que el usuario pueda cambiar su correo
sin afectar su cuenta.
"""
from django.contrib.auth import get_user_model
from django.utils.text import slugify


def username_desde_nombre(nombre, excluir_pk=None):
    """Devuelve un username único y seguro a partir del nombre.

    ``María José`` -> ``maria-jose``. Si ya existe, añade ``-2``, ``-3``, etc.
    """
    consulta = get_user_model().objects.all()
    if excluir_pk is not None:
        consulta = consulta.exclude(pk=excluir_pk)

    base = (slugify(nombre or "") or "usuario")[:150]
    candidato = base
    numero = 2
    while consulta.filter(username__iexact=candidato).exists():
        sufijo = f"-{numero}"
        candidato = f"{base[:150 - len(sufijo)]}{sufijo}"
        numero += 1
    return candidato
