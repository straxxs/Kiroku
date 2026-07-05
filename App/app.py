import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from modulos.auth import login, registrar_usuario
from modulos.cursos import (
    crear_curso, editar_curso, listar_cursos, eliminar_curso,
    obtener_curso, listar_alumnos_curso,
    unir_usuario_a_curso, salir_de_curso,
)
from modulos.materias import (
    crear_materia, editar_materia, listar_materias_por_curso,
    eliminar_materia, obtener_materia,
)
from modulos.usuarios import (
    listar_usuarios, eliminar_usuario,
    obtener_usuario, actualizar_perfil,
)
from modulos.apuntes import (
    crear_apunte, agregar_archivo_apunte, listar_apuntes_por_materia,
    obtener_apunte, eliminar_apunte,
)


app = Flask(__name__)
app.secret_key = "mitin_2026"

# ---------- Config de subida de archivos ----------
UPLOAD_APUNTES = os.path.join(app.static_folder, "uploads", "apuntes")
os.makedirs(UPLOAD_APUNTES, exist_ok=True)
os.makedirs(os.path.join(app.static_folder, "uploads", "avatares"), exist_ok=True)

EXT_APUNTES = {"pdf", "png", "jpg", "jpeg", "docx", "doc", "txt", "pptx"}
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB máx

def extension_ok(nombre, permitidas):
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in permitidas


# ---------- Helpers ----------
def requiere_login():
    return "id_usuario" in session


def requiere_admin():
    return session.get("rol") == "admin"


def es_mi_curso(id_curso):
    """True si es admin o moderador de ESE curso (puede gestionar)."""
    if session.get("rol") == "admin":
        return True
    if session.get("rol") != "moderador":
        return False
    return str(session.get("id_curso")) == str(id_curso)


def puede_ver_materia(id_curso):
    """Admin ve todo; el resto solo su propio curso."""
    if session.get("rol") == "admin":
        return True
    return str(session.get("id_curso")) == str(id_curso)

@app.context_processor
def inyectar_usuario():
    if "id_usuario" not in session:
        return {}
    return {
        "session_avatar": session.get("avatar") or "uploads/avatares/no_avatar.png",
        "nombre": session.get("nombre"),
        "rol": session.get("rol"),
        "session_id_curso": session.get("id_curso"),
    }

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
            session["avatar"] = usuario.get("avatar")
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
    puede_gestionar = es_mi_curso(id_curso)
    return render_template(
        "curso.html",
        curso=curso,
        puede_gestionar=puede_gestionar,
        rol=session.get("rol"),
    )


@app.route("/materia/<int:id_materia>")
def pagina_materia(id_materia):
    if not requiere_login():
        return redirect(url_for("login_route"))

    materia = obtener_materia(id_materia)
    if not materia:
        return "La materia no existe", 404

    if not puede_ver_materia(materia["id_curso"]):
        return "No tenés acceso a esta materia", 403

    curso = obtener_curso(materia["id_curso"])
    puede_gestionar = es_mi_curso(materia["id_curso"])
    return render_template(
        "materia.html",
        materia=materia,
        curso=curso,
        puede_gestionar=puede_gestionar,
        rol=session.get("rol"),
    )


# ====================== PERFIL ======================

@app.route("/perfil")
def pagina_perfil():
    if not requiere_login():
        return redirect(url_for("login_route"))
    usuario = obtener_usuario(session["id_usuario"])
    return render_template("perfil.html", usuario=usuario, rol=session.get("rol"))


# Lista de avatares válidos (los 10 predefinidos)
AVATARES_VALIDOS = [f"avatar{i}.png" for i in range(0, 10)]


@app.route("/perfil/actualizar", methods=["POST"])
def perfil_actualizar():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401

    nombre = request.form.get("nombre")
    avatar = request.form.get("avatar")  # ej: "avatar3.png"

    avatar_ruta = None
    if avatar:
        if avatar not in AVATARES_VALIDOS:
            return jsonify({"ok": False, "mensaje": "Avatar no válido"}), 400
        avatar_ruta = f"uploads/avatares/{avatar}"

    if actualizar_perfil(session["id_usuario"], nombre, avatar_ruta):
        if nombre and nombre.strip():
            session["nombre"] = nombre.strip()
        if avatar_ruta:
            session["avatar"] = avatar_ruta
        return jsonify({"ok": True, "mensaje": "Perfil actualizado"})
    return jsonify({"ok": False, "mensaje": "No se pudo actualizar el perfil, es posible que el nombre se repita"})

# ====================== CURSOS (API) ======================

@app.route("/cursos", methods=["GET"])
def cursos_listar():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    return jsonify({"ok": True, "cursos": listar_cursos()})


@app.route("/cursos/unirse", methods=["POST"])
def cursos_unirse():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    if session.get("id_curso"):
        return jsonify({"ok": False, "mensaje": "Ya pertenecés a un curso. Salí primero."}), 400

    id_curso = request.form.get("id_curso")
    if not id_curso or not id_curso.isdigit():
        return jsonify({"ok": False, "mensaje": "Código de curso inválido"}), 400

    if not obtener_curso(int(id_curso)):
        return jsonify({"ok": False, "mensaje": "Ese curso no existe"}), 404

    if unir_usuario_a_curso(session["id_usuario"], id_curso):
        session["id_curso"] = int(id_curso)
        return jsonify({"ok": True, "mensaje": "¡Te uniste al curso!", "id": int(id_curso)})
    return jsonify({"ok": False, "mensaje": "No se pudo unir"})


@app.route("/cursos/salir", methods=["POST"])
def cursos_salir():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    if session.get("rol") == "admin":
        return jsonify({"ok": False, "mensaje": "El admin no puede salir de un curso"}), 400
    if not session.get("id_curso"):
        return jsonify({"ok": False, "mensaje": "No estás en ningún curso"}), 400

    if salir_de_curso(session["id_usuario"]):
        session["id_curso"] = None
        session["rol"] = "alumno"
        return jsonify({"ok": True, "mensaje": "Saliste del curso"})
    return jsonify({"ok": False, "mensaje": "No se pudo salir del curso"})


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
    if eliminar_curso(id_curso, UPLOAD_APUNTES):
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

    if eliminar_materia(id_materia, UPLOAD_APUNTES):
        return jsonify({"ok": True, "mensaje": "Materia eliminada"})
    return jsonify({"ok": False, "mensaje": "No se pudo eliminar"})


# ====================== APUNTES (API) ======================

@app.route("/materias/<int:id_materia>/apuntes", methods=["GET"])
def apuntes_por_materia(id_materia):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    materia = obtener_materia(id_materia)
    if not materia:
        return jsonify({"ok": False, "mensaje": "La materia no existe"}), 404
    if not puede_ver_materia(materia["id_curso"]):
        return jsonify({"ok": False, "mensaje": "Sin acceso"}), 403

    apuntes = listar_apuntes_por_materia(id_materia)
    return jsonify({
        "ok": True,
        "apuntes": apuntes,
        "id_usuario": session["id_usuario"],
        "puede_gestionar": es_mi_curso(materia["id_curso"]),
    })


@app.route("/apuntes/crear", methods=["POST"])
def apuntes_crear():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401

    id_materia = request.form.get("id_materia")
    materia = obtener_materia(id_materia) if id_materia else None
    if not materia:
        return jsonify({"ok": False, "mensaje": "Materia inválida"}), 404
    if not puede_ver_materia(materia["id_curso"]):
        return jsonify({"ok": False, "mensaje": "No pertenecés a este curso"}), 403

    descripcion = request.form.get("descripcion", "")
    archivo = request.files.get("archivo")

    if not archivo or not archivo.filename:
        return jsonify({"ok": False, "mensaje": "Tenés que subir un archivo"}), 400
    if not extension_ok(archivo.filename, EXT_APUNTES):
        return jsonify({"ok": False, "mensaje": "Tipo de archivo no permitido"}), 400

    id_apunte = crear_apunte(
        descripcion, session["id_usuario"],
        materia["id_curso"], id_materia,
    )
    if not id_apunte:
        return jsonify({"ok": False, "mensaje": "Error al crear el apunte"}), 500

    nombre_seguro = secure_filename(f"apunte{id_apunte}_{archivo.filename}")
    archivo.save(os.path.join(UPLOAD_APUNTES, nombre_seguro))
    tipo = archivo.filename.rsplit(".", 1)[1].lower()
    agregar_archivo_apunte(id_apunte, f"uploads/apuntes/{nombre_seguro}", tipo)

    return jsonify({"ok": True, "mensaje": "¡Apunte subido!", "id": id_apunte})


@app.route("/apuntes/eliminar/<int:id_apunte>", methods=["POST"])
def apuntes_eliminar(id_apunte):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    apunte = obtener_apunte(id_apunte)
    if not apunte:
        return jsonify({"ok": False, "mensaje": "El apunte no existe"}), 404

    es_autor = apunte["id_usuario_creador"] == session["id_usuario"]
    if not (es_autor or es_mi_curso(apunte["id_curso"])):
        return jsonify({"ok": False, "mensaje": "No podés borrar este apunte"}), 403

    if eliminar_apunte(id_apunte, UPLOAD_APUNTES):
        return jsonify({"ok": True, "mensaje": "Apunte eliminado"})
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