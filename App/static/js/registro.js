document.getElementById("registroForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    fetch("/registro", {
        method: "POST",
        body: formData
    })
        .then(res => res.json())
        .then(data => {
            alert(data.mensaje);
            if (data.ok) {
                window.location.href = "/login";
            }
        })
        .catch(() => alert("Hubo un error de conexión."));
});