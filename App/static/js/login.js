document.getElementById("loginForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    fetch("/login", {
        method: "POST",
        body: formData
    })
        .then(res => res.json())
        .then(data => {
            alert(data.mensaje);
            if (data.ok) {
                window.location.href = "/home";
            }
        })
        .catch(() => alert("Hubo un error de conexión."));
});