import pymysql
from db.conexion import obtener_conexion


def obtener_o_crear_profesor(nombre, cursor):
    """
    Devuelve el id de un profesor por nombre.
    Si no existe, lo crea. Usa un cursor ya abierto (misma transacción).
    Devuelve None si no se pasa nombre.
    """
    if not nombre or not nombre.strip():
        return None

    nombre = nombre.strip()

    # ¿Ya existe?
    cursor.execute("SELECT id FROM Profesor WHERE nombre = %s", (nombre,))
    fila = cursor.fetchone()
    if fila:
        # fila puede venir como tupla o dict según el cursor
        return fila[0] if isinstance(fila, (tuple, list)) else fila["id"]

    # No existe -> lo creamos
    cursor.execute("INSERT INTO Profesor(nombre) VALUES (%s)", (nombre,))
    return cursor.lastrowid