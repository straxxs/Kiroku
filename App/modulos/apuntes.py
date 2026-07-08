import os
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


def listar_apuntes_por_materia(id_materia, id_usuario=None, solo_aprobados=True):
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        sql = """
            SELECT a.id, a.titulo, a.descripcion, a.estado, a.fecha_subida,
                a.id_usuario_creador, u.nombre AS autor, u.avatar AS autor_avatar,
                IFNULL(AVG(cal.calificacion), 0) AS promedio,
                COUNT(DISTINCT cal.id) AS cant_calificaciones
            FROM Apunte a
            LEFT JOIN Usuario u ON a.id_usuario_creador = u.id
            LEFT JOIN Calificacion cal ON cal.id_apunte = a.id
            WHERE a.id_materia = %s
        """
        if solo_aprobados:
            sql += " AND a.estado = 'aprobado'"
        sql += " GROUP BY a.id ORDER BY a.fecha_subida DESC"
        cursor.execute(sql, (id_materia,))
        apuntes = cursor.fetchall()

        for ap in apuntes:
            ap["promedio"] = round(float(ap["promedio"]), 1)
            # Archivos
            cursor.execute("SELECT id, ruta, tipo FROM Archivo_Apunte WHERE id_apunte = %s", (ap["id"],))
            ap["archivos"] = cursor.fetchall()
            # Datos del usuario actual (si se pasa)
            if id_usuario:
                cursor.execute(
                    "SELECT 1 FROM Guardado WHERE id_alumno = %s AND id_apunte = %s",
                    (id_usuario, ap["id"]),
                )
                ap["guardado"] = cursor.fetchone() is not None
                cursor.execute(
                    "SELECT calificacion FROM Calificacion WHERE id_alumno = %s AND id_apunte = %s",
                    (id_usuario, ap["id"]),
                )
                fila = cursor.fetchone()
                ap["mi_calificacion"] = fila["calificacion"] if fila else 0
            else:
                ap["guardado"] = False
                ap["mi_calificacion"] = 0
        return apuntes
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


def eliminar_apunte(id_apunte, carpeta_apuntes):
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # Rutas para borrar del disco
        cursor.execute("SELECT ruta FROM Archivo_Apunte WHERE id_apunte = %s", (id_apunte,))
        rutas = [fila["ruta"] for fila in cursor.fetchall()]

        # Borrar dependencias primero (FKs)
        cursor.execute("DELETE FROM Calificacion WHERE id_apunte = %s", (id_apunte,))
        cursor.execute("DELETE FROM Guardado WHERE id_apunte = %s", (id_apunte,))
        cursor.execute("DELETE FROM Archivo_Apunte WHERE id_apunte = %s", (id_apunte,))
        cursor.execute("DELETE FROM Apunte WHERE id = %s", (id_apunte,))
        conn.commit()

        for ruta in rutas:
            ruta_completa = os.path.join(carpeta_apuntes, os.path.basename(ruta))
            if os.path.exists(ruta_completa):
                try:
                    os.remove(ruta_completa)
                except OSError as e:
                    print(f"No se pudo borrar {ruta_completa}: {e}")

        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al eliminar apunte: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()