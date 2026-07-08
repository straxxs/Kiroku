const ID_MATERIA = document.body.dataset.idMateria;
const PUEDE_GESTIONAR = document.body.dataset.puedeGestionar === "true";
let MI_ID = null;

const EXT_IMG = ["png", "jpg", "jpeg", "webp", "gif"];
const EXT_VIDEO = ["mp4", "webm", "ogg"];
const ICONOS = {
    pdf: "📕", doc: "📘", docx: "📘", txt: "📄",
    pptx: "📙", ppt: "📙", xlsx: "📗", xls: "📗",
};


// ---------- Genera el preview de UN archivo ----------
function htmlPreview(f) {
    const url = `/static/${f.ruta}`;
    const tipo = (f.tipo || "").toLowerCase();

    // Imagen -> thumbnail + lightbox
    if (EXT_IMG.includes(tipo)) {
        return `
            <div class="preview-item">
                <img class="preview-img" src="${url}" alt="imagen"
                     onclick="abrirLightbox('${url}')">
                <div class="preview-footer">
                    <span class="tipo">${tipo}</span>
                    <a href="${url}">
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
                    <a href="${url}" target="_blank">
                    <button class="Btn2"><strong>Ver archivo</strong></button>
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
                    <a href="${url}">
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
    const icono = ICONOS[tipo] || "📎";
    return `
        <div class="preview-item">
            <div class="preview-generico">
                <div class="icono">${icono}</div>
                <div class="nombre">Archivo ${tipo}</div>
                <a href="${url}" download>
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

// ---------- Botón de archivo bonito ----------
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
                cont.innerHTML = '<p class="vacio">Todavía no hay apuntes. 📄</p>';
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

                const div = document.createElement("div");
                div.className = "card";
                div.style.marginBottom = "14px";
                div.id = `apunte-${a.id}`;
                div.innerHTML = `
                    <div class="autor-linea">
                        ${htmlAvatar(a.autor, a.autor_avatar, "avatar-chico")}
                        <strong>${a.autor || "Anónimo"}</strong>
                        ${a.estado && a.estado !== 'aprobado'
                            ? `<span class="badge-rol rol-alumno">${a.estado}</span>` : ""}
                    </div>
                    <h3 style="margin:6px 0;color:var(--tinta);">${a.titulo || "(sin título)"}</h3>
                    <p>${a.descripcion || "<em>Sin descripción</em>"}</p>
                    <div class="preview-grid">${previews}</div>

                    <div class="valoracion-fila">
                        ${estrellas}
                        <span class="valoracion-promedio">
                            ${a.promedio} / 5 (${a.cant_calificaciones})
                        </span>
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
function borrarApunte(id) {
    if (!confirm("¿Eliminar este apunte?")) return;
    fetch(`/apuntes/eliminar/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            mostrarToast(data.mensaje, data.ok ? "ok" : "error");
            if (data.ok) cargarApuntes();
        });
}


// ---------- Subir apunte ----------
const formApunte = document.getElementById("formApunte");
if (formApunte) {
    formApunte.addEventListener("submit", function (e) {
        e.preventDefault();
        const fd = new FormData(this);
        fd.append("id_materia", ID_MATERIA);
        fetch("/apuntes/crear", { method: "POST", body: fd })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) {
                    this.reset();
                    fileTexto.textContent = "Elegí archivos o arrastralos acá (opcional)";
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
                checkbox.checked = (data.estado === "guardado");
            } else {
                checkbox.checked = !checkbox.checked; // revertir
            }
        })
        .catch(() => {
            checkbox.checked = !checkbox.checked;
            mostrarToast("Error de conexión", "error");
        });
}

cargarApuntes();