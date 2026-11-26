/* ============================================================
   BirdWatch · Mapa de lugares con Leaflet + Esri World Street Map.
   Los datos se inyectan desde Django con json_script (#datos-marcadores).
   Este mapa NO muestra avistamientos de aves, solo lugares de interés.

   QA: encuadre regional (minZoom/maxBounds/noWrap) y respaldo ante fallos
   del proveedor de teselas (BUG-07 y BUG-09).
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

    // Límites regionales (Cundinamarca / Tequendama): evita el mapamundi
    // repetido y las franjas grises al alejar el zoom.
    var ZOOM_MINIMO = 10;
    var LIMITES = [[4.1, -74.8], [5.1, -73.7]];
    var mapa = L.map(contenedor, {
        scrollWheelZoom: false,
        minZoom: ZOOM_MINIMO,
        maxZoom: 19,
        maxBounds: LIMITES,
        maxBoundsViscosity: 1.0
    }).setView(centro, 12);

    var teselaVacia = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
    var urlEsri = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}";
    var urlOsm = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

    function crearCapa(respaldo) {
        var opciones = {
            minZoom: ZOOM_MINIMO,
            maxZoom: 19,
            noWrap: true,
            errorTileUrl: teselaVacia
        };
        if (respaldo) {
            opciones.attribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
            return L.tileLayer(urlOsm, opciones);
        }
        opciones.attribution = 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom, 2012';
        return L.tileLayer(urlEsri, opciones);
    }

    var capaTeselas = crearCapa(false).addTo(mapa);
    var erroresPrincipales = 0;
    var usandoRespaldo = false;
    var aviso = null;

    function mostrarAviso(texto) {
        if (!aviso) {
            aviso = document.createElement("div");
            aviso.className = "mapa-aviso";
            aviso.setAttribute("role", "status");
            contenedor.parentNode.appendChild(aviso);
        }
        aviso.textContent = texto;
    }

    function ocultarAviso() {
        if (aviso && aviso.parentNode) {
            aviso.parentNode.removeChild(aviso);
        }
        aviso = null;
    }

    function textoEstado() {
        var sinCoordenadas = lugares.length - dibujables.length;
        var mensaje = dibujables.length
            ? "Mostrando " + dibujables.length + " lugar(es) en el mapa."
            : "Aún no hay lugares con coordenadas.";
        if (sinCoordenadas) {
            mensaje += " " + sinCoordenadas + " lugar(es) tienen la ubicación por definir.";
        }
        return mensaje;
    }

    function actualizarEstado(extra) {
        if (estado) {
            estado.textContent = textoEstado() + (extra || "");
        }
    }

    function activarRespaldo() {
        if (usandoRespaldo) { return; }
        usandoRespaldo = true;
        mapa.removeLayer(capaTeselas);
        capaTeselas = crearCapa(true).addTo(mapa);
        capaTeselas.on("tileerror", function () {
            mostrarAviso("El mapa base no está disponible en este momento. Revisa tu conexión.");
            actualizarEstado(" No se pudieron cargar las teselas del mapa.");
        });
        capaTeselas.on("tileload", function () {
            ocultarAviso();
            actualizarEstado(" Se usa la capa de respaldo de OpenStreetMap.");
        });
        mostrarAviso("El proveedor principal no responde. Se cambió a OpenStreetMap.");
        actualizarEstado(" Se usa la capa de respaldo de OpenStreetMap.");
    }

    // Tras varios errores seguidos se cambia de proveedor en vez de
    // dejar un recuadro gris sin explicación.
    capaTeselas.on("tileerror", function () {
        erroresPrincipales += 1;
        if (erroresPrincipales >= 3) {
            activarRespaldo();
        }
    });
    capaTeselas.on("tileload", function () {
        if (!usandoRespaldo) { erroresPrincipales = 0; }
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
        setTimeout(function () { mapa.invalidateSize(); }, 150);
    });

    actualizarEstado();
})();
