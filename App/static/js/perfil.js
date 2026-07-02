const avatarActual = document.body.dataset.avatarActual;
const grid = document.getElementById("avatarGrid");
const inputElegido = document.getElementById("avatarElegido");
const preview = document.getElementById("avatarPreview");

// Marcar el avatar actual como seleccionado al cargar
document.querySelectorAll(".avatar-opcion").forEach(img => {
    if (img.dataset.avatar === avatarActual) {
        img.classList.add("avatar-seleccionado");
    }

    img.addEventListener("click", function () {
        // Sacar la selección anterior
        document.querySelectorAll(".avatar-opcion")
            .forEach(el => el.classList.remove("avatar-seleccionado"));
        // Marcar este
        this.classList.add("avatar-seleccionado");
        // Guardar el valor y actualizar el preview
        inputElegido.value = this.dataset.avatar;
        preview.src = this.src;
    });
});

// Enviar formulario
document.getElementById("formPerfil").addEventListener("submit", function (e) {
    e.preventDefault();
    fetch("/perfil/actualizar", { method: "POST", body: new FormData(this) })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) setTimeout(() => location.reload(), 800);
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
});