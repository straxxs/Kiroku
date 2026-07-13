// ---------- Datos del curso (leídos del <body>) ----------
const ID_CURSO = document.body.dataset.idCurso;
const PUEDE_GESTIONAR = document.body.dataset.puedeGestionar === "true";
const ID_CREADOR = document.body.dataset.idCreador;
const ID_USUARIO = document.body.dataset.idUsuario;
const ES_CREADOR = String(ID_CREADOR) === String(ID_USUARIO);

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