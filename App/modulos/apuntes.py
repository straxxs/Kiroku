import os
import pymysql
from db.conexion import obtener_conexion


def crear_apunte(titulo, descripcion, id_usuario, id_curso, id_materia, rol="alumno"):
    if not id_materia or not id_curso or not titulo:
        return False
    estado = "aprobado" if rol in ("moderador", "admin") else "pendiente"
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Apunte(titulo, descripcion, id_usuario_creador, id_curso, id_materia, estado)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (titulo, descripcion, id_usuario, id_curso, id_materia, estado))
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
        cursor.execute("INSERT INTO Archivo_Apunte(ruta, tipo, id_apunte) VALUES (%s,%s,%s)",
                       (ruta, tipo, id_apunte))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al agregar archivo: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def apunte_pertenece_a_cursos(ruta_archivo, ids_cursos):
    """
    True si el archivo pertenece a un apunte de alguno de esos cursos.
    Usado para autorizar descargas.
    """
    if not ids_cursos:
        return False
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        placeholders = ",".join(["%s"] * len(ids_cursos))
        cursor.execute(f"""
            SELECT 1 FROM Archivo_Apunte af
            JOIN Apunte a ON af.id_apunte = a.id
            WHERE af.ruta = %s AND a.id_curso IN ({placeholders})
            LIMIT 1
        """, (ruta_archivo, *ids_cursos))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error en apunte_pertenece_a_cursos: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def _traer_archivos(cursor, apuntes):
    for ap in apuntes:
        cursor.execute("SELECT id, ruta, tipo FROM Archivo_Apunte WHERE id_apunte = %s", (ap["id"],))
        ap["archivos"] = cursor.fetchall()
    return apuntes


def listar_apuntes_por_materia(id_materia, id_usuario=None, solo_aprobados=True):
    """Lista apuntes. SIN me_gusta. Optimizado en batch (evita N+1)."""
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
        if not apuntes:
            return []

        ids = [a["id"] for a in apuntes]
        ph = ",".join(["%s"] * len(ids))

        # Archivos en un solo query
        cursor.execute(
            f"SELECT id, ruta, tipo, id_apunte FROM Archivo_Apunte WHERE id_apunte IN ({ph})", ids)
        por_apunte = {}
        for f in cursor.fetchall():
            por_apunte.setdefault(f["id_apunte"], []).append(
                {"id": f["id"], "ruta": f["ruta"], "tipo": f["tipo"]})

        guardados, calificaciones = set(), {}
        if id_usuario:
            cursor.execute(
                f"SELECT id_apunte FROM Guardado WHERE id_alumno=%s AND id_apunte IN ({ph})",
                (id_usuario, *ids))
            guardados = {r["id_apunte"] for r in cursor.fetchall()}

            cursor.execute(
                f"SELECT id_apunte, calificacion FROM Calificacion WHERE id_alumno=%s AND id_apunte IN ({ph})",
                (id_usuario, *ids))
            calificaciones = {r["id_apunte"]: r["calificacion"] for r in cursor.fetchall()}
            
                    # ---- Contador de comentarios (batch, sin N+1) ----
            cursor.execute(f"""
                SELECT id_apunte, COUNT(*) AS cantidad
                FROM comentario
                WHERE id_apunte IN ({ph}) AND estado = 'activo'
                GROUP BY id_apunte
            """, ids)
            comentarios_por_apunte = {r["id_apunte"]: r["cantidad"] for r in cursor.fetchall()}

            for ap in apuntes:
                ap["promedio"] = round(float(ap["promedio"]), 1)
                ap["archivos"] = por_apunte.get(ap["id"], [])
                ap["guardado"] = ap["id"] in guardados
                ap["mi_calificacion"] = calificaciones.get(ap["id"], 0)
                ap["cant_comentarios"] = comentarios_por_apunte.get(ap["id"], 0)   # 🆕
            return apuntes
        for ap in apuntes:
            ap["promedio"] = round(float(ap["promedio"]), 1)
            ap["archivos"] = por_apunte.get(ap["id"], [])
            ap["guardado"] = ap["id"] in guardados
            ap["mi_calificacion"] = calificaciones.get(ap["id"], 0)
        return apuntes
    except Exception as e:
        print(f"Error al listar apuntes: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def listar_apuntes_pendientes(id_curso):
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
        cursor.execute("UPDATE Apunte SET estado=%s WHERE id=%s", (estado, id_apunte))
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
            SELECT id, titulo, descripcion, estado,
                   id_usuario_creador, id_curso, id_materia
            FROM Apunte WHERE id = %s
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
        cursor.execute("SELECT ruta FROM Archivo_Apunte WHERE id_apunte=%s", (id_apunte,))
        rutas = [f["ruta"] for f in cursor.fetchall()]

        cursor.execute("DELETE FROM Calificacion WHERE id_apunte=%s", (id_apunte,))
        cursor.execute("DELETE FROM Guardado WHERE id_apunte=%s", (id_apunte,))
        # (línea de me_gusta eliminada)
        cursor.execute("DELETE FROM Archivo_Apunte WHERE id_apunte=%s", (id_apunte,))
        cursor.execute("DELETE FROM Apunte WHERE id=%s", (id_apunte,))
        borrado = cursor.rowcount > 0
        conn.commit()

        for ruta in rutas:
            completa = os.path.join(carpeta_apuntes, os.path.basename(ruta))
            if os.path.exists(completa):
                try:
                    os.remove(completa)
                except OSError as e:
                    print(f"No se pudo borrar {completa}: {e}")
        return borrado
    except Exception as e:
        print(f"Error al eliminar apunte: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()