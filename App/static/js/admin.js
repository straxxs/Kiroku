// ---------- Usuarios ----------
function cargarUsuarios() {
    fetch("/admin/usuarios")
        .then(res => res.json())
        .then(data => {
            const tabla = document.getElementById("tablaUsuarios");
            tabla.innerHTML = "";

            if (!data.usuarios || data.usuarios.length === 0) {
                tabla.innerHTML = '<tr><td colspan="5" class="vacio">No hay usuarios.</td></tr>';
                return;
            }

            data.usuarios.forEach(u => {
                const curso = u.anio ? `${u.anio}° ${u.division}` : "-";
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${u.id}</td>
                    <td>${u.nombre}</td>
                    <td><span class="badge-rol rol-${u.rol}">${u.rol}</span></td>
                    <td>${curso}</td>
                    <td class="acciones">
                        <button class="btn btn-rojo btn-chico" onclick="borrarUsuario(${u.id})">Eliminar</button>
                    </td>`;
                tabla.appendChild(tr);
            });
        });
}

function borrarUsuario(id) {
    if (!confirm("¿Seguro que querés eliminar este usuario?")) return;
    fetch(`/admin/usuarios/eliminar/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            alert(data.mensaje);
            if (data.ok) cargarUsuarios();
        });
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
                    <td>${c.anio}</td>
                    <td>${c.division}</td>
                    <td>${c.creador || "-"}</td>
                    <td class="acciones">
                        <a href="/curso/${c.id}" class="btn btn-celeste btn-chico">Ver</a>
                        <button class="btn btn-rojo btn-chico" onclick="borrarCurso(${c.id})">Eliminar</button>
                    </td>`;
                tabla.appendChild(tr);
            });
        });
}

function borrarCurso(id) {
    if (!confirm("¿Eliminar este curso? Se perderán sus materias y apuntes.")) return;
    fetch(`/cursos/eliminar/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            alert(data.mensaje);
            if (data.ok) cargarCursos();
        });
}

cargarUsuarios();
cargarCursos();