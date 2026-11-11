from django.shortcuts import render


def home(request):
    """Página principal (home) del Birdwatch."""
    return render(request, "aves/home.html")
