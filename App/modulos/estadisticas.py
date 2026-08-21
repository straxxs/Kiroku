import pymysql
from db.conexion import obtener_conexion


def estadisticas_generales():
    """Métricas generales del sistema para el admin."""
    conn = obtener_conexion()
    if not conn:
        return {}
    cursor = conn.cursor()
    try:
        stats = {}

        cursor.execute("SELECT COUNT(*) FROM usuario")
        stats["total_usuarios"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM usuario WHERE estado = 'activo'")
        stats["usuarios_activos"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM usuario WHERE estado = 'bloqueado'")
        stats["usuarios_bloqueados"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM curso")
        stats["total_cursos"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM materia")
        stats["total_materias"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM apunte")
        stats["total_apuntes"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM apunte WHERE estado = 'aprobado'")
        stats["apuntes_aprobados"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM apunte WHERE estado = 'pendiente'")
        stats["apuntes_pendientes"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM apunte WHERE estado = 'rechazado'")
        stats["apuntes_rechazados"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM usuario_curso")
        stats["total_inscripciones"] = cursor.fetchone()[0]

        return stats
    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


def apuntes_mas_valorados(limite=10):
    """Top apuntes con mejor promedio de estrellas."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT a.id, a.titulo, u.nombre AS autor,
                   ROUND(AVG(cal.calificacion), 1) AS promedio,
                   COUNT(DISTINCT cal.id) AS cant_calificaciones
            FROM Apunte a
            LEFT JOIN Calificacion cal ON cal.id_apunte = a.id
            LEFT JOIN Usuario u ON a.id_usuario_creador = u.id
            WHERE a.estado = 'aprobado'
            GROUP BY a.id
            HAVING cant_calificaciones > 0
            ORDER BY promedio DESC, cant_calificaciones DESC
            LIMIT %s
        """, (limite,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def materias_mas_consultadas(limite=10):
    """Materias con más apuntes (proxy de consultas)."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT m.nombre AS materia,
                   c.anio, c.division,
                   COUNT(a.id) AS cantidad_apuntes
            FROM Materia m
            LEFT JOIN Apunte a ON a.id_materia = m.id AND a.estado = 'aprobado'
            LEFT JOIN Curso c ON m.id_curso = c.id
            GROUP BY m.id
            ORDER BY cantidad_apuntes DESC
            LIMIT %s
        """, (limite,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def ranking_colaboradores(limite=10):
    """Top usuarios que más apuntes subieron (aprobados)."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT u.nombre AS autor, u.avatar,
                   COUNT(a.id) AS apuntes_subidos,
                   ROUND(AVG(cal.calificacion), 1) AS promedio_recibido
            FROM Apunte a
            JOIN Usuario u ON a.id_usuario_creador = u.id
            LEFT JOIN Calificacion cal ON cal.id_apunte = a.id
            WHERE a.estado = 'aprobado'
            GROUP BY u.id
            ORDER BY apuntes_subidos DESC
            LIMIT %s
        """, (limite,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def apuntes_por_estado():
    """Cantidad de apuntes por estado (para gráfico pie)."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT estado, COUNT(*) AS cantidad
            FROM Apunte
            GROUP BY estado
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def apuntes_por_fecha(dias=30):
    """Apuntes subidos por día (para gráfico de línea)."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT DATE(fecha_subida) AS fecha, COUNT(*) AS cantidad
            FROM Apunte
            WHERE fecha_subida >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY DATE(fecha_subida)
            ORDER BY fecha ASC
        """, (dias,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ==================== ESTADÍSTICAS POR CURSO (MODERADOR) ====================

def stats_curso_resumen(id_curso):
    """Resumen de un curso. SIN métrica de likes."""
    conn = obtener_conexion()
    if not conn:
        return {}
    cursor = conn.cursor()
    try:
        stats = {}
        # Miembros ahora se cuentan desde usuario_curso
        cursor.execute("SELECT COUNT(*) FROM usuario_curso WHERE id_curso=%s", (id_curso,))
        stats["total_alumnos"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Materia WHERE id_curso=%s", (id_curso,))
        stats["total_materias"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Apunte WHERE id_curso=%s", (id_curso,))
        stats["total_apuntes"] = cursor.fetchone()[0]

        for est in ("aprobado", "pendiente", "rechazado"):
            cursor.execute("SELECT COUNT(*) FROM Apunte WHERE id_curso=%s AND estado=%s",
                           (id_curso, est))
            stats[est + "s"] = cursor.fetchone()[0]

        cursor.execute("""
            SELECT ROUND(AVG(cal.calificacion),1) FROM Calificacion cal
            JOIN Apunte a ON cal.id_apunte = a.id WHERE a.id_curso=%s
        """, (id_curso,))
        row = cursor.fetchone()
        stats["promedio_valoracion"] = row[0] if row and row[0] else 0

        # ❌ eliminado: stats["total_me_gusta"]
        return stats
    except Exception as e:
        print(f"Error stats_curso_resumen: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


def stats_curso_por_estado(id_curso):
    """Apuntes por estado en un curso."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT estado, COUNT(*) AS cantidad
            FROM Apunte WHERE id_curso = %s
            GROUP BY estado
        """, (id_curso,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def stats_curso_materias(id_curso):
    """Materias con más apuntes en un curso."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT m.nombre AS materia, COUNT(a.id) AS cantidad
            FROM Materia m
            LEFT JOIN Apunte a ON a.id_materia = m.id AND a.estado = 'aprobado'
            WHERE m.id_curso = %s
            GROUP BY m.id
            ORDER BY cantidad DESC
        """, (id_curso,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def stats_curso_ranking(id_curso):
    """Alumnos que más apuntes subieron en un curso."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT u.nombre AS autor, u.avatar,
                   COUNT(a.id) AS apuntes_subidos,
                   ROUND(AVG(cal.calificacion), 1) AS promedio_recibido
            FROM Apunte a
            JOIN Usuario u ON a.id_usuario_creador = u.id
            LEFT JOIN Calificacion cal ON cal.id_apunte = a.id
            WHERE a.id_curso = %s AND a.estado = 'aprobado'
            GROUP BY u.id
            ORDER BY apuntes_subidos DESC
            LIMIT 10
        """, (id_curso,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def stats_curso_por_fecha(id_curso, dias=90):
    """Apuntes subidos por día en un curso (incluye días sin apuntes con cantidad 0)."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT DATE(fecha_subida) AS fecha, COUNT(*) AS cantidad
            FROM Apunte
            WHERE id_curso = %s
              AND fecha_subida >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY DATE(fecha_subida)
            ORDER BY fecha ASC
        """, (id_curso, dias))
        datos = {str(r["fecha"]): r["cantidad"] for r in cursor.fetchall()}
        from datetime import date, timedelta
        hoy = date.today()
        resultado = []
        for i in range(dias, -1, -1):
            dia = hoy - timedelta(days=i)
            clave = str(dia)
            resultado.append({"fecha": clave, "cantidad": datos.get(clave, 0)})
        return resultado
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def stats_curso_top_valorados(id_curso, limite=5):
    """Mejores apuntes valorados de un curso."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT a.titulo, u.nombre AS autor,
                   ROUND(AVG(cal.calificacion), 1) AS promedio,
                   COUNT(DISTINCT cal.id) AS cant_calificaciones
            FROM Apunte a
            LEFT JOIN Calificacion cal ON cal.id_apunte = a.id
            LEFT JOIN Usuario u ON a.id_usuario_creador = u.id
            WHERE a.id_curso = %s AND a.estado = 'aprobado'
            GROUP BY a.id
            HAVING cant_calificaciones > 0
            ORDER BY promedio DESC, cant_calificaciones DESC
            LIMIT %s
        """, (id_curso, limite))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()
