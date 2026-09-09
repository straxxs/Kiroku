"""
Calendario académico de KIROKU.

═══════════════════════════════════════════════════════════════
ARQUITECTURA: REGISTRO DE FUENTES (provider registry)
═══════════════════════════════════════════════════════════════

El calendario NO almacena copias de datos que viven en otras tablas.
Cada "fuente" es una función que devuelve eventos NORMALIZADOS, y
obtener_eventos() las mezcla en el momento de responder.

    MODO A · PROYECCIÓN  (recomendado, es el que usamos)
        La tarea de proyecto sigue viviendo en su tabla.
        El calendario la lee en vivo -> imposible desincronizar.

    MODO B · MATERIALIZACIÓN  (solo si algún día hace falta)
        Se inserta una fila en `evento` con origen_tipo='tarea'
        y origen_id=<id>. El UNIQUE(origen_tipo, origen_id) evita
        duplicados. Requiere sincronizar en cada UPDATE/DELETE.

───────────────────────────────────────────────────────────────
CÓMO AGREGAR PROYECTOS DE EQUIPO (3 pasos, sin migrar nada):

  1) Escribir la función fuente:

        def _fuente_proyectos(ctx):
            # ctx = {cursor, id_usuario, cursos, desde, hasta, filtros}
            ctx["cursor"].execute(...)   # SELECT sobre tarea/proyecto
            return [_normalizar(...) for fila in ctx["cursor"].fetchall()]

  2) Registrarla:

        registrar_fuente("proyectos", _fuente_proyectos)

  3) Listo. El endpoint y el frontend no cambian.
───────────────────────────────────────────────────────────────
"""
import datetime
import traceback
import pymysql
from db.conexion import obtener_conexion

TIPOS_VALIDOS   = ("examen", "entrega", "tarea", "reunion", "otro")
AMBITOS_VALIDOS = ("personal", "curso", "proyecto")

MAX_TITULO      = 120
MAX_DESCRIPCION = 500
DIAS_PROXIMO    = 7        # umbral para el estado "próximo"
RANGO_MAX_DIAS  = 400      # techo del rango consultable (protege la BD)

ANIO_MIN, ANIO_MAX = 2020, 2100


# ============================================================
# REGISTRO DE FUENTES
# ============================================================

_FUENTES = {}


def registrar_fuente(nombre, funcion):
    """Registra una fuente de eventos. Ver docstring del módulo."""
    _FUENTES[nombre] = funcion


def fuentes_registradas():
    return list(_FUENTES.keys())


# ============================================================
# NORMALIZACIÓN
# ============================================================

def _normalizar(id_real, origen, tipo, ambito, titulo, fecha, hora=None,
                descripcion=None, id_curso=None, curso_nombre=None,
                id_materia=None, materia_nombre=None, id_autor=None,
                autor=None, editable=False, eliminable=False,
                completado=False, url_origen=None, color=None,
                fecha_fin=None):
    """Construye el dict normalizado. TODA fuente debe usar esta función."""
    f_str = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha)

    if hora is None:
        h_str = None
    elif isinstance(hora, datetime.timedelta):          # MySQL TIME → timedelta
        total = int(hora.total_seconds())
        h_str = f"{total // 3600:02d}:{(total % 3600) // 60:02d}"
    elif hasattr(hora, "strftime"):
        h_str = hora.strftime("%H:%M")
    else:
        h_str = str(hora)[:5]

    return {
        "id": f"{origen}:{id_real}",
        "id_real": id_real,
        "origen": origen,
        "tipo": tipo if tipo in TIPOS_VALIDOS else "otro",
        "ambito": ambito,
        "titulo": titulo,
        "descripcion": descripcion or "",
        "fecha": f_str,
        "hora": h_str,
        "fecha_fin": (fecha_fin.strftime("%Y-%m-%d")
                      if hasattr(fecha_fin, "strftime") else fecha_fin),
        "id_curso": id_curso,
        "curso_nombre": curso_nombre,
        "id_materia": id_materia,
        "materia_nombre": materia_nombre,
        "id_autor": id_autor,
        "autor": autor,
        "editable": bool(editable),
        "eliminable": bool(eliminable),
        "completado": bool(completado),
        "estado": _calcular_estado(f_str, h_str, completado),
        "url_origen": url_origen,
        "color": color,
    }


def _calcular_estado(fecha_str, hora_str, completado):
    """completado > vencido > hoy > proximo > futuro. Nunca se persiste."""
    if completado:
        return "completado"
    try:
        y, m, d = (int(x) for x in fecha_str.split("-"))
        fecha = datetime.date(y, m, d)
    except (ValueError, AttributeError):
        return "futuro"

    hoy = datetime.date.today()

    if fecha < hoy:
        return "vencido"
    if fecha == hoy:
        if hora_str:
            try:
                hh, mm = (int(x) for x in hora_str.split(":")[:2])
                ahora = datetime.datetime.now()
                if (hh, mm) < (ahora.hour, ahora.minute):
                    return "vencido"
            except ValueError:
                pass
        return "hoy"
    return "proximo" if (fecha - hoy).days <= DIAS_PROXIMO else "futuro"


# ============================================================
# FUENTE 1 · EVENTOS MANUALES (tabla `evento`)
# ============================================================

def _fuente_manual(ctx):
    cursor     = ctx["cursor"]
    id_usuario = ctx["id_usuario"]
    cursos     = ctx["cursos"]          # ids de cursos del usuario
    mods       = ctx["cursos_moderados"]
    f          = ctx["filtros"]

    # Visibilidad: mis eventos personales + eventos de mis cursos
    condiciones = ["(e.ambito = 'personal' AND e.id_usuario_creador = %s)"]
    params = [id_usuario]

    if cursos:
        ph = ",".join(["%s"] * len(cursos))
        condiciones.append(f"(e.ambito = 'curso' AND e.id_curso IN ({ph}))")
        params += list(cursos)

    sql = f"""
        SELECT e.id, e.titulo, e.descripcion, e.tipo, e.ambito,
               e.fecha, e.hora, e.fecha_fin, e.color,
               e.id_usuario_creador, e.id_curso, e.id_materia,
               u.nombre AS autor,
               c.anio, c.division,
               m.nombre AS materia_nombre,
               (SELECT 1 FROM evento_completado ec
                 WHERE ec.id_usuario = %s AND ec.origen_tipo = 'manual'
                   AND ec.origen_id = e.id) AS completado
        FROM evento e
        LEFT JOIN Usuario u ON e.id_usuario_creador = u.id
        LEFT JOIN Curso   c ON e.id_curso   = c.id
        LEFT JOIN Materia m ON e.id_materia = m.id
        WHERE e.estado = 'activo'
          AND e.fecha BETWEEN %s AND %s
          AND ({' OR '.join(condiciones)})
    """
    params = [id_usuario, ctx["desde"], ctx["hasta"]] + params

    if f.get("id_curso"):
        sql += " AND e.id_curso = %s"
        params.append(f["id_curso"])
    if f.get("id_materia"):
        sql += " AND e.id_materia = %s"
        params.append(f["id_materia"])
    if f.get("tipo"):
        sql += " AND e.tipo = %s"
        params.append(f["tipo"])

    sql += " ORDER BY e.fecha ASC, e.hora IS NULL, e.hora ASC LIMIT 500"
    cursor.execute(sql, tuple(params))

    salida = []
    for r in cursor.fetchall():
        es_autor = int(r["id_usuario_creador"]) == int(id_usuario)
        # Moderador puede gestionar eventos de curso ajenos
        puede = es_autor or (r["ambito"] == "curso" and r["id_curso"] in mods)
        salida.append(_normalizar(
            id_real=r["id"], origen="manual", tipo=r["tipo"], ambito=r["ambito"],
            titulo=r["titulo"], descripcion=r["descripcion"],
            fecha=r["fecha"], hora=r["hora"], fecha_fin=r["fecha_fin"],
            id_curso=r["id_curso"],
            curso_nombre=(f"{r['anio']}° {r['division']}°" if r["anio"] else None),
            id_materia=r["id_materia"], materia_nombre=r["materia_nombre"],
            id_autor=r["id_usuario_creador"], autor=r["autor"],
            editable=puede, eliminable=puede,
            completado=bool(r["completado"]), color=r["color"],
        ))
    return salida


registrar_fuente("manual", _fuente_manual)


# ============================================================
# FUENTE 2 · PROYECTOS DE EQUIPO  🔜 STUB
# ============================================================

_TABLAS_CACHE = {}


def _existe_tabla(cursor, nombre):
    if nombre in _TABLAS_CACHE:
        return _TABLAS_CACHE[nombre]
    try:
        cursor.execute("SHOW TABLES LIKE %s", (nombre,))
        existe = cursor.fetchone() is not None
    except Exception:
        existe = False
    _TABLAS_CACHE[nombre] = existe
    return existe


def _fuente_proyectos(ctx):
    """
    Proyecta las tareas de proyecto como eventos del calendario.

    HOY devuelve [] porque las tablas todavía no existen.
    Cuando implementes proyectos, descomentá el bloque y ajustá los
    nombres de columna. NO hay que tocar nada más del calendario.
    """
    cursor = ctx["cursor"]
    if not (_existe_tabla(cursor, "tarea") and _existe_tabla(cursor, "proyecto")):
        return []

    # ───────── PLANTILLA LISTA PARA USAR ─────────
    # f = ctx["filtros"]
    # sql = """
    #     SELECT t.id, t.titulo, t.descripcion, t.fecha_limite, t.hora_limite,
    #            t.estado AS estado_tarea,
    #            p.id AS id_proyecto, p.nombre AS proyecto_nombre,
    #            p.id_curso, p.id_materia, p.id_lider,
    #            c.anio, c.division, m.nombre AS materia_nombre,
    #            u.nombre AS autor,
    #            (SELECT 1 FROM evento_completado ec
    #               WHERE ec.id_usuario = %s AND ec.origen_tipo = 'tarea'
    #                 AND ec.origen_id = t.id) AS completado
    #     FROM tarea t
    #     JOIN proyecto p            ON t.id_proyecto = p.id
    #     JOIN proyecto_miembro pm   ON pm.id_proyecto = p.id AND pm.id_usuario = %s
    #     LEFT JOIN Curso   c ON p.id_curso   = c.id
    #     LEFT JOIN Materia m ON p.id_materia = m.id
    #     LEFT JOIN Usuario u ON t.id_asignado = u.id
    #     WHERE t.fecha_limite BETWEEN %s AND %s
    #     ORDER BY t.fecha_limite ASC
    #     LIMIT 300
    # """
    # cursor.execute(sql, (ctx["id_usuario"], ctx["id_usuario"],
    #                      ctx["desde"], ctx["hasta"]))
    # salida = []
    # for r in cursor.fetchall():
    #     salida.append(_normalizar(
    #         id_real=r["id"], origen="tarea", tipo="tarea", ambito="proyecto",
    #         titulo=f"{r['titulo']} · {r['proyecto_nombre']}",
    #         descripcion=r["descripcion"],
    #         fecha=r["fecha_limite"], hora=r["hora_limite"],
    #         id_curso=r["id_curso"],
    #         curso_nombre=(f"{r['anio']}° {r['division']}°" if r["anio"] else None),
    #         id_materia=r["id_materia"], materia_nombre=r["materia_nombre"],
    #         autor=r["autor"],
    #         editable=False,      # ⬅ se edita EN EL PROYECTO, no acá
    #         eliminable=False,
    #         completado=bool(r["completado"]) or r["estado_tarea"] == "completada",
    #         url_origen=f"/proyecto/{r['id_proyecto']}#tarea-{r['id']}",
    #         color="violeta",
    #     ))
    # return salida
    return []


registrar_fuente("proyectos", _fuente_proyectos)


# ============================================================
# LECTURA · mezcla de todas las fuentes
# ============================================================

def obtener_eventos(id_usuario, cursos, cursos_moderados,
                    desde=None, hasta=None, filtros=None):
    """
    Devuelve los eventos visibles para el usuario en un rango.

    Args:
        cursos           : ids de cursos a los que pertenece
        cursos_moderados : ids de cursos que modera (define permisos de edición)
        desde / hasta    : 'YYYY-MM-DD' (por defecto: mes actual ±1)
        filtros          : {id_curso, id_materia, tipo, ocultar_completados}
    """
    hoy = datetime.date.today()
    if not desde:
        desde = (hoy.replace(day=1) - datetime.timedelta(days=40)).isoformat()
    if not hasta:
        hasta = (hoy + datetime.timedelta(days=90)).isoformat()

    # Techo de rango: protege la BD de un ?desde=1900&hasta=2100
    try:
        d1 = datetime.date.fromisoformat(desde)
        d2 = datetime.date.fromisoformat(hasta)
        if (d2 - d1).days > RANGO_MAX_DIAS:
            d2 = d1 + datetime.timedelta(days=RANGO_MAX_DIAS)
            hasta = d2.isoformat()
        if d2 < d1:
            desde, hasta = hasta, desde
    except ValueError:
        return []

    filtros = filtros or {}
    conn = obtener_conexion()
    if not conn:
        return []
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    eventos = []
    try:
        ctx = {
            "cursor": cursor,
            "id_usuario": id_usuario,
            "cursos": list(cursos or []),
            "cursos_moderados": set(cursos_moderados or []),
            "desde": desde,
            "hasta": hasta,
            "filtros": filtros,
        }
        for nombre, fuente in _FUENTES.items():
            try:
                eventos.extend(fuente(ctx) or [])
            except Exception as e:
                # Una fuente rota NO debe tumbar el calendario completo
                print(f"[calendario] Fuente '{nombre}' falló: {e}")
                traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

    if filtros.get("ocultar_completados"):
        eventos = [e for e in eventos if not e["completado"]]

    eventos.sort(key=lambda e: (e["fecha"], e["hora"] or "99:99"))
    return eventos


def proximos_eventos(id_usuario, cursos, cursos_moderados, limite=5, dias=30):
    """Widget de inicio: próximos N eventos no completados (incluye vencidos recientes)."""
    hoy = datetime.date.today()
    eventos = obtener_eventos(
        id_usuario, cursos, cursos_moderados,
        desde=(hoy - datetime.timedelta(days=7)).isoformat(),
        hasta=(hoy + datetime.timedelta(days=dias)).isoformat(),
        filtros={"ocultar_completados": True},
    )
    orden = {"vencido": 0, "hoy": 1, "proximo": 2, "futuro": 3}
    eventos.sort(key=lambda e: (orden.get(e["estado"], 9),
                                e["fecha"], e["hora"] or "99:99"))
    return eventos[:limite]


def obtener_evento(id_evento):
    """Evento manual crudo (para validar permisos antes de editar/borrar)."""
    conn = obtener_conexion()
    if not conn:
        return None
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT id, titulo, descripcion, tipo, ambito, fecha, hora, fecha_fin,
                   id_usuario_creador, id_curso, id_materia, origen_tipo, estado
            FROM evento WHERE id = %s
        """, (id_evento,))
        return cursor.fetchone()
    except Exception as e:
        print(f"[calendario] Error al obtener evento: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ============================================================
# VALIDACIÓN
# ============================================================

def validar_datos(titulo, fecha, hora=None, fecha_fin=None,
                  descripcion=None, tipo=None, ambito=None):
    """Valida el payload. Devuelve (ok, mensaje, datos_limpios)."""
    d = {}

    t = (titulo or "").strip()
    if not t:
        return False, "El título es obligatorio.", {}
    if len(t) > MAX_TITULO:
        return False, f"El título no puede superar {MAX_TITULO} caracteres.", {}
    d["titulo"] = t

    if not fecha:
        return False, "La fecha es obligatoria.", {}
    try:
        f = datetime.date.fromisoformat(fecha.strip())
    except (ValueError, AttributeError):
        return False, "Fecha inválida (formato AAAA-MM-DD).", {}
    if not (ANIO_MIN <= f.year <= ANIO_MAX):
        return False, f"El año debe estar entre {ANIO_MIN} y {ANIO_MAX}.", {}
    d["fecha"] = f.isoformat()

    h = (hora or "").strip()
    if h:
        try:
            hh, mm = (int(x) for x in h.split(":")[:2])
            if not (0 <= hh <= 23 and 0 <= mm <= 59):
                raise ValueError
            d["hora"] = f"{hh:02d}:{mm:02d}"
        except (ValueError, IndexError):
            return False, "Hora inválida (formato HH:MM).", {}
    else:
        d["hora"] = None

    ff = (fecha_fin or "").strip()
    if ff:
        try:
            f2 = datetime.date.fromisoformat(ff)
        except ValueError:
            return False, "Fecha de fin inválida.", {}
        if f2 < f:
            return False, "La fecha de fin no puede ser anterior a la de inicio.", {}
        d["fecha_fin"] = f2.isoformat()
    else:
        d["fecha_fin"] = None

    desc = (descripcion or "").strip()
    if len(desc) > MAX_DESCRIPCION:
        return False, f"La descripción no puede superar {MAX_DESCRIPCION} caracteres.", {}
    d["descripcion"] = desc or None

    d["tipo"] = tipo if tipo in TIPOS_VALIDOS else "otro"
    d["ambito"] = ambito if ambito in AMBITOS_VALIDOS else "personal"
    return True, "", d


def materia_pertenece_a_curso(id_materia, id_curso):
    """Evita etiquetar un evento con una materia de otro curso."""
    if not id_materia:
        return True
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM Materia WHERE id = %s AND id_curso = %s",
                       (id_materia, id_curso))
        return cursor.fetchone() is not None
    except Exception:
        return False
    finally:
        cursor.close()
        conn.close()


# ============================================================
# ESCRITURA
# ============================================================

def crear_evento(datos, id_usuario, id_curso=None, id_materia=None, color=None):
    conn = obtener_conexion()
    if not conn:
        return False, "Sin conexión a la base de datos."
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO evento
                (titulo, descripcion, tipo, ambito, fecha, hora, fecha_fin,
                 id_usuario_creador, id_curso, id_materia, color, origen_tipo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'manual')
        """, (datos["titulo"], datos["descripcion"], datos["tipo"], datos["ambito"],
              datos["fecha"], datos["hora"], datos["fecha_fin"],
              id_usuario, id_curso, id_materia, color))
        conn.commit()
        return cursor.lastrowid, ""
    except Exception as e:
        conn.rollback()
        print(f"[calendario] Error al crear: {e}")
        traceback.print_exc()
        return False, "No se pudo crear el evento."
    finally:
        cursor.close()
        conn.close()


def editar_evento(id_evento, datos, id_curso=None, id_materia=None):
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE evento
            SET titulo=%s, descripcion=%s, tipo=%s, ambito=%s,
                fecha=%s, hora=%s, fecha_fin=%s,
                id_curso=%s, id_materia=%s, fecha_edicion=NOW()
            WHERE id=%s AND origen_tipo='manual'
        """, (datos["titulo"], datos["descripcion"], datos["tipo"], datos["ambito"],
              datos["fecha"], datos["hora"], datos["fecha_fin"],
              id_curso, id_materia, id_evento))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"[calendario] Error al editar: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def eliminar_evento(id_evento):
    conn = obtener_conexion()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM evento_completado "
                       "WHERE origen_tipo='manual' AND origen_id=%s", (id_evento,))
        cursor.execute("DELETE FROM evento WHERE id=%s AND origen_tipo='manual'",
                       (id_evento,))
        borrado = cursor.rowcount > 0
        conn.commit()
        return borrado
    except Exception as e:
        conn.rollback()
        print(f"[calendario] Error al eliminar: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def alternar_completado(id_usuario, origen_tipo, origen_id):
    """Marca/desmarca como completado (por usuario). → 'completado'|'pendiente'|None"""
    conn = obtener_conexion()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 1 FROM evento_completado
            WHERE id_usuario=%s AND origen_tipo=%s AND origen_id=%s
        """, (id_usuario, origen_tipo, origen_id))
        if cursor.fetchone():
            cursor.execute("""
                DELETE FROM evento_completado
                WHERE id_usuario=%s AND origen_tipo=%s AND origen_id=%s
            """, (id_usuario, origen_tipo, origen_id))
            conn.commit()
            return "pendiente"
        cursor.execute("""
            INSERT INTO evento_completado (id_usuario, origen_tipo, origen_id)
            VALUES (%s,%s,%s)
        """, (id_usuario, origen_tipo, origen_id))
        conn.commit()
        return "completado"
    except Exception as e:
        conn.rollback()
        print(f"[calendario] Error en completado: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def contar_eventos_curso(id_usuario):
    """Métrica para el logro ORGANIZADO."""
    conn = obtener_conexion()
    if not conn:
        return 0
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM evento
            WHERE id_usuario_creador=%s AND ambito='curso' AND estado='activo'
        """, (id_usuario,))
        return cursor.fetchone()[0]
    except Exception:
        return 0
    finally:
        cursor.close()
        conn.close()