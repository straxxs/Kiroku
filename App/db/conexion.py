import pymysql

def obtener_conexion():
    try:
        conn = pymysql.connect(
            host= "127.0.0.1",
            port = 3307,
            user= "root",
            password= "",
            database= "apuntes_db"
        )
        return conn
    except pymysql.MySQLError as e:
        print("error al conectar la base de datos: {e}")
        return None