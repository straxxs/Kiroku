// ---------- Datos del curso (leídos del <body>) ----------
const ID_CURSO = document.body.dataset.idCurso;
const PUEDE_GESTIONAR = document.body.dataset.puedeGestionar === "true";


// ---------- Materias ----------
function cargarMaterias() {
    fetch(`/cursos/${ID_CURSO}/materias`)
        .then(res => res.json())
        .then(data => {
            const tabla = document.getElementById("tablaMaterias");
            tabla.innerHTML = "";

            if (!data.materias || data.materias.length === 0) {
                tabla.innerHTML = '<tr><td colspan="3" class="vacio">No hay materias todavía.</td></tr>';
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
                    <td>${m.nombre}</td>
                    <td>${m.nombre_profesor || "-"}</td>
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
                li.innerHTML = `
                    <span class="autor-linea" style="margin-bottom:0;">
                        ${htmlAvatar(a.nombre, a.avatar, "avatar-chico")}
                        <span>${a.nombre}</span>
                    </span>
                    <span class="badge-rol rol-${a.rol}">${a.rol}</span>`;
                lista.appendChild(li);
            });
        });
}


// ---------- Crear materia ----------
const formMateria = document.getElementById("formMateria");
if (formMateria) {
    formMateria.addEventListener("submit", function (e) {
        e.preventDefault();
        const fd = new FormData(this);
        fd.append("id_curso", ID_CURSO);
        fetch("/materias/crear", { method: "POST", body: fd })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) { this.reset(); cargarMaterias(); }
            });
    });
}


// ---------- Editar materia ----------
function editarMateria(id, nombreActual, profesorActual) {
    const nombre = prompt("Nuevo nombre de la materia:", nombreActual);
    if (nombre === null) return;
    const profesor = prompt("Nombre del profesor (vacío = sin profesor):", profesorActual);

    const fd = new FormData();
    fd.append("nombre", nombre);
    fd.append("profesor", profesor || "");

    fetch(`/materias/editar/${id}`, { method: "POST", body: fd })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarMaterias();
        });
}


// ---------- Borrar materia ----------
function borrarMateria(id) {
    if (!confirm("¿Eliminar esta materia? Se perderán sus apuntes.")) return;
    fetch(`/materias/eliminar/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarMaterias();
        });
}


// ---------- Editar curso ----------
const formEditarCurso = document.getElementById("formEditarCurso");
if (formEditarCurso) {
    formEditarCurso.addEventListener("submit", function (e) {
        e.preventDefault();
        fetch(`/cursos/editar/${ID_CURSO}`, { method: "POST", body: new FormData(this) })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) setTimeout(() => location.reload(), 800);
            });
    });
}


// ---------- Copiar código de invitación ----------
function copiarCodigo(codigo) {
    navigator.clipboard.writeText(codigo)
        .then(() => mostrarToast("Código copiado: " + codigo, "ok"))
        .catch(() => mostrarToast("Código del curso: " + codigo, "ok"));
}


cargarMaterias();
cargarAlumnos();