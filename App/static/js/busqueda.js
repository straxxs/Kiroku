// ---------- Motor de búsqueda (home) ----------
const inputBusqueda = document.getElementById("q");
const selectOrden = document.getElementById("orden");
const btnBuscar = document.getElementById("btnBuscar");
const contResultados = document.getElementById("resultadosBusqueda");

const EXT_IMG_B = ["png", "jpg", "jpeg", "webp", "gif"];

function hacerBusqueda() {
    if (!contResultados) return;
    const q = (inputBusqueda?.value || "").trim();
    const orden = selectOrden?.value || "recientes";

    contResultados.innerHTML = '<p class="vacio">Buscando...</p>';

    fetch(`/buscar?q=${encodeURIComponent(q)}&orden=${encodeURIComponent(orden)}`)
        .then(res => res.json())
        .then(data => {
            if (!data.ok) {
                contResultados.innerHTML = `<p class="vacio">${data.mensaje || "No se pudo buscar"}</p>`;
                return;
            }
            if (!data.apuntes || data.apuntes.length === 0) {
                contResultados.innerHTML = '<p class="vacio">No se encontraron apuntes. 🔍</p>';
                return;
            }

            contResultados.innerHTML = "";
            data.apuntes.forEach(a => {
                // Mini preview de la primera imagen, si hay
                const primerArchivo = (a.archivos || [])[0];
                let miniatura = "";
                if (primerArchivo && EXT_IMG_B.includes((primerArchivo.tipo || "").toLowerCase())) {
                    miniatura = `<img src="/static/${primerArchivo.ruta}" alt=""
                        style="width:60px;height:60px;object-fit:cover;border-radius:10px;flex-shrink:0;">`;
                } else if (primerArchivo) {
                    miniatura = `<div style="width:60px;height:60px;display:flex;align-items:center;
                        justify-content:center;background:var(--crema);border-radius:10px;font-size:26px;
                        flex-shrink:0;">📎</div>`;
                }

                const div = document.createElement("div");
                div.className = "card";
                div.style.marginBottom = "12px";
                div.innerHTML = `
                    <div style="display:flex;gap:12px;align-items:flex-start;">
                        ${miniatura}
                        <div style="flex:1;">
                            <div class="autor-linea" style="margin-bottom:4px;">
                                ${htmlAvatar(a.autor, a.autor_avatar, "avatar-chico")}
                                <strong>${a.autor || "Anónimo"}</strong>
                                <span class="valoracion-promedio">
                                    · ⭐ ${a.promedio} (${a.cant_calificaciones})
                                </span>
                            </div>
                            <h3 style="margin:4px 0;color:var(--tinta);">${a.titulo || "(sin título)"}</h3>
                            <p style="color:var(--tinta-soft);margin:2px 0;">
                                ${a.materia || "Sin materia"}
                            </p>
                            <p style="margin:4px 0;">${a.descripcion || "<em>Sin descripción</em>"}</p>
                            <a href="/materia/${a.id_materia}#apunte-${a.id}"
                               class="btn btn-celeste btn-chico">Ver apunte</a>
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

    // Buscar con Enter
    inputBusqueda?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") { e.preventDefault(); hacerBusqueda(); }
    });

    // Rebuscar al cambiar el orden
    selectOrden?.addEventListener("change", hacerBusqueda);

    // Búsqueda inicial (muestra todo el curso)
    hacerBusqueda();
}