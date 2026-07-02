// Abrir/cerrar el dropdown del avatar en el header
document.addEventListener("click", function (e) {
    const avatar = document.getElementById("perfilAvatar");
    const menu = document.getElementById("perfilDropdown");
    if (!avatar || !menu) return;

    if (avatar.contains(e.target)) {
        menu.classList.toggle("abierto");
    } else if (!menu.contains(e.target)) {
        menu.classList.remove("abierto");
    }
});