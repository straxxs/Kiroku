// ---------- Datos del curso (leídos del <body>) ----------
const ID_CURSO = document.body.dataset.idCurso;
const PUEDE_GESTIONAR = document.body.dataset.puedeGestionar === "true";
const ID_CREADOR = document.body.dataset.idCreador;
const ID_USUARIO = document.body.dataset.idUsuario;
const ES_CREADOR = String(ID_CREADOR) === String(ID_USUARIO);

const EXT_IMG = ["png", "jpg", "jpeg", "webp", "gif"];
const EXT_VIDEO = ["mp4", "webm", "ogg"];
const IC={"file-text":'<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',"file":'<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>',"presentation":'<path d="M2 3h20"/><path d="M21 3v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3"/><path d="m7 21 5-5 5 5"/>',"table":'<path d="M12 3v18"/><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/>',"paperclip":'<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',"pencil":'<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/>','trash-2':'<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>',"crown":'<path d="M11.562 3.266a.5.5 0 0 1 .876 0L15.39 8.87a1 1 0 0 0 1.516.294L21.183 5.5a.5.5 0 0 1 .798.519l-2.834 10.246a1 1 0 0 1-.956.734H5.81a1 1 0 0 1-.957-.734L2.02 6.02a.5.5 0 0 1 .798-.519l4.276 3.664a1 1 0 0 0 1.516-.294z"/>','user-minus':'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="17" x2="22" y1="11" y2="11"/>','check-circle':'<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>','x-circle':'<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>','sparkles':'<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>','log-out':'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>','heart':'<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>','search':'<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>'};
function L(n,s){s=s||16;return `<svg class="luc" xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${IC[n]}</svg>`}
const ICONOS = {
    pdf: L("file-text"), doc: L("file"), docx: L("file"), txt: L("file-text"),
    pptx: L("presentation"), ppt: L("presentation"), xlsx: L("table"), xls: L("table"),
};

// ---------- Preview de archivo ----------
function htmlPreviewMini(f) {
    const url = `/static/${f.ruta}`;
    const tipo = (f.tipo || "").toLowerCase();

    if (EXT_IMG.includes(tipo)) {
        return `<div class="preview-item"><img class="preview-img" src="${url}" alt="imagen" onclick="abrirLightbox('${url}')" style="cursor:pointer;"></div>`;
    }
    if (tipo === "pdf") {
        return `<div class="preview-item"><iframe class="preview-pdf" src="${url}#toolbar=0"></iframe></div>`;
    }
    if (EXT_VIDEO.includes(tipo)) {
        return `<div class="preview-item"><video class="preview-video" controls src="${url}"></video></div>`;
    }
    const icono = ICONOS[tipo] || L("paperclip");
    return `<div class="preview-item"><div class="preview-generico"><div class="icono">${icono}</div><div class="nombre">Archivo ${tipo}</div></div></div>`;
}

function abrirLightbox(url) {
    let lb = document.getElementById("lightbox");
    if (!lb) {
        lb = document.createElement("div");
        lb.id = "lightbox";
        lb.className = "lightbox";
        lb.innerHTML = `<span class="lightbox-cerrar">&times;</span><img src="" alt="ampliada">`;
        document.body.appendChild(lb);
        lb.addEventListener("click", () => lb.classList.remove("abierto"));
    }
    lb.querySelector("img").src = url;
    lb.classList.add("abierto");
}


// ---------- Materias ----------
function cargarMaterias() {
        fetch(`/cursos/${ID_CURSO}/materias`)
        .then(res => res.json())
        .then(data => {
            const tabla = document.getElementById("tablaMaterias");
            tabla.innerHTML = "";

            if (!data.materias || data.materias.length === 0) {
                tabla.innerHTML = '<tr><td colspan="3" class="vacio">No hay materias todavía. Pedile a un moderador que agregue una.</td></tr>';
                return;
            }

            data.materias.forEach(m => {
                const tr = document.createElement("tr");

                let acciones = `
                    <a href="/materia/${m.id}" class="btn btn-celeste btn-chico">Entrar</a>`;

                if (PUEDE_GESTIONAR) {
                    const nombreSeguro = (m.nombre || "").replace(/'/g, "\\'");
                    const profeSeguro = (m.nombre_profesor || "").replace(/'/g, "\\'");
                    acciones += `
                        <button class="btn btn-amarillo btn-chico"
                            onclick="editarMateria(${m.id}, '${nombreSeguro}', '${profeSeguro}')">
                            Editar
                        </button>
                        <button class="btn btn-rojo btn-chico" onclick="borrarMateria(${m.id})">
                            Eliminar
                        </button>`;
                }

                tr.innerHTML = `
                    <td>${escapeHtml(m.nombre)}</td>
                    <td>${escapeHtml(m.nombre_profesor || "-")}</td>
                    <td class="acciones">${acciones}</td>`;
                tabla.appendChild(tr);
            });
        });
}


// ---------- Alumnos ----------
function cargarAlumnos() {
    fetch(`/cursos/${ID_CURSO}/alumnos`)
        .then(res => res.json())
        .then(data => {
            const lista = document.getElementById("listaAlumnos");
            lista.innerHTML = "";

            if (!data.alumnos || data.alumnos.length === 0) {
                lista.innerHTML = '<li class="vacio">No hay integrantes.</li>';
                return;
            }

            data.alumnos.forEach(a => {
                const li = document.createElement("li");

                let boton = "";
                if (ES_CREADOR && a.rol === "alumno") {
                    boton = `<button class="btn btn-celeste btn-chico"
                                onclick="hacerModerador(${a.id})">Hacer moderador</button>`;
                } else if (ES_CREADOR && a.rol === "moderador" && String(a.id) !== String(ID_CREADOR)) {
                    boton = `<button class="btn btn-rojo btn-chico"
                                onclick="bajarModerador(${a.id})">Quitar moderador</button>`;
                }

                li.innerHTML = `
                    <span class="autor-linea" style="margin-bottom:0;">
                        ${htmlAvatar(a.nombre, a.avatar, "avatar-chico")}
                        <span>${escapeHtml(a.nombre)}</span>
                    </span>
                    <span style="display:flex;align-items:center;gap:8px;">
                        <span class="badge-rol rol-${escapeHtml(a.rol)}">${escapeHtml(a.rol)}</span>
                        ${boton}
                    </span>`;
                lista.appendChild(li);
            });
        });
}


// ---------- Crear materia ----------
const formMateria = document.getElementById("formMateria");
if (formMateria) {
    formMateria.addEventListener("submit", function (e) {
        e.preventDefault();
        if (!this.reportValidity()) return;
        const fd = new FormData(this);
        fd.append("id_curso", ID_CURSO);
        fetch("/materias/crear", { method: "POST", body: fd })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) { this.reset(); cargarMaterias(); }
            })
            .catch(() => mostrarToast("Error de conexión", "error"));
    });
}


// ---------- Editar materia ----------
async function editarMateria(id, nombreActual, profesorActual) {
    const valores = await kirokuEdit(L("pencil", 20), "Editar materia", [
        { id: "nombre", label: "Nombre de la materia", valor: nombreActual, placeholder: "Ej: Matemática" },
        { id: "profesor", label: "Profesor/a", valor: profesorActual, placeholder: "Vacío = sin profesor" }
    ]);
    if (!valores) return;

    const fd = new FormData();
    fd.append("nombre", valores.nombre);
    fd.append("profesor", valores.profesor || "");

    fetch(`/materias/editar/${id}`, { method: "POST", body: fd })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarMaterias();
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}


// ---------- Borrar materia ----------
async function borrarMateria(id) {
    const ok = await kirokuConfirm(L("trash-2", 20), "Eliminar materia", "Se perderán todos sus apuntes. ¿Continuar?", "Eliminar", "Cancelar");
    if (!ok) return;
    fetch(`/materias/eliminar/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarMaterias();
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}


// ---------- Editar curso ----------
const formEditarCurso = document.getElementById("formEditarCurso");
if (formEditarCurso) {
    formEditarCurso.addEventListener("submit", function (e) {
        e.preventDefault();
        if (!this.reportValidity()) return;
        fetch(`/cursos/editar/${ID_CURSO}`, { method: "POST", body: new FormData(this) })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) setTimeout(() => location.reload(), 800);
            })
            .catch(() => mostrarToast("Error de conexión", "error"));
    });
}


// ---------- Copiar código de invitación ----------
function copiarCodigo(codigo) {
    navigator.clipboard.writeText(codigo)
        .then(() => mostrarToast("Código copiado: " + codigo, "ok"))
        .catch(() => mostrarToast("Código del curso: " + codigo, "ok"));
}

// ---------- Ascender alumno a moderador ----------
async function hacerModerador(idUsuario) {
    const ok = await kirokuConfirm(L("crown", 20), "Ascender a moderador", "¿Convertir a este alumno en moderador del curso?", "Ascender", "Cancelar");
    if (!ok) return;
    const fd = new FormData();
    fd.append("id_usuario", idUsuario);
    fetch(`/cursos/${ID_CURSO}/ascender`, { method: "POST", body: fd })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarAlumnos();
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

// ---------- Quitar moderador ----------
async function bajarModerador(idUsuario) {
    const ok = await kirokuConfirm(L("user-minus", 20), "Quitar moderador", "¿Volver a alumno a este moderador?", "Quitar", "Cancelar");
    if (!ok) return;
    const fd = new FormData();
    fd.append("id_usuario", idUsuario);
    fetch(`/cursos/${ID_CURSO}/descender`, { method: "POST", body: fd })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarAlumnos();
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

// ---------- Apuntes pendientes (moderación) ----------
function cargarPendientes() {
    if (!PUEDE_GESTIONAR) return;
    fetch(`/cursos/${ID_CURSO}/pendientes`)
        .then(res => res.json())
        .then(data => {
            const cont = document.getElementById("listaPendientes");
            if (!cont) return;
            cont.innerHTML = "";

            if (!data.apuntes || data.apuntes.length === 0) {
                cont.innerHTML = '<p class="vacio">No hay apuntes pendientes. '+L("sparkles",20)+'</p>';
                return;
            }

            data.apuntes.forEach(a => {
                const previews = (a.archivos || []).map(htmlPreviewMini).join("");
                const div = document.createElement("div");
                div.className = "card card-apunte";
                div.style.marginBottom = "12px";
                div.innerHTML = `
                    <strong>${escapeHtml(a.titulo)}</strong> — <em>${escapeHtml(a.materia || "")}</em><br>
                    <span>Por ${escapeHtml(a.autor)}</span>
                    <p>${escapeHtml(a.descripcion || "")}</p>
                    ${previews ? `<div class="preview-grid">${previews}</div>` : ""}
                    <div class="acciones" style="margin-top:10px;">
                        <button class="btn btn-amarillo btn-chico" onclick="aprobar(${a.id})">${L("check-circle",16)} Aprobar</button>
                        <button class="btn btn-rojo btn-chico" onclick="rechazar(${a.id})">${L("x-circle",16)} Rechazar</button>
                    </div>`;
                cont.appendChild(div);
            });
        });
}

function aprobar(id) {
    fetch(`/apuntes/${id}/aprobar`, { method: "POST" })
        .then(res => res.json())
        .then(data => { mostrarToast(data.mensaje, data.ok ? "ok" : "error"); if (data.ok) cargarPendientes(); })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

function rechazar(id) {
    fetch(`/apuntes/${id}/rechazar`, { method: "POST" })
        .then(res => res.json())
        .then(data => { mostrarToast(data.mensaje, data.ok ? "ok" : "error"); if (data.ok) cargarPendientes(); })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

cargarMaterias();
cargarAlumnos();
cargarPendientes();