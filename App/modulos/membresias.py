"""
Gestión de la relación muchos-a-muchos Usuario ↔ Curso.
Reemplaza el antiguo campo usuario.id_curso.
"""
import pymysql
from db.conexion import obtener_conexion


def listar_cursos_de_usuario(id_usuario):
    """Devuelve todos los cursos a los que pertenece el usuario."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT c.id, c.anio, c.division, c.id_creador, c.codigo_invitacion,
                   uc.rol_curso, uc.fecha_union,
                   cr.nombre AS creador,
                   (c.id_creador = %s) AS soy_creador
            FROM usuario_curso uc
            JOIN Curso c ON uc.id_curso = c.id
            LEFT JOIN Usuario cr ON c.id_creador = cr.id
            WHERE uc.id_usuario = %s
            ORDER BY c.anio, c.division
        """, (id_usuario, id_usuario))
        cursos = cursor.fetchall()
        for c in cursos:
            c["soy_creador"] = bool(c["soy_creador"])
        return cursos
    except Exception as e:
        print(f"Error al listar cursos del usuario: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def pertenece_a_curso(id_usuario, id_curso):
    """True si el usuario es miembro del curso."""
    if not id_usuario or not id_curso:
        return False
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM usuario_curso WHERE id_usuario = %s AND id_curso = %s",
            (id_usuario, id_curso),
        )
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error en pertenece_a_curso: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def rol_en_curso(id_usuario, id_curso):
    """Devuelve 'moderador', 'alumno' o None si no pertenece."""
    if not id_usuario or not id_curso:
        return None
    conn = obtener_conexion()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT rol_curso FROM usuario_curso WHERE id_usuario = %s AND id_curso = %s",
            (id_usuario, id_curso),
        )
        fila = cursor.fetchone()
        return fila[0] if fila else None
    except Exception as e:
        print(f"Error en rol_en_curso: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def agregar_miembro(id_usuario, id_curso, rol_curso="alumno"):
    """
    Agrega un usuario al curso. Devuelve:
      True      -> agregado
      "duplicado" -> ya pertenecía
      False     -> error / curso inexistente
    """
    if rol_curso not in ("alumno", "moderador"):
        return False
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM Curso WHERE id = %s", (id_curso,))
        if not cursor.fetchone():
            return False

        cursor.execute(
            "SELECT 1 FROM usuario_curso WHERE id_usuario = %s AND id_curso = %s",
            (id_usuario, id_curso),
        )
        if cursor.fetchone():
            return "duplicado"

        cursor.execute("""
            INSERT INTO usuario_curso (id_usuario, id_curso, rol_curso)
            VALUES (%s, %s, %s)
        """, (id_usuario, id_curso, rol_curso))
        conn.commit()
        return True
    except pymysql.err.IntegrityError:
        conn.rollback()
        return "duplicado"
    except Exception as e:
        print(f"Error al agregar miembro: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def quitar_miembro(id_usuario, id_curso):
    """
    Saca al usuario del curso. Devuelve:
      True         -> salió
      "es_creador" -> es el creador (debe eliminar el curso)
      False        -> no pertenecía / error
    """
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT id_creador FROM Curso WHERE id = %s", (id_curso,))
        curso = cursor.fetchone()
        if curso and curso["id_creador"] == id_usuario:
            return "es_creador"

        cursor.execute(
            "DELETE FROM usuario_curso WHERE id_usuario = %s AND id_curso = %s",
            (id_usuario, id_curso),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al quitar miembro: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def cambiar_rol_en_curso(id_usuario, id_curso, nuevo_rol):
    """Cambia el rol del usuario dentro de un curso puntual."""
    if nuevo_rol not in ("alumno", "moderador"):
        return False
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE usuario_curso SET rol_curso = %s
            WHERE id_usuario = %s AND id_curso = %s
        """, (nuevo_rol, id_usuario, id_curso))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al cambiar rol en curso: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def listar_miembros_curso(id_curso):
    """Todos los miembros de un curso con su rol dentro de él."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT u.id, u.nombre, u.avatar, u.rol AS rol_global,
                   uc.rol_curso, uc.fecha_union
            FROM usuario_curso uc
            JOIN Usuario u ON uc.id_usuario = u.id
            WHERE uc.id_curso = %s
            ORDER BY uc.rol_curso DESC, u.nombre
        """, (id_curso,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al listar miembros: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def ids_cursos_de_usuario(id_usuario):
    """Lista plana de IDs (útil para filtros IN (...))."""
    return [c["id"] for c in listar_cursos_de_usuario(id_usuario)]