import os
import pymysql
from db.conexion import obtener_conexion


def crear_apunte(descripcion, id_usuario, id_curso, id_materia):
    if not id_materia or not id_curso:
        return False
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Apunte(descripcion, id_usuario_creador, id_curso, id_materia)
            VALUES (%s, %s, %s, %s)
        """, (descripcion, id_usuario, id_curso, id_materia))
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


def listar_apuntes_por_materia(id_materia):
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT a.id, a.descripcion, a.id_usuario_creador,
                   u.nombre AS autor, u.avatar AS autor_avatar
            FROM Apunte a
            LEFT JOIN Usuario u ON a.id_usuario_creador = u.id
            WHERE a.id_materia = %s
            ORDER BY a.id DESC
        """, (id_materia,))
        apuntes = cursor.fetchall()

        for ap in apuntes:
            cursor.execute("""
                SELECT id, ruta, tipo FROM Archivo_Apunte WHERE id_apunte = %s
            """, (ap["id"],))
            ap["archivos"] = cursor.fetchall()
        return apuntes
    except Exception as e:
        print(f"Error al listar apuntes: {e}")
        return []
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
            SELECT a.id, a.descripcion, a.id_usuario_creador, a.id_curso, a.id_materia
            FROM Apunte a WHERE a.id = %s
        """, (id_apunte,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error al obtener apunte: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def _borrar_archivos_fisicos(rutas, carpeta_apuntes):
    """Borra del disco los archivos dados. 'rutas' son como 'uploads/apuntes/x.png'."""
    for ruta in rutas:
        nombre = os.path.basename(ruta)  # x.png
        ruta_completa = os.path.join(carpeta_apuntes, nombre)
        if os.path.exists(ruta_completa):
            try:
                os.remove(ruta_completa)
            except OSError as e:
                print(f"No se pudo borrar el archivo {ruta_completa}: {e}")


def eliminar_apunte(id_apunte, carpeta_apuntes):
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # Obtenemos las rutas para borrarlas del disco después
        cursor.execute("SELECT ruta FROM Archivo_Apunte WHERE id_apunte = %s", (id_apunte,))
        rutas = [fila["ruta"] for fila in cursor.fetchall()]

        cursor.execute("DELETE FROM Archivo_Apunte WHERE id_apunte = %s", (id_apunte,))
        cursor.execute("DELETE FROM Apunte WHERE id = %s", (id_apunte,))
        conn.commit()

        _borrar_archivos_fisicos(rutas, carpeta_apuntes)
        return True
    except Exception as e:
        print(f"Error al eliminar apunte: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()