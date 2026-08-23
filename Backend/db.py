import mysql.connector
import config

def conectar():
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME
    )

def _armar_reserva_con_mesas(cursor, filas_reservas):
    resultado = []
    for fila in filas_reservas:
        cursor.execute("SELECT numero_mesa FROM reserva_mesas WHERE id_reserva = %s", (fila["id"],))
        mesas = [m["numero_mesa"] for m in cursor.fetchall()]
        fila["mesas"] = mesas
        resultado.append(fila)
    return resultado

def crear_reserva(nombre, personas, dia, inicio_str, fin_str, inicio_min, fin_min, mesas):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reservas (nombre, personas, dia, inicio_str, fin_str, inicio_min, fin_min, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pendiente')",
        (nombre, personas, dia, inicio_str, fin_str, inicio_min, fin_min)
    )
    id_reserva = cursor.lastrowid
    for m in mesas:
        cursor.execute(
            "INSERT INTO reserva_mesas (id_reserva, numero_mesa) VALUES (%s, %s)",
            (id_reserva, m)
        )
    conn.commit()
    conn.close()
    return id_reserva

def obtener_reservas_por_dia(dia):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reservas WHERE dia = %s AND estado != 'Rechazada'", (dia,))
    filas = cursor.fetchall()
    resultado = _armar_reserva_con_mesas(cursor, filas)
    conn.close()
    return resultado

def obtener_reservas_por_nombre(nombre):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reservas WHERE nombre = %s", (nombre,))
    filas = cursor.fetchall()
    resultado = _armar_reserva_con_mesas(cursor, filas)
    conn.close()
    return resultado