import pymysql
import hashlib
from db.conexion import obtener_conexion

def hashear_contraseña(contraseña):
    h = hashlib.sha256()
    h.update(contraseña.encode('utf-8'))
    return h.hexdigest()

def registrar_usuario(nombre, contraseña):
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()

    if not nombre or not contraseña:
        return False

    try:
        sql = "INSERT INTO usuario(nombre, contrasena, rol) values(%s,%s,%s)"
        cursor.execute(sql, (nombre, hashear_contraseña(contraseña), "alumno"))
        conn.commit()
        return True
    except pymysql.err.IntegrityError:
        print("El usuario ya existe")
        return False
    
    except Exception as e:
        print(f"Error en el registro{e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def login(nombre, contraseña):
    conn= obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        sql = "SELECT * FROM usuario WHERE nombre = %s"
        cursor.execute(sql, (nombre,))
        usuario = cursor.fetchone()

        if usuario and usuario["contrasena"] == hashear_contraseña(contraseña):
            return usuario
        else:
            return False

    except Exception as e:
        print(f"Error en login: {e}")
        return False

    finally:
        cursor.close()
        conn.close()