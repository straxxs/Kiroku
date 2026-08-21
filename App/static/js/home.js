(function () {
// ---------- Crear curso (sin abandonar los otros) ----------
const formCurso = document.getElementById("formCurso");
if (formCurso) {
    formCurso.addEventListener("submit", function (e) {
        e.preventDefault();
        if (!this.reportValidity()) return;
        if (typeof sonidoEnviar === "function") sonidoEnviar();
        fetch("/cursos/crear", { method: "POST", body: new FormData(this) })
            .then(r => r.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) setTimeout(() => window.location.href = "/curso/" + data.id, 900);
            })
            .catch(() => mostrarToast("Hubo un error de conexión.", "error"));
    });
}

// ---------- Unirse a otro curso ----------
const formUnirse = document.getElementById("formUnirse");
if (formUnirse) {
    formUnirse.addEventListener("submit", function (e) {
        e.preventDefault();
        if (!this.reportValidity()) return;
        if (typeof sonidoEnviar === "function") sonidoEnviar();
        fetch("/cursos/unirse", { method: "POST", body: new FormData(this) })
            .then(r => r.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) setTimeout(() => window.location.href = "/curso/" + data.id, 900);
            })
            .catch(() => mostrarToast("Hubo un error de conexión.", "error"));
    });
}

// ---------- Salir / Eliminar un curso PUNTUAL (delegación de eventos) ----------
document.addEventListener("click", async function (e) {
    const btnSalir = e.target.closest('[data-accion="salir-curso"]');
    if (btnSalir) {
        const id = btnSalir.dataset.curso;
        const nombre = btnSalir.dataset.nombre;
        const ok = await kirokuConfirm(L("log-out", 20), "Salir del curso",
            `¿Salir de ${nombre}? Vas a conservar tus otros cursos.`, "Salir", "Quedarme");
        if (!ok) return;
        fetch(`/cursos/${id}/salir`, { method: "POST" })
            .then(r => r.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) setTimeout(() => location.reload(), 800);
            })
            .catch(() => mostrarToast("Error de conexión", "error"));
        return;
    }

    const btnEliminar = e.target.closest('[data-accion="eliminar-curso"]');
    if (btnEliminar) {
        const id = btnEliminar.dataset.curso;
        const nombre = btnEliminar.dataset.nombre;
        const ok = await kirokuConfirm(L("trash-2", 20), "Eliminar curso",
            `Se eliminarán TODAS las materias, apuntes y archivos de ${nombre}. Los integrantes perderán el acceso. ¿Continuar?`,
            "Eliminar", "Cancelar");
        if (!ok) return;
        fetch(`/cursos/eliminar/${id}`, { method: "POST" })
            .then(r => r.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) setTimeout(() => location.reload(), 800);
            })
            .catch(() => mostrarToast("Error de conexión", "error"));
    }
});
})();