import os
import pymysql
import secrets
import string
from db.conexion import obtener_conexion


def _generar_codigo_invitacion():
    chars = string.ascii_uppercase + string.digits
    p1 = ''.join(secrets.choice(chars) for _ in range(4))
    p2 = ''.join(secrets.choice(chars) for _ in range(4))
    return f"{p1}-{p2}"


def crear_curso(anio, division, id_creador):
    """
    Crea el curso y registra al creador como MODERADOR en usuario_curso.
    Ya NO toca usuario.id_curso ni usuario.rol (multi-curso).
    """
    if not anio or not division or not str(anio).isdigit():
        return False

    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        # Código único (reintentos por colisión improbable)
        for _ in range(5):
            codigo = _generar_codigo_invitacion()
            cursor.execute("SELECT 1 FROM Curso WHERE codigo_invitacion = %s", (codigo,))
            if not cursor.fetchone():
                break
        else:
            return False

        cursor.execute(
            "INSERT INTO Curso(anio, division, id_creador, codigo_invitacion) VALUES (%s,%s,%s,%s)",
            (anio, division, id_creador, codigo),
        )
        nuevo_id = cursor.lastrowid

        # El creador entra como moderador DE ESE CURSO
        cursor.execute("""
            INSERT INTO usuario_curso (id_usuario, id_curso, rol_curso)
            VALUES (%s, %s, 'moderador')
        """, (id_creador, nuevo_id))

        conn.commit()
        return {"id": nuevo_id, "codigo": codigo}
    except Exception as e:
        print(f"Error al crear curso: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def editar_curso(id_curso, anio, division):
    if not anio or not str(anio).isdigit() or not division:
        return False
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Curso SET anio=%s, division=%s WHERE id=%s",
                       (anio, division, id_curso))
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
    """Listado global (solo admin)."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT c.id, c.anio, c.division, c.id_creador, u.nombre AS creador,
                   (SELECT COUNT(*) FROM usuario_curso uc WHERE uc.id_curso = c.id) AS cant_miembros
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
            SELECT c.id, c.anio, c.division, c.id_creador, c.codigo_invitacion,
                   u.nombre AS creador
            FROM Curso c LEFT JOIN Usuario u ON c.id_creador = u.id
            WHERE c.id = %s
        """, (id_curso,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error al obtener curso: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def obtener_curso_por_codigo(codigo):
    conn = obtener_conexion()
    if not conn:
        return None
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT id, anio, division FROM Curso WHERE codigo_invitacion = %s", (codigo,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error al buscar curso por código: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def eliminar_curso(id_curso, carpeta_apuntes):
    """Elimina el curso y todo su contenido. usuario_curso cae por CASCADE."""
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT af.ruta FROM Archivo_Apunte af
            JOIN Apunte a ON af.id_apunte = a.id WHERE a.id_curso = %s
        """, (id_curso,))
        rutas = [f["ruta"] for f in cursor.fetchall()]

        cursor.execute("""DELETE af FROM Archivo_Apunte af
                          JOIN Apunte a ON af.id_apunte=a.id WHERE a.id_curso=%s""", (id_curso,))
        cursor.execute("""DELETE c FROM Calificacion c
                          JOIN Apunte a ON c.id_apunte=a.id WHERE a.id_curso=%s""", (id_curso,))
        cursor.execute("""DELETE g FROM Guardado g
                          JOIN Apunte a ON g.id_apunte=a.id WHERE a.id_curso=%s""", (id_curso,))
        # (bloque me_gusta eliminado — la tabla ya no existe)
        cursor.execute("DELETE FROM Apunte WHERE id_curso=%s", (id_curso,))
        cursor.execute("DELETE FROM Materia WHERE id_curso=%s", (id_curso,))

        # Membresías (explícito, aunque haya ON DELETE CASCADE)
        cursor.execute("DELETE FROM usuario_curso WHERE id_curso=%s", (id_curso,))

        # Legacy: limpiar el campo viejo si todavía existe
        try:
            cursor.execute("UPDATE Usuario SET id_curso = NULL WHERE id_curso = %s", (id_curso,))
        except Exception:
            pass

        cursor.execute("DELETE FROM Curso WHERE id=%s", (id_curso,))
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
        print(f"Error al eliminar curso: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()