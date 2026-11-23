/* ============================================================
   BirdWatch · Mapa de lugares con Leaflet + OpenStreetMap.
   Los datos se inyectan desde Django con json_script (#datos-marcadores).
   Este mapa NO muestra avistamientos de aves, solo lugares de interés.
   ============================================================ */
(function () {
    "use strict";

    var estado = document.getElementById("mapa-estado");
    var nodo = document.getElementById("datos-marcadores");
    var contenedor = document.getElementById("mapa");

    if (!contenedor || !nodo || typeof L === "undefined") {
        if (estado) {
            estado.textContent = "No se pudo cargar el mapa. Revisa tu conexión a Leaflet.";
        }
        return;
    }

    var lugares = [];
    try {
        lugares = JSON.parse(nodo.textContent) || [];
    } catch (error) {
        if (estado) { estado.textContent = "Los datos del mapa no son válidos."; }
        return;
    }

    function escapar(texto) {
        return String(texto || "").replace(/[&<>"']/g, function (caracter) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[caracter];
        });
    }

    // Centro aproximado del área de San Antonio del Tequendama / Soacha.
    var centro = [4.59, -74.31];
    var dibujables = lugares.filter(function (lugar) {
        return typeof lugar.latitud === "number" && typeof lugar.longitud === "number";
    });
    if (dibujables.length) {
        centro = [dibujables[0].latitud, dibujables[0].longitud];
    }

    var mapa = L.map(contenedor, { scrollWheelZoom: false }).setView(centro, 12);

    var capaTeselas = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
        errorTileUrl: "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    }).addTo(mapa);

    // El proxy de algunas redes falla al abrir el túnel y deja teselas en blanco.
    // Reintentamos unas veces con espera antes de darlas por perdidas.
    var reintentos = 0;
    var temporizador = null;
    var teselasConError = false;
    mapa.on("tileerror", function () {
        teselasConError = true;
        if (reintentos >= 3 || temporizador) { return; }
        reintentos += 1;
        temporizador = setTimeout(function () {
            temporizador = null;
            capaTeselas.redraw();
        }, 1200 * reintentos);
    });

    var capa = L.layerGroup().addTo(mapa);
    var limites = [];
    var iconos = { parque: "🌲", zoologico: "🦁", reserva: "🌳", otro: "📍" };

    dibujables.forEach(function (lugar) {
        var icono = L.divIcon({
            className: "marcador-birdwatch",
            html: iconos[lugar.tipo] || iconos.otro,
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        var marca = L.marker([lugar.latitud, lugar.longitud], { icon: icono }).addTo(capa);
        var html =
            "<strong>" + escapar(lugar.nombre) + "</strong><br>" +
            "<em>" + escapar(lugar.tipo_texto) + "</em><br>" +
            escapar(lugar.ubicacion) +
            (lugar.descripcion ? "<p>" + escapar(lugar.descripcion) + "</p>" : "");
        marca.bindPopup(html);
        limites.push([lugar.latitud, lugar.longitud]);
    });

    if (limites.length > 1) {
        mapa.fitBounds(L.latLngBounds(limites).pad(0.35));
    }

    mapa.on("load", function () {
        reintentos = 0;
        teselasConError = false;
        setTimeout(function () { mapa.invalidateSize(); }, 150);
    });

    if (estado) {
        var sinCoordenadas = lugares.length - dibujables.length;
        var mensaje = dibujables.length
            ? "Mostrando " + dibujables.length + " lugar(es) en el mapa."
            : "Aún no hay lugares con coordenadas.";
        if (sinCoordenadas) {
            mensaje += " " + sinCoordenadas + " lugar(es) tienen la ubicación por definir.";
        }
        if (teselasConError && reintentos >= 3) {
            mensaje += " Algunas teselas no cargaron; recarga la página.";
        }
        estado.textContent = mensaje;
    }
})();
