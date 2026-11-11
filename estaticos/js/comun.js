/* BirdWatch · Utilidades comunes de todas las páginas. */
(function () {
    'use strict';

    // Registro del service worker (PWA), solo en localhost o HTTPS.
    if (
        'serviceWorker' in navigator &&
        (location.hostname === 'localhost' || location.hostname === '127.0.0.1' || location.protocol === 'https:')
    ) {
        window.addEventListener('load', function () {
            navigator.serviceWorker.register('/sw.js').catch(function () {
                /* si falla, la app sigue funcionando en línea */
            });
        });
    }

    // Lee una cookie del documento (para el token CSRF de Django).
    function obtenerCookie(nombre) {
        if (!document.cookie) return null;
        var partes = document.cookie.split(';');
        for (var i = 0; i < partes.length; i++) {
            var trozo = partes[i].trim().split('=');
            if (trozo[0] === nombre) return decodeURIComponent(trozo.slice(1).join('='));
        }
        return null;
    }

    // fetch con el encabezado X-CSRFToken en peticiones que lo necesitan.
    function enviar(url, opciones) {
        opciones = opciones || {};
        var metodo = (opciones.method || 'GET').toUpperCase();
        opciones.headers = opciones.headers || {};
        if (metodo !== 'GET' && metodo !== 'HEAD') {
            var token = obtenerCookie('csrftoken');
            if (token) opciones.headers['X-CSRFToken'] = token;
        }
        return fetch(url, opciones);
    }

    // Formatea una fecha ISO en español de Colombia.
    function formatearFecha(iso) {
        try {
            return new Date(iso).toLocaleString('es-CO', {
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return iso;
        }
    }

    window.BirdWatch = {
        obtenerCookie: obtenerCookie,
        enviar: enviar,
        formatearFecha: formatearFecha
    };
})();
