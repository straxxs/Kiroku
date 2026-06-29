const formCurso = document.getElementById("formCurso");

if (formCurso) {
    formCurso.addEventListener("submit", function (e) {
        e.preventDefault();
        fetch("/cursos/crear", { method: "POST", body: new FormData(this) })
            .then(res => res.json())
            .then(data => {
                alert(data.mensaje);
                if (data.ok) {
                    window.location.href = "/curso/" + data.id;
                }
            })
            .catch(() => alert("Hubo un error de conexión."));
    });
}