from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from modulos.auth import login, registrar_usuario
from modulos.cursos import (
    crear_curso, editar_curso, listar_cursos, eliminar_curso,
    obtener_curso, listar_alumnos_curso,
)
from modulos.materias import (
    crear_materia, editar_materia, listar_materias_por_curso,
    eliminar_materia, obtener_materia,
)
from modulos.usuarios import listar_usuarios, eliminar_usuario

app = Flask(__name__)
app.secret_key = "mitin_2026"


# ---------- Helpers ----------
def requiere_login():
    return "id_usuario" in session


def requiere_admin():
    return session.get("rol") == "admin"


def es_mi_curso(id_curso):
    """Admin puede todo. Moderador solo su curso asignado."""
    if session.get("rol") == "admin":
        return True
    return str(session.get("id_curso")) == str(id_curso)


# ====================== AUTH ======================

@app.route("/")
def index():
    return redirect(url_for("login_route"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        contraseña = request.form["contraseña"]
        if registrar_usuario(nombre, contraseña):
            return jsonify({"ok": True, "mensaje": "¡Registro exitoso! Ahora iniciá sesión."})
        return jsonify({"ok": False, "mensaje": "Error al registrar (el usuario quizás ya existe)."})
    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login_route():
    if request.method == "POST":
        nombre = request.form["nombre"]
        contraseña = request.form["contraseña"]
        usuario = login(nombre, contraseña)
        if usuario:
            session["id_usuario"] = usuario["id"]
            session["nombre"] = usuario["nombre"]
            session["rol"] = usuario["rol"]
            session["id_curso"] = usuario["id_curso"]
            return jsonify({
                "ok": True,
                "mensaje": f"¡Bienvenido {usuario['nombre']}!",
                "rol": usuario["rol"],
            })
        return jsonify({"ok": False, "mensaje": "Credenciales incorrectas."})
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_route"))


# ====================== PÁGINAS ======================

@app.route("/home")
def home():
    if not requiere_login():
        return redirect(url_for("login_route"))
    return render_template(
        "home.html",
        nombre=session.get("nombre"),
        rol=session.get("rol"),
        id_curso=session.get("id_curso"),
    )


@app.route("/admin")
def panel_admin():
    if not requiere_login():
        return redirect(url_for("login_route"))
    if not requiere_admin():
        return "No tenés permisos", 403
    return render_template("admin.html", nombre=session.get("nombre"))


@app.route("/curso/<int:id_curso>")
def pagina_curso(id_curso):
    if not requiere_login():
        return redirect(url_for("login_route"))
    curso = obtener_curso(id_curso)
    if not curso:
        return "El curso no existe", 404
    # ¿Puede gestionar este curso? (moderador de este curso o admin)
    puede_gestionar = es_mi_curso(id_curso)
    return render_template(
        "curso.html",
        curso=curso,
        puede_gestionar=puede_gestionar,
        rol=session.get("rol"),
    )


# ====================== CURSOS (API) ======================

@app.route("/cursos", methods=["GET"])
def cursos_listar():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    return jsonify({"ok": True, "cursos": listar_cursos()})


@app.route("/cursos/<int:id_curso>", methods=["GET"])
def curso_detalle(id_curso):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    curso = obtener_curso(id_curso)
    if not curso:
        return jsonify({"ok": False, "mensaje": "El curso no existe"}), 404
    return jsonify({
        "ok": True,
        "curso": curso,
        "puede_gestionar": es_mi_curso(id_curso),
    })


@app.route("/cursos/<int:id_curso>/alumnos", methods=["GET"])
def curso_alumnos(id_curso):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    return jsonify({"ok": True, "alumnos": listar_alumnos_curso(id_curso)})


@app.route("/cursos/crear", methods=["POST"])
def cursos_crear():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    if session.get("id_curso"):
        return jsonify({"ok": False, "mensaje": "Ya tenés un curso asignado"}), 400

    anio = request.form.get("anio")
    division = request.form.get("division")
    id_u = session["id_usuario"]

    nuevo_id = crear_curso(anio, division, id_u)
    if nuevo_id:
        session["rol"] = "moderador"
        session["id_curso"] = nuevo_id
        return jsonify({
            "ok": True,
            "mensaje": "¡Curso creado! Ahora sos moderador.",
            "id": nuevo_id,
        })
    return jsonify({"ok": False, "mensaje": "Error al crear el curso"})


@app.route("/cursos/editar/<int:id_curso>", methods=["POST"])
def cursos_editar(id_curso):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    if not es_mi_curso(id_curso):
        return jsonify({"ok": False, "mensaje": "No podés editar este curso"}), 403

    anio = request.form.get("anio")
    division = request.form.get("division")
    if editar_curso(id_curso, anio, division):
        return jsonify({"ok": True, "mensaje": "Curso actualizado"})
    return jsonify({"ok": False, "mensaje": "No se pudo actualizar"})


@app.route("/cursos/eliminar/<int:id_curso>", methods=["POST"])
def cursos_eliminar(id_curso):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    if not requiere_admin():
        return jsonify({"ok": False, "mensaje": "Solo el admin puede borrar cursos"}), 403
    if eliminar_curso(id_curso):
        return jsonify({"ok": True, "mensaje": "Curso eliminado"})
    return jsonify({"ok": False, "mensaje": "No se pudo eliminar"})


# ====================== MATERIAS (API) ======================

@app.route("/cursos/<int:id_curso>/materias", methods=["GET"])
def materias_por_curso(id_curso):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    return jsonify({"ok": True, "materias": listar_materias_por_curso(id_curso)})


@app.route("/materias/crear", methods=["POST"])
def materias_crear():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401

    id_curso = request.form.get("id_curso")
    if not es_mi_curso(id_curso):
        return jsonify({"ok": False, "mensaje": "Solo podés agregar materias a tu curso"}), 403

    nombre = request.form.get("nombre")
    nombre_profesor = request.form.get("profesor")
    nuevo_id = crear_materia(nombre, id_curso, nombre_profesor)
    if nuevo_id:
        return jsonify({"ok": True, "mensaje": "Materia creada", "id": nuevo_id})
    return jsonify({"ok": False, "mensaje": "Error al crear la materia"})


@app.route("/materias/editar/<int:id_materia>", methods=["POST"])
def materias_editar(id_materia):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401

    materia = obtener_materia(id_materia)
    if not materia:
        return jsonify({"ok": False, "mensaje": "La materia no existe"}), 404
    if not es_mi_curso(materia["id_curso"]):
        return jsonify({"ok": False, "mensaje": "No podés editar materias de otro curso"}), 403

    nombre = request.form.get("nombre")
    nombre_profesor = request.form.get("profesor")
    if editar_materia(id_materia, nombre, nombre_profesor):
        return jsonify({"ok": True, "mensaje": "Materia actualizada"})
    return jsonify({"ok": False, "mensaje": "No se pudo actualizar"})


@app.route("/materias/eliminar/<int:id_materia>", methods=["POST"])
def materias_eliminar(id_materia):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401

    materia = obtener_materia(id_materia)
    if not materia:
        return jsonify({"ok": False, "mensaje": "La materia no existe"}), 404
    if not es_mi_curso(materia["id_curso"]):
        return jsonify({"ok": False, "mensaje": "No podés borrar materias de otro curso"}), 403

    if eliminar_materia(id_materia):
        return jsonify({"ok": True, "mensaje": "Materia eliminada"})
    return jsonify({"ok": False, "mensaje": "No se pudo eliminar"})


# ====================== ADMIN (API) ======================

@app.route("/admin/usuarios", methods=["GET"])
def admin_usuarios():
    if not requiere_admin():
        return jsonify({"ok": False, "mensaje": "No tenés permisos"}), 403
    return jsonify({"ok": True, "usuarios": listar_usuarios()})


@app.route("/admin/usuarios/eliminar/<int:id_usuario>", methods=["POST"])
def admin_eliminar_usuario(id_usuario):
    if not requiere_admin():
        return jsonify({"ok": False, "mensaje": "No tenés permisos"}), 403
    if eliminar_usuario(id_usuario):
        return jsonify({"ok": True, "mensaje": "Usuario eliminado"})
    return jsonify({"ok": False, "mensaje": "No se pudo eliminar"})


if __name__ == "__main__":
    app.run(debug=True)