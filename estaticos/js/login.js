/* BirdWatch · Página de inicio de sesión. */
(function () {
    'use strict';

    var campoUsuario = document.getElementById('id-usuario');
    if (campoUsuario) campoUsuario.focus();

    var boton = document.getElementById('mostrar-clave');
    var campoClave = document.getElementById('id-contrasena');
    if (boton && campoClave) {
        boton.addEventListener('click', function () {
            var oculta = campoClave.type === 'password';
            campoClave.type = oculta ? 'text' : 'password';
            boton.textContent = oculta ? '🙈' : '👁';
            boton.setAttribute('aria-pressed', oculta ? 'true' : 'false');
        });
    }
})();
