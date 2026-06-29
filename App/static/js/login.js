document.getElementById("loginForm").addEventListener("submit", function (e) {
    e.preventDefault();
    fetch("/login", { method: "POST", body: new FormData(this) })
        .then(res => res.json())
        .then(data => {
            alert(data.mensaje);
            if (data.ok) {
                if (data.rol === "admin") {
                    window.location.href = "/admin";
                } else {
                    window.location.href = "/home";
                }
            }
        })
        .catch(() => alert("Hubo un error de conexión."));
});