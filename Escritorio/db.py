import mysql.connector

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="restaurante"
    )

# ==================== Reservas ====================

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

def _armar_reserva_con_mesas(cursor, filas_reservas):
    resultado = []
    for fila in filas_reservas:
        cursor.execute("SELECT numero_mesa FROM reserva_mesas WHERE id_reserva = %s", (fila["id"],))
        mesas = [m["numero_mesa"] for m in cursor.fetchall()]
        fila["mesas"] = mesas
        resultado.append(fila)
    return resultado

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

def obtener_reservas_pendientes():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reservas WHERE estado = 'Pendiente'")
    filas = cursor.fetchall()
    resultado = _armar_reserva_con_mesas(cursor, filas)
    conn.close()
    return resultado

def obtener_reservas_aceptadas():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reservas WHERE estado = 'Aceptada'")
    filas = cursor.fetchall()
    resultado = _armar_reserva_con_mesas(cursor, filas)
    conn.close()
    return resultado

def actualizar_estado_reserva(id_reserva, nuevo_estado):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE reservas SET estado = %s WHERE id = %s", (nuevo_estado, id_reserva))
    conn.commit()
    conn.close()

# ==================== Vendedores ====================

def obtener_contrasena_vendedor(nombre):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT contrasena FROM vendedores WHERE nombre = %s", (nombre,))
    fila = cursor.fetchone()
    conn.close()
    if fila:
        return fila["contrasena"]
    return None

def existe_vendedor(nombre):
    return obtener_contrasena_vendedor(nombre) is not None

def crear_vendedor(nombre, contrasena):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vendedores (nombre, contrasena) VALUES (%s, %s)", (nombre, contrasena))
    conn.commit()
    conn.close()

def eliminar_vendedor(nombre):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendedores WHERE nombre = %s", (nombre,))
    conn.commit()
    conn.close()

def actualizar_contrasena_vendedor(nombre, nueva_contrasena):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE vendedores SET contrasena = %s WHERE nombre = %s", (nueva_contrasena, nombre))
    conn.commit()
    conn.close()