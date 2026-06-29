import pymysql
from db.conexion import obtener_conexion


def crear_curso(anio, division, id_creador):
    """Crea el curso, asigna el curso al usuario y lo vuelve moderador."""
    if not anio or not division:
        return False

    conn = obtener_conexion()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Curso(anio, division, id_creador) VALUES (%s, %s, %s)",
            (anio, division, id_creador),
        )
        nuevo_id = cursor.lastrowid

        cursor.execute(
            "UPDATE Usuario SET id_curso = %s, rol = 'moderador' WHERE id = %s",
            (nuevo_id, id_creador),
        )

        conn.commit()
        return nuevo_id
    except Exception as e:
        print(f"Error al crear curso: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def editar_curso(id_curso, anio, division):
    conn = obtener_conexion()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Curso SET anio = %s, division = %s WHERE id = %s",
            (anio, division, id_curso),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al editar curso: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def listar_cursos():
    conn = obtener_conexion()
    if not conn:
        return []

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT c.id, c.anio, c.division, c.id_creador, u.nombre AS creador
            FROM Curso c
            LEFT JOIN Usuario u ON c.id_creador = u.id
            ORDER BY c.anio, c.division
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al listar cursos: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def obtener_curso(id_curso):
    conn = obtener_conexion()
    if not conn:
        return None

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT c.id, c.anio, c.division, c.id_creador, u.nombre AS creador
            FROM Curso c
            LEFT JOIN Usuario u ON c.id_creador = u.id
            WHERE c.id = %s
        """, (id_curso,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error al obtener curso: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def listar_alumnos_curso(id_curso):
    conn = obtener_conexion()
    if not conn:
        return []

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT id, nombre, rol
            FROM Usuario
            WHERE id_curso = %s
            ORDER BY rol DESC, nombre
        """, (id_curso,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al listar alumnos: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def eliminar_curso(id_curso):
    conn = obtener_conexion()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # Soltamos a los usuarios del curso para no romper su FK
        cursor.execute("UPDATE Usuario SET id_curso = NULL WHERE id_curso = %s", (id_curso,))
        cursor.execute("DELETE FROM Curso WHERE id = %s", (id_curso,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al eliminar curso: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()