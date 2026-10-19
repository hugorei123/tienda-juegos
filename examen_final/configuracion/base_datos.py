import psycopg

# Unico lugar donde se configuran los datos de conexion de la plantilla.
CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "tienda_juegos",
    "user": "postgres",
    "password": "",
}


def obtener_conexion():
    """
    Crea y devuelve una conexion nueva a PostgreSQL.
    El RepositorioGenerico se encarga de commit/rollback y cierre.
    """
    return psycopg.connect(**CONFIG)