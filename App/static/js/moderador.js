let idCursoActual = null;

// ---------- Cargar info de mi curso ----------
function cargarCurso() {
    fetch("/cursos/mio")
        .then(res => res.json())
        .then(data => {
            const info = document.getElementById("infoCurso");
            const formEditar = document.getElementById("formEditar");

            if (!data.curso) {
                info.innerHTML = '<p class="vacio">Todavía no tenés un curso asignado.</p>';
                return;
            }

            idCursoActual = data.curso.id;
            info.innerHTML = `<p><strong>${data.curso.anio}° ${data.curso.division}</strong> (ID: ${data.curso.id})</p>`;

            // Precargar el form de edición
            document.getElementById("editAnio").value = data.curso.anio;
            document.getElementById("editDivision").value = data.curso.division;
            formEditar.style.display = "block";

            cargarMaterias();
        });
}

// ---------- Cargar materias ----------
function cargarMaterias() {
    if (!idCursoActual) return;
    fetch(`/cursos/${idCursoActual}/materias`)
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
                tr.innerHTML = `
                    <td>${m.nombre}</td>
                    <td>${m.nombre_profesor || "-"}</td>
                    <td class="acciones">
                        <button class="btn btn-rojo btn-chico" onclick="borrarMateria(${m.id})">Eliminar</button>
                    </td>`;
                tabla.appendChild(tr);
            });
        });
}

// ---------- Editar curso ----------
document.getElementById("formEditar").addEventListener("submit", function (e) {
    e.preventDefault();
    if (!idCursoActual) return;
    fetch(`/cursos/editar/${idCursoActual}`, { method: "POST", body: new FormData(this) })
        .then(res => res.json())
        .then(data => {
            alert(data.mensaje);
            if (data.ok) cargarCurso();
        });
});

// ---------- Crear materia ----------
document.getElementById("formMateria").addEventListener("submit", function (e) {
    e.preventDefault();
    if (!idCursoActual) {
        alert("Primero necesitás tener un curso.");
        return;
    }
    const fd = new FormData(this);
    fd.append("id_curso", idCursoActual);
    fetch("/materias/crear", { method: "POST", body: fd })
        .then(res => res.json())
        .then(data => {
            alert(data.mensaje);
            if (data.ok) { this.reset(); cargarMaterias(); }
        });
});

// ---------- Borrar materia ----------
function borrarMateria(id) {
    if (!confirm("¿Eliminar esta materia?")) return;
    fetch(`/materias/eliminar/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            alert(data.mensaje);
            if (data.ok) cargarMaterias();
        });
}

cargarCurso();