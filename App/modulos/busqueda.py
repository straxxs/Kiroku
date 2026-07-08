import pymysql
from db.conexion import obtener_conexion


def buscar_apuntes(id_curso, texto="", orden="recientes"):
    """
    Busca apuntes APROBADOS dentro de un curso.
    - texto: filtra por título, autor o materia (LIKE).
    - orden: 'recientes' (default) o 'valorados' (mejor promedio).
    """
    conn = obtener_conexion()
    if not conn:
        return []

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        sql = """
            SELECT a.id, a.titulo, a.descripcion, a.fecha_subida, a.id_materia,
                   m.nombre AS materia,
                   u.nombre AS autor, u.avatar AS autor_avatar,
                   IFNULL(AVG(cal.calificacion), 0) AS promedio,
                   COUNT(DISTINCT cal.id) AS cant_calificaciones
            FROM Apunte a
            LEFT JOIN Materia m ON a.id_materia = m.id
            LEFT JOIN Usuario u ON a.id_usuario_creador = u.id
            LEFT JOIN Calificacion cal ON cal.id_apunte = a.id
            WHERE a.id_curso = %s AND a.estado = 'aprobado'
        """
        params = [id_curso]

        if texto and texto.strip():
            like = f"%{texto.strip()}%"
            sql += " AND (a.titulo LIKE %s OR u.nombre LIKE %s OR m.nombre LIKE %s)"
            params += [like, like, like]

        sql += " GROUP BY a.id"

        if orden == "valorados":
            sql += " ORDER BY promedio DESC, cant_calificaciones DESC, a.fecha_subida DESC"
        else:  # recientes
            sql += " ORDER BY a.fecha_subida DESC"

        cursor.execute(sql, tuple(params))
        apuntes = cursor.fetchall()

        for ap in apuntes:
            ap["promedio"] = round(float(ap["promedio"]), 1)
            cursor.execute(
                "SELECT id, ruta, tipo FROM Archivo_Apunte WHERE id_apunte = %s",
                (ap["id"],),
            )
            ap["archivos"] = cursor.fetchall()

        return apuntes
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return []
    finally:
        cursor.close()
        conn.close()