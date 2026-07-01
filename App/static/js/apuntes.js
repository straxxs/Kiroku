// ---------- Datos de la materia (leídos del <body>) ----------
const ID_MATERIA = document.body.dataset.idMateria;
const PUEDE_GESTIONAR = document.body.dataset.puedeGestionar === "true";
let MI_ID = null;


// ---------- Cargar apuntes ----------
function cargarApuntes() {
    fetch(`/materias/${ID_MATERIA}/apuntes`)
        .then(res => res.json())
        .then(data => {
            MI_ID = data.id_usuario;
            const cont = document.getElementById("listaApuntes");
            cont.innerHTML = "";

            if (!data.apuntes || data.apuntes.length === 0) {
                cont.innerHTML = '<p class="vacio">Todavía no hay apuntes. 📄</p>';
                return;
            }

            data.apuntes.forEach(a => {
                const puedeBorrar = (a.id_usuario_creador === MI_ID) || PUEDE_GESTIONAR;

                const archivosHtml = (a.archivos || []).map(f =>
                    `<a class="btn btn-celeste btn-chico"
                        href="/static/${f.ruta}" target="_blank">
                        Ver archivo (${f.tipo})
                     </a>`
                ).join(" ");

                const div = document.createElement("div");
                div.className = "card";
                div.style.marginBottom = "14px";
                div.innerHTML = `
                    <p><strong>${a.autor || "Anónimo"}</strong></p>
                    <p>${a.descripcion || "<em>Sin descripción</em>"}</p>
                    <div class="acciones">
                        ${archivosHtml}
                        ${puedeBorrar
                            ? `<button class="btn btn-rojo btn-chico"
                                 onclick="borrarApunte(${a.id})">Eliminar</button>`
                            : ""}
                    </div>`;
                cont.appendChild(div);
            });
        })
        .catch(() => mostrarToast("Error al cargar apuntes", "error"));
}


// ---------- Borrar apunte ----------
function borrarApunte(id) {
    if (!confirm("¿Eliminar este apunte?")) return;
    fetch(`/apuntes/eliminar/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarApuntes();
        });
}


// ---------- Subir apunte ----------
const formApunte = document.getElementById("formApunte");
if (formApunte) {
    formApunte.addEventListener("submit", function (e) {
        e.preventDefault();
        const fd = new FormData(this);
        fd.append("id_materia", ID_MATERIA);
        fetch("/apuntes/crear", { method: "POST", body: fd })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) { this.reset(); cargarApuntes(); }
            })
            .catch(() => mostrarToast("Error de conexión", "error"));
    });
}


cargarApuntes();