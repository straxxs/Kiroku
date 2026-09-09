"""
Motor de gamificación de KIROKU.

REGLA DE ORO: el XP SOLO se modifica desde este módulo, invocado desde el
backend. No existe ningún endpoint que permita a JavaScript sumar puntos.

Diseño:
  - xp_evento  : ledger append-only (fuente de verdad, auditable)
  - usuario_xp : agregado materializado (lectura rápida)
  - Revertir XP = insertar evento negativo, NUNCA borrar del ledger.

Uso típico:
    from modulos.gamificacion import otorgar, revertir
    otorgar(id_usuario=7, codigo="APUNTE_APROBADO", objeto=f"apunte:{id}",
            id_curso=3, actor=id_moderador)
"""
import datetime
import traceback
import pymysql
from db.conexion import obtener_conexion

# Tope global diario de XP positivo (última red de seguridad anti-farming)
TOPE_DIARIO_GLOBAL = 150


# ============================================================
# MÉTRICAS PARA LOGROS
# Agregar un logro nuevo = agregar una entrada acá + 1 INSERT en `logro`.
# Cada query recibe (id_usuario,) y devuelve un único valor numérico.
# ============================================================
METRICAS = {
    "apuntes_aprobados": """
        SELECT COUNT(*) FROM Apunte
        WHERE id_usuario_creador = %s AND estado = 'aprobado'
    """,
    "promedio_recibido": """
        SELECT IFNULL(
            (SELECT AVG(c.calificacion) FROM Calificacion c
             JOIN Apunte a ON c.id_apunte = a.id
             WHERE a.id_usuario_creador = %s
             HAVING COUNT(*) >= 5), 0)
    """,
    "valoraciones_dadas": """
        SELECT COUNT(*) FROM Calificacion WHERE id_alumno = %s
    """,
    "guardados_recibidos": """
        SELECT COUNT(*) FROM Guardado g
        JOIN Apunte a ON g.id_apunte = a.id
        WHERE a.id_usuario_creador = %s AND g.id_alumno <> %s
    """,
    "comentarios": """
        SELECT COUNT(*) FROM comentario
        WHERE id_usuario = %s AND estado = 'activo'
    """,
    "materias_distintas": """
        SELECT COUNT(DISTINCT id_materia) FROM Apunte
        WHERE id_usuario_creador = %s AND estado = 'aprobado'
    """,
    "cantidad_cursos": """
        SELECT COUNT(*) FROM usuario_curso WHERE id_usuario = %s
    """,
    "racha_dias": """
        SELECT IFNULL(racha_maxima, 0) FROM usuario_xp WHERE id_usuario = %s
    """,
    "apuntes_moderados": """
        SELECT COUNT(*) FROM xp_evento
        WHERE id_usuario = %s AND codigo_regla = 'MODERAR_APUNTE' AND es_reversion = 0
    """,
    "xp_total": """
        SELECT IFNULL(xp_total, 0) FROM usuario_xp WHERE id_usuario = %s
    """,
        "eventos_curso": """
        SELECT COUNT(*) FROM evento
        WHERE id_usuario_creador = %s AND ambito = 'curso' AND estado = 'activo'
    """,
}

# Métricas que necesitan el id_usuario dos veces
_METRICAS_DOBLE_PARAM = {"guardados_recibidos"}


# ============================================================
# HELPERS INTERNOS
# ============================================================

def _obtener_regla(cursor, codigo):
    cursor.execute(
        "SELECT * FROM regla_puntos WHERE codigo = %s AND activa = 1", (codigo,))
    return cursor.fetchone()


def _xp_positivo_hoy(cursor, id_usuario):
    cursor.execute("""
        SELECT IFNULL(SUM(puntos), 0) AS total FROM xp_evento
        WHERE id_usuario = %s AND puntos > 0 AND DATE(fecha) = CURDATE()
    """, (id_usuario,))
    return int(cursor.fetchone()["total"] or 0)


def _eventos_hoy(cursor, id_usuario, codigo):
    cursor.execute("""
        SELECT COUNT(*) AS n FROM xp_evento
        WHERE id_usuario = %s AND codigo_regla = %s
          AND es_reversion = 0 AND DATE(fecha) = CURDATE()
    """, (id_usuario, codigo))
    return int(cursor.fetchone()["n"] or 0)


def _segundos_desde_ultimo(cursor, id_usuario, codigo):
    cursor.execute("""
        SELECT TIMESTAMPDIFF(SECOND, MAX(fecha), NOW()) AS seg
        FROM xp_evento
        WHERE id_usuario = %s AND codigo_regla = %s AND es_reversion = 0
    """, (id_usuario, codigo))
    fila = cursor.fetchone()
    return fila["seg"] if fila and fila["seg"] is not None else 10 ** 9


def _nivel_para_xp(cursor, xp):
    cursor.execute("""
        SELECT * FROM nivel
        WHERE xp_minimo <= %s AND (xp_maximo IS NULL OR xp_maximo >= %s)
        ORDER BY xp_minimo DESC LIMIT 1
    """, (xp, xp))
    return cursor.fetchone() or {"id": 1, "codigo": "principiante", "nombre": "Principiante"}


def _actualizar_agregado(cursor, id_usuario, puntos):
    """Suma puntos al agregado y devuelve (xp_nuevo, nivel_anterior, nivel_nuevo)."""
    cursor.execute("SELECT xp_total, id_nivel FROM usuario_xp WHERE id_usuario = %s",
                   (id_usuario,))
    fila = cursor.fetchone()
    if not fila:
        cursor.execute(
            "INSERT INTO usuario_xp (id_usuario, xp_total, id_nivel) VALUES (%s, 0, 1)",
            (id_usuario,))
        xp_anterior, nivel_anterior = 0, 1
    else:
        xp_anterior, nivel_anterior = int(fila["xp_total"]), int(fila["id_nivel"])

    xp_nuevo = xp_anterior + puntos
    nivel_nuevo = _nivel_para_xp(cursor, xp_nuevo)

    cursor.execute("""
        UPDATE usuario_xp
        SET xp_total   = %s,
            id_nivel   = %s,
            xp_ganado  = xp_ganado  + %s,
            xp_perdido = xp_perdido + %s
        WHERE id_usuario = %s
    """, (xp_nuevo, nivel_nuevo["id"],
          max(puntos, 0), abs(min(puntos, 0)), id_usuario))

    return xp_nuevo, nivel_anterior, nivel_nuevo


# ============================================================
# FUNCIÓN CENTRAL — otorgar XP
# ============================================================

def otorgar(id_usuario, codigo, objeto=None, id_curso=None,
            actor=None, meta=None, silencioso=True):
    """
    Otorga puntos a un usuario aplicando TODAS las reglas anti-abuso.

    Args:
        id_usuario : quién recibe el XP
        codigo     : código de regla_puntos (ej. 'APUNTE_APROBADO')
        objeto     : clave de idempotencia (ej. 'apunte:42'). Obligatoria si unico=1
        id_curso   : contexto para rankings por curso
        actor      : quién disparó la acción (para el chequeo de no-auto-acción)
        meta       : texto libre para auditoría
        silencioso : si True nunca lanza excepción (no rompe el request principal)

    Returns:
        dict {ok, motivo, puntos, xp_total, nivel, subio_nivel, nivel_anterior,
              logros_nuevos}
    """
    resultado = {"ok": False, "motivo": "", "puntos": 0, "xp_total": None,
                 "nivel": None, "subio_nivel": False, "nivel_anterior": None,
                 "logros_nuevos": []}

    if not id_usuario:
        resultado["motivo"] = "sin_usuario"
        return resultado

    conn = obtener_conexion()
    if not conn:
        resultado["motivo"] = "sin_conexion"
        return resultado

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        regla = _obtener_regla(cursor, codigo)
        if not regla:
            resultado["motivo"] = "regla_inexistente_o_inactiva"
            return resultado

        # ---- CAPA 2: no auto-acción ----
        if actor is not None and not regla["permite_auto"] and int(actor) == int(id_usuario):
            resultado["motivo"] = "auto_accion_bloqueada"
            return resultado

        puntos = int(regla["puntos"])

        # ---- CAPA 3: caps (solo para XP positivo) ----
        if puntos > 0:
            if regla["cap_diario"] is not None:
                if _eventos_hoy(cursor, id_usuario, codigo) >= int(regla["cap_diario"]):
                    resultado["motivo"] = "cap_diario_alcanzado"
                    return resultado

            if _xp_positivo_hoy(cursor, id_usuario) + puntos > TOPE_DIARIO_GLOBAL:
                resultado["motivo"] = "tope_global_diario"
                return resultado

            # ---- CAPA 4: cooldown ----
            if regla["cooldown_seg"]:
                if _segundos_desde_ultimo(cursor, id_usuario, codigo) < int(regla["cooldown_seg"]):
                    resultado["motivo"] = "cooldown_activo"
                    return resultado

        # ---- CAPA 1: idempotencia ----
        # Para reglas no-únicas, el objeto lleva timestamp para no colisionar
        clave = objeto
        if not regla["unico"]:
            clave = f"{objeto or codigo}@{datetime.datetime.now():%Y%m%d%H%M%S%f}"
        elif clave is None:
            clave = codigo   # regla única de por vida (ej. PERFIL_COMPLETO)

        try:
            cursor.execute("""
                INSERT INTO xp_evento
                    (id_usuario, codigo_regla, puntos, clave_objeto, id_curso, id_actor, meta)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (id_usuario, codigo, puntos, clave, id_curso, actor,
                  (meta or "")[:255]))
        except pymysql.err.IntegrityError:
            conn.rollback()
            resultado["motivo"] = "ya_otorgado"
            return resultado

        # ---- Agregado + nivel ----
        xp_nuevo, nivel_ant, nivel_new = _actualizar_agregado(cursor, id_usuario, puntos)
        conn.commit()

        resultado.update({
            "ok": True, "motivo": "otorgado", "puntos": puntos,
            "xp_total": xp_nuevo,
            "nivel": {"id": nivel_new["id"], "codigo": nivel_new["codigo"],
                      "nombre": nivel_new["nombre"]},
            "nivel_anterior": nivel_ant,
            "subio_nivel": nivel_new["id"] > nivel_ant,
        })
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"[gamificacion] Error en otorgar({codigo}): {e}")
        traceback.print_exc()
        resultado["motivo"] = "error"
        if not silencioso:
            raise
    finally:
        cursor.close()
        conn.close()

    # Los logros se evalúan fuera de la transacción principal
    if resultado["ok"]:
        try:
            resultado["logros_nuevos"] = evaluar_logros(id_usuario)
        except Exception as e:
            print(f"[gamificacion] Error al evaluar logros: {e}")

    return resultado


# ============================================================
# REVERSIÓN — anular XP de una acción deshecha
# ============================================================

def revertir(id_usuario, codigo, objeto, meta=None):
    """
    Anula el XP de una acción deshecha (apunte borrado, guardado quitado...).
    Inserta un evento negativo; NO borra del ledger.
    """
    if not id_usuario or not objeto:
        return {"ok": False, "motivo": "parametros"}

    conn = obtener_conexion()
    if not conn:
        return {"ok": False, "motivo": "sin_conexion"}

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # ¿Existe el evento original y todavía no fue revertido?
        cursor.execute("""
            SELECT puntos, id_curso FROM xp_evento
            WHERE id_usuario = %s AND codigo_regla = %s
              AND clave_objeto = %s AND es_reversion = 0
        """, (id_usuario, codigo, objeto))
        original = cursor.fetchone()
        if not original:
            return {"ok": False, "motivo": "sin_evento_original"}

        cursor.execute("""
            SELECT 1 FROM xp_evento
            WHERE id_usuario = %s AND codigo_regla = %s
              AND clave_objeto = %s AND es_reversion = 1
        """, (id_usuario, codigo, objeto))
        if cursor.fetchone():
            return {"ok": False, "motivo": "ya_revertido"}

        compensacion = -int(original["puntos"])
        cursor.execute("""
            INSERT INTO xp_evento
                (id_usuario, codigo_regla, puntos, clave_objeto, id_curso, es_reversion, meta)
            VALUES (%s, %s, %s, %s, %s, 1, %s)
        """, (id_usuario, codigo, compensacion, objeto, original["id_curso"],
              (meta or "reversión")[:255]))

        xp_nuevo, nivel_ant, nivel_new = _actualizar_agregado(cursor, id_usuario, compensacion)
        conn.commit()
        return {"ok": True, "motivo": "revertido", "puntos": compensacion,
                "xp_total": xp_nuevo, "bajo_nivel": nivel_new["id"] < nivel_ant}
    except Exception as e:
        conn.rollback()
        print(f"[gamificacion] Error en revertir({codigo}): {e}")
        traceback.print_exc()
        return {"ok": False, "motivo": "error"}
    finally:
        cursor.close()
        conn.close()


# ============================================================
# LOGROS
# ============================================================

def _calcular_metrica(cursor, clave, id_usuario):
    sql = METRICAS.get(clave)
    if not sql:
        return None
    params = (id_usuario, id_usuario) if clave in _METRICAS_DOBLE_PARAM else (id_usuario,)
    cursor.execute(sql, params)
    fila = cursor.fetchone()
    if not fila:
        return 0
    valor = list(fila.values())[0]
    return float(valor or 0)


def _cumple(valor, operador, objetivo):
    objetivo = float(objetivo)
    return {
        ">=": valor >= objetivo, ">": valor > objetivo, "=": valor == objetivo,
        "<=": valor <= objetivo, "<": valor < objetivo,
    }.get(operador, False)


def evaluar_logros(id_usuario):
    """
    Revisa todos los logros activos y desbloquea los que correspondan.
    Devuelve la lista de logros recién obtenidos.
    """
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    nuevos = []
    try:
        cursor.execute("""
            SELECT l.* FROM logro l
            LEFT JOIN usuario_logro ul
                   ON ul.codigo_logro = l.codigo AND ul.id_usuario = %s
            WHERE l.activo = 1 AND ul.codigo_logro IS NULL
            ORDER BY l.orden
        """, (id_usuario,))
        pendientes = cursor.fetchall()

        cache = {}
        for lg in pendientes:
            m = lg["metrica"]
            if m not in cache:
                cache[m] = _calcular_metrica(cursor, m, id_usuario)
            valor = cache[m]
            if valor is None:
                continue
            if _cumple(valor, lg["operador"], lg["valor"]):
                try:
                    cursor.execute("""
                        INSERT INTO usuario_logro (id_usuario, codigo_logro)
                        VALUES (%s, %s)
                    """, (id_usuario, lg["codigo"]))
                    conn.commit()
                    nuevos.append({
                        "codigo": lg["codigo"], "nombre": lg["nombre"],
                        "descripcion": lg["descripcion"], "icono": lg["icono"],
                        "xp_bonus": int(lg["xp_bonus"] or 0),
                    })
                except pymysql.err.IntegrityError:
                    conn.rollback()
    except Exception as e:
        print(f"[gamificacion] Error en evaluar_logros: {e}")
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

    # Bonus de XP por logro (fuera del cursor anterior para evitar recursión)
    for lg in nuevos:
        if lg["xp_bonus"] > 0:
            _otorgar_bonus_logro(id_usuario, lg["codigo"], lg["xp_bonus"])
    return nuevos


def _otorgar_bonus_logro(id_usuario, codigo_logro, bonus):
    """Bonus de XP por desbloquear un logro (sin re-evaluar logros → sin recursión)."""
    conn = obtener_conexion()
    if not conn:
        return
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            INSERT IGNORE INTO regla_puntos
                (codigo, descripcion, puntos, unico, permite_auto)
            VALUES ('LOGRO_BONUS', 'Bonus por desbloquear un logro', 0, 1, 1)
        """)
        cursor.execute("""
            INSERT INTO xp_evento
                (id_usuario, codigo_regla, puntos, clave_objeto, meta)
            VALUES (%s, 'LOGRO_BONUS', %s, %s, %s)
        """, (id_usuario, bonus, f"logro:{codigo_logro}", f"Logro {codigo_logro}"))
        _actualizar_agregado(cursor, id_usuario, bonus)
        conn.commit()
    except pymysql.err.IntegrityError:
        conn.rollback()
    except Exception as e:
        conn.rollback()
        print(f"[gamificacion] Error en bonus de logro: {e}")
    finally:
        cursor.close()
        conn.close()


# ============================================================
# RACHA DIARIA
# ============================================================

def registrar_actividad_diaria(id_usuario):
    """
    Actualiza la racha y otorga LOGIN_DIARIO (1 vez por día).
    Se llama desde el login.
    """
    conn = obtener_conexion()
    if not conn:
        return None
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT racha_dias, racha_maxima, ultimo_dia_activo FROM usuario_xp WHERE id_usuario = %s",
            (id_usuario,))
        fila = cursor.fetchone()
        if not fila:
            cursor.execute(
                "INSERT INTO usuario_xp (id_usuario, xp_total, id_nivel) VALUES (%s, 0, 1)",
                (id_usuario,))
            conn.commit()
            fila = {"racha_dias": 0, "racha_maxima": 0, "ultimo_dia_activo": None}

        hoy = datetime.date.today()
        ultimo = fila["ultimo_dia_activo"]

        if ultimo == hoy:
            return {"racha": fila["racha_dias"], "ya_registrado": True}

        if ultimo == hoy - datetime.timedelta(days=1):
            racha = int(fila["racha_dias"] or 0) + 1      # día consecutivo
        else:
            racha = 1                                      # se cortó la racha

        maxima = max(racha, int(fila["racha_maxima"] or 0))
        cursor.execute("""
            UPDATE usuario_xp
            SET racha_dias = %s, racha_maxima = %s, ultimo_dia_activo = %s
            WHERE id_usuario = %s
        """, (racha, maxima, hoy, id_usuario))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[gamificacion] Error en racha: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

    otorgar(id_usuario, "LOGIN_DIARIO", objeto=f"dia:{datetime.date.today()}")
    return {"racha": racha, "ya_registrado": False}


# ============================================================
# LECTURA (para perfil, rankings y API)
# ============================================================

def progreso_usuario(id_usuario):
    """Estado completo de gamificación de un usuario."""
    conn = obtener_conexion()
    if not conn:
        return {}
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT ux.xp_total, ux.xp_ganado, ux.xp_perdido,
                   ux.racha_dias, ux.racha_maxima, ux.ultimo_dia_activo,
                   n.id AS nivel_id, n.codigo AS nivel_codigo, n.nombre AS nivel_nombre,
                   n.color AS nivel_color, n.icono AS nivel_icono,
                   n.xp_minimo, n.xp_maximo, n.descripcion AS nivel_desc
            FROM usuario_xp ux
            JOIN nivel n ON ux.id_nivel = n.id
            WHERE ux.id_usuario = %s
        """, (id_usuario,))
        base = cursor.fetchone()

        if not base:
            cursor.execute(
                "INSERT IGNORE INTO usuario_xp (id_usuario, xp_total, id_nivel) VALUES (%s,0,1)",
                (id_usuario,))
            conn.commit()
            base = {"xp_total": 0, "xp_ganado": 0, "xp_perdido": 0,
                    "racha_dias": 0, "racha_maxima": 0, "ultimo_dia_activo": None,
                    "nivel_id": 1, "nivel_codigo": "principiante",
                    "nivel_nombre": "Principiante", "nivel_color": "gris",
                    "nivel_icono": "🌱", "xp_minimo": 0, "xp_maximo": 49,
                    "nivel_desc": ""}

        xp = int(base["xp_total"])

        # Progreso hacia el siguiente nivel
        cursor.execute(
            "SELECT * FROM nivel WHERE xp_minimo > %s ORDER BY xp_minimo ASC LIMIT 1", (xp,))
        siguiente = cursor.fetchone()
        if siguiente:
            piso = max(int(base["xp_minimo"]), 0)
            techo = int(siguiente["xp_minimo"])
            rango = max(techo - piso, 1)
            progreso = max(0, min(100, round((xp - piso) / rango * 100)))
            falta = max(techo - xp, 0)
        else:
            progreso, falta = 100, 0

        # Logros obtenidos
        cursor.execute("""
            SELECT l.codigo, l.nombre, l.descripcion, l.icono, l.categoria,
                   ul.fecha, ul.visto
            FROM usuario_logro ul
            JOIN logro l ON ul.codigo_logro = l.codigo
            WHERE ul.id_usuario = %s
            ORDER BY ul.fecha DESC
        """, (id_usuario,))
        obtenidos = cursor.fetchall()
        for lg in obtenidos:
            if lg.get("fecha"):
                lg["fecha"] = lg["fecha"].strftime("%Y-%m-%d")

        # Logros pendientes (los ocultos no se muestran)
        cursor.execute("""
            SELECT l.codigo, l.nombre, l.descripcion, l.icono, l.categoria,
                   l.metrica, l.valor
            FROM logro l
            LEFT JOIN usuario_logro ul
                   ON ul.codigo_logro = l.codigo AND ul.id_usuario = %s
            WHERE l.activo = 1 AND l.oculto = 0 AND ul.codigo_logro IS NULL
            ORDER BY l.orden
        """, (id_usuario,))
        pendientes = cursor.fetchall()

        # Progreso parcial de cada pendiente
        cache = {}
        for lg in pendientes:
            m = lg["metrica"]
            if m not in cache:
                cache[m] = _calcular_metrica(cursor, m, id_usuario) or 0
            objetivo = float(lg["valor"])
            lg["actual"] = round(cache[m], 1)
            lg["objetivo"] = objetivo
            lg["progreso"] = min(100, round(cache[m] / objetivo * 100)) if objetivo else 0
            lg.pop("metrica", None)
            lg.pop("valor", None)

        cursor.execute("""
            SELECT COUNT(*) AS n FROM logro WHERE activo = 1 AND oculto = 0
        """)
        total_logros = cursor.fetchone()["n"]

        if base.get("ultimo_dia_activo"):
            base["ultimo_dia_activo"] = str(base["ultimo_dia_activo"])

        return {
            "xp_total": xp,
            "xp_ganado": int(base["xp_ganado"]),
            "xp_perdido": int(base["xp_perdido"]),
            "racha_dias": int(base["racha_dias"]),
            "racha_maxima": int(base["racha_maxima"]),
            "nivel": {
                "id": base["nivel_id"], "codigo": base["nivel_codigo"],
                "nombre": base["nivel_nombre"], "color": base["nivel_color"],
                "icono": base["nivel_icono"], "descripcion": base["nivel_desc"],
            },
            "siguiente_nivel": ({
                "nombre": siguiente["nombre"], "icono": siguiente["icono"],
                "xp_minimo": int(siguiente["xp_minimo"]),
            } if siguiente else None),
            "progreso_pct": progreso,
            "xp_faltante": falta,
            "logros_obtenidos": obtenidos,
            "logros_pendientes": pendientes,
            "total_logros": total_logros,
        }
    except Exception as e:
        print(f"[gamificacion] Error en progreso_usuario: {e}")
        traceback.print_exc()
        return {}
    finally:
        cursor.close()
        conn.close()


def ranking(id_curso=None, limite=20):
    """Ranking por XP. Si id_curso, solo el XP generado en ese curso."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        if id_curso:
            cursor.execute("""
                SELECT u.id, u.nombre, u.avatar,
                       IFNULL(SUM(e.puntos), 0) AS xp,
                       n.nombre AS nivel_nombre, n.icono AS nivel_icono,
                       n.color AS nivel_color
                FROM usuario_curso uc
                JOIN Usuario u ON uc.id_usuario = u.id
                LEFT JOIN xp_evento e ON e.id_usuario = u.id AND e.id_curso = %s
                LEFT JOIN usuario_xp ux ON ux.id_usuario = u.id
                LEFT JOIN nivel n ON ux.id_nivel = n.id
                WHERE uc.id_curso = %s
                GROUP BY u.id
                ORDER BY xp DESC, u.nombre ASC
                LIMIT %s
            """, (id_curso, id_curso, limite))
        else:
            cursor.execute("""
                SELECT u.id, u.nombre, u.avatar, ux.xp_total AS xp,
                       n.nombre AS nivel_nombre, n.icono AS nivel_icono,
                       n.color AS nivel_color
                FROM usuario_xp ux
                JOIN Usuario u ON ux.id_usuario = u.id
                JOIN nivel n ON ux.id_nivel = n.id
                WHERE u.estado = 'activo'
                ORDER BY ux.xp_total DESC, u.nombre ASC
                LIMIT %s
            """, (limite,))
        filas = cursor.fetchall()
        for i, f in enumerate(filas, start=1):
            f["puesto"] = i
            f["xp"] = int(f["xp"] or 0)
        return filas
    except Exception as e:
        print(f"[gamificacion] Error en ranking: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def historial(id_usuario, limite=30):
    """Últimos movimientos de XP (para el perfil avanzado)."""
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT e.puntos, e.fecha, e.es_reversion, e.meta,
                   r.descripcion, e.codigo_regla
            FROM xp_evento e
            LEFT JOIN regla_puntos r ON e.codigo_regla = r.codigo
            WHERE e.id_usuario = %s
            ORDER BY e.fecha DESC
            LIMIT %s
        """, (id_usuario, limite))
        filas = cursor.fetchall()
        for f in filas:
            f["fecha"] = f["fecha"].strftime("%Y-%m-%d %H:%M")
            if f["es_reversion"]:
                f["descripcion"] = f"↩ Anulado: {f['descripcion'] or f['codigo_regla']}"
        return filas
    except Exception as e:
        print(f"[gamificacion] Error en historial: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def marcar_logros_vistos(id_usuario):
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE usuario_logro SET visto = 1 WHERE id_usuario = %s AND visto = 0",
            (id_usuario,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()