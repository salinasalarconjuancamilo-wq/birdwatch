/* BirdWatch · Carrusel de aves representativas de San Antonio del Tequendama. */
(function () {
    'use strict';

    var carrusel = document.getElementById('carrusel');
    if (!carrusel) return;

    var diapositivas = Array.prototype.slice.call(carrusel.querySelectorAll('.diapositiva'));
    var puntos = document.getElementById('carrusel-puntos');
    var botonAnterior = document.getElementById('carrusel-anterior');
    var botonSiguiente = document.getElementById('carrusel-siguiente');

    var INTERVALO = 6000; // milisegundos entre aves
    var temporizador = null;
    var pausado = false;
    var indiceActual = 0;

    // Imagen de reserva si alguna foto aún no se ha descargado.
    var RESERVA = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 427">' +
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">' +
        '<stop offset="0" stop-color="#d8f3dc"/><stop offset="1" stop-color="#52b788"/>' +
        '</linearGradient></defs>' +
        '<rect width="640" height="427" fill="url(#g)"/>' +
        '<text x="320" y="200" font-family="Segoe UI, sans-serif" font-size="28" fill="#1b4332" text-anchor="middle">Foto en camino</text>' +
        '<text x="320" y="236" font-family="Segoe UI, sans-serif" font-size="22" fill="#1b4332" text-anchor="middle">🌿</text>' +
        '</svg>'
    );

    Array.prototype.forEach.call(carrusel.querySelectorAll('img'), function (imagen) {
        imagen.addEventListener('error', function () {
            // Solo se reemplaza una vez para no entrar en un bucle.
            if (imagen.dataset.reserva !== 'si') {
                imagen.dataset.reserva = 'si';
                imagen.src = RESERVA;
            }
        });
    });

    function crearPuntos() {
        if (!puntos) return;
        diapositivas.forEach(function (_, i) {
            var punto = document.createElement('button');
            punto.type = 'button';
            punto.setAttribute('role', 'tab');
            punto.setAttribute('aria-label', 'Ver ave ' + (i + 1) + ' de ' + diapositivas.length);
            punto.addEventListener('click', function () {
                irA(i);
                reiniciar();
            });
            puntos.appendChild(punto);
        });
    }

    function pintarPuntos() {
        if (!puntos) return;
        Array.prototype.forEach.call(puntos.children, function (punto, i) {
            punto.classList.toggle('activo', i === indiceActual);
            punto.setAttribute('aria-selected', i === indiceActual ? 'true' : 'false');
        });
    }

    function indiceVisible() {
        var posicion = carrusel.scrollLeft;
        for (var i = 0; i < diapositivas.length; i++) {
            if (diapositivas[i].offsetLeft >= posicion - 8) return i;
        }
        return diapositivas.length - 1;
    }

    function irA(indice) {
        indice = Math.max(0, Math.min(diapositivas.length - 1, indice));
        indiceActual = indice;
        carrusel.scrollTo({ left: diapositivas[indice].offsetLeft, behavior: 'smooth' });
        pintarPuntos();
    }

    function avanzar() {
        irA((indiceActual + 1) % diapositivas.length);
    }

    function iniciar() {
        if (pausado || document.hidden) return;
        temporizador = window.setInterval(avanzar, INTERVALO);
    }

    function detener() {
        if (temporizador !== null) {
            window.clearInterval(temporizador);
            temporizador = null;
        }
    }

    function reiniciar() {
        detener();
        iniciar();
    }

    // Sincroniza los puntos cuando el usuario desliza con el dedo.
    var sincronizando = false;
    carrusel.addEventListener('scroll', function () {
        if (sincronizando) return;
        sincronizando = true;
        window.requestAnimationFrame(function () {
            indiceActual = indiceVisible();
            pintarPuntos();
            sincronizando = false;
        });
    }, { passive: true });

    if (botonAnterior) {
        botonAnterior.addEventListener('click', function () {
            irA(indiceActual - 1);
            reiniciar();
        });
    }
    if (botonSiguiente) {
        botonSiguiente.addEventListener('click', function () {
            irA(indiceActual + 1);
            reiniciar();
        });
    }

    // Teclado: flechas izquierda y derecha.
    carrusel.addEventListener('keydown', function (evento) {
        if (evento.key === 'ArrowLeft') { irA(indiceActual - 1); reiniciar(); }
        if (evento.key === 'ArrowRight') { irA(indiceActual + 1); reiniciar(); }
    });

    // Pausar al interactuar con el carrusel.
    carrusel.addEventListener('mouseenter', function () { pausado = true; detener(); });
    carrusel.addEventListener('mouseleave', function () { pausado = false; iniciar(); });
    carrusel.addEventListener('touchstart', function () { pausado = true; detener(); }, { passive: true });
    carrusel.addEventListener('touchend', function () {
        window.setTimeout(function () { pausado = false; iniciar(); }, 8000);
    });
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) detener();
        else iniciar();
    });

    crearPuntos();
    pintarPuntos();
    iniciar();
})();
