(function(){
const ID_MATERIA = document.body.dataset.idMateria;
const PUEDE_GESTIONAR = document.body.dataset.puedeGestionar === "true";
let MI_ID = null;

const EXT_IMG = ["png", "jpg", "jpeg", "webp", "gif"];
const EXT_VIDEO = ["mp4", "webm", "ogg"];
const IC={"file-text":'<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',"file":'<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>',"paperclip":'<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>','trash-2':'<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>','heart':'<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>','sparkles':'<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>','star':`<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>`};
function L(n,s){s=s||16;return `<svg class="luc" xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${IC[n]}</svg>`}
const ICONOS = {
    pdf: L("file-text"), doc: L("file"), docx: L("file"), txt: L("file-text"),
    pptx: L("presentation"), ppt: L("presentation"), xlsx: L("table"), xls: L("table"),
};


// ---------- Genera el preview de UN archivo ----------
function htmlPreview(f) {
    const url = `/static/${f.ruta}`;
    const descarga = `/descargar/${encodeURIComponent(f.ruta)}`;
    const tipo = (f.tipo || "").toLowerCase();

    // Imagen -> thumbnail + lightbox
    if (EXT_IMG.includes(tipo)) {
        return `
            <div class="preview-item">
                <img class="preview-img" src="${url}" alt="imagen"
                     onclick="abrirLightbox('${url}')">
                <div class="preview-footer">
                    <span class="tipo">${tipo}</span>
                    <a href="${descarga}">
                    <button class="Btn">
                        <svg class="svgIcon" viewBox="0 0 384 512" height="10px" xmlns="http://www.w3.org/2000/svg"><path d="M169.4 470.6c12.5 12.5 32.8 12.5 45.3 0l160-160c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L224 370.8 224 64c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 306.7L54.6 265.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l160 160z"></path></svg>
                        <span class="icon2"></span>
                        <span class="tooltip">Download</span>
                    </button>
                    </a>
                </div>
            </div>`;
    }

    // PDF -> iframe embebido (primera vista)
    if (tipo === "pdf") {
        return `
            <div class="preview-item">
                <iframe class="preview-pdf" src="${url}#toolbar=0"></iframe>
                <div class="preview-footer">
                    <span class="tipo">pdf</span>
                    <a href="${descarga}">
                    <button class="Btn2"><strong>Descargar</strong></button>
                    </a>
                </div>
            </div>`;
    }

    // Video -> player embebido
    if (EXT_VIDEO.includes(tipo)) {
        return `
            <div class="preview-item">
                <video class="preview-video" controls src="${url}"></video>
                <div class="preview-footer">
                    <span class="tipo">${tipo}</span>
                    <a href="${descarga}">
                    <button class="Btn">
                        <svg class="svgIcon" viewBox="0 0 384 512" height="10px" xmlns="http://www.w3.org/2000/svg"><path d="M169.4 470.6c12.5 12.5 32.8 12.5 45.3 0l160-160c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L224 370.8 224 64c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 306.7L54.6 265.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l160 160z"></path></svg>
                        <span class="icon2"></span>
                        <span class="tooltip">Download</span>
                    </button>
                    </a>
                </div>
            </div>`;
    }

    // Otros (docx, xlsx, txt...) -> ícono + descarga
    const icono = ICONOS[tipo] || L("paperclip");
    return `
        <div class="preview-item">
            <div class="preview-generico">
                <div class="icono">${icono}</div>
                <div class="nombre">Archivo ${tipo}</div>
                <a href="${descarga}">
                <button class="Btn">
                    <svg class="svgIcon" viewBox="0 0 384 512" height="10px" xmlns="http://www.w3.org/2000/svg"><path d="M169.4 470.6c12.5 12.5 32.8 12.5 45.3 0l160-160c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L224 370.8 224 64c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 306.7L54.6 265.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l160 160z"></path></svg>
                    <span class="icon2"></span>
                    <span class="tooltip">Download</span>
                </button>
                </a>
            </div>
            <div class="preview-footer">
                <span class="tipo">${tipo}</span>
            </div>
        </div>`;
}

// ---------- Botón de archivo bonito (múltiples, opcional) ----------
const fileDrop = document.getElementById("fileDrop");
const inputArchivo = document.getElementById("archivo");
const fileTexto = document.getElementById("fileTexto");

function textoArchivos(files) {
    if (!files || files.length === 0) return "Elegí archivos o arrastralos acá (opcional)";
    if (files.length === 1) return files[0].name;
    return `${files.length} archivos seleccionados`;
}

if (fileDrop && inputArchivo) {
    fileDrop.addEventListener("click", () => inputArchivo.click());

    inputArchivo.addEventListener("change", function () {
        fileTexto.textContent = textoArchivos(this.files);
        fileDrop.classList.toggle("tiene-archivo", this.files.length > 0);
    });

    fileDrop.addEventListener("dragover", (e) => { e.preventDefault(); fileDrop.classList.add("tiene-archivo"); });
    fileDrop.addEventListener("dragleave", () => {
        if (!inputArchivo.files.length) fileDrop.classList.remove("tiene-archivo");
    });
    fileDrop.addEventListener("drop", (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length) {
            inputArchivo.files = e.dataTransfer.files;
            fileTexto.textContent = textoArchivos(e.dataTransfer.files);
            fileDrop.classList.add("tiene-archivo");
        }
    });
}

// ---------- Cargar apuntes ----------
function cargarApuntes() {
    fetch(`/materias/${ID_MATERIA}/apuntes`)
        .then(res => res.json())
        .then(data => {
            MI_ID = data.id_usuario;
            const cont = document.getElementById("listaApuntes");
            cont.innerHTML = "";

            if (!data.apuntes || data.apuntes.length === 0) {
                cont.innerHTML = '<p class="vacio">Todavía no hay apuntes. '+L("file-text",20)+'<br><small>Usá el formulario de arriba para subir el primero.</small></p>';
                return;
            }

            data.apuntes.forEach(a => {
                const puedeBorrar = (a.id_usuario_creador === MI_ID) || PUEDE_GESTIONAR;

                const previews = (a.archivos || []).map(htmlPreview).join("");

                const estrellas = generarEstrellas(a.id, a.mi_calificacion);
                const btnGuardar = `
                        <label class="container">
                            <input 
                                type="checkbox" 
                                ${a.guardado ? 'checked' : ''}
                                onchange="toggleGuardar(${a.id}, this)"
                            />
                            
                            <svg class="save-regular" xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 384 512">
                                <path d="M0 48C0 21.5 21.5 0 48 0l0 48V441.4l130.1-92.9c8.3-6 19.6-6 27.9 0L336 441.4V48H48V0H336c26.5 0 48 21.5 48 48V488c0 9-5 17.2-13 21.3s-17.6 3.4-24.9-1.8L192 397.5 37.9 507.5c-7.3 5.2-16.9 5.9-24.9 1.8S0 497 0 488V48z"></path>
                            </svg>

                            <svg class="save-solid" xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 384 512">
                                <path d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"></path>
                            </svg>
                        </label>
                        `;

                const btnMeGusta = `
                    <button class="btn-megusta ${a.mi_me_gusta ? 'activo' : ''}"
                        onclick="toggleMeGusta(${a.id}, this)" title="Me gusta">
                        <span class="megusta-icono">${L("heart",18)}</span>
                        <span class="megusta-count">${a.me_gusta_count || 0}</span>
                    </button>`;

                const div = document.createElement("div");
                div.className = "card card-apunte";
                div.id = `apunte-${a.id}`;
                div.innerHTML = `
                    <div class="autor-linea">
                        ${htmlAvatar(a.autor, a.autor_avatar, "avatar-chico")}
                        <strong>${escapeHtml(a.autor || "Anónimo")}</strong>
                        ${a.estado && a.estado !== 'aprobado'
                            ? `<span class="badge-rol rol-alumno">${escapeHtml(a.estado)}</span>` : ""}
                    </div>
                    <h3 style="margin:6px 0;color:var(--tinta);">${escapeHtml(a.titulo || "(sin título)")}</h3>
                    <p>${escapeHtml(a.descripcion || "")}</p>
                    <div class="preview-grid">${previews}</div>

                    <div class="valoracion-fila">
                        ${estrellas}
                        <span class="valoracion-promedio">
                            ${a.promedio} / 5 (${a.cant_calificaciones})
                        </span>
                        ${btnMeGusta}
                        ${btnGuardar}
                    </div>

                    <div class="acciones" style="margin-top:10px;">
                        ${puedeBorrar
                            ? `<button class="btn btn-rojo btn-chico"
                                onclick="borrarApunte(${a.id})">Eliminar</button>`
                            : ""}
                    </div>`;
                cont.appendChild(div);
            });
            activarHoverEstrellas();
            resaltarApunteDelHash();    
        })
        .catch(() => mostrarToast("Error al cargar apuntes", "error"));
}


// ---------- Borrar apunte ----------
async function borrarApunte(id) {
    const ok = await kirokuConfirm(L("trash-2", 20), "Eliminar apunte", "¿Eliminar este apunte? No se podrá recuperar.", "Eliminar", "Cancelar");
    if (!ok) return;
    fetch(`/apuntes/eliminar/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarApuntes();
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}


// ---------- Subir apunte ----------
const formApunte = document.getElementById("formApunte");
if (formApunte) {
    formApunte.addEventListener("submit", function (e) {
        e.preventDefault();
        if (!this.reportValidity()) return;
        const fd = new FormData(this);
        fd.append("id_materia", ID_MATERIA);
        const archivos = fd.getAll("archivo").filter(a => a && a.name);
        if (archivos.length === 0) {
            mostrarToast("Debés subir al menos un archivo", "error");
            return;
        }
        fetch("/apuntes/crear", { method: "POST", body: fd })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) {
                    this.reset();
                    fileTexto.textContent = "Elegí archivos o arrastralos acá";
                    fileDrop.classList.remove("tiene-archivo");
                    cargarApuntes();
                }
            })
            .catch(() => mostrarToast("Error de conexión", "error"));
    });
}


// ---------- Lightbox ----------
function abrirLightbox(url) {
    let lb = document.getElementById("lightbox");
    if (!lb) {
        lb = document.createElement("div");
        lb.id = "lightbox";
        lb.className = "lightbox";
        lb.innerHTML = `<span class="lightbox-cerrar">&times;</span><img src="" alt="ampliada">`;
        document.body.appendChild(lb);
        lb.addEventListener("click", () => lb.classList.remove("abierto"));
    }
    lb.querySelector("img").src = url;
    lb.classList.add("abierto");
}

// ---------- Resaltar apunte al venir desde "Guardados" ----------
function resaltarApunteDelHash() {
    if (!location.hash.startsWith("#apunte-")) return;
    const el = document.querySelector(location.hash);
    if (!el) return;
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.classList.add("apunte-resaltado");
    setTimeout(() => el.classList.remove("apunte-resaltado"), 2500);
}

// ---------- Estrellas ----------
function generarEstrellas(idApunte, miCalificacion) {
    let html = `<span class="estrellas" data-apunte="${idApunte}">`;
    for (let i = 1; i <= 5; i++) {
        const activa = i <= miCalificacion ? "activa" : "";
        html += `<span class="estrella ${activa}" data-valor="${i}" title="${i} de 5"
                    onclick="calificar(${idApunte}, ${i})">★</span>`;
    }
    html += `</span>`;
    return html;
}

// ---------- Hover de estrellas (pinta de izquierda a derecha) ----------
function activarHoverEstrellas() {
    document.querySelectorAll(".estrellas").forEach(grupo => {
        const estrellas = grupo.querySelectorAll(".estrella");

        estrellas.forEach(estrella => {
            estrella.addEventListener("mouseover", () => {
                const valor = parseInt(estrella.dataset.valor, 10);
                estrellas.forEach(e => {
                    e.classList.toggle("hover-activa", parseInt(e.dataset.valor, 10) <= valor);
                });
            });
        });

        // Al salir del grupo, se quita el hover y vuelve a mostrar la calificación fija
        grupo.addEventListener("mouseleave", () => {
            estrellas.forEach(e => e.classList.remove("hover-activa"));
        });
    });
}

function calificar(idApunte, estrellas) {
    const fd = new FormData();
    fd.append("estrellas", estrellas);
    fetch(`/apuntes/${idApunte}/calificar`, { method: "POST", body: fd })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (!data.ok) return;

            // Actualizar SOLO este apunte, sin recargar todo
            const card = document.getElementById(`apunte-${idApunte}`);
            if (!card) return;

            // Pintar estrellas fijas según la nueva calificación
            card.querySelectorAll(".estrella").forEach(e => {
                const valor = parseInt(e.dataset.valor, 10);
                e.classList.toggle("activa", valor <= data.mi_calificacion);
            });

            // Actualizar el promedio
            const prom = card.querySelector(".valoracion-promedio");
            if (prom) prom.textContent = `${data.promedio} / 5 (${data.cantidad})`;
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

// ---------- Guardar ----------
function toggleGuardar(idApunte, checkbox) {
    fetch(`/apuntes/${idApunte}/guardar`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) {
                if (typeof sonidoPop === "function") sonidoPop();
                checkbox.checked = (data.estado === "guardado");
            } else {
                checkbox.checked = !checkbox.checked;
            }
        })
        .catch(() => {
            checkbox.checked = !checkbox.checked;
            mostrarToast("Error de conexión", "error");
        });
}

// ---------- Me Gusta ----------
function toggleMeGusta(idApunte, boton) {
    fetch(`/apuntes/${idApunte}/me-gusta`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) {
                if (typeof sonidoLike === "function") sonidoLike();
                boton.classList.toggle("activo", data.estado === "gustado");
                const countEl = boton.querySelector(".megusta-count");
                if (countEl) countEl.textContent = data.cantidad;
            }
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

cargarApuntes();

window.calificar = calificar;
window.toggleGuardar = toggleGuardar;
window.toggleMeGusta = toggleMeGusta;
window.borrarApunte = borrarApunte;
window.abrirLightbox = abrirLightbox;

})();