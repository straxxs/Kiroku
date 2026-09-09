/**
 * Gamificación — SOLO LECTURA.
 * Este archivo nunca otorga XP: solo consume endpoints GET.
 * Todo el cálculo de puntos vive en el backend (modulos/gamificacion.py).
 */
(function () {
const esc = (typeof escapeHtml === "function") ? escapeHtml : (s => String(s ?? ""));
const av  = (typeof htmlAvatar === "function") ? htmlAvatar : (() => "");

function barraProgreso(p) {
    const nivel = p.nivel || {};
    const sig = p.siguiente_nivel;
    return `
    <div class="xp-panel xp-nivel-${esc(nivel.color || 'gris')}">
        <div class="xp-cabecera">
            <span class="xp-icono">${esc(nivel.icono || '🌱')}</span>
            <div class="xp-titulos">
                <span class="xp-nivel-nombre">${esc(nivel.nombre || '—')}</span>
                <span class="xp-nivel-desc">${esc(nivel.descripcion || '')}</span>
            </div>
            <span class="xp-total">${p.xp_total} <small>XP</small></span>
        </div>
        <div class="xp-barra">
            <div class="xp-barra-fill" style="width:${p.progreso_pct}%"></div>
        </div>
        <div class="xp-pie">
            ${sig
                ? `<span>Faltan <strong>${p.xp_faltante} XP</strong> para ${esc(sig.icono)} ${esc(sig.nombre)}</span>`
                : `<span>¡Nivel máximo alcanzado!</span>`}
            ${p.racha_dias > 0 ? `<span class="xp-racha">🔥 ${p.racha_dias} días</span>` : ''}
        </div>
    </div>`;
}

function tarjetaLogro(l, obtenido) {
    if (obtenido) {
        return `<div class="logro logro-obtenido" title="${esc(l.descripcion)}">
                    <span class="logro-icono">${esc(l.icono)}</span>
                    <span class="logro-nombre">${esc(l.nombre)}</span>
                    <span class="logro-fecha">${esc(l.fecha || '')}</span>
                </div>`;
    }
    return `<div class="logro logro-pendiente" title="${esc(l.descripcion)}">
                <span class="logro-icono">${esc(l.icono)}</span>
                <span class="logro-nombre">${esc(l.nombre)}</span>
                <div class="logro-progreso">
                    <div class="logro-progreso-fill" style="width:${l.progreso}%"></div>
                </div>
                <span class="logro-contador">${l.actual}/${l.objetivo}</span>
            </div>`;
}

async function cargarProgreso() {
    const cont = document.getElementById("gamificacionPanel");
    if (!cont) return;
    try {
        const data = await pedirJSON("/gamificacion/mi-progreso");
        const p = data.progreso || {};
        const obt = p.logros_obtenidos || [];
        const pen = p.logros_pendientes || [];

        cont.innerHTML = `
            ${barraProgreso(p)}
            <div class="xp-stats">
                <div class="xp-stat"><strong>${p.xp_ganado}</strong><span>Ganado</span></div>
                <div class="xp-stat"><strong>${p.xp_perdido}</strong><span>Perdido</span></div>
                <div class="xp-stat"><strong>${obt.length}/${p.total_logros}</strong><span>Logros</span></div>
                <div class="xp-stat"><strong>${p.racha_maxima}</strong><span>Mejor racha</span></div>
            </div>
            <h3 class="logros-titulo">Logros desbloqueados</h3>
            <div class="logros-grid">
                ${obt.length ? obt.map(l => tarjetaLogro(l, true)).join("")
                             : '<p class="vacio">Todavía no desbloqueaste ninguno. ¡Subí un apunte!</p>'}
            </div>
            ${pen.length ? `
                <h3 class="logros-titulo">En progreso</h3>
                <div class="logros-grid">${pen.map(l => tarjetaLogro(l, false)).join("")}</div>` : ''}
        `;

        // Notificar logros nuevos
        const nuevos = obt.filter(l => !l.visto);
        if (nuevos.length) {
            nuevos.forEach((l, i) => setTimeout(() => {
                mostrarToast(`🏆 ¡Logro desbloqueado! ${l.icono} ${l.nombre}`, "ok");
                if (typeof sonidoExito === "function") sonidoExito();
            }, i * 900));
            pedirJSON("/gamificacion/logros-vistos", { method: "POST" }).catch(() => {});
        }
    } catch (err) {
        cont.innerHTML = `<p class="vacio">${esc(err.message)}</p>`;
        reportarError(err, "gamificacion:progreso");
    }
}

async function cargarRanking(idCurso) {
    const cont = document.getElementById("rankingXP");
    if (!cont) return;
    cont.innerHTML = '<p class="vacio">Cargando ranking...</p>';
    try {
        const url = idCurso ? `/gamificacion/ranking?id_curso=${idCurso}` : "/gamificacion/ranking";
        const data = await pedirJSON(url);
        const r = data.ranking || [];
        if (!r.length) { cont.innerHTML = '<p class="vacio">Sin datos todavía.</p>'; return; }

        const medalla = n => n === 1 ? "🥇" : n === 2 ? "🥈" : n === 3 ? "🥉" : `#${n}`;
        cont.innerHTML = `<ol class="ranking-lista">${r.map(u => `
            <li class="ranking-item ${u.puesto <= 3 ? 'ranking-podio' : ''}">
                <span class="ranking-puesto">${medalla(u.puesto)}</span>
                ${av(u.nombre, u.avatar, "avatar-chico")}
                <span class="ranking-nombre">${esc(u.nombre)}</span>
                <span class="ranking-nivel">${esc(u.nivel_icono || '')}</span>
                <span class="ranking-xp">${u.xp} XP</span>
            </li>`).join("")}</ol>`;
    } catch (err) {
        cont.innerHTML = `<p class="vacio">${esc(err.message)}</p>`;
        reportarError(err, "gamificacion:ranking");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    cargarProgreso();
    const cont = document.getElementById("rankingXP");
    if (cont) cargarRanking(cont.dataset.curso || null);
});

window.cargarRankingXP = cargarRanking;
})();