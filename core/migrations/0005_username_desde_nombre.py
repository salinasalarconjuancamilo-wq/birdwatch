"""El username deja de ser el correo: se deriva del nombre.

Dos fases para evitar chocar con la restricción de unicidad mientras se
renombran cuentas que ya existen.
"""
from django.conf import settings
from django.db import migrations
from django.utils.text import slugify


def _candidato(usuario, usar_correo):
    if usar_correo:
        base = ((usuario.email or "").strip() or (usuario.first_name or "usuario"))[:150]
    else:
        nombre = (usuario.first_name or "").strip()
        if not nombre or "@" in nombre:
            nombre = (
                (usuario.email or "").split("@")[0]
                .replace(".", " ")
                .replace("_", " ")
                .strip()
                or "usuario"
            )
        base = (slugify(nombre) or "usuario")[:150]

    candidato = base
    numero = 2
    return candidato, numero, base


def _renombrar(apps, schema_editor, usar_correo=False):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    usuarios = list(User.objects.all().order_by("pk"))

    # Fase 1: liberar todos los usernames actuales.
    for usuario in usuarios:
        if not usuario.username.startswith("__tmp_"):
            usuario.username = f"__tmp_{usuario.pk}"
            usuario.save(update_fields=["username"])

    # Fase 2: asignar los definitivos.
    for usuario in usuarios:
        candidato, numero, base = _candidato(usuario, usar_correo)
        while User.objects.filter(username__iexact=candidato).exclude(pk=usuario.pk).exists():
            sufijo = f"-{numero}"
            candidato = f"{base[:150 - len(sufijo)]}{sufijo}"
            numero += 1
        usuario.username = candidato
        usuario.save(update_fields=["username"])


def adelante(apps, schema_editor):
    _renombrar(apps, schema_editor, usar_correo=False)


def atras(apps, schema_editor):
    _renombrar(apps, schema_editor, usar_correo=True)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_controlacceso"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(adelante, atras),
    ]
