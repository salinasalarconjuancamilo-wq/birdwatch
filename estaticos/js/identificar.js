/* BirdWatch · Identificación de aves por el canto.
   Graba el micrófono del navegador (AudioWorklet o ScriptProcessor),
   construye un WAV mono de 48 kHz, lo envía a /analizar/ (Django lo
   reenvía a BirdNET) y muestra los resultados y el historial. */
(function () {
    'use strict';

    var util = window.BirdWatch || {};
    var enviar = util.enviar || window.fetch;
    var formatearFecha = util.formatearFecha || String;

    var FRECUENCIA = 48000;   // BirdNET analiza audio de 48 kHz
    var DURACION_MAXIMA = 15;  // segundos de grabación
    var DURACION_MINIMA = 1.5; // segundos mínimos aceptables
    var BARRAS = 26;           // barras del medidor de nivel

    var boton = document.getElementById('boton-grabar');
    var botonEstado = document.getElementById('boton-grabar-estado');
    var panelGrabacion = document.getElementById('panel-grabacion');
    var nivel = document.getElementById('nivel');
    var cronometro = document.getElementById('cronometro');
    var estadoAnalisis = document.getElementById('estado-analisis');
    var avisoError = document.getElementById('aviso-error');
    var resultados = document.getElementById('resultados');
    var historial = document.getElementById('historial');
    var avisoServicio = document.getElementById('aviso-servicio');

    var estado = 'inactivo'; // inactivo | grabando | analizando
    var flujo = null;        // MediaStream del micrófono
    var contexto = null;     // AudioContext
    var nodo = null;         // nodo capturador de muestras
    var acumulado = [];      // trozos de Float32Array recibidos
    var muestrasTotales = 0;
    var nivelActual = 0;
    var temporizador = null;
    var barras = [];

    /* AudioWorklet que envía trozos de audio al hilo principal. */
    var CODIGO_WORKLET = [
        'class GrabadorBirdWatch extends AudioWorkletProcessor {',
        '  constructor() {',
        '    super();',
        '    this.tamano = 2048;',
        '    this.buffer = new Float32Array(this.tamano);',
        '    this.posicion = 0;',
        '  }',
        '  process(entradas) {',
        '    var canal = entradas[0] && entradas[0][0];',
        '    if (canal) {',
        '      for (var i = 0; i < canal.length; i++) {',
        '        this.buffer[this.posicion++] = canal[i];',
        '        if (this.posicion === this.tamano) {',
        '          this.port.postMessage(this.buffer.slice(0));',
        '          this.posicion = 0;',
        '        }',
        '      }',
        '    }',
        '    return true;',
        '  }',
        '}',
        'registerProcessor("grabador-birdwatch", GrabadorBirdWatch);'
    ].join('\n');

    /* ---------------- Utilidades de interfaz ---------------- */

    function mostrarError(texto) {
        avisoError.textContent = texto;
        avisoError.classList.remove('oculto');
    }

    function limpiarError() {
        avisoError.classList.add('oculto');
        avisoError.textContent = '';
    }

    function crearBarras() {
        if (!nivel) return;
        for (var i = 0; i < BARRAS; i++) {
            var barra = document.createElement('span');
            nivel.appendChild(barra);
            barras.push(barra);
        }
    }

    function pintarNivel() {
        var altura = Math.max(0.04, Math.min(1, nivelActual));
        for (var i = 0; i < barras.length; i++) {
            var factor = 0.55 + Math.random() * 0.65;
            var porcentaje = Math.max(4, Math.min(100, altura * factor * 100));
            barras[i].style.height = porcentaje + '%';
        }
    }

    function formatearTiempo(segundos) {
        var s = Math.min(DURACION_MAXIMA, Math.floor(segundos));
        var minutos = Math.floor(s / 60);
        var resto = s % 60;
        return minutos + ':' + (resto < 10 ? '0' : '') + resto;
    }

    /* ---------------- Captura de audio ---------------- */

    function recibirMuestras(datos) {
        if (estado !== 'grabando') return;
        acumulado.push(datos);
        muestrasTotales += datos.length;

        var suma = 0;
        for (var i = 0; i < datos.length; i++) suma += datos[i] * datos[i];
        var rms = Math.sqrt(suma / datos.length);
        nivelActual = Math.max(rms * 4, nivelActual * 0.82);
        pintarNivel();
    }

    function montarNodoAntiguo(fuente) {
        nodo = contexto.createScriptProcessor(4096, 1, 1);
        nodo.onaudioprocess = function (evento) {
            recibirMuestras(evento.inputBuffer.getChannelData(0).slice(0));
        };
        fuente.connect(nodo);
        nodo.connect(contexto.destination);
    }

    function montarNodo() {
        var fuente = contexto.createMediaStreamSource(flujo);
        if (contexto.audioWorklet) {
            var url = URL.createObjectURL(new Blob([CODIGO_WORKLET], { type: 'application/javascript' }));
            return contexto.audioWorklet.addModule(url).then(function () {
                URL.revokeObjectURL(url);
                nodo = new AudioWorkletNode(contexto, 'grabador-birdwatch');
                nodo.port.onmessage = function (mensaje) {
                    recibirMuestras(new Float32Array(mensaje.data));
                };
                fuente.connect(nodo);
                // Conexión silenciosa para que el worklet procese sin retroalimentación.
                var silencio = contexto.createGain();
                silencio.gain.value = 0;
                nodo.connect(silencio);
                silencio.connect(contexto.destination);
            }).catch(function () {
                montarNodoAntiguo(fuente);
            });
        }
        montarNodoAntiguo(fuente);
        return Promise.resolve();
    }

    function mensajePermiso(error) {
        var nombre = error && error.name;
        if (nombre === 'NotAllowedError' || nombre === 'PermissionDeniedError') {
            return 'No se dio permiso para usar el micrófono. Áctivalo con el candado de la barra de direcciones y vuelve a intentar.';
        }
        if (nombre === 'NotFoundError' || nombre === 'DevicesNotFoundError') {
            return 'No se encontró ningún micrófono conectado a este equipo.';
        }
        if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            return 'El micrófono solo funciona en HTTPS o en localhost; abre la página con una de esas dos direcciones.';
        }
        return 'No fue posible acceder al micrófono: ' + (error && error.message ? error.message : 'error desconocido');
    }

    function grabar() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            mostrarError('Tu navegador no permite usar el micrófono. Prueba con Chrome, Edge o Firefox actualizados.');
            return;
        }
        navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: false,
                noiseSuppression: false,
                autoGainControl: false,
                channelCount: 1
            }
        }).then(function (flujoAudio) {
            flujo = flujoAudio;
            var Constructor = window.AudioContext || window.webkitAudioContext;
            try {
                contexto = new Constructor({ sampleRate: FRECUENCIA });
            } catch (error) {
                contexto = new Constructor();
            }
            var preparado = contexto.resume ? contexto.resume() : Promise.resolve();
            return preparado.then(function () {
                return montarNodo();
            }).then(function () {
                comenzarGrabacion();
            });
        }).catch(function (error) {
            flujo = null;
            mostrarError(mensajePermiso(error));
        });
    }

    function comenzarGrabacion() {
        estado = 'grabando';
        acumulado = [];
        muestrasTotales = 0;
        nivelActual = 0;
        limpiarError();
        boton.classList.add('grabando');
        botonEstado.textContent = 'Detener';
        panelGrabacion.classList.remove('oculto');
        cronometro.textContent = '0:00';
        var inicioTiempo = performance.now();
        temporizador = window.setInterval(function () {
            var transcurrido = (performance.now() - inicioTiempo) / 1000;
            cronometro.textContent = formatearTiempo(transcurrido);
            if (transcurrido >= DURACION_MAXIMA) detenerYAnalizar();
        }, 100);
    }

    /* ---------------- Detener y analizar ---------------- */

    function detenerYAnalizar() {
        if (estado !== 'grabando') return;
        estado = 'analizando';
        boton.disabled = true;

        if (temporizador !== null) {
            window.clearInterval(temporizador);
            temporizador = null;
        }
        if (nodo) {
            try { nodo.disconnect(); } catch (error) { /* ignorar */ }
            nodo = null;
        }
        if (flujo) {
            flujo.getTracks().forEach(function (pista) { pista.stop(); });
            flujo = null;
        }
        var frecuenciaOrigen = contexto ? contexto.sampleRate : FRECUENCIA;
        if (contexto) {
            contexto.close();
            contexto = null;
        }

        boton.classList.remove('grabando');
        botonEstado.textContent = 'Espera…';
        panelGrabacion.classList.add('oculto');
        cronometro.textContent = '0:00';

        var duracion = muestrasTotales / frecuenciaOrigen;
        if (duracion < DURACION_MINIMA) {
            estado = 'inactivo';
            boton.disabled = false;
            botonEstado.textContent = 'Grabar';
            mostrarError('La grabación duró muy poco. Intenta grabar al menos 3 segundos del canto del ave.');
            return;
        }

        var muestras = new Float32Array(muestrasTotales);
        var posicion = 0;
        for (var i = 0; i < acumulado.length; i++) {
            muestras.set(acumulado[i], posicion);
            posicion += acumulado[i].length;
        }
        acumulado = [];

        estadoAnalisis.classList.remove('oculto');
        limpiarError();

        remuestrear(muestras, frecuenciaOrigen, FRECUENCIA)
            .then(function (finales) {
                return analizar(construirWav(finales, FRECUENCIA));
            })
            .then(function (respuesta) {
                return respuesta.json().catch(function () { return {}; }).then(function (cuerpo) {
                    if (!respuesta.ok) {
                        throw new Error(cuerpo.error || 'El servidor no pudo analizar la grabación.');
                    }
                    return cuerpo;
                });
            })
            .then(function (cuerpo) {
                pintarResultados(cuerpo.resultados || []);
                cargarHistorial();
            })
            .catch(function (error) {
                mostrarError(error.message || 'Ocurrió un error al analizar la grabación.');
            })
            .then(function () {
                estadoAnalisis.classList.add('oculto');
                estado = 'inactivo';
                boton.disabled = false;
                botonEstado.textContent = 'Grabar';
            });
    }

    /* Cambia la frecuencia de muestreo a 48 kHz si el micrófono dio otra. */
    function remuestrear(muestras, frecuenciaOrigen, frecuenciaDestino) {
        if (frecuenciaOrigen === frecuenciaDestino || typeof OfflineAudioContext === 'undefined') {
            return Promise.resolve(muestras);
        }
        try {
            var longitud = Math.max(1, Math.ceil(muestras.length * frecuenciaDestino / frecuenciaOrigen));
            var fueraDeLinea = new OfflineAudioContext(1, longitud, frecuenciaDestino);
            var buffer = fueraDeLinea.createBuffer(1, muestras.length, frecuenciaOrigen);
            buffer.copyToChannel(muestras, 0);
            var fuente = fueraDeLinea.createBufferSource();
            fuente.buffer = buffer;
            fuente.connect(fueraDeLinea.destination);
            fuente.start();
            return fueraDeLinea.startRendering().then(function (renderizado) {
                return renderizado.getChannelData(0);
            });
        } catch (error) {
            return Promise.resolve(muestras);
        }
    }

    /* Construye un archivo WAV (PCM 16 bits, mono) a partir de las muestras. */
    function construirWav(muestras, frecuencia) {
        var longitudDatos = muestras.length * 2;
        var buffer = new ArrayBuffer(44 + longitudDatos);
        var vista = new DataView(buffer);

        function texto(desplazamiento, cadena) {
            for (var i = 0; i < cadena.length; i++) {
                vista.setUint8(desplazamiento + i, cadena.charCodeAt(i));
            }
        }

        texto(0, 'RIFF');
        vista.setUint32(4, 36 + longitudDatos, true);
        texto(8, 'WAVE');
        texto(12, 'fmt ');
        vista.setUint32(16, 16, true);            // tamaño del bloque fmt
        vista.setUint16(20, 1, true);              // formato PCM
        vista.setUint16(22, 1, true);              // canal mono
        vista.setUint32(24, frecuencia, true);    // frecuencia de muestreo
        vista.setUint32(28, frecuencia * 2, true);// bytes por segundo
        vista.setUint16(32, 2, true);              // alineación de bloque
        vista.setUint16(34, 16, true);             // bits por muestra
        texto(36, 'data');
        vista.setUint32(40, longitudDatos, true);

        var desplazamiento = 44;
        for (var i = 0; i < muestras.length; i++, desplazamiento += 2) {
            var muestra = Math.max(-1, Math.min(1, muestras[i]));
            vista.setInt16(desplazamiento, muestra < 0 ? muestra * 0x8000 : muestra * 0x7FFF, true);
        }
        return new Blob([vista], { type: 'audio/wav' });
    }

    function analizar(wav) {
        var datos = new FormData();
        datos.append('audio', wav, 'grabacion-birdwatch.wav');
        return enviar('/analizar/', { method: 'POST', body: datos });
    }

    /* ---------------- Presentación de resultados ---------------- */

    function pintarResultados(lista) {
        resultados.innerHTML = '';
        if (!lista.length) {
            var vacio = document.createElement('p');
            vacio.className = 'sin-resultados';
            vacio.textContent = 'No se identificaron aves con confianza suficiente. Acércate al canto o graba entre 3 y 15 segundos.';
            resultados.appendChild(vacio);
            return;
        }

        lista.forEach(function (r) {
            var tarjeta = document.createElement('article');
            tarjeta.className = 'resultado';

            var cabecera = document.createElement('div');
            cabecera.className = 'resultado-cabecera';
            var nombre = document.createElement('h3');
            nombre.className = 'resultado-nombre';
            nombre.textContent = r.especie_es || r.especie_en;
            var porcentaje = document.createElement('span');
            porcentaje.className = 'resultado-porcentaje';
            porcentaje.textContent = Math.round(r.confianza * 100) + '%';
            cabecera.appendChild(nombre);
            cabecera.appendChild(porcentaje);
            tarjeta.appendChild(cabecera);

            if (r.nombre_cientifico) {
                var cientifico = document.createElement('p');
                cientifico.className = 'resultado-cientifico';
                cientifico.textContent = r.nombre_cientifico;
                tarjeta.appendChild(cientifico);
            }

            var barra = document.createElement('div');
            barra.className = 'barra-confianza';
            var relleno = document.createElement('span');
            relleno.style.width = Math.max(3, Math.round(r.confianza * 100)) + '%';
            barra.appendChild(relleno);
            tarjeta.appendChild(barra);

            var meta = document.createElement('p');
            meta.className = 'resultado-meta';
            var partes = [];
            if (r.tipo_sonido) partes.push(r.tipo_sonido);
            if (!r.especie_es && r.especie_en) partes.push('Nombre en inglés: ' + r.especie_en);
            meta.textContent = partes.join(' · ');
            if (meta.textContent) tarjeta.appendChild(meta);

            resultados.appendChild(tarjeta);
        });
    }

    function cargarHistorial() {
        return fetch('/historial/')
            .then(function (respuesta) { return respuesta.json(); })
            .then(function (cuerpo) {
                historial.innerHTML = '';
                var detecciones = cuerpo.detecciones || [];
                if (!detecciones.length) {
                    var vacio = document.createElement('p');
                    vacio.className = 'sin-resultados';
                    vacio.textContent = 'Aún no tienes detecciones guardadas en la base de datos.';
                    historial.appendChild(vacio);
                    return;
                }
                detecciones.forEach(function (d) {
                    var fila = document.createElement('div');
                    fila.className = 'historial-fila';

                    var fuerte = document.createElement('strong');
                    fuerte.textContent = d.especie_es || d.especie_en;
                    fila.appendChild(fuerte);

                    var fecha = document.createElement('span');
                    fecha.className = 'historial-fecha';
                    fecha.textContent = formatearFecha(d.creado_en);
                    fila.appendChild(fecha);

                    var confianza = document.createElement('span');
                    confianza.className = 'historial-confianza';
                    confianza.textContent = Math.round(d.confianza * 100) + '%';
                    fila.appendChild(confianza);

                    historial.appendChild(fila);
                });
            })
            .catch(function () {
                historial.innerHTML = '';
                var aviso = document.createElement('p');
                aviso.className = 'sin-resultados';
                aviso.textContent = 'No se pudo cargar el historial de detecciones.';
                historial.appendChild(aviso);
            });
    }

    /* ---------------- Arranque de la página ---------------- */

    crearBarras();

    boton.addEventListener('click', function () {
        if (estado === 'grabando') detenerYAnalizar();
        else if (estado === 'inactivo') grabar();
    });

    cargarHistorial();

    // Aviso si el analizador BirdNET no está corriendo en el servidor.
    if (avisoServicio && window.fetch) {
        fetch('/estado/').then(function (r) { return r.json(); }).then(function (estadoServicio) {
            if (!estadoServicio.birdnet) avisoServicio.classList.remove('oculto');
        }).catch(function () { /* sin novedad */ });
    }
})();
