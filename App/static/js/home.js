(function () {
// ---------- Crear curso ----------
const IC={"log-out":'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>'};
function L(n,s){s=s||16;return `<svg class="luc" xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${IC[n]}</svg>`}
const formCurso = document.getElementById("formCurso");
if (formCurso) {
    formCurso.addEventListener("submit", function (e) {
        e.preventDefault();
        if (!this.reportValidity()) return;
        if (typeof sonidoEnviar === "function") sonidoEnviar();
        fetch("/cursos/crear", { method: "POST", body: new FormData(this) })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) setTimeout(() => window.location.href = "/curso/" + data.id, 800);
            })
            .catch(() => mostrarToast("Hubo un error de conexión.", "error"));
    });
}

// ---------- Unirse a un curso ----------
const formUnirse = document.getElementById("formUnirse");
if (formUnirse) {
    formUnirse.addEventListener("submit", function (e) {
        e.preventDefault();
        if (!this.reportValidity()) return;
        if (typeof sonidoEnviar === "function") sonidoEnviar();
        fetch("/cursos/unirse", { method: "POST", body: new FormData(this) })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) setTimeout(() => window.location.href = "/curso/" + data.id, 800);
            })
            .catch(() => mostrarToast("Hubo un error de conexión.", "error"));
    });
}

// ---------- Salir del curso ----------
const btnSalir = document.getElementById("btnSalir");
if (btnSalir) {
    btnSalir.addEventListener("click", async function () {
        const ok = await kirokuConfirm(L("log-out", 20), "Salir del curso", "¿Seguro que querés salir de tu curso?", "Salir", "Quedarme");
        if (!ok) return;
        fetch("/cursos/salir", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) setTimeout(() => window.location.reload(), 800);
            })
            .catch(() => mostrarToast("Hubo un error de conexión.", "error"));
    });
}
})();