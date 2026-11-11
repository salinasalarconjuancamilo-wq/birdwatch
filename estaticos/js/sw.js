/* BirdWatch · Service worker (PWA).
   Guarda en caché solo los archivos estáticos; las páginas, el inicio
   de sesión y las peticiones de análisis siempre van a la red. */

var NOMBRE_CACHE = 'birdwatch-estaticos-v2';

self.addEventListener('install', function (evento) {
    evento.waitUntil(
        caches.open(NOMBRE_CACHE)
            .then(function (cache) {
                return cache.addAll([
                    '/estaticos/css/estilos.css',
                    '/estaticos/js/comun.js',
                    '/estaticos/js/carrusel.js',
                    '/estaticos/js/login.js',
                    '/estaticos/img/logo.jpeg',
                    '/estaticos/manifest.webmanifest'
                ]);
            })
            .then(function () {
                return self.skipWaiting();
            })
    );
});

self.addEventListener('activate', function (evento) {
    evento.waitUntil(
        caches.keys()
            .then(function (nombres) {
                return Promise.all(
                    nombres
                        .filter(function (nombre) { return nombre !== NOMBRE_CACHE; })
                        .map(function (nombre) { return caches.delete(nombre); })
                );
            })
            .then(function () {
                return self.clients.claim();
            })
    );
});

self.addEventListener('fetch', function (evento) {
    var peticion = evento.request;

    // Nunca interceptar POST (análisis de audio) ni peticiones de datos.
    if (peticion.method !== 'GET') return;

    var url = new URL(peticion.url);
    if (url.origin !== self.location.origin) return;

    // Solo los estáticos se sirven de la caché; todo lo demás, a la red.
    if (!url.pathname.startsWith('/estaticos/')) return;

    evento.respondWith(
        caches.match(peticion).then(function (enCache) {
            if (enCache) return enCache;
            return fetch(peticion).then(function (respuesta) {
                if (respuesta.ok) {
                    var copia = respuesta.clone();
                    caches.open(NOMBRE_CACHE).then(function (cache) {
                        cache.put(peticion, copia);
                    });
                }
                return respuesta;
            });
        })
    );
});
