import pymysql
from db.conexion import obtener_conexion


def crear_apunte(titulo, descripcion, id_usuario, id_curso, id_materia):
    if not id_materia or not id_curso or not titulo:
        return False
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Apunte(titulo, descripcion, id_usuario_creador, id_curso, id_materia, estado)
            VALUES (%s, %s, %s, %s, %s, 'pendiente')
        """, (titulo, descripcion, id_usuario, id_curso, id_materia))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al crear apunte: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def agregar_archivo_apunte(id_apunte, ruta, tipo):
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Archivo_Apunte(ruta, tipo, id_apunte)
            VALUES (%s, %s, %s)
        """, (ruta, tipo, id_apunte))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al agregar archivo: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def _traer_archivos(cursor, apuntes):
    """Adjunta la lista de archivos a cada apunte."""
    for ap in apuntes:
        cursor.execute("SELECT id, ruta, tipo FROM Archivo_Apunte WHERE id_apunte = %s", (ap["id"],))
        ap["archivos"] = cursor.fetchall()
    return apuntes


def listar_apuntes_por_materia(id_materia, solo_aprobados=True):
    """Lista apuntes de una materia. Si solo_aprobados, filtra los 'aprobado'."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        sql = """
            SELECT a.id, a.titulo, a.descripcion, a.estado, a.fecha_subida,
                   a.id_usuario_creador, u.nombre AS autor, u.avatar AS autor_avatar
            FROM Apunte a
            LEFT JOIN Usuario u ON a.id_usuario_creador = u.id
            WHERE a.id_materia = %s
        """
        if solo_aprobados:
            sql += " AND a.estado = 'aprobado'"
        sql += " ORDER BY a.fecha_subida DESC"
        cursor.execute(sql, (id_materia,))
        return _traer_archivos(cursor, cursor.fetchall())
    except Exception as e:
        print(f"Error al listar apuntes: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def listar_apuntes_pendientes(id_curso):
    """Apuntes pendientes de un curso (para el moderador)."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT a.id, a.titulo, a.descripcion, a.estado, a.fecha_subida,
                   a.id_materia, m.nombre AS materia,
                   u.nombre AS autor, u.avatar AS autor_avatar
            FROM Apunte a
            LEFT JOIN Usuario u ON a.id_usuario_creador = u.id
            LEFT JOIN Materia m ON a.id_materia = m.id
            WHERE a.id_curso = %s AND a.estado = 'pendiente'
            ORDER BY a.fecha_subida ASC
        """, (id_curso,))
        return _traer_archivos(cursor, cursor.fetchall())
    except Exception as e:
        print(f"Error al listar pendientes: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def cambiar_estado_apunte(id_apunte, estado):
    if estado not in ("aprobado", "rechazado", "pendiente"):
        return False
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Apunte SET estado = %s WHERE id = %s", (estado, id_apunte))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al cambiar estado: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def obtener_apunte(id_apunte):
    conn = obtener_conexion()
    if not conn:
        return None
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT a.id, a.titulo, a.descripcion, a.estado,
                   a.id_usuario_creador, a.id_curso, a.id_materia
            FROM Apunte a WHERE a.id = %s
        """, (id_apunte,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error al obtener apunte: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def eliminar_apunte(id_apunte):
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Archivo_Apunte WHERE id_apunte = %s", (id_apunte,))
        cursor.execute("DELETE FROM Apunte WHERE id = %s", (id_apunte,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al eliminar apunte: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()