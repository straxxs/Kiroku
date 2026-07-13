import os
import pymysql
import secrets
import string
from db.conexion import obtener_conexion


def _generar_codigo_invitacion():
    """Genera un código de invitación alfanumérico tipo XXXX-XXXX."""
    chars = string.ascii_uppercase + string.digits
    parte1 = ''.join(secrets.choice(chars) for _ in range(4))
    parte2 = ''.join(secrets.choice(chars) for _ in range(4))
    return f"{parte1}-{parte2}"


def crear_curso(anio, division, id_creador):
    """Crea el curso, asigna el curso al usuario y lo vuelve moderador."""
    if not anio or not division:
        return False
    if not str(anio).isdigit():
        return False

    conn = obtener_conexion()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        codigo = _generar_codigo_invitacion()
        cursor.execute(
            "INSERT INTO Curso(anio, division, id_creador, codigo_invitacion) VALUES (%s, %s, %s, %s)",
            (anio, division, id_creador, codigo),
        )
        nuevo_id = cursor.lastrowid

        cursor.execute(
            "UPDATE Usuario SET id_curso = %s, rol = 'moderador' WHERE id = %s",
            (nuevo_id, id_creador),
        )

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
            SELECT c.id, c.anio, c.division, c.id_creador, c.codigo_invitacion, u.nombre AS creador
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
            SELECT id, nombre, rol, avatar
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


def eliminar_curso(id_curso, carpeta_apuntes):
    conn = obtener_conexion()
    if not conn:
        return False

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # 1. Rutas de archivos de todos los apuntes del curso
        cursor.execute("""
            SELECT af.ruta
            FROM Archivo_Apunte af
            JOIN Apunte a ON af.id_apunte = a.id
            WHERE a.id_curso = %s
        """, (id_curso,))
        rutas = [fila["ruta"] for fila in cursor.fetchall()]

        # 2. Borrar archivos (BD)
        cursor.execute("""
            DELETE af FROM Archivo_Apunte af
            JOIN Apunte a ON af.id_apunte = a.id
            WHERE a.id_curso = %s
        """, (id_curso,))

        # 2b. Borrar calificaciones, guardados y me_gusta de esos apuntes
        cursor.execute("""
            DELETE c FROM Calificacion c
            JOIN Apunte a ON c.id_apunte = a.id
            WHERE a.id_curso = %s
        """, (id_curso,))
        cursor.execute("""
            DELETE g FROM Guardado g
            JOIN Apunte a ON g.id_apunte = a.id
            WHERE a.id_curso = %s
        """, (id_curso,))
        cursor.execute("""
            DELETE mg FROM me_gusta mg
            JOIN Apunte a ON mg.id_apunte = a.id
            WHERE a.id_curso = %s
        """, (id_curso,))

        # 3. Borrar apuntes del curso
        cursor.execute("DELETE FROM Apunte WHERE id_curso = %s", (id_curso,))

        # 4. Borrar materias del curso
        cursor.execute("DELETE FROM Materia WHERE id_curso = %s", (id_curso,))

        # 5. Soltar usuarios: sacarles el curso y bajar moderadores a alumno
        cursor.execute("""
            UPDATE Usuario
            SET id_curso = NULL,
                rol = IF(rol = 'moderador', 'alumno', rol)
            WHERE id_curso = %s
        """, (id_curso,))

        # 6. Borrar el curso
        cursor.execute("DELETE FROM Curso WHERE id = %s", (id_curso,))
        conn.commit()

        # 7. Borrar archivos físicos
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
        print(f"Error al eliminar curso: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def obtener_curso_por_codigo(codigo):
    """Busca un curso por su código de invitación alfanumérico."""
    conn = obtener_conexion()
    if not conn:
        return None
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT id, anio, division FROM Curso WHERE codigo_invitacion = %s", (codigo,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error al buscar curso por código: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def unir_usuario_a_curso(id_usuario, id_curso):
    """El alumno se une a un curso existente. No cambia su rol (sigue siendo alumno)."""
    conn = obtener_conexion()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # Verificar que el curso exista
        cursor.execute("SELECT id FROM Curso WHERE id = %s", (id_curso,))
        if not cursor.fetchone():
            return False

        cursor.execute(
            "UPDATE Usuario SET id_curso = %s WHERE id = %s",
            (id_curso, id_usuario),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al unir usuario a curso: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def salir_de_curso(id_usuario):
    """El usuario deja su curso actual. Si era moderador, vuelve a alumno.
    No permite salir si es el creador del curso (debe eliminar el curso primero)."""
    conn = obtener_conexion()
    if not conn:
        return False

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT id_curso, rol FROM Usuario WHERE id = %s", (id_usuario,))
        user = cursor.fetchone()
        if not user or not user["id_curso"]:
            return False

        if user["rol"] == "moderador":
            cursor.execute("SELECT id_creador FROM Curso WHERE id = %s", (user["id_curso"],))
            curso = cursor.fetchone()
            if curso and curso["id_creador"] == id_usuario:
                return False

        cursor.execute(
            "UPDATE Usuario SET id_curso = NULL, rol = 'alumno' WHERE id = %s AND rol != 'admin'",
            (id_usuario,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al salir del curso: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def eliminar_curso_como_creador(id_curso, id_usuario, carpeta_apuntes):
    """Solo el creador del curso puede eliminarlo."""
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT id_creador FROM Curso WHERE id = %s", (id_curso,))
        curso = cursor.fetchone()
        if not curso or curso["id_creador"] != id_usuario:
            return False
    finally:
        cursor.close()
        conn.close()
    return eliminar_curso(id_curso, carpeta_apuntes)