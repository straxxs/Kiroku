import pymysql
from db.conexion import obtener_conexion


def listar_usuarios():
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT u.id, u.nombre, u.rol, u.id_curso, u.avatar,
                c.anio, c.division
            FROM Usuario u
            LEFT JOIN Curso c ON u.id_curso = c.id
            ORDER BY u.nombre
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al listar usuarios: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def eliminar_usuario(id_usuario):
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Usuario WHERE id = %s", (id_usuario,))
        conn.commit()
        return cursor.rowcount > 0
    except pymysql.err.IntegrityError:
        print("No se puede eliminar el usuario (tiene datos asociados)")
        conn.rollback()
        return False
    except Exception as e:
        print(f"Error al eliminar usuario: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# ---------- NUEVO: gestión de perfil ----------
def obtener_usuario(id_usuario):
    conn = obtener_conexion()
    if not conn:
        return None
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT u.id, u.nombre, u.rol, u.id_curso, u.avatar,
                c.anio, c.division
            FROM Usuario u
            LEFT JOIN Curso c ON u.id_curso = c.id
            WHERE u.id = %s
        """, (id_usuario,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error al obtener usuario: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def actualizar_perfil(id_usuario, nombre=None, avatar=None):
    """Actualiza nombre y/o avatar. Devuelve True/False."""
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        campos = []
        valores = []
        if nombre and nombre.strip():
            campos.append("nombre = %s")
            valores.append(nombre.strip())
        if avatar is not None:
            campos.append("avatar = %s")
            valores.append(avatar)

        if not campos:
            return False

        valores.append(id_usuario)
        sql = f"UPDATE Usuario SET {', '.join(campos)} WHERE id = %s"
        cursor.execute(sql, tuple(valores))
        conn.commit()
        return True
    except pymysql.err.IntegrityError:
        print("Ese nombre de usuario ya está en uso")
        conn.rollback()
        return False
    except Exception as e:
        print(f"Error al actualizar perfil: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def ascender_a_moderador(id_usuario, id_curso):
    """Vuelve moderador a un alumno, solo si pertenece al curso indicado."""
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Usuario SET rol = 'moderador' WHERE id = %s AND id_curso = %s AND rol = 'alumno'",
            (id_usuario, id_curso),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al ascender a moderador: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()