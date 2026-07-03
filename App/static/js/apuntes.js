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
const fileDrop = document.getElementById("fileDrop");
const inputArchivo = document.getElementById("archivo");
const fileTexto = document.getElementById("fileTexto");

if (fileDrop && inputArchivo) {
    // Click en la zona abre el selector
    fileDrop.addEventListener("click", () => inputArchivo.click());

    // Al elegir archivo, mostrar el nombre
    inputArchivo.addEventListener("change", function () {
        if (this.files && this.files[0]) {
            fileTexto.textContent = this.files[0].name;
            fileDrop.classList.add("tiene-archivo");
        } else {
            fileTexto.textContent = "Elegí un archivo o arrastralo acá";
            fileDrop.classList.remove("tiene-archivo");
        }
    });

    // Drag & drop
    fileDrop.addEventListener("dragover", (e) => {
        e.preventDefault();
        fileDrop.classList.add("tiene-archivo");
    });
    fileDrop.addEventListener("dragleave", () => {
        if (!inputArchivo.files.length) fileDrop.classList.remove("tiene-archivo");
    });
    fileDrop.addEventListener("drop", (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length) {
            inputArchivo.files = e.dataTransfer.files;
            fileTexto.textContent = e.dataTransfer.files[0].name;
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

                const div = document.createElement("div");
                div.className = "card";
                div.style.marginBottom = "14px";
                div.innerHTML = `
                    <div class="autor-linea">
                        ${htmlAvatar(a.autor, a.autor_avatar, "avatar-chico")}
                        <strong>${a.autor || "Anónimo"}</strong>
                    </div>
                    <p>${a.descripcion || "<em>Sin descripción</em>"}</p>
                    <div class="preview-grid">${previews}</div>
                    <div class="acciones" style="margin-top:10px;">
                        ${puedeBorrar
                            ? `<button class="btn btn-rojo btn-chico"
                                 onclick="borrarApunte(${a.id})">Eliminar</button>`
                            : ""}
                    </div>`;
                cont.appendChild(div);
            });
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
                    fileTexto.textContent = "Elegí un archivo o arrastralo acá";
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


cargarApuntes();