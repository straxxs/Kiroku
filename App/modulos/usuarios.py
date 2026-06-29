import pymysql
from db.conexion import obtener_conexion


def listar_usuarios():
    conn = obtener_conexion()
    if not conn:
        return []

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT u.id, u.nombre, u.apellido, u.rol, u.id_curso, c.anio, c.division
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
        print("No se puede eliminar el usuario porque tiene datos asociados")
        return False
    except Exception as e:
        print(f"Error al eliminar usuario: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()