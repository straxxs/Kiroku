/**
 * Calendario académico — vanilla JS, sin librerías externas.
 *
 * Monta 3 componentes según los elementos presentes en la página:
 *   #calGrid          -> vista mes
 *   #listaEventos     -> vista lista
 *   #proximosEventos  -> widget de inicio (home.html)
 *
 * Los permisos (editable/eliminable) los define el BACKEND: acá solo
 * se respetan los flags que vienen en el JSON.
 */
(function () {

// ---------- Fallbacks defensivos ----------
async function api(url, o = {}) {
    if (typeof window.pedirJSON === "function") return window.pedirJSON(url, o);
    const r = await fetch(url, { credentials: "same-origin", ...o });
    const t = await r.text();
    let d; try { d = t ? JSON.parse(t) : null; }
    catch { throw new Error(`Error ${r.status} del servidor.`); }
    if (!r.ok) throw new Error((d && d.mensaje) || `Error ${r.status}`);
    return d;
}
function avisar(e, ctx) {
    if (typeof window.reportarError === "function") return window.reportarError(e, ctx);
    console.error(`[${ctx}]`, e);
    if (typeof mostrarToast === "function") mostrarToast(e.message, "error");
}
const esc = s => (typeof escapeHtml === "function") ? escapeHtml(s)
    : String(s ?? "").replace(/[&<>"']/g, c =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// ---------- Constantes ----------
const MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
               "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
const ICONO_TIPO = { examen:"📝", entrega:"📤", tarea:"✏️", reunion:"👥", otro:"📌" };
const NOMBRE_TIPO = { examen:"Examen", entrega:"Entrega", tarea:"Tarea",
                      reunion:"Reunión", otro:"Otro" };

// Fechas SIEMPRE como string 'YYYY-MM-DD' → cero problemas de timezone
const ymd = (y, m, d) =>
    `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
const hoyStr = () => { const h = new Date(); return ymd(h.getFullYear(), h.getMonth(), h.getDate()); };

function fechaLegible(f) {
    const [y, m, d] = f.split("-").map(Number);
    return `${d} de ${MESES[m - 1]} de ${y}`;
}

// ---------- Estado ----------
let anio = new Date().getFullYear();
let mes  = new Date().getMonth();     // 0-indexed
let eventos = [];
let vista = "mes";

const $ = id => document.getElementById(id);


// ============================================================
// CARGA
// ============================================================

function filtrosActuales() {
    const p = new URLSearchParams();
    const c = $("filtroCurso")?.value;
    const m = $("filtroMateria")?.value;
    const t = $("filtroTipo")?.value;
    if (c) p.set("id_curso", c);
    if (m) p.set("id_materia", m);
    if (t) p.set("tipo", t);
    if ($("filtroPendientes")?.checked) p.set("ocultar_completados", "1");
    return p;
}

async function cargarEventos() {
    const p = filtrosActuales();
    // Rango: mes visible ± 1 (cubre las celdas de relleno)
    p.set("desde", ymd(anio, mes - 1, 1));
    const fin = new Date(anio, mes + 2, 0);
    p.set("hasta", ymd(fin.getFullYear(), fin.getMonth(), fin.getDate()));

    try {
        const data = await api(`/calendario/eventos?${p.toString()}`);
        eventos = data.eventos || [];
        render();
    } catch (err) {
        eventos = [];
        const cont = $("calGrid") || $("listaEventos");
        if (cont) avisar(err, "calendario:cargar");
        render();
    }
}

async function cargarMateriasFiltro() {
    const sel = $("filtroMateria");
    if (!sel) return;
    sel.innerHTML = '<option value="">Todas</option>';
    const idCurso = $("filtroCurso")?.value;
    if (!idCurso) return;
    try {
        const d = await api(`/cursos/${idCurso}/materias`);
        (d.materias || []).forEach(m => {
            const o = document.createElement("option");
            o.value = m.id; o.textContent = m.nombre;
            sel.appendChild(o);
        });
    } catch (e) { console.warn("[calendario] materias:", e); }
}


// ============================================================
// RENDER · VISTA MES
// ============================================================

function renderMes() {
    const grid = $("calGrid");
    if (!grid) return;

    $("mesTitulo").textContent = `${MESES[mes]} ${anio}`;

    // Limpiar todo menos los encabezados de día
    grid.querySelectorAll(".cal-celda").forEach(e => e.remove());

    const primero = new Date(anio, mes, 1);
    const offset = (primero.getDay() + 6) % 7;      // semana arranca lunes
    const diasMes = new Date(anio, mes + 1, 0).getDate();
    const diasMesAnt = new Date(anio, mes, 0).getDate();
    const hoy = hoyStr();

    // Agrupar eventos por fecha
    const porFecha = {};
    eventos.forEach(e => (porFecha[e.fecha] = porFecha[e.fecha] || []).push(e));

    const frag = document.createDocumentFragment();

    const celda = (num, fecha, fuera) => {
        const evs = porFecha[fecha] || [];
        const div = document.createElement("div");
        div.className = "cal-celda" + (fuera ? " cal-fuera" : "") +
                        (fecha === hoy ? " cal-hoy" : "") +
                        (evs.length ? " cal-con-eventos" : "");
        div.dataset.fecha = fecha;

        let puntos = evs.slice(0, 4)
            .map(e => `<i class="cal-punto est-${esc(e.estado)}" title="${esc(e.titulo)}"></i>`)
            .join("");
        if (evs.length > 4) puntos += `<span class="cal-mas">+${evs.length - 4}</span>`;

        div.innerHTML = `<span class="cal-num">${num}</span>
                         <div class="cal-puntos">${puntos}</div>`;
        return div;
    };

    for (let i = offset; i > 0; i--)
        frag.appendChild(celda(diasMesAnt - i + 1, ymd(anio, mes - 1, diasMesAnt - i + 1), true));
    for (let d = 1; d <= diasMes; d++)
        frag.appendChild(celda(d, ymd(anio, mes, d), false));
    const resto = (7 - ((offset + diasMes) % 7)) % 7;
    for (let d = 1; d <= resto; d++)
        frag.appendChild(celda(d, ymd(anio, mes + 1, d), true));

    grid.appendChild(frag);
}

function mostrarDia(fecha) {
    const cont = $("detalleDia");
    if (!cont) return;
    const evs = eventos.filter(e => e.fecha === fecha);

    cont.hidden = false;
    cont.innerHTML = `
        <div class="cal-detalle-head">
            <h3>${esc(fechaLegible(fecha))}</h3>
            <button class="btn btn-amarillo btn-chico"
                    data-accion="nuevo-en-fecha" data-fecha="${fecha}">+ Agregar</button>
        </div>
        ${evs.length
            ? `<div class="cal-eventos">${evs.map(tarjeta).join("")}</div>`
            : '<p class="vacio">Sin eventos este día.</p>'}`;

    document.querySelectorAll(".cal-celda.seleccionada")
        .forEach(c => c.classList.remove("seleccionada"));
    document.querySelector(`.cal-celda[data-fecha="${fecha}"]`)
        ?.classList.add("seleccionada");
}


// ============================================================
// RENDER · TARJETA DE EVENTO (compartida)
// ============================================================

function tarjeta(e, compacta = false) {
    const meta = [
        e.hora ? `🕐 ${esc(e.hora)}` : "",
        e.materia_nombre ? esc(e.materia_nombre) : "",
        e.curso_nombre ? esc(e.curso_nombre) : "",
        e.ambito === "personal" ? "🔒 Personal" : "",
        e.ambito === "proyecto" ? "🧩 Proyecto" : "",
    ].filter(Boolean).join(" · ");

    const acciones = [];
    // El origen externo se edita en su propia pantalla
    if (e.url_origen) {
        acciones.push(`<a href="${esc(e.url_origen)}" class="btn btn-violeta btn-chico">Ver origen</a>`);
    }
    if (e.editable) {
        acciones.push(`<button class="btn btn-amarillo btn-chico"
            data-accion="editar-evento" data-id="${e.id_real}">Editar</button>`);
    }
    if (e.eliminable) {
        acciones.push(`<button class="btn btn-rojo btn-chico"
            data-accion="borrar-evento" data-id="${e.id_real}">Eliminar</button>`);
    }

    return `
    <div class="cal-evento est-borde-${esc(e.estado)} ${e.completado ? "ev-completado" : ""}"
         data-id="${esc(e.id)}">
        <button class="ev-check" data-accion="completar"
                data-origen="${esc(e.origen)}" data-oid="${e.id_real}"
                title="${e.completado ? "Marcar como pendiente" : "Marcar como hecho"}">
            ${e.completado ? "✅" : "⬜"}
        </button>
        <div class="ev-cuerpo">
            <div class="ev-head">
                <span class="ev-tipo">${ICONO_TIPO[e.tipo] || "📌"}</span>
                <strong class="ev-titulo">${esc(e.titulo)}</strong>
                <span class="badge-estado est-${esc(e.estado)}">${esc(e.estado)}</span>
            </div>
            ${meta ? `<div class="ev-meta">${meta}</div>` : ""}
            ${(!compacta && e.descripcion)
                ? `<p class="ev-desc">${esc(e.descripcion)}</p>` : ""}
            ${acciones.length ? `<div class="ev-acciones">${acciones.join("")}</div>` : ""}
        </div>
    </div>`;
}


// ============================================================
// RENDER · VISTA LISTA
// ============================================================

function renderLista() {
    const cont = $("listaEventos");
    if (!cont) return;
    if (!eventos.length) {
        cont.innerHTML = '<p class="vacio">No hay eventos con esos filtros.</p>';
        return;
    }
    // Agrupar por fecha, con encabezado por día
    const grupos = {};
    eventos.forEach(e => (grupos[e.fecha] = grupos[e.fecha] || []).push(e));
    const hoy = hoyStr();

    cont.innerHTML = Object.keys(grupos).sort().map(f => `
        <div class="cal-grupo">
            <h4 class="cal-grupo-fecha ${f === hoy ? "es-hoy" : ""}">
                ${esc(fechaLegible(f))}${f === hoy ? " · HOY" : ""}
            </h4>
            <div class="cal-eventos">${grupos[f].map(e => tarjeta(e)).join("")}</div>
        </div>`).join("");
}


// ============================================================
// WIDGET · PRÓXIMOS EVENTOS (inicio)
// ============================================================

async function cargarProximos() {
    const cont = $("proximosEventos");
    if (!cont) return;
    try {
        const d = await api("/calendario/proximos?limite=5");
        const evs = d.eventos || [];
        cont.innerHTML = evs.length
            ? `<div class="cal-eventos">${evs.map(e => tarjeta(e, true)).join("")}</div>
               <a href="/calendario" class="btn btn-celeste btn-chico"
                  style="margin-top:10px;">Ver calendario completo</a>`
            : `<p class="vacio">No tenés eventos próximos. 🎉
                 <a href="/calendario" class="btn btn-celeste btn-chico"
                    style="margin-left:8px;">Agregar uno</a></p>`;
    } catch (err) {
        cont.innerHTML = `<p class="vacio">${esc(err.message)}</p>`;
    }
}


function render() {
    if (vista === "mes") renderMes(); else renderLista();
}


// ============================================================
// MODAL DE EVENTO (crear / editar)
// ============================================================

function abrirModal(evento = null, fechaPre = null) {
    const editando = !!evento;
    let ov = $("modalEvento");
    if (!ov) {
        ov = document.createElement("div");
        ov.id = "modalEvento";
        ov.className = "kiroku-modal-overlay";
        document.body.appendChild(ov);
        ov.addEventListener("click", e => { if (e.target === ov) cerrarModal(); });
    }

    const cursosSel = Array.from($("filtroCurso")?.options || [])
        .filter(o => o.value)
        .map(o => `<option value="${o.value}" data-rol="${o.dataset.rol || ""}"
                     ${evento && String(evento.id_curso) === o.value ? "selected" : ""}>
                     ${esc(o.textContent.trim())}</option>`).join("");

    const tipoSel = Object.keys(NOMBRE_TIPO).map(t =>
        `<option value="${t}" ${evento?.tipo === t ? "selected" : ""}>
            ${ICONO_TIPO[t]} ${NOMBRE_TIPO[t]}</option>`).join("");

    ov.innerHTML = `
    <div class="kiroku-modal kiroku-modal-ancho">
        <div class="kiroku-modal-icon">📅</div>
        <h3>${editando ? "Editar evento" : "Nuevo evento"}</h3>
        <form id="formEvento" class="cal-form">
            <div class="campo">
                <label for="evTitulo">Título *</label>
                <input type="text" id="evTitulo" maxlength="120" required
                       value="${esc(evento?.titulo || "")}"
                       placeholder="Ej: Parcial de Matemática">
            </div>
            <div class="form-row">
                <div class="campo">
                    <label for="evTipo">Tipo</label>
                    <select id="evTipo">${tipoSel}</select>
                </div>
                <div class="campo">
                    <label for="evAmbito">Visibilidad</label>
                    <select id="evAmbito">
                        <option value="personal" ${evento?.ambito !== "curso" ? "selected" : ""}>
                            🔒 Solo para mí</option>
                        <option value="curso" ${evento?.ambito === "curso" ? "selected" : ""}>
                            👥 Todo el curso</option>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="campo">
                    <label for="evFecha">Fecha *</label>
                    <input type="date" id="evFecha" required
                           value="${esc(evento?.fecha || fechaPre || hoyStr())}">
                </div>
                <div class="campo">
                    <label for="evHora">Hora límite</label>
                    <input type="time" id="evHora" value="${esc(evento?.hora || "")}">
                </div>
            </div>
            <div class="form-row">
                <div class="campo">
                    <label for="evCurso">Curso</label>
                    <select id="evCurso">
                        <option value="">— Sin curso —</option>
                        ${cursosSel}
                    </select>
                </div>
                <div class="campo">
                    <label for="evMateria">Materia</label>
                    <select id="evMateria"><option value="">— Sin materia —</option></select>
                </div>
            </div>
            <div class="campo">
                <label for="evDesc">Descripción</label>
                <textarea id="evDesc" rows="3" maxlength="500"
                          placeholder="Detalles (opcional)">${esc(evento?.descripcion || "")}</textarea>
                <small class="campo-hint" id="evDescCont">0/500</small>
            </div>
            <p class="cal-aviso" id="evAviso" hidden>
                ⚠️ Para publicar en todo el curso necesitás ser moderador de ese curso.
            </p>
            <div class="kiroku-modal-acciones">
                <button type="submit" class="btn btn-amarillo">
                    ${editando ? "Guardar" : "Crear evento"}
                </button>
                <button type="button" class="btn btn-gris" id="evCancelar">Cancelar</button>
            </div>
        </form>
    </div>`;

    requestAnimationFrame(() => ov.classList.add("visible"));

    const selCurso  = $("evCurso");
    const selMat    = $("evMateria");
    const selAmbito = $("evAmbito");
    const aviso     = $("evAviso");
    const desc      = $("evDesc");

    function contarDesc() { $("evDescCont").textContent = `${desc.value.length}/500`; }
    desc.addEventListener("input", contarDesc);
    contarDesc();

    async function cargarMaterias(preSel) {
        selMat.innerHTML = '<option value="">— Sin materia —</option>';
        if (!selCurso.value) return;
        try {
            const d = await api(`/cursos/${selCurso.value}/materias`);
            (d.materias || []).forEach(m => {
                const o = document.createElement("option");
                o.value = m.id; o.textContent = m.nombre;
                if (String(preSel) === String(m.id)) o.selected = true;
                selMat.appendChild(o);
            });
        } catch (e) { console.warn(e); }
    }

    // Aviso si elige "todo el curso" sin ser moderador de ese curso
    function revisarPermiso() {
        const opt = selCurso.selectedOptions[0];
        const esMod = opt && opt.dataset.rol === "moderador";
        const quiereCurso = selAmbito.value === "curso";
        aviso.hidden = !(quiereCurso && selCurso.value && !esMod);
        if (quiereCurso && !selCurso.value) {
            aviso.hidden = false;
            aviso.textContent = "⚠️ Elegí el curso donde querés publicar el evento.";
        } else if (!aviso.hidden) {
            aviso.textContent = "⚠️ Para publicar en todo el curso necesitás ser " +
                                "moderador de ese curso.";
        }
    }

    selCurso.addEventListener("change", () => { cargarMaterias(null); revisarPermiso(); });
    selAmbito.addEventListener("change", revisarPermiso);
    cargarMaterias(evento?.id_materia);
    revisarPermiso();

    $("evCancelar").onclick = cerrarModal;

    $("formEvento").addEventListener("submit", async ev => {
        ev.preventDefault();
        const fd = new FormData();
        fd.append("titulo", $("evTitulo").value.trim());
        fd.append("fecha", $("evFecha").value);
        fd.append("hora", $("evHora").value);
        fd.append("tipo", $("evTipo").value);
        fd.append("ambito", selAmbito.value);
        fd.append("descripcion", desc.value.trim());
        if (selCurso.value) fd.append("id_curso", selCurso.value);
        if (selMat.value)   fd.append("id_materia", selMat.value);

        const url = editando
            ? `/calendario/eventos/${evento.id_real}/editar`
            : "/calendario/eventos/crear";
        const btn = ev.target.querySelector('button[type="submit"]');
        btn.disabled = true;
        try {
            const d = await api(url, { method: "POST", body: fd });
            mostrarToast(d.mensaje, "ok");
            if (typeof sonidoPop === "function") sonidoPop();
            cerrarModal();
            await cargarEventos();
            cargarProximos();
        } catch (err) {
            avisar(err, "calendario:guardar");
        } finally {
            btn.disabled = false;
        }
    });

    setTimeout(() => $("evTitulo").focus(), 120);
}

function cerrarModal() {
    $("modalEvento")?.classList.remove("visible");
}


// ============================================================
// EVENTOS DE UI (delegación)
// ============================================================

document.addEventListener("click", async e => {

    // Celda del mes → detalle del día
    const celda = e.target.closest(".cal-celda");
    if (celda) { mostrarDia(celda.dataset.fecha); return; }

    if (e.target.closest("#btnNuevoEvento")) { abrirModal(); return; }

    const nuevoEn = e.target.closest('[data-accion="nuevo-en-fecha"]');
    if (nuevoEn) { abrirModal(null, nuevoEn.dataset.fecha); return; }

    // Completar / descompletar
    const chk = e.target.closest('[data-accion="completar"]');
    if (chk) {
        const { origen, oid } = chk.dataset;
        try {
            const d = await api(`/calendario/eventos/${origen}/${oid}/completar`,
                                { method: "POST" });
            mostrarToast(d.mensaje, "ok");
            if (typeof sonidoPop === "function") sonidoPop();
            await cargarEventos();
            const sel = document.querySelector(".cal-celda.seleccionada");
            if (sel) mostrarDia(sel.dataset.fecha);
            cargarProximos();
        } catch (err) { avisar(err, "calendario:completar"); }
        return;
    }

    // Editar
    const edit = e.target.closest('[data-accion="editar-evento"]');
    if (edit) {
        const ev = eventos.find(x => x.origen === "manual" &&
                                     String(x.id_real) === edit.dataset.id);
        if (ev) abrirModal(ev);
        return;
    }

    // Eliminar
    const del = e.target.closest('[data-accion="borrar-evento"]');
    if (del) {
        const ok = await kirokuConfirm(
            (typeof L === "function" ? L("trash-2", 20) : "🗑️"),
            "Eliminar evento", "¿Seguro que querés eliminar este evento?",
            "Eliminar", "Cancelar");
        if (!ok) return;
        try {
            const d = await api(`/calendario/eventos/${del.dataset.id}/eliminar`,
                                { method: "POST" });
            mostrarToast(d.mensaje, "ok");
            await cargarEventos();
            const sel = document.querySelector(".cal-celda.seleccionada");
            if (sel) mostrarDia(sel.dataset.fecha);
            cargarProximos();
        } catch (err) { avisar(err, "calendario:eliminar"); }
        return;
    }

    // Navegación de mes
    if (e.target.closest("#mesAnterior")) {
        mes--; if (mes < 0) { mes = 11; anio--; }
        $("detalleDia") && ($("detalleDia").hidden = true);
        cargarEventos(); return;
    }
    if (e.target.closest("#mesSiguiente")) {
        mes++; if (mes > 11) { mes = 0; anio++; }
        $("detalleDia") && ($("detalleDia").hidden = true);
        cargarEventos(); return;
    }
    if (e.target.closest("#irHoy")) {
        const h = new Date();
        anio = h.getFullYear(); mes = h.getMonth();
        await cargarEventos();
        mostrarDia(hoyStr()); return;
    }

    // Cambio de vista
    const vb = e.target.closest(".cal-vista-btn");
    if (vb) {
        vista = vb.dataset.vista;
        document.querySelectorAll(".cal-vista-btn").forEach(b => {
            const act = b === vb;
            b.classList.toggle("activa", act);
            b.classList.toggle("btn-celeste", act);
            b.classList.toggle("btn-gris", !act);
        });
        $("vistaMes").hidden = vista !== "mes";
        $("vistaLista").hidden = vista !== "lista";
        render();
    }
});

// Filtros
["filtroCurso", "filtroMateria", "filtroTipo", "filtroPendientes"].forEach(id => {
    document.addEventListener("change", e => {
        if (e.target.id !== id) return;
        if (id === "filtroCurso") cargarMateriasFiltro();
        cargarEventos();
    });
});

// Teclado: ← → mes, Esc cierra modal
document.addEventListener("keydown", e => {
    if (e.key === "Escape") cerrarModal();
    if (!$("calGrid") || vista !== "mes") return;
    if (document.activeElement.tagName.match(/INPUT|TEXTAREA|SELECT/)) return;
    if (e.key === "ArrowLeft")  $("mesAnterior")?.click();
    if (e.key === "ArrowRight") $("mesSiguiente")?.click();
});


// ============================================================
// ARRANQUE
// ============================================================

function iniciar() {
    // En móvil arrancar en lista (el grid es incómodo en pantallas chicas)
    if (window.innerWidth < 560 && $("vistaLista")) {
        document.querySelector('.cal-vista-btn[data-vista="lista"]')?.click();
    }
    if ($("calGrid") || $("listaEventos")) {
        cargarMateriasFiltro();
        cargarEventos().then(() => { if (vista === "mes") mostrarDia(hoyStr()); });
    }
    cargarProximos();
}

if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", iniciar);
else iniciar();

window.recargarCalendario = cargarEventos;
})();