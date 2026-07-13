// ---------- Usuarios ----------
function cargarUsuarios() {
    fetch("/admin/usuarios")
        .then(res => res.json())
        .then(data => {
            const tabla = document.getElementById("tablaUsuarios");
            tabla.innerHTML = "";

            if (!data.usuarios || data.usuarios.length === 0) {
                tabla.innerHTML = '<tr><td colspan="6" class="vacio">No hay usuarios.</td></tr>';
                return;
            }

            data.usuarios.forEach(u => {
                const curso = u.anio ? `${u.anio}° ${u.division}°` : "-";
                const tr = document.createElement("tr");
                const estadoBadge = u.estado === "bloqueado"
                    ? '<span class="badge-rol rol-bloqueado">bloqueado</span>'
                    : '<span class="badge-rol rol-alumno">activo</span>';

                const opcionesRol = ["alumno", "moderador", "admin"]
                    .map(r => `<option value="${r}" ${u.rol === r ? "selected" : ""}>${r}</option>`)
                    .join("");

                tr.innerHTML = `
                    <td>${u.id}</td>
                    <td>
                        <div class="autor-linea">
                            ${htmlAvatar(u.nombre, u.avatar, "avatar-chico")}
                            <span>${escapeHtml(u.nombre)}</span>
                        </div>
                    </td>
                    <td>
                        <select class="select-rol" onchange="cambiarRol(${u.id}, this.value)">
                            ${opcionesRol}
                        </select>
                    </td>
                    <td>${estadoBadge}</td>
                    <td>${curso}</td>
                    <td class="acciones">
                        <button class="btn ${u.estado === 'bloqueado' ? 'btn-celeste' : 'btn-rojo'} btn-chico"
                            onclick="toggleEstado(${u.id}, '${u.estado === 'bloqueado' ? 'activo' : 'bloqueado'}')">
                            ${u.estado === 'bloqueado' ? 'Activar' : 'Bloquear'}
                        </button>
                        <button class="btn btn-rojo btn-chico" onclick="borrarUsuario(${u.id})">Eliminar</button>
                    </td>`;
                tabla.appendChild(tr);
            });
        });
}

async function borrarUsuario(id) {
    const ok = await kirokuConfirm(L("trash-2", 20), "Eliminar usuario", "¿Seguro que querés eliminar este usuario? No se podrá recuperar.", "Eliminar", "Cancelar");
    if (!ok) return;
    fetch(`/admin/usuarios/eliminar/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarUsuarios();
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

function toggleEstado(id, nuevoEstado) {
    const fd = new FormData();
    fd.append("estado", nuevoEstado);
    fetch(`/admin/usuarios/${id}/estado`, { method: "POST", body: fd })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarUsuarios();
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

function cambiarRol(id, nuevoRol) {
    const fd = new FormData();
    fd.append("rol", nuevoRol);
    fetch(`/admin/usuarios/${id}/rol`, { method: "POST", body: fd })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarUsuarios();
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

// ---------- Cursos ----------
function cargarCursos() {
    fetch("/cursos")
        .then(res => res.json())
        .then(data => {
            const tabla = document.getElementById("tablaCursos");
            tabla.innerHTML = "";

            if (!data.cursos || data.cursos.length === 0) {
                tabla.innerHTML = '<tr><td colspan="5" class="vacio">No hay cursos.</td></tr>';
                return;
            }

            data.cursos.forEach(c => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${c.id}</td>
                    <td>${escapeHtml(c.anio)}</td>
                    <td>${escapeHtml(c.division)}</td>
                    <td>${escapeHtml(c.creador || "-")}</td>
                    <td class="acciones">
                        <a href="/curso/${c.id}" class="btn btn-celeste btn-chico">Ver</a>
                        <button class="btn btn-rojo btn-chico" onclick="borrarCurso(${c.id})">Eliminar</button>
                    </td>`;
                tabla.appendChild(tr);
            });
        });
}

async function borrarCurso(id) {
    const ok = await kirokuConfirm(L("trash-2", 20), "Eliminar curso", "Se perderán todas sus materias y apuntes. ¿Continuar?", "Eliminar", "Cancelar");
    if (!ok) return;
    fetch(`/cursos/eliminar/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarCursos();
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

cargarUsuarios();
cargarCursos();
