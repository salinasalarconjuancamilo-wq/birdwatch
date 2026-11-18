/* ============================================================
   BirdWatch · Mapa interactivo con Leaflet + OpenStreetMap.
   Los datos se inyectan desde Django con json_script (#datos-marcadores).
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

    var marcadores = [];
    try {
        marcadores = JSON.parse(nodo.textContent) || [];
    } catch (error) {
        if (estado) { estado.textContent = "Los datos del mapa no son válidos."; }
        return;
    }

    // Centro aproximado del Parque Ecológico San Antonio del Tequendama.
    var centro = [4.5589, -74.2933];
    if (marcadores.length) {
        centro = [marcadores[0].latitud, marcadores[0].longitud];
    }

    var mapa = L.map(contenedor, { scrollWheelZoom: false }).setView(centro, 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(mapa);

    var capa = L.layerGroup().addTo(mapa);
    var limites = [];

    marcadores.forEach(function (item) {
        var icono = L.divIcon({
            className: "marcador-birdwatch",
            html: item.caso_especial ? "★" : "🐦",
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        var marca = L.marker([item.latitud, item.longitud], { icon: icono }).addTo(capa);
        var foto = item.foto
            ? '<p><img src="' + item.foto + '" alt="Foto de ' + item.especie + '" style="max-width:100%;max-height:150px;border-radius:8px"></p>'
            : "";
        var html =
            "<strong><a href=\"" + item.detalle + "\">" + item.especie + "</a></strong><br>" +
            "<em>" + (item.cientifico || "") + "</em><br>" +
            item.lugar + " · " + item.zona + "<br>" +
            "Fecha: " + item.fecha + " · Cantidad: " + item.cantidad + "<br>" +
            (item.caso_especial ? "<strong>★ Caso especial</strong><br>" : "") +
            "Validaciones: " + item.validaciones + "<br>" +
            (item.notas ? "<p>" + item.notas + "</p>" : "") +
            foto;
        marca.bindPopup(html);
        limites.push([item.latitud, item.longitud]);
    });

    if (limites.length > 1) {
        mapa.fitBounds(L.latLngBounds(limites).pad(0.25));
    }

    mapa.on("load", function () {
        setTimeout(function () { mapa.invalidateSize(); }, 150);
    });

    if (estado) {
        estado.textContent = marcadores.length
            ? "Mostrando " + marcadores.length + " avistamiento(s) en el mapa."
            : "Aún no hay avistamientos con coordenadas. ¡Registra el primero!";
    }
})();
