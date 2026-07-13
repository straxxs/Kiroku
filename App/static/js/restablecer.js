const form = document.getElementById("restablecerForm");
if (form) {
    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const token = this.dataset.token;
        const contraseña = document.getElementById("contraseña").value;
        const confirmar = document.getElementById("confirmar").value;

        if (contraseña.length < 8) {
            mostrarToast("La contraseña debe tener al menos 8 caracteres.", "error");
            return;
        }
        if (!/[A-Z]/.test(contraseña)) {
            mostrarToast("La contraseña debe tener al menos 1 letra mayúscula.", "error");
            return;
        }
        if (!/[a-z]/.test(contraseña)) {
            mostrarToast("La contraseña debe tener al menos 1 letra minúscula.", "error");
            return;
        }
        if (!/\d/.test(contraseña)) {
            mostrarToast("La contraseña debe tener al menos 1 número.", "error");
            return;
        }
        if (contraseña !== confirmar) {
            mostrarToast("Las contraseñas no coinciden.", "error");
            return;
        }

        const btn = form.querySelector('button[type="submit"]');
        const textoOriginal = btn.textContent;
        btn.disabled = true;
        btn.textContent = "Guardando...";

        const fd = new FormData();
        fd.append("contraseña", contraseña);
        fetch("/restablecer/" + token, { method: "POST", body: fd })
            .then(res => res.json())
            .then(data => {
                mostrarToast(data.mensaje, data.ok ? "ok" : "error");
                if (data.ok) setTimeout(() => window.location.href = "/login", 1200);
            })
            .catch(() => mostrarToast("Hubo un error de conexión.", "error"))
            .finally(() => {
                btn.disabled = false;
                btn.textContent = textoOriginal;
            });
    });
}
