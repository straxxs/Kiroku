import os
import re
import datetime
import pymysql
import jwt as pyjwt
from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, send_file
from werkzeug.utils import secure_filename
from modulos.auth import (
    login, registrar_usuario, generar_token_jwt, verificar_token_jwt,
    JWT_SECRET,
)
from modulos.validacion import (
    validar_contraseña, validar_nombre_usuario, validar_email,
)
from modulos.cursos import (
    crear_curso, editar_curso, listar_cursos, eliminar_curso,
    obtener_curso, listar_alumnos_curso,
    unir_usuario_a_curso, salir_de_curso,
    obtener_curso_por_codigo, eliminar_curso_como_creador,
)
from modulos.materias import (
    crear_materia, editar_materia, listar_materias_por_curso,
    eliminar_materia, obtener_materia,
)
from modulos.usuarios import (
    listar_usuarios, eliminar_usuario,
    obtener_usuario, actualizar_perfil, ascender_a_moderador, descender_a_alumno,
    cambiar_estado_usuario, cambiar_rol_usuario,
)
from modulos.apuntes import (
    crear_apunte, agregar_archivo_apunte, listar_apuntes_por_materia,
    listar_apuntes_pendientes, cambiar_estado_apunte,
    obtener_apunte, eliminar_apunte,
)
from modulos.valoraciones import (
    calificar_apunte, alternar_guardado, listar_guardados, obtener_promedio,
    alternar_me_gusta, contar_me_gusta,
)
from modulos.busqueda import buscar_apuntes
from modulos.recuperacion import (
    generar_token, resetear_contraseña, obtener_usuario_por_email,
)
from modulos.estadisticas import (
    estadisticas_generales, apuntes_mas_valorados,
    materias_mas_consultadas, ranking_colaboradores,
    apuntes_por_estado, apuntes_por_fecha,
    stats_curso_resumen, stats_curso_por_estado,
    stats_curso_materias, stats_curso_ranking,
    stats_curso_por_fecha, stats_curso_top_valorados,
)
from modulos.auditoria import registrar_accion

app = Flask(__name__)
app.secret_key = os.environ.get("KIROKU_SECRET_KEY", "kiroku_secret_key_2026_mitin_fallback")

JWT_COOKIE = "kiroku_token"

# ---------- Config de subida de archivos ----------
UPLOAD_APUNTES = os.path.join(app.static_folder, "uploads", "apuntes")
os.makedirs(UPLOAD_APUNTES, exist_ok=True)
os.makedirs(os.path.join(app.static_folder, "uploads", "avatares"), exist_ok=True)

EXT_APUNTES = {"pdf", "png", "jpg", "jpeg", "docx", "doc", "txt", "pptx"}
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


# ---------- Headers de seguridad ----------
@app.after_request
def agregar_headers_seguridad(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


def extension_ok(nombre, permitidas):
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in permitidas


# ---------- Helpers JWT ----------
def _obtener_usuario_jwt():
    """Lee el JWT de la cookie y devuelve el payload (dict) o None."""
    token = request.cookies.get(JWT_COOKIE)
    if not token:
        return None
    return verificar_token_jwt(token)


def requiere_login():
    return _obtener_usuario_jwt() is not None


def _usuario_actual():
    return _obtener_usuario_jwt() or {}


def requiere_admin():
    return _usuario_actual().get("rol") == "admin"


def es_mi_curso(id_curso):
    u = _usuario_actual()
    if u.get("rol") == "admin":
        return True
    if u.get("rol") != "moderador":
        return False
    return str(u.get("id_curso")) == str(id_curso)


def puede_ver_materia(id_curso):
    u = _usuario_actual()
    if u.get("rol") == "admin":
        return True
    return str(u.get("id_curso")) == str(id_curso)


def _ip_cliente():
    return request.headers.get("X-Forwarded-For", request.remote_addr)


@app.context_processor
def inyectar_usuario():
    u = _usuario_actual()
    if not u:
        return {}
    return {
        "session_avatar": u.get("avatar") or "uploads/avatares/no_avatar.png",
        "nombre": u.get("nombre"),
        "rol": u.get("rol"),
        "session_id_curso": u.get("id_curso"),
    }

# ====================== AUTH ======================

@app.route("/")
def index():
    return redirect(url_for("login_route"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        contraseña = request.form.get("contraseña", "")
        confirmar = request.form.get("confirmar_contraseña", "")
        email = request.form.get("email", "").strip()

        # Validar nombre de usuario
        ok_nombre, errores_nombre = validar_nombre_usuario(nombre)
        if not ok_nombre:
            return jsonify({"ok": False, "mensaje": "Usuario: " + " ".join(errores_nombre)})

        # Validar email
        ok_email, errores_email = validar_email(email)
        if not ok_email:
            return jsonify({"ok": False, "mensaje": "Email: " + " ".join(errores_email)})

        # Validar contraseña
        ok_pass, errores_pass = validar_contraseña(contraseña)
        if not ok_pass:
            return jsonify({"ok": False, "mensaje": "Contraseña: " + " ".join(errores_pass)})

        # Confirmar contraseña
        if contraseña != confirmar:
            return jsonify({"ok": False, "mensaje": "Las contraseñas no coinciden."})

        if registrar_usuario(nombre, contraseña, email):
            return jsonify({"ok": True, "mensaje": "¡Registro exitoso! Ahora iniciá sesión."})
        return jsonify({"ok": False, "mensaje": "El usuario o email ya está registrado."})
    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login_route():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        contraseña = request.form.get("contraseña", "")
        if not nombre or not contraseña:
            return jsonify({"ok": False, "mensaje": "Completá todos los campos."})
        usuario = login(nombre, contraseña)
        if usuario:
            token = generar_token_jwt(usuario)
            registrar_accion(usuario["id"], "login", "Inicio de sesión", _ip_cliente())
            resp = make_response(jsonify({
                "ok": True,
                "mensaje": f"¡Bienvenido {usuario['nombre']}!",
                "rol": usuario["rol"],
            }))
            resp.set_cookie(JWT_COOKIE, token, httponly=True, samesite="Lax", max_age=86400)
            return resp
        return jsonify({"ok": False, "mensaje": "Credenciales incorrectas."})
    return render_template("login.html")


@app.route("/logout")
def logout():
    u = _usuario_actual()
    if u:
        registrar_accion(u.get("id"), "logout", "Cierre de sesión", _ip_cliente())
    resp = make_response(redirect(url_for("login_route")))
    resp.delete_cookie(JWT_COOKIE)
    return resp


# ====================== RECUPERACIÓN DE CONTRASEÑA (RF-03) ======================

@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            return jsonify({"ok": False, "mensaje": "Ingresá tu email."})
        usuario = obtener_usuario_por_email(email)
        if not usuario:
            return jsonify({"ok": True, "mensaje": "Si el email está registrado, recibiste un enlace de recuperación."})
        token = generar_token(usuario["id"])
        if token:
            enlace = url_for("restablecer", token=token, _external=True)
            print(f"\n{'='*60}")
            print(f"RECUPERACIÓN DE CONTRASEÑA para {usuario['nombre']}")
            print(f"Enlace: {enlace}")
            print(f"{'='*60}\n")
            return jsonify({"ok": True, "mensaje": f"Enlace de recuperación: {enlace}", "enlace": enlace})
        return jsonify({"ok": True, "mensaje": "Si el email está registrado, recibiste un enlace de recuperación."})
    return render_template("recuperar.html")


@app.route("/restablecer/<token>", methods=["GET", "POST"])
def restablecer(token):
    from modulos.recuperacion import validar_token
    if request.method == "GET":
        id_usuario = validar_token(token)
        if not id_usuario:
            return render_template("restablecer.html", token_invalido=True)
        return render_template("restablecer.html", token=token, token_invalido=False)
    from modulos.validacion import validar_contraseña
    contraseña = request.form.get("contraseña", "")
    ok_pass, errores_pass = validar_contraseña(contraseña)
    if not ok_pass:
        return jsonify({"ok": False, "mensaje": "Contraseña: " + " ".join(errores_pass)})
    if resetear_contraseña(token, contraseña):
        return jsonify({"ok": True, "mensaje": "¡Contraseña actualizada! Ahora iniciá sesión."})
    return jsonify({"ok": False, "mensaje": "Token inválido o expirado."})


# ====================== PÁGINAS ======================

@app.route("/home")
def home():
    if not requiere_login():
        return redirect(url_for("login_route"))
    u = _usuario_actual()
    return render_template(
        "home.html",
        nombre=u.get("nombre"),
        rol=u.get("rol"),
        id_curso=u.get("id_curso"),
    )


@app.route("/admin")
def panel_admin():
    if not requiere_login():
        return redirect(url_for("login_route"))
    if not requiere_admin():
        return "No tenés permisos", 403
    u = _usuario_actual()
    return render_template("admin.html", nombre=u.get("nombre"))


@app.route("/admin/estadisticas")
def panel_estadisticas():
    if not requiere_login():
        return redirect(url_for("login_route"))
    if not requiere_admin():
        return "No tenés permisos", 403
    u = _usuario_actual()
    return render_template("estadisticas.html", nombre=u.get("nombre"))


@app.route("/descargar/<path:ruta>")
def descargar_archivo(ruta):
    """Endpoint que fuerza la descarga del archivo en vez de abrirlo."""
    if not requiere_login():
        return redirect(url_for("login_route"))
    seguro = os.path.basename(ruta)
    ruta_completa = os.path.join(app.static_folder, "uploads", "apuntes", seguro)
    if not os.path.isfile(ruta_completa):
        return "Archivo no encontrado", 404
    return send_file(ruta_completa, as_attachment=True)


@app.route("/curso/<int:id_curso>/estadisticas")
def estadisticas_curso(id_curso):
    if not requiere_login():
        return redirect(url_for("login_route"))
    if not es_mi_curso(id_curso):
        return "No tenés acceso a las estadísticas de este curso", 403
    curso = obtener_curso(id_curso)
    return render_template("estadisticas_curso.html", curso=curso)


@app.route("/curso/<int:id_curso>/stats", methods=["GET"])
def curso_stats_api(id_curso):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    if not es_mi_curso(id_curso):
        return jsonify({"ok": False, "mensaje": "Sin permisos"}), 403
    return jsonify({
        "ok": True,
        "resumen": stats_curso_resumen(id_curso),
        "por_estado": stats_curso_por_estado(id_curso),
        "materias": stats_curso_materias(id_curso),
        "ranking": stats_curso_ranking(id_curso),
        "por_fecha": stats_curso_por_fecha(id_curso),
        "top_valorados": stats_curso_top_valorados(id_curso),
    })


@app.route("/curso/<int:id_curso>")
def pagina_curso(id_curso):
    if not requiere_login():
        return redirect(url_for("login_route"))
    curso = obtener_curso(id_curso)
    if not curso:
        return "El curso no existe", 404
    puede_gestionar = es_mi_curso(id_curso)
    u = _usuario_actual()
    return render_template(
        "curso.html",
        curso=curso,
        puede_gestionar=puede_gestionar,
        rol=u.get("rol"),
        id_usuario_actual=u.get("id"),
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
    u = _usuario_actual()
    return render_template(
        "materia.html",
        materia=materia,
        curso=curso,
        puede_gestionar=puede_gestionar,
        rol=u.get("rol"),
    )


# ====================== PERFIL ======================

@app.route("/perfil")
def pagina_perfil():
    if not requiere_login():
        return redirect(url_for("login_route"))
    u = _usuario_actual()
    usuario = obtener_usuario(u["id"])
    return render_template("perfil.html", usuario=usuario, rol=u.get("rol"))


AVATARES_VALIDOS = [f"avatar{i}.png" for i in range(0, 10)]


@app.route("/perfil/actualizar", methods=["POST"])
def perfil_actualizar():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401

    u = _usuario_actual()
    nombre = request.form.get("nombre")
    avatar = request.form.get("avatar")

    avatar_ruta = None
    if avatar:
        if avatar not in AVATARES_VALIDOS:
            return jsonify({"ok": False, "mensaje": "Avatar no válido"}), 400
        avatar_ruta = f"uploads/avatares/{avatar}"

    if actualizar_perfil(u["id"], nombre, avatar_ruta):
        registrar_accion(u["id"], "perfil_actualizado", f"Nombre: {nombre}", _ip_cliente())
        u_fresco = obtener_usuario(u["id"])
        nuevo_token = _refrescar_token_curso(u_fresco, u_fresco.get("id_curso"))
        resp = jsonify({"ok": True, "mensaje": "Perfil actualizado"})
        resp.set_cookie(JWT_COOKIE, nuevo_token, httponly=True, samesite="Lax", max_age=86400)
        return resp
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
    u = _usuario_actual()
    if u.get("id_curso"):
        return jsonify({"ok": False, "mensaje": "Ya pertenecés a un curso. Salí primero."}), 400

    codigo = request.form.get("codigo", "").strip()
    if not codigo:
        return jsonify({"ok": False, "mensaje": "Ingresá un código de invitación"}), 400

    curso = obtener_curso_por_codigo(codigo)
    if not curso:
        return jsonify({"ok": False, "mensaje": "Código inválido o curso no encontrado"}), 404

    id_curso = curso["id"]
    if unir_usuario_a_curso(u["id"], id_curso):
        registrar_accion(u["id"], "curso_unido", f"Curso: {curso.get('anio')}° {curso.get('division')}° (ID: {id_curso})", _ip_cliente())
        token = _refrescar_token_curso(u, id_curso)
        resp = jsonify({"ok": True, "mensaje": "¡Te uniste al curso!", "id": id_curso})
        resp.set_cookie(JWT_COOKIE, token, httponly=True, samesite="Lax", max_age=86400)
        return resp
    return jsonify({"ok": False, "mensaje": "No se pudo unir"})


@app.route("/cursos/salir", methods=["POST"])
def cursos_salir():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    u = _usuario_actual()
    if u.get("rol") == "admin":
        return jsonify({"ok": False, "mensaje": "El admin no puede salir de un curso"}), 400
    if not u.get("id_curso"):
        return jsonify({"ok": False, "mensaje": "No estás en ningún curso"}), 400

    resultado = salir_de_curso(u["id"])
    if resultado == False:
        return jsonify({"ok": False, "mensaje": "Sos el creador del curso. Eliminalo primero."}), 400
    if resultado:
        registrar_accion(u["id"], "curso_salido", None, _ip_cliente())
        token = _refrescar_token_curso(u, None, rol_forzado="alumno")
        resp = jsonify({"ok": True, "mensaje": "Saliste del curso"})
        resp.set_cookie(JWT_COOKIE, token, httponly=True, samesite="Lax", max_age=86400)
        return resp
    return jsonify({"ok": False, "mensaje": "No se pudo salir del curso"})


def _refrescar_token_curso(usuario_actual, id_curso, rol_forzado=None):
    """Genera un nuevo JWT con id_curso y rol actualizados."""
    payload = {
        "id": usuario_actual["id"],
        "nombre": usuario_actual["nombre"],
        "rol": rol_forzado or usuario_actual.get("rol"),
        "id_curso": id_curso,
        "avatar": usuario_actual.get("avatar"),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        "iat": datetime.datetime.utcnow(),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")


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
    u = _usuario_actual()
    if u.get("id_curso"):
        return jsonify({"ok": False, "mensaje": "Ya tenés un curso asignado"}), 400

    anio = request.form.get("anio")
    division = request.form.get("division")

    resultado = crear_curso(anio, division, u["id"])
    if resultado:
        nuevo_id = resultado["id"]
        registrar_accion(u["id"], "curso_creado", f"Curso: {anio}° {division}° (ID: {nuevo_id})", _ip_cliente())
        token = _refrescar_token_curso(u, nuevo_id, rol_forzado="moderador")
        resp = jsonify({
            "ok": True,
            "mensaje": "¡Curso creado! Ahora sos moderador.",
            "id": nuevo_id,
        })
        resp.set_cookie(JWT_COOKIE, token, httponly=True, samesite="Lax", max_age=86400)
        return resp
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
        registrar_accion(_usuario_actual()["id"], "curso_editado", f"Curso ID: {id_curso}", _ip_cliente())
        return jsonify({"ok": True, "mensaje": "Curso actualizado"})
    return jsonify({"ok": False, "mensaje": "No se pudo actualizar"})


@app.route("/cursos/eliminar/<int:id_curso>", methods=["POST"])
def cursos_eliminar(id_curso):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    u = _usuario_actual()
    if not requiere_admin() and not es_mi_curso(id_curso):
        return jsonify({"ok": False, "mensaje": "No tenés permisos para borrar este curso"}), 403
    if not requiere_admin():
        curso = obtener_curso(id_curso)
        if not curso or curso["id_creador"] != u["id"]:
            return jsonify({"ok": False, "mensaje": "Solo el creador o un admin pueden borrar el curso"}), 403
    if eliminar_curso(id_curso, UPLOAD_APUNTES):
        registrar_accion(u["id"], "curso_eliminado", f"Curso ID: {id_curso}", _ip_cliente())
        if not requiere_admin():
            token = _refrescar_token_curso(u, None, rol_forzado="alumno")
            resp = jsonify({"ok": True, "mensaje": "Curso eliminado"})
            resp.set_cookie(JWT_COOKIE, token, httponly=True, samesite="Lax", max_age=86400)
            return resp
        return jsonify({"ok": True, "mensaje": "Curso eliminado"})
    return jsonify({"ok": False, "mensaje": "No se pudo eliminar"})

@app.route("/cursos/<int:id_curso>/ascender", methods=["POST"])
def curso_ascender(id_curso):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    if not es_mi_curso(id_curso):
        return jsonify({"ok": False, "mensaje": "No gestionás este curso"}), 403

    id_destino = request.form.get("id_usuario")
    if not id_destino:
        return jsonify({"ok": False, "mensaje": "Falta el usuario"}), 400

    if ascender_a_moderador(id_destino, id_curso):
        registrar_accion(_usuario_actual()["id"], "usuario_ascendido", f"Usuario {id_destino} → moderador en curso {id_curso}", _ip_cliente())
        return jsonify({"ok": True, "mensaje": "¡Ahora es moderador!"})
    return jsonify({"ok": False, "mensaje": "No se pudo ascender (¿ya es moderador?)"})

@app.route("/cursos/<int:id_curso>/descender", methods=["POST"])
def curso_descender(id_curso):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    if not es_mi_curso(id_curso):
        return jsonify({"ok": False, "mensaje": "No gestionás este curso"}), 403

    u = _usuario_actual()
    curso = obtener_curso(id_curso)
    if not curso:
        return jsonify({"ok": False, "mensaje": "Curso no encontrado"}), 404
    if u["id"] != curso["id_creador"]:
        return jsonify({"ok": False, "mensaje": "Solo el creador del curso puede quitar moderadores"}), 403

    id_destino = request.form.get("id_usuario")
    if not id_destino:
        return jsonify({"ok": False, "mensaje": "Falta el usuario"}), 400

    if descender_a_alumno(id_destino, id_curso, curso["id_creador"]):
        registrar_accion(u["id"], "usuario_descendido", f"Usuario {id_destino} → alumno en curso {id_curso}", _ip_cliente())
        return jsonify({"ok": True, "mensaje": "Ahora es alumno"})
    return jsonify({"ok": False, "mensaje": "No se pudo descender (¿es el creador?)"})

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
        registrar_accion(_usuario_actual()["id"], "materia_creada", f"Materia: {nombre} en curso {id_curso}", _ip_cliente())
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
        registrar_accion(_usuario_actual()["id"], "materia_editada", f"Materia ID: {id_materia}", _ip_cliente())
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
        registrar_accion(_usuario_actual()["id"], "materia_eliminada", f"Materia ID: {id_materia}", _ip_cliente())
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

    u = _usuario_actual()
    gestiona = es_mi_curso(materia["id_curso"])
    apuntes = listar_apuntes_por_materia(id_materia, id_usuario=u["id"], solo_aprobados=not gestiona)
    return jsonify({
        "ok": True,
        "apuntes": apuntes,
        "id_usuario": u["id"],
        "puede_gestionar": gestiona,
    })


@app.route("/apuntes/crear", methods=["POST"])
def apuntes_crear():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    u = _usuario_actual()

    id_materia = request.form.get("id_materia")
    materia = obtener_materia(id_materia) if id_materia else None
    if not materia:
        return jsonify({"ok": False, "mensaje": "Materia inválida"}), 404
    if not puede_ver_materia(materia["id_curso"]):
        return jsonify({"ok": False, "mensaje": "No pertenecés a este curso"}), 403

    titulo = request.form.get("titulo", "").strip()
    descripcion = request.form.get("descripcion", "")
    archivos = request.files.getlist("archivo")

    if not titulo:
        return jsonify({"ok": False, "mensaje": "El título es obligatorio"}), 400

    archivos = [a for a in archivos if a and a.filename]

    if not archivos:
        return jsonify({"ok": False, "mensaje": "Debés subir al menos un archivo"}), 400

    for archivo in archivos:
        if not extension_ok(archivo.filename, EXT_APUNTES):
            return jsonify({"ok": False, "mensaje": f"Tipo de archivo no permitido: {archivo.filename}"}), 400

    id_apunte = crear_apunte(titulo, descripcion, u["id"], materia["id_curso"], id_materia, u.get("rol", "alumno"))
    if not id_apunte:
        return jsonify({"ok": False, "mensaje": "Error al crear el apunte"}), 500

    for archivo in archivos:
        nombre_seguro = secure_filename(f"apunte{id_apunte}_{archivo.filename}")
        archivo.save(os.path.join(UPLOAD_APUNTES, nombre_seguro))
        tipo = archivo.filename.rsplit(".", 1)[1].lower()
        agregar_archivo_apunte(id_apunte, f"uploads/apuntes/{nombre_seguro}", tipo)

    registrar_accion(u["id"], "apunte_creado", f"Apunte '{titulo}' (ID: {id_apunte})", _ip_cliente())
    if u.get("rol") in ("moderador", "admin"):
        return jsonify({"ok": True, "mensaje": "¡Apunte subido y publicado!", "id": id_apunte})
    return jsonify({"ok": True, "mensaje": "¡Apunte subido! Queda pendiente de aprobación.", "id": id_apunte})

@app.route("/apuntes/eliminar/<int:id_apunte>", methods=["POST"])
def apuntes_eliminar(id_apunte):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    u = _usuario_actual()
    apunte = obtener_apunte(id_apunte)
    if not apunte:
        return jsonify({"ok": False, "mensaje": "El apunte no existe"}), 404

    es_autor = apunte["id_usuario_creador"] == u["id"]
    if not (es_autor or es_mi_curso(apunte["id_curso"])):
        return jsonify({"ok": False, "mensaje": "No podés borrar este apunte"}), 403

    if eliminar_apunte(id_apunte, UPLOAD_APUNTES):
        registrar_accion(u["id"], "apunte_eliminado", f"Apunte ID: {id_apunte}", _ip_cliente())
        return jsonify({"ok": True, "mensaje": "Apunte eliminado"})
    return jsonify({"ok": False, "mensaje": "No se pudo eliminar"})

@app.route("/buscar", methods=["GET"])
def buscar():
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401

    u = _usuario_actual()
    id_curso = u.get("id_curso")
    if not id_curso:
        return jsonify({"ok": False, "mensaje": "No pertenecés a ningún curso", "apuntes": []})

    texto = request.args.get("q", "")
    orden = request.args.get("orden", "recientes")
    materia_id = request.args.get("materia_id")
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")

    if materia_id:
        try:
            materia_id = int(materia_id)
        except (ValueError, TypeError):
            materia_id = None

    apuntes = buscar_apuntes(id_curso, texto, orden, materia_id, fecha_desde, fecha_hasta)
    return jsonify({"ok": True, "apuntes": apuntes})

# ====================== VALORACIONES (RF-07) ======================

@app.route("/apuntes/<int:id_apunte>/calificar", methods=["POST"])
def apunte_calificar(id_apunte):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    apunte = obtener_apunte(id_apunte)
    if not apunte:
        return jsonify({"ok": False, "mensaje": "El apunte no existe"}), 404
    if not puede_ver_materia(apunte["id_curso"]):
        return jsonify({"ok": False, "mensaje": "Sin acceso"}), 403

    u = _usuario_actual()
    try:
        estrellas = int(request.form.get("estrellas"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "mensaje": "Calificación inválida"}), 400

    if calificar_apunte(u["id"], id_apunte, estrellas):
        promedio, cantidad = obtener_promedio(id_apunte)
        return jsonify({
            "ok": True,
            "mensaje": "¡Gracias por tu valoración!",
            "promedio": promedio,
            "cantidad": cantidad,
            "mi_calificacion": estrellas,
        })
    return jsonify({"ok": False, "mensaje": "No se pudo calificar"})


@app.route("/apuntes/<int:id_apunte>/guardar", methods=["POST"])
def apunte_guardar(id_apunte):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    apunte = obtener_apunte(id_apunte)
    if not apunte:
        return jsonify({"ok": False, "mensaje": "El apunte no existe"}), 404
    if not puede_ver_materia(apunte["id_curso"]):
        return jsonify({"ok": False, "mensaje": "Sin acceso"}), 403

    u = _usuario_actual()
    resultado = alternar_guardado(u["id"], id_apunte)
    if resultado == "guardado":
        return jsonify({"ok": True, "mensaje": "Apunte guardado", "estado": "guardado"})
    elif resultado == "quitado":
        return jsonify({"ok": True, "mensaje": "Apunte quitado de guardados", "estado": "quitado"})
    return jsonify({"ok": False, "mensaje": "No se pudo procesar"})


# ====================== ME GUSTA (RF-07) ======================

@app.route("/apuntes/<int:id_apunte>/me-gusta", methods=["POST"])
def apunte_me_gusta(id_apunte):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    apunte = obtener_apunte(id_apunte)
    if not apunte:
        return jsonify({"ok": False, "mensaje": "El apunte no existe"}), 404
    if not puede_ver_materia(apunte["id_curso"]):
        return jsonify({"ok": False, "mensaje": "Sin acceso"}), 403

    u = _usuario_actual()
    resultado = alternar_me_gusta(u["id"], id_apunte)
    if resultado == "gustado":
        cantidad = contar_me_gusta(id_apunte)
        return jsonify({"ok": True, "mensaje": "¡Me gusta!", "estado": "gustado", "cantidad": cantidad})
    elif resultado == "quitado":
        cantidad = contar_me_gusta(id_apunte)
        return jsonify({"ok": True, "mensaje": "Like quitado", "estado": "quitado", "cantidad": cantidad})
    return jsonify({"ok": False, "mensaje": "No se pudo procesar"})


@app.route("/guardados")
def pagina_guardados():
    if not requiere_login():
        return redirect(url_for("login_route"))
    u = _usuario_actual()
    apuntes = listar_guardados(u["id"])
    return render_template("guardados.html", apuntes=apuntes)

# ====================== MODERACIÓN DE APUNTES (RF-08) ======================

@app.route("/cursos/<int:id_curso>/pendientes", methods=["GET"])
def apuntes_pendientes(id_curso):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    if not es_mi_curso(id_curso):
        return jsonify({"ok": False, "mensaje": "No gestionás este curso"}), 403
    return jsonify({"ok": True, "apuntes": listar_apuntes_pendientes(id_curso)})


@app.route("/apuntes/<int:id_apunte>/aprobar", methods=["POST"])
def apunte_aprobar(id_apunte):
    return _moderar_apunte(id_apunte, "aprobado")


@app.route("/apuntes/<int:id_apunte>/rechazar", methods=["POST"])
def apunte_rechazar(id_apunte):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    apunte = obtener_apunte(id_apunte)
    if not apunte:
        return jsonify({"ok": False, "mensaje": "El apunte no existe"}), 404
    if not es_mi_curso(apunte["id_curso"]):
        return jsonify({"ok": False, "mensaje": "No podés moderar este apunte"}), 403

    if eliminar_apunte(id_apunte, UPLOAD_APUNTES):
        registrar_accion(_usuario_actual()["id"], "apunte_rechazado", f"Apunte ID: {id_apunte}", _ip_cliente())
        return jsonify({"ok": True, "mensaje": "Apunte rechazado y eliminado"})
    return jsonify({"ok": False, "mensaje": "No se pudo eliminar"})

def _moderar_apunte(id_apunte, estado):
    if not requiere_login():
        return jsonify({"ok": False, "mensaje": "No autenticado"}), 401
    apunte = obtener_apunte(id_apunte)
    if not apunte:
        return jsonify({"ok": False, "mensaje": "El apunte no existe"}), 404
    if not es_mi_curso(apunte["id_curso"]):
        return jsonify({"ok": False, "mensaje": "No podés moderar este apunte"}), 403
    if cambiar_estado_apunte(id_apunte, estado):
        registrar_accion(_usuario_actual()["id"], f"apunte_{estado}", f"Apunte ID: {id_apunte}", _ip_cliente())
        return jsonify({"ok": True, "mensaje": f"Apunte {estado}"})
    return jsonify({"ok": False, "mensaje": "No se pudo actualizar"})

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
        registrar_accion(_usuario_actual()["id"], "usuario_eliminado", f"Usuario ID: {id_usuario}", _ip_cliente())
        return jsonify({"ok": True, "mensaje": "Usuario eliminado"})
    return jsonify({"ok": False, "mensaje": "No se pudo eliminar"})


@app.route("/admin/usuarios/<int:id_usuario>/estado", methods=["POST"])
def admin_cambiar_estado(id_usuario):
    if not requiere_admin():
        return jsonify({"ok": False, "mensaje": "No tenés permisos"}), 403
    nuevo_estado = request.form.get("estado")
    if not nuevo_estado:
        return jsonify({"ok": False, "mensaje": "Falta el estado"}), 400
    if cambiar_estado_usuario(id_usuario, nuevo_estado):
        registrar_accion(_usuario_actual()["id"], "usuario_estado_cambiado",
                         f"Usuario {id_usuario} → {nuevo_estado}", _ip_cliente())
        return jsonify({"ok": True, "mensaje": f"Usuario {'activado' if nuevo_estado == 'activo' else 'bloqueado'}"})
    return jsonify({"ok": False, "mensaje": "No se pudo cambiar el estado"})


@app.route("/admin/usuarios/<int:id_usuario>/rol", methods=["POST"])
def admin_cambiar_rol(id_usuario):
    if not requiere_admin():
        return jsonify({"ok": False, "mensaje": "No tenés permisos"}), 403
    nuevo_rol = request.form.get("rol")
    if not nuevo_rol:
        return jsonify({"ok": False, "mensaje": "Falta el rol"}), 400
    if cambiar_rol_usuario(id_usuario, nuevo_rol):
        registrar_accion(_usuario_actual()["id"], "rol_cambiado",
                         f"Usuario {id_usuario} → rol {nuevo_rol}", _ip_cliente())
        return jsonify({"ok": True, "mensaje": f"Rol cambiado a {nuevo_rol}"})
    return jsonify({"ok": False, "mensaje": "No se pudo cambiar el rol"})


# ====================== ESTADÍSTICAS (RF-10) ======================

@app.route("/admin/stats", methods=["GET"])
def admin_stats():
    if not requiere_admin():
        return jsonify({"ok": False, "mensaje": "No tenés permisos"}), 403
    return jsonify({
        "ok": True,
        "generales": estadisticas_generales(),
        "apuntes_valorados": apuntes_mas_valorados(),
        "materias_consultadas": materias_mas_consultadas(),
        "ranking": ranking_colaboradores(),
        "por_estado": apuntes_por_estado(),
        "por_fecha": apuntes_por_fecha(),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
