/**
 * Comentarios en apuntes — carga bajo demanda + delegación de eventos.
 * Requiere: api.js, toast.js, avatar.js, icons.js, modal.js
 */
(function () {
const MAX = 500;
const esc = (typeof escapeHtml === "function") ? escapeHtml : (s => String(s ?? ""));
const av  = (typeof htmlAvatar === "function") ? htmlAvatar : (() => "");

/** Escapa y preserva saltos de línea. */
function textoSeguro(txt) {
    return esc(txt).replace(/\n/g, "<br>");
}

function formatearFecha(iso) {
    if (!iso) return "";
    const d = new Date(iso.replace(" ", "T"));
    if (isNaN(d)) return esc(iso);
    const ahora = new Date();
    const seg = Math.floor((ahora - d) / 1000);
    if (seg < 60)    return "hace un momento";
    if (seg < 3600)  return `hace ${Math.floor(seg / 60)} min`;
    if (seg < 86400) return `hace ${Math.floor(seg / 3600)} h`;
    if (seg < 604800) return `hace ${Math.floor(seg / 86400)} d`;
    const MESES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
    return `${d.getDate()} ${MESES[d.getMonth()]} ${d.getFullYear()}, ` +
           `${String(d.getHours()).padStart(2,"0")}:${String(d.getMinutes()).padStart(2,"0")}`;
}

function htmlComentario(c) {
    if (c.estado === "eliminado") {
        return `<div class="comentario comentario-eliminado" data-id="${c.id}">
                    <span class="comentario-tombstone">
                        🗑️ Comentario eliminado
                        ${c.eliminado_por_nombre ? `por ${esc(c.eliminado_por_nombre)}` : ""}
                    </span>
                </div>`;
    }
    const btnBorrar = c.puede_eliminar
        ? `<button class="comentario-borrar" data-accion="borrar-comentario"
                   data-id="${c.id}" title="Eliminar comentario">✕</button>`
        : "";
    const badgeReportes = (c.reportes > 0)
        ? `<span class="comentario-reportes" title="Reportes pendientes">⚑ ${c.reportes}</span>` : "";

    return `
        <div class="comentario ${c.es_mio ? 'comentario-mio' : ''}" data-id="${c.id}">
            ${av(c.autor, c.autor_avatar, "avatar-chico")}
            <div class="comentario-cuerpo">
                <div class="comentario-head">
                    <strong class="comentario-autor">${esc(c.autor || "Anónimo")}</strong>
                    ${c.es_mio ? '<span class="comentario-vos">vos</span>' : ''}
                    <span class="comentario-fecha">${formatearFecha(c.fecha_creacion)}</span>
                    ${badgeReportes}
                    ${btnBorrar}
                </div>
                <p class="comentario-texto">${textoSeguro(c.contenido)}</p>
            </div>
        </div>`;
}

/** HTML del bloque completo (lo inserta apuntes.js en cada card). */
function bloqueComentarios(idApunte, cantidad) {
    return `
    <div class="comentarios-bloque" data-apunte="${idApunte}">
        <button class="btn-comentarios" data-accion="toggle-comentarios" data-apunte="${idApunte}">
            💬 <span class="com-label">Comentarios</span>
            <span class="com-count">${cantidad || 0}</span>
        </button>
        <div class="comentarios-panel" hidden>
            <div class="comentarios-lista"><p class="vacio">Cargando...</p></div>
            <form class="comentario-form" data-apunte="${idApunte}">
                <textarea class="comentario-input" maxlength="${MAX}" rows="2"
                          placeholder="Escribí un comentario..." required></textarea>
                <div class="comentario-form-pie">
                    <span class="comentario-contador">0/${MAX}</span>
                    <button type="submit" class="btn btn-celeste btn-chico">Comentar</button>
                </div>
            </form>
        </div>
    </div>`;
}

async function cargarComentarios(idApunte, panel) {
    const lista = panel.querySelector(".comentarios-lista");
    lista.innerHTML = '<p class="vacio">Cargando...</p>';
    try {
        const data = await pedirJSON(`/apuntes/${idApunte}/comentarios`);
        const cs = data.comentarios || [];
        const visibles = cs.filter(c => c.estado === "activo" || data.es_moderador);
        lista.innerHTML = visibles.length
            ? visibles.map(htmlComentario).join("")
            : '<p class="vacio">Todavía no hay comentarios. ¡Sé el primero!</p>';
        actualizarContador(idApunte, data.total);
    } catch (err) {
        lista.innerHTML = `<p class="vacio">${esc(err.message)}</p>`;
        reportarError(err, "comentarios:cargar");
    }
}

function actualizarContador(idApunte, total) {
    const bloque = document.querySelector(`.comentarios-bloque[data-apunte="${idApunte}"]`);
    const span = bloque?.querySelector(".com-count");
    if (span && total !== undefined) span.textContent = total;
}

// ---------- Delegación de eventos (funciona con apuntes cargados por AJAX) ----------

document.addEventListener("click", async function (e) {
    // Abrir / cerrar panel
    const toggle = e.target.closest('[data-accion="toggle-comentarios"]');
    if (toggle) {
        const idApunte = toggle.dataset.apunte;
        const panel = toggle.parentElement.querySelector(".comentarios-panel");
        const abierto = !panel.hidden;
        panel.hidden = abierto;
        toggle.classList.toggle("abierto", !abierto);
        if (!abierto && !panel.dataset.cargado) {
            panel.dataset.cargado = "1";
            await cargarComentarios(idApunte, panel);
        }
        return;
    }

    // Eliminar comentario
    const borrar = e.target.closest('[data-accion="borrar-comentario"]');
    if (borrar) {
        const id = borrar.dataset.id;
        const bloque = borrar.closest(".comentarios-bloque");
        const idApunte = bloque?.dataset.apunte;
        const ok = await kirokuConfirm(
            (typeof L === "function" ? L("trash-2", 20) : "🗑️"),
            "Eliminar comentario",
            "¿Seguro que querés eliminar este comentario?",
            "Eliminar", "Cancelar");
        if (!ok) return;
        try {
            const data = await pedirJSON(`/comentarios/${id}/eliminar`, { method: "POST" });
            mostrarToast(data.mensaje, "ok");
            const panel = bloque.querySelector(".comentarios-panel");
            await cargarComentarios(idApunte, panel);
        } catch (err) {
            reportarError(err, "comentarios:eliminar");
        }
    }
});

// Contador de caracteres
document.addEventListener("input", function (e) {
    const ta = e.target.closest(".comentario-input");
    if (!ta) return;
    const cont = ta.parentElement.querySelector(".comentario-contador");
    if (cont) {
        const n = ta.value.length;
        cont.textContent = `${n}/${MAX}`;
        cont.classList.toggle("cerca-limite", n > MAX * 0.9);
    }
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
});

// Enviar comentario
document.addEventListener("submit", async function (e) {
    const form = e.target.closest(".comentario-form");
    if (!form) return;
    e.preventDefault();

    const idApunte = form.dataset.apunte;
    const ta = form.querySelector(".comentario-input");
    const texto = ta.value.trim();

    if (!texto) { mostrarToast("El comentario no puede estar vacío.", "error"); ta.focus(); return; }
    if (texto.length > MAX) { mostrarToast(`Máximo ${MAX} caracteres.`, "error"); return; }

    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    const fd = new FormData();
    fd.append("contenido", texto);
    try {
        const data = await pedirJSON(`/apuntes/${idApunte}/comentarios`, { method: "POST", body: fd });
        mostrarToast(data.mensaje, "ok");
        if (typeof sonidoPop === "function") sonidoPop();
        ta.value = "";
        ta.style.height = "auto";
        form.querySelector(".comentario-contador").textContent = `0/${MAX}`;
        await cargarComentarios(idApunte, form.closest(".comentarios-panel"));
    } catch (err) {
        reportarError(err, "comentarios:crear");
    } finally {
        btn.disabled = false;
    }
});

// Ctrl+Enter para enviar
document.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        const ta = e.target.closest(".comentario-input");
        if (ta) ta.closest("form")?.requestSubmit();
    }
});

window.bloqueComentarios = bloqueComentarios;
})();