(function () {
const $ = id => document.getElementById(id);

const selectCurso     = $("cursoBusqueda");
const inputBusqueda   = $("q");
const selectOrden     = $("orden");
const selectMateria   = $("filtroMateria");
const inputFechaDesde = $("fechaDesde");
const inputFechaHasta = $("fechaHasta");
const btnBuscar       = $("btnBuscar");
const cont            = $("resultadosBusqueda");

if (!btnBuscar || !cont) return;   // esta página no tiene búsqueda

// Fallbacks por si algún helper no cargó (no queremos ReferenceError)
const esc  = (typeof escapeHtml === "function") ? escapeHtml : (s => String(s ?? ""));
const ic   = (typeof L === "function") ? L : (() => "");
const av   = (typeof htmlAvatar === "function") ? htmlAvatar : (() => "");
const IMGS = (typeof EXT_IMG !== "undefined") ? EXT_IMG : ["png","jpg","jpeg","webp","gif"];

function cursoActual() {
    if (selectCurso) return selectCurso.value || "";
    return document.body.dataset.idCurso || "";   // fallback legacy
}

async function cargarMateriasFiltro() {
    if (!selectMateria) return;
    selectMateria.innerHTML = '<option value="">Todas las materias</option>';
    const idCurso = cursoActual();
    if (!idCurso) return;
    try {
        const data = await pedirJSON(`/cursos/${idCurso}/materias`);
        (data.materias || []).forEach(m => {
            const opt = document.createElement("option");
            opt.value = m.id;
            opt.textContent = m.nombre;
            selectMateria.appendChild(opt);
        });
    } catch (err) {
        console.warn("[busqueda] No se pudieron cargar las materias:", err);
    }
}

function tarjeta(a) {
    const primero = (a.archivos || [])[0];
    let mini = "";
    if (primero && IMGS.includes((primero.tipo || "").toLowerCase())) {
        mini = `<img src="/static/${esc(primero.ruta)}" alt=""
                 style="width:60px;height:60px;object-fit:cover;border-radius:10px;flex-shrink:0;">`;
    } else if (primero) {
        mini = `<div style="width:60px;height:60px;display:flex;align-items:center;
                 justify-content:center;background:var(--crema);border-radius:10px;
                 flex-shrink:0;">${ic("paperclip", 28)}</div>`;
    }
    const div = document.createElement("div");
    div.className = "card card-apunte";
    div.innerHTML = `
        <div style="display:flex;gap:12px;align-items:flex-start;">
            ${mini}
            <div style="flex:1;">
                <div class="autor-linea" style="margin-bottom:4px;">
                    ${av(a.autor, a.autor_avatar, "avatar-chico")}
                    <strong>${esc(a.autor || "Anónimo")}</strong>
                    <span class="valoracion-promedio">
                        · ${ic("star", 14)} ${a.promedio} (${a.cant_calificaciones})
                    </span>
                </div>
                <p style="color:var(--celeste-dark);font-weight:700;font-size:13px;
                          margin:4px 0 2px;text-transform:uppercase;">
                    ${esc(a.materia || "Sin materia")}
                </p>
                <h3 style="margin:2px 0;color:var(--tinta);">${esc(a.titulo || "(sin título)")}</h3>
                <p style="color:var(--tinta-soft);margin:2px 0;font-size:13px;">${esc(a.descripcion || "")}</p>
                <a href="/materia/${a.id_materia}#apunte-${a.id}"
                   class="btn btn-celeste btn-chico" style="margin-top:8px;">Ver apunte</a>
            </div>
        </div>`;
    return div;
}

async function hacerBusqueda() {
    cont.innerHTML = '<p class="vacio">Buscando...</p>';

    const params = new URLSearchParams();
    const idCurso = cursoActual();
    if (idCurso) params.set("id_curso", idCurso);
    if (inputBusqueda?.value.trim()) params.set("q", inputBusqueda.value.trim());
    params.set("orden", selectOrden?.value || "recientes");
    if (selectMateria?.value)   params.set("materia_id",  selectMateria.value);
    if (inputFechaDesde?.value) params.set("fecha_desde", inputFechaDesde.value);
    if (inputFechaHasta?.value) params.set("fecha_hasta", inputFechaHasta.value);

    // --- Fase 1: red + HTTP ---
    let data;
    try {
        data = await pedirJSON(`/buscar?${params.toString()}`);
    } catch (err) {
        cont.innerHTML = `<p class="vacio">${esc(err.message)}</p>`;
        reportarError(err, "busqueda:fetch");
        return;
    }

    // --- Fase 2: render (errores acá NO se confunden con red) ---
    try {
        if (!data.ok) {
            cont.innerHTML = `<p class="vacio">${esc(data.mensaje || "No se pudo buscar")}</p>`;
            return;
        }
        const apuntes = data.apuntes || [];
        if (apuntes.length === 0) {
            cont.innerHTML = `<p class="vacio">No se encontraron apuntes con esos filtros. ${ic("search-x", 20)}</p>`;
            return;
        }
        cont.innerHTML = "";
        const frag = document.createDocumentFragment();
        apuntes.forEach(a => frag.appendChild(tarjeta(a)));
        cont.appendChild(frag);
    } catch (err) {
        cont.innerHTML = '<p class="vacio">Error al mostrar los resultados (ver consola).</p>';
        reportarError(err, "busqueda:render");
    }
}

let timer = null;
const buscarDebounce = () => { clearTimeout(timer); timer = setTimeout(hacerBusqueda, 350); };

btnBuscar.addEventListener("click", hacerBusqueda);
inputBusqueda?.addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); hacerBusqueda(); }
});
inputBusqueda?.addEventListener("input", buscarDebounce);
selectCurso?.addEventListener("change", async () => { await cargarMateriasFiltro(); hacerBusqueda(); });
selectOrden?.addEventListener("change", hacerBusqueda);
selectMateria?.addEventListener("change", hacerBusqueda);
inputFechaDesde?.addEventListener("change", hacerBusqueda);
inputFechaHasta?.addEventListener("change", hacerBusqueda);

(async () => { await cargarMateriasFiltro(); hacerBusqueda(); })();
})();