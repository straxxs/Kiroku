"""
Comentarios en apuntes. Soft delete + base para reportes.
"""
import traceback
import pymysql
from db.conexion import obtener_conexion

MAX_LONGITUD = 500
MIN_LONGITUD = 1


def validar_contenido(texto):
    """Valida el texto del comentario. Devuelve (ok, mensaje, texto_limpio)."""
    if texto is None:
        return False, "El comentario no puede estar vacío.", ""
    limpio = texto.strip()
    if len(limpio) < MIN_LONGITUD:
        return False, "El comentario no puede estar vacío.", ""
    if len(limpio) > MAX_LONGITUD:
        return False, f"Máximo {MAX_LONGITUD} caracteres (tenés {len(limpio)}).", ""
    # Colapsa saltos de línea excesivos
    while "\n\n\n" in limpio:
        limpio = limpio.replace("\n\n\n", "\n\n")
    return True, "", limpio


def crear_comentario(id_apunte, id_usuario, contenido):
    """Crea un comentario. Devuelve el id o (False, mensaje)."""
    ok, msg, limpio = validar_contenido(contenido)
    if not ok:
        return False, msg

    conn = obtener_conexion()
    if not conn:
        return False, "Sin conexión a la base de datos."
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM Apunte WHERE id = %s", (id_apunte,))
        if not cursor.fetchone():
            return False, "El apunte no existe."

        cursor.execute("""
            INSERT INTO comentario (id_apunte, id_usuario, contenido)
            VALUES (%s, %s, %s)
        """, (id_apunte, id_usuario, limpio))
        conn.commit()
        return cursor.lastrowid, ""
    except Exception as e:
        print(f"[comentarios] Error al crear: {e}")
        traceback.print_exc()
        conn.rollback()
        return False, "No se pudo publicar el comentario."
    finally:
        cursor.close()
        conn.close()


def listar_comentarios(id_apunte, incluir_eliminados=False, limite=200):
    """
    Comentarios de un apunte ordenados por fecha (más antiguos primero).
    Si incluir_eliminados=True (moderadores), devuelve tombstones.
    """
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        sql = """
            SELECT c.id, c.contenido, c.fecha_creacion, c.fecha_edicion,
                   c.estado, c.id_usuario,
                   u.nombre AS autor, u.avatar AS autor_avatar,
                   e.nombre AS eliminado_por_nombre,
                   (SELECT COUNT(*) FROM reporte_comentario r
                     WHERE r.id_comentario = c.id AND r.estado = 'pendiente') AS reportes
            FROM comentario c
            LEFT JOIN Usuario u ON c.id_usuario = u.id
            LEFT JOIN Usuario e ON c.eliminado_por = e.id
            WHERE c.id_apunte = %s
        """
        if not incluir_eliminados:
            sql += " AND c.estado = 'activo'"
        sql += " ORDER BY c.fecha_creacion ASC LIMIT %s"

        cursor.execute(sql, (id_apunte, limite))
        filas = cursor.fetchall()

        for f in filas:
            for campo in ("fecha_creacion", "fecha_edicion"):
                if f.get(campo):
                    f[campo] = f[campo].strftime("%Y-%m-%d %H:%M:%S")
            if f["estado"] == "eliminado":
                f["contenido"] = ""   # nunca exponer el texto borrado
        return filas
    except Exception as e:
        print(f"[comentarios] Error al listar: {e}")
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        conn.close()


def obtener_comentario(id_comentario):
    """Comentario + id_curso del apunte (para validar permisos)."""
    conn = obtener_conexion()
    if not conn:
        return None
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT c.id, c.id_apunte, c.id_usuario, c.estado, c.contenido,
                   a.id_curso
            FROM comentario c
            JOIN Apunte a ON c.id_apunte = a.id
            WHERE c.id = %s
        """, (id_comentario,))
        return cursor.fetchone()
    except Exception as e:
        print(f"[comentarios] Error al obtener: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def eliminar_comentario(id_comentario, id_usuario_elimina):
    """Soft delete: marca estado='eliminado' y registra quién lo hizo."""
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE comentario
            SET estado = 'eliminado',
                eliminado_por = %s,
                fecha_eliminacion = NOW()
            WHERE id = %s AND estado = 'activo'
        """, (id_usuario_elimina, id_comentario))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[comentarios] Error al eliminar: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def contar_comentarios(id_apunte):
    conn = obtener_conexion()
    if not conn:
        return 0
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM comentario WHERE id_apunte = %s AND estado = 'activo'",
            (id_apunte,))
        return cursor.fetchone()[0]
    except Exception:
        return 0
    finally:
        cursor.close()
        conn.close()


def contar_por_apuntes(ids_apuntes):
    """Contador batch: {id_apunte: cantidad}. Evita N+1 al listar apuntes."""
    if not ids_apuntes:
        return {}
    conn = obtener_conexion()
    if not conn:
        return {}
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        ph = ",".join(["%s"] * len(ids_apuntes))
        cursor.execute(f"""
            SELECT id_apunte, COUNT(*) AS cantidad
            FROM comentario
            WHERE id_apunte IN ({ph}) AND estado = 'activo'
            GROUP BY id_apunte
        """, tuple(ids_apuntes))
        return {r["id_apunte"]: r["cantidad"] for r in cursor.fetchall()}
    except Exception as e:
        print(f"[comentarios] Error en contar_por_apuntes: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


# ---------------- REPORTES (base preparada, sin UI todavía) ----------------

def reportar_comentario(id_comentario, id_usuario, motivo="otro", detalle=None):
    """Registra un reporte. Devuelve True / 'duplicado' / False."""
    if motivo not in ("spam", "ofensivo", "incorrecto", "otro"):
        motivo = "otro"
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO reporte_comentario (id_comentario, id_usuario_reporta, motivo, detalle)
            VALUES (%s, %s, %s, %s)
        """, (id_comentario, id_usuario, motivo, (detalle or "")[:300]))
        conn.commit()
        return True
    except pymysql.err.IntegrityError:
        conn.rollback()
        return "duplicado"
    except Exception as e:
        print(f"[comentarios] Error al reportar: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()