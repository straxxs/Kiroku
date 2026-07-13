function kirokuConfirm(icono, titulo, texto, btnConfirmar, btnCancelar) {
    return new Promise(resolve => {
        let overlay = document.getElementById("kirokuModalOverlay");
        if (!overlay) {
            overlay = document.createElement("div");
            overlay.id = "kirokuModalOverlay";
            overlay.className = "kiroku-modal-overlay";
            overlay.innerHTML = `
                <div class="kiroku-modal">
                    <div class="kiroku-modal-icon"></div>
                    <h3></h3>
                    <p></p>
                    <div class="kiroku-modal-acciones">
                        <button class="btn btn-celeste btn-chico" id="kirokuModalConfirmar"></button>
                        <button class="btn btn-gris btn-chico" id="kirokuModalCancelar"></button>
                    </div>
                </div>`;
            document.body.appendChild(overlay);

            overlay.addEventListener("click", e => {
                if (e.target === overlay) { cerrar(); resolve(null); }
            });
        }

        overlay.querySelector(".kiroku-modal-icon").innerHTML = icono;
        overlay.querySelector("h3").textContent = titulo;
        overlay.querySelector("p").textContent = texto;
        overlay.querySelector("#kirokuModalConfirmar").textContent = btnConfirmar || "Aceptar";
        overlay.querySelector("#kirokuModalCancelar").textContent = btnCancelar || "Cancelar";

        requestAnimationFrame(() => overlay.classList.add("visible"));

        function cerrar() { overlay.classList.remove("visible"); }

        overlay.querySelector("#kirokuModalConfirmar").onclick = () => { cerrar(); resolve(true); };
        overlay.querySelector("#kirokuModalCancelar").onclick = () => { cerrar(); resolve(false); };
    });
}

function kirokuEdit(icono, titulo, campos, btnGuardar, btnCancelar) {
    return new Promise(resolve => {
        let overlay = document.getElementById("kirokuEditOverlay");
        if (!overlay) {
            overlay = document.createElement("div");
            overlay.id = "kirokuEditOverlay";
            overlay.className = "kiroku-modal-overlay";

            overlay.innerHTML = `
                <div class="kiroku-modal">
                    <div class="kiroku-modal-icon"></div>
                    <h3></h3>
                    <div class="kiroku-modal-campos"></div>
                    <div class="kiroku-modal-acciones" style="margin-top:16px;">
                        <button class="btn btn-amarillo btn-chico" id="kirokuEditGuardar"></button>
                        <button class="btn btn-gris btn-chico" id="kirokuEditCancelar"></button>
                    </div>
                </div>`;
            document.body.appendChild(overlay);

            overlay.addEventListener("click", e => {
                if (e.target === overlay) { cerrar(); resolve(null); }
            });
        }

        overlay.querySelector(".kiroku-modal-icon").innerHTML = icono;
        overlay.querySelector("h3").textContent = titulo;
        overlay.querySelector("#kirokuEditGuardar").textContent = btnGuardar || "Guardar";
        overlay.querySelector("#kirokuEditCancelar").textContent = btnCancelar || "Cancelar";

        const contenedor = overlay.querySelector(".kiroku-modal-campos");
        contenedor.innerHTML = "";
        campos.forEach(c => {
            const div = document.createElement("div");
            div.className = "campo";
            div.innerHTML = `<label>${c.label}</label>
                <input type="${c.type || 'text'}" value="${c.valor || ''}" placeholder="${c.placeholder || ''}"
                    data-campo="${c.id}">`;
            contenedor.appendChild(div);
        });

        const primerInput = contenedor.querySelector("input");
        if (primerInput) setTimeout(() => primerInput.focus(), 100);

        requestAnimationFrame(() => overlay.classList.add("visible"));

        function cerrar() { overlay.classList.remove("visible"); }

        overlay.querySelector("#kirokuEditGuardar").onclick = () => {
            const valores = {};
            campos.forEach(c => {
                const inp = contenedor.querySelector(`[data-campo="${c.id}"]`);
                valores[c.id] = inp ? inp.value.trim() : "";
            });
            cerrar();
            resolve(valores);
        };

        overlay.querySelector("#kirokuEditCancelar").onclick = () => { cerrar(); resolve(null); };

        contenedor.querySelectorAll("input").forEach(inp => {
            inp.addEventListener("keydown", e => {
                if (e.key === "Enter") {
                    overlay.querySelector("#kirokuEditGuardar").click();
                }
            });
        });
    });
}
