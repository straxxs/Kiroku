import os
import pymysql
import bcrypt
import jwt
import datetime
import secrets
from db.conexion import obtener_conexion

JWT_SECRET = os.environ.get("KIROKU_JWT_SECRET", "kiroku_secret_key_2026_mitin_f8a2c3d5e7g9h1j3k5l7m9n1p3r5t7v9x1z")
JWT_EXPIRACION_HORAS = 24


def hashear_contraseña(contraseña):
    """Hashea una contraseña con bcrypt."""
    return bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verificar_contraseña(contraseña, hash_almacenado):
    """Verifica una contraseña contra su hash bcrypt."""
    try:
        if isinstance(hash_almacenado, str):
            hash_almacenado = hash_almacenado.encode('utf-8')
        return bcrypt.checkpw(contraseña.encode('utf-8'), hash_almacenado)
    except Exception:
        return False


def es_hash_bcrypt(hash_str):
    """Detecta si un hash es bcrypt (empieza con $2b$)."""
    return isinstance(hash_str, str) and hash_str.startswith("$2b$")


def migrar_hash_si_es_necesario(contraseña, hash_viejo, id_usuario):
    """Si el hash es SHA-256 legacy, lo migra a bcrypt. Devuelve True si la pass es correcta."""
    if es_hash_bcrypt(hash_viejo):
        return verificar_contraseña(contraseña, hash_viejo)

    import hashlib
    hash_sha = hashlib.sha256(contraseña.encode('utf-8')).hexdigest()
    if hash_sha == hash_viejo:
        nuevo_hash = hashear_contraseña(contraseña)
        conn = obtener_conexion()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE usuario SET contrasena = %s WHERE id = %s",
                               (nuevo_hash, id_usuario))
                conn.commit()
            except Exception:
                conn.rollback()
            finally:
                cursor.close()
                conn.close()
        return True
    return False


def generar_token_jwt(usuario):
    """Genera un JWT con los datos del usuario."""
    payload = {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "rol": usuario["rol"],
        "id_curso": usuario.get("id_curso"),
        "avatar": usuario.get("avatar"),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRACION_HORAS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verificar_token_jwt(token):
    """Verifica y decodifica un JWT. Devuelve el payload o None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def registrar_usuario(nombre, contraseña, email):
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()

    if not nombre or not contraseña or not email:
        return False

    try:
        sql = "INSERT INTO usuario(nombre, contrasena, rol, email) VALUES(%s, %s, %s, %s)"
        cursor.execute(sql, (nombre, hashear_contraseña(contraseña), "alumno", email))
        conn.commit()
        return True
    except pymysql.err.IntegrityError:
        print("El usuario o email ya existe")
        return False
    except Exception as e:
        print(f"Error en el registro: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def login(nombre_o_email, contraseña):
    conn = obtener_conexion()
    if not conn:
        return None, "error"
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        sql = "SELECT * FROM usuario WHERE nombre = %s OR email = %s"
        cursor.execute(sql, (nombre_o_email, nombre_o_email))
        usuario = cursor.fetchone()

        if not usuario:
            return None, "no_existe"

        if usuario.get("estado") == "bloqueado":
            return None, "bloqueado"

        if migrar_hash_si_es_necesario(contraseña, usuario["contrasena"], usuario["id"]):
            return usuario, "ok"
        return None, "clave"
    except Exception as e:
        print(f"Error en login: {e}")
        return None, "error"
    finally:
        cursor.close()
        conn.close()
