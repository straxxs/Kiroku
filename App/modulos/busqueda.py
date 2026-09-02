import traceback
import pymysql
from db.conexion import obtener_conexion


def buscar_apuntes(id_curso, texto="", orden="recientes",
                   materia_id=None, fecha_desde=None, fecha_hasta=None):
    """Busca apuntes APROBADOS dentro de UN curso, con filtros combinados."""
    conn = obtener_conexion()
    if not conn:
        print("[busqueda] Sin conexión a la BD")
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
            LEFT JOIN Materia m      ON a.id_materia = m.id
            LEFT JOIN Usuario u      ON a.id_usuario_creador = u.id
            LEFT JOIN Calificacion cal ON cal.id_apunte = a.id
            WHERE a.id_curso = %s AND a.estado = 'aprobado'
        """
        params = [id_curso]

        if texto and texto.strip():
            like = f"%{texto.strip()}%"
            sql += " AND (a.titulo LIKE %s OR a.descripcion LIKE %s OR u.nombre LIKE %s OR m.nombre LIKE %s)"
            params += [like, like, like, like]

        if materia_id:
            sql += " AND a.id_materia = %s"
            params.append(materia_id)

        if fecha_desde:
            sql += " AND a.fecha_subida >= %s"
            params.append(f"{fecha_desde} 00:00:00")

        if fecha_hasta:
            sql += " AND a.fecha_subida <= %s"
            params.append(f"{fecha_hasta} 23:59:59")

        sql += " GROUP BY a.id"
        sql += (" ORDER BY promedio DESC, cant_calificaciones DESC, a.fecha_subida DESC"
                if orden == "valorados" else " ORDER BY a.fecha_subida DESC")
        sql += " LIMIT 100"

        cursor.execute(sql, tuple(params))
        apuntes = cursor.fetchall()
        if not apuntes:
            return []

        # Archivos en un solo query (evita N+1)
        ids = [a["id"] for a in apuntes]
        ph = ",".join(["%s"] * len(ids))
        cursor.execute(
            f"SELECT id, ruta, tipo, id_apunte FROM Archivo_Apunte WHERE id_apunte IN ({ph})",
            ids)
        por_apunte = {}
        for f in cursor.fetchall():
            por_apunte.setdefault(f["id_apunte"], []).append(
                {"id": f["id"], "ruta": f["ruta"], "tipo": f["tipo"]})

        for ap in apuntes:
            ap["promedio"] = round(float(ap["promedio"] or 0), 1)
            ap["archivos"] = por_apunte.get(ap["id"], [])
            if ap.get("fecha_subida"):
                ap["fecha_subida"] = ap["fecha_subida"].strftime("%Y-%m-%d %H:%M:%S")

        return apuntes

    except Exception as e:
        print(f"[busqueda] Error: {e}")
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        conn.close()