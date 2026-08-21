(function(){
const selectCurso     = document.getElementById("cursoBusqueda");
const inputBusqueda   = document.getElementById("q");
const selectOrden     = document.getElementById("orden");
const selectMateria   = document.getElementById("filtroMateria");
const inputFechaDesde = document.getElementById("fechaDesde");
const inputFechaHasta = document.getElementById("fechaHasta");
const btnBuscar       = document.getElementById("btnBuscar");
const contResultados  = document.getElementById("resultadosBusqueda");

if (!btnBuscar || !selectCurso) return;

function cursoActual() { return selectCurso.value; }

// Las materias dependen del CURSO SELECCIONADO
function cargarMateriasFiltro() {
    const idCurso = cursoActual();
    selectMateria.innerHTML = '<option value="">Todas las materias</option>';
    if (!idCurso) return;
    fetch(`/cursos/${idCurso}/materias`)
        .then(r => r.json())
        .then(data => {
            if (!data.ok || !data.materias) return;
            data.materias.forEach(m => {
                const opt = document.createElement("option");
                opt.value = m.id;
                opt.textContent = m.nombre;
                selectMateria.appendChild(opt);
            });
        });
}

function hacerBusqueda() {
    const idCurso = cursoActual();
    if (!idCurso) {
        contResultados.innerHTML = '<p class="vacio">Elegí un curso primero.</p>';
        return;
    }
    contResultados.innerHTML = '<p class="vacio">Buscando...</p>';

    const params = new URLSearchParams({
        id_curso: idCurso,
        q: (inputBusqueda?.value || "").trim(),
        orden: selectOrden?.value || "recientes",
    });
    if (selectMateria?.value)   params.set("materia_id", selectMateria.value);
    if (inputFechaDesde?.value) params.set("fecha_desde", inputFechaDesde.value);
    if (inputFechaHasta?.value) params.set("fecha_hasta", inputFechaHasta.value);

    fetch(`/buscar?${params.toString()}`)
        .then(r => r.json())
        .then(data => {
            if (!data.ok) {
                contResultados.innerHTML = `<p class="vacio">${escapeHtml(data.mensaje || "No se pudo buscar")}</p>`;
                return;
            }
            if (!data.apuntes || data.apuntes.length === 0) {
                contResultados.innerHTML = '<p class="vacio">No se encontraron apuntes en este curso. ' + L("search-x", 20) + '</p>';
                return;
            }
            contResultados.innerHTML = "";
            data.apuntes.forEach(a => {
                const primero = (a.archivos || [])[0];
                let mini = "";
                if (primero && EXT_IMG.includes((primero.tipo || "").toLowerCase())) {
                    mini = `<img src="/static/${escapeHtml(primero.ruta)}" alt=""
                        style="width:60px;height:60px;object-fit:cover;border-radius:10px;flex-shrink:0;">`;
                } else if (primero) {
                    mini = `<div style="width:60px;height:60px;display:flex;align-items:center;
                        justify-content:center;background:var(--crema);border-radius:10px;
                        flex-shrink:0;">${L("paperclip", 28)}</div>`;
                }

                const div = document.createElement("div");
                div.className = "card card-apunte";
                div.innerHTML = `
                    <div style="display:flex;gap:12px;align-items:flex-start;">
                        ${mini}
                        <div style="flex:1;">
                            <div class="autor-linea" style="margin-bottom:4px;">
                                ${htmlAvatar(a.autor, a.autor_avatar, "avatar-chico")}
                                <strong>${escapeHtml(a.autor || "Anónimo")}</strong>
                                <span class="valoracion-promedio">
                                    · ${L("star", 14)} ${a.promedio} (${a.cant_calificaciones})
                                </span>
                            </div>
                            <p style="color:var(--celeste-dark);font-weight:700;font-size:13px;margin:4px 0 2px;text-transform:uppercase;">
                                ${escapeHtml(a.materia || "Sin materia")}
                            </p>
                            <h3 style="margin:2px 0;color:var(--tinta);">${escapeHtml(a.titulo || "(sin título)")}</h3>
                            <p style="color:var(--tinta-soft);margin:2px 0;font-size:13px;">${escapeHtml(a.descripcion || "")}</p>
                            <a href="/materia/${a.id_materia}#apunte-${a.id}"
                               class="btn btn-celeste btn-chico" style="margin-top:8px;">Ver apunte</a>
                        </div>
                    </div>`;
                contResultados.appendChild(div);
            });
        })
        .catch(() => { contResultados.innerHTML = '<p class="vacio">Error de conexión.</p>'; });
}

btnBuscar.addEventListener("click", hacerBusqueda);
inputBusqueda?.addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); hacerBusqueda(); }
});
selectCurso.addEventListener("change", () => { cargarMateriasFiltro(); hacerBusqueda(); });
selectOrden?.addEventListener("change", hacerBusqueda);
selectMateria?.addEventListener("change", hacerBusqueda);
inputFechaDesde?.addEventListener("change", hacerBusqueda);
inputFechaHasta?.addEventListener("change", hacerBusqueda);

cargarMateriasFiltro();
hacerBusqueda();
})();