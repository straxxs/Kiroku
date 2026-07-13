(function(){
// ---------- Motor de búsqueda (home) con filtros avanzados ----------
const inputBusqueda = document.getElementById("q");
const selectOrden = document.getElementById("orden");
const selectMateria = document.getElementById("filtroMateria");
const inputFechaDesde = document.getElementById("fechaDesde");
const inputFechaHasta = document.getElementById("fechaHasta");
const btnBuscar = document.getElementById("btnBuscar");
const contResultados = document.getElementById("resultadosBusqueda");

const EXT_IMG_B = ["png", "jpg", "jpeg", "webp", "gif"];
const IC={'search':'<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>','paperclip':'<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>','star':'<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>','search-x':'<path d="m13.5 8.5-5 5"/><path d="m8.5 8.5 5 5"/><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>'};
function L(n,s){s=s||16;return `<svg class="luc" xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${IC[n]}</svg>`}

// Cargar materias del curso para el filtro
function cargarMateriasFiltro() {
    const body = document.body;
    const idCurso = body?.dataset?.idCurso;
    if (!idCurso || !selectMateria) return;

    fetch(`/cursos/${idCurso}/materias`)
        .then(res => res.json())
        .then(data => {
            selectMateria.innerHTML = '<option value="">Todas las materias</option>';
            if (data.materias) {
                data.materias.forEach(m => {
                    const opt = document.createElement("option");
                    opt.value = m.id;
                    opt.textContent = m.nombre;
                    selectMateria.appendChild(opt);
                });
            }
        });
}

function hacerBusqueda() {
    if (!contResultados) return;
    const q = (inputBusqueda?.value || "").trim();
    const orden = selectOrden?.value || "recientes";
    const materiaId = selectMateria?.value || "";
    const fechaDesde = inputFechaDesde?.value || "";
    const fechaHasta = inputFechaHasta?.value || "";

    contResultados.innerHTML = '<p class="vacio">Buscando...</p>';

    const params = new URLSearchParams({ q, orden });
    if (materiaId) params.set("materia_id", materiaId);
    if (fechaDesde) params.set("fecha_desde", fechaDesde);
    if (fechaHasta) params.set("fecha_hasta", fechaHasta);

    fetch(`/buscar?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
            if (!data.ok) {
                contResultados.innerHTML = `<p class="vacio">${data.mensaje || "No se pudo buscar"}</p>`;
                return;
            }
            if (!data.apuntes || data.apuntes.length === 0) {
                contResultados.innerHTML = '<p class="vacio">No se encontraron apuntes. '+L("search-x",20)+'</p>';
                return;
            }

            contResultados.innerHTML = "";
            data.apuntes.forEach(a => {
                const primerArchivo = (a.archivos || [])[0];
                let miniatura = "";
                if (primerArchivo && EXT_IMG_B.includes((primerArchivo.tipo || "").toLowerCase())) {
                    miniatura = `<img src="/static/${primerArchivo.ruta}" alt=""
                        style="width:60px;height:60px;object-fit:cover;border-radius:10px;flex-shrink:0;">`;
                } else if (primerArchivo) {
                    miniatura = `<div style="width:60px;height:60px;display:flex;align-items:center;
                        justify-content:center;background:var(--crema);border-radius:10px;
                        flex-shrink:0;">${L("paperclip",28)}</div>`;
                }

                const div = document.createElement("div");
                div.className = "card card-apunte";
                div.innerHTML = `
                    <div style="display:flex;gap:12px;align-items:flex-start;">
                        ${miniatura}
                        <div style="flex:1;">
                            <div class="autor-linea" style="margin-bottom:4px;">
                                ${htmlAvatar(a.autor, a.autor_avatar, "avatar-chico")}
                                <strong>${escapeHtml(a.autor || "Anónimo")}</strong>
                                <span class="valoracion-promedio">
                                    · ${L("star",14)} ${a.promedio} (${a.cant_calificaciones})
                                </span>
                            </div>
                            <p style="color:var(--celeste-dark);font-weight:700;font-size:13px;margin:4px 0 2px;text-transform:uppercase;letter-spacing:0.03em;">
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
        .catch(() => {
            contResultados.innerHTML = '<p class="vacio">Error de conexión.</p>';
        });
}

if (btnBuscar) {
    btnBuscar.addEventListener("click", hacerBusqueda);
    inputBusqueda?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") { e.preventDefault(); hacerBusqueda(); }
    });
    selectOrden?.addEventListener("change", hacerBusqueda);
    selectMateria?.addEventListener("change", hacerBusqueda);
    inputFechaDesde?.addEventListener("change", hacerBusqueda);
    inputFechaHasta?.addEventListener("change", hacerBusqueda);

    cargarMateriasFiltro();
    hacerBusqueda();
}
})();
