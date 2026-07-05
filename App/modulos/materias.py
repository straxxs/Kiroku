import os
import pymysql
from db.conexion import obtener_conexion
from modulos.profesores import obtener_o_crear_profesor


def crear_materia(nombre, id_curso, nombre_profesor=None):
    """
    Crea una materia. Si se pasa nombre_profesor y no existe, lo crea.
    Todo en la misma transacción.
    """
    if not nombre or not id_curso:
        return False

    conn = obtener_conexion()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        id_profesor = obtener_o_crear_profesor(nombre_profesor, cursor)

        cursor.execute(
            "INSERT INTO Materia(nombre, id_profesor, id_curso) VALUES (%s, %s, %s)",
            (nombre, id_profesor, id_curso),
        )
        conn.commit()
        return cursor.lastrowid
    except pymysql.err.IntegrityError:
        print("Curso inexistente")
        conn.rollback()
        return False
    except Exception as e:
        print(f"Error al crear materia: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def editar_materia(id_materia, nombre, nombre_profesor=None):
    if not nombre:
        return False

    conn = obtener_conexion()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        id_profesor = obtener_o_crear_profesor(nombre_profesor, cursor)

        cursor.execute(
            "UPDATE Materia SET nombre = %s, id_profesor = %s WHERE id = %s",
            (nombre, id_profesor, id_materia),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al editar materia: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def listar_materias_por_curso(id_curso):
    conn = obtener_conexion()
    if not conn:
        return []

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT m.id, m.nombre, m.id_curso, m.id_profesor, p.nombre AS nombre_profesor
            FROM Materia m
            LEFT JOIN Profesor p ON m.id_profesor = p.id
            WHERE m.id_curso = %s
            ORDER BY m.nombre
        """, (id_curso,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al listar materias: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def obtener_materia(id_materia):
    conn = obtener_conexion()
    if not conn:
        return None

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT m.id, m.nombre, m.id_profesor, m.id_curso, p.nombre AS nombre_profesor
            FROM Materia m
            LEFT JOIN Profesor p ON m.id_profesor = p.id
            WHERE m.id = %s
        """, (id_materia,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error al obtener materia: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def eliminar_materia(id_materia, carpeta_apuntes):
    conn = obtener_conexion()
    if not conn:
        return False

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # 1. Rutas de archivos de todos los apuntes de la materia
        cursor.execute("""
            SELECT af.ruta
            FROM Archivo_Apunte af
            JOIN Apunte a ON af.id_apunte = a.id
            WHERE a.id_materia = %s
        """, (id_materia,))
        rutas = [fila["ruta"] for fila in cursor.fetchall()]

        # 2. Borrar archivos (BD) de esos apuntes
        cursor.execute("""
            DELETE af FROM Archivo_Apunte af
            JOIN Apunte a ON af.id_apunte = a.id
            WHERE a.id_materia = %s
        """, (id_materia,))

        # 3. Borrar apuntes de la materia
        cursor.execute("DELETE FROM Apunte WHERE id_materia = %s", (id_materia,))

        # 4. Borrar la materia
        cursor.execute("DELETE FROM Materia WHERE id = %s", (id_materia,))
        conn.commit()

        # 5. Borrar archivos físicos del disco
        for ruta in rutas:
            nombre = os.path.basename(ruta)
            ruta_completa = os.path.join(carpeta_apuntes, nombre)
            if os.path.exists(ruta_completa):
                try:
                    os.remove(ruta_completa)
                except OSError as e:
                    print(f"No se pudo borrar {ruta_completa}: {e}")

        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al eliminar materia: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()