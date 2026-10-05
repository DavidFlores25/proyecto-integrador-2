import uuid
import unicodedata
from datetime import date, timedelta

import mysql.connector


def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="restaurante"
    )


# ==================== Utilidades ====================

_DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]


def _norm(texto):
    """Quita tildes y pasa a minusculas: 'Miércoles' -> 'miercoles'."""
    texto = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower().strip()


def _indice_dia(dia):
    for i, d in enumerate(_DIAS):
        if _norm(d) == _norm(dia):
            return i
    return None


def _proxima_fecha_de_dia(dia):
    """Fecha del proximo 'dia' de la semana (hoy cuenta si coincide)."""
    idx = _indice_dia(dia)
    if idx is None:
        return date.today()
    return date.today() + timedelta(days=(idx - date.today().weekday()) % 7)


def _min_a_time(minutos):
    return f"{int(minutos) // 60:02d}:{int(minutos) % 60:02d}:00"


def _time_a_min(valor):
    # mysql.connector devuelve TIME como timedelta
    return int(valor.total_seconds() // 60)


def _min_a_texto(minutos):
    h, m = divmod(int(minutos), 60)
    h = h % 24
    sufijo = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d}{sufijo}"


_SELECT_RESERVAS = """
    SELECT r.id, r.nombre, r.personas, r.fecha, r.hora_inicio, r.hora_fin,
           c.correo, c.telefono, e.nombre AS estado
    FROM reservas r
    JOIN clientes c ON c.id_cliente = r.id_cliente
    JOIN estados  e ON e.id_estado  = r.id_estado
"""


def _armar_reserva_con_mesas(cursor, filas_reservas):
    """Agrega las claves que el resto del programa espera (dia, minutos, textos, mesas)."""
    resultado = []
    for fila in filas_reservas:
        ini = _time_a_min(fila["hora_inicio"])
        fin = _time_a_min(fila["hora_fin"])
        fila["inicio_min"] = ini
        fila["fin_min"] = fin
        fila["inicio_str"] = _min_a_texto(ini)
        fila["fin_str"] = _min_a_texto(fin)
        fila["dia"] = _DIAS[fila["fecha"].weekday()]
        cursor.execute(
            "SELECT numero_mesa FROM reserva_mesas WHERE id_reserva = %s ORDER BY numero_mesa",
            (fila["id"],)
        )
        fila["mesas"] = [m["numero_mesa"] for m in cursor.fetchall()]
        resultado.append(fila)
    return resultado


def _consultar(where="", params=()):
    conn = conectar()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(_SELECT_RESERVAS + (" WHERE " + where if where else ""), params)
        filas = cursor.fetchall()
        return _armar_reserva_con_mesas(cursor, filas)
    finally:
        conn.close()


# ==================== Reservas ====================

def crear_reserva(nombre, personas, dia, inicio_str, fin_str, inicio_min, fin_min,
                  mesas, telefono=None, correo="", fecha=None):
    # inicio_str y fin_str ya no se guardan: se calculan desde hora_inicio/hora_fin.
    if fecha is None:
        fecha = _proxima_fecha_de_dia(dia)

    correo = (correo or "").strip()
    if not correo:
        # clientes.correo es obligatorio y unico
        correo = f"sin_correo_{uuid.uuid4().hex[:12]}@ejemplo.local"
    telefono = (telefono or None)

    conn = conectar()
    try:
        cursor = conn.cursor()

        # Buscar o crear cliente por correo
        cursor.execute("SELECT id_cliente FROM clientes WHERE correo = %s", (correo,))
        fila = cursor.fetchone()
        if fila:
            id_cliente = fila[0]
            if telefono:
                cursor.execute(
                    "UPDATE clientes SET telefono = %s WHERE id_cliente = %s",
                    (telefono, id_cliente)
                )
        else:
            cursor.execute(
                "INSERT INTO clientes (correo, telefono) VALUES (%s, %s)",
                (correo, telefono)
            )
            id_cliente = cursor.lastrowid

        # Reserva (estado inicial: Pendiente)
        cursor.execute(
            """INSERT INTO reservas
               (nombre, id_cliente, personas, fecha, hora_inicio, hora_fin, id_estado)
               VALUES (%s, %s, %s, %s, %s, %s,
                       (SELECT id_estado FROM estados WHERE nombre = 'Pendiente'))""",
            (nombre, id_cliente, personas, fecha,
             _min_a_time(inicio_min), _min_a_time(fin_min))
        )
        id_reserva = cursor.lastrowid

        for m in mesas:
            cursor.execute(
                "INSERT INTO reserva_mesas (id_reserva, numero_mesa) VALUES (%s, %s)",
                (id_reserva, m)
            )
        conn.commit()
        return id_reserva
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def obtener_reservas_por_dia(dia):
    """Reservas ACEPTADAS cuya fecha cae en ese dia de la semana."""
    idx = _indice_dia(dia)
    if idx is None:
        return []
    return _consultar("e.nombre = 'Aceptada' AND WEEKDAY(r.fecha) = %s", (idx,))


def obtener_reservas_por_nombre(nombre):
    return _consultar("r.nombre = %s", (nombre,))


def obtener_reservas_por_fecha(fecha):
    """Reservas ACEPTADAS de una fecha exacta (las que bloquean mesas)."""
    return _consultar("r.fecha = %s AND e.nombre = 'Aceptada'", (fecha,))


def obtener_reservas_pendientes():
    return _consultar("e.nombre = 'Pendiente'")


def obtener_reservas_aceptadas():
    return _consultar("e.nombre = 'Aceptada'")


def obtener_reservas_por_estado(estado):
    return _consultar("e.nombre = %s", (estado,))


def obtener_todas_las_reservas():
    return _consultar()


def actualizar_estado_reserva(id_reserva, nuevo_estado):
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE reservas
               SET id_estado = (SELECT id_estado FROM estados WHERE nombre = %s)
               WHERE id = %s""",
            (nuevo_estado, id_reserva)
        )
        conn.commit()
    finally:
        conn.close()


# ==================== Vendedores / usuarios ====================

def obtener_contrasena_vendedor(nombre):
    conn = conectar()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT contrasena FROM vendedores WHERE nombre = %s", (nombre,))
        fila = cursor.fetchone()
    finally:
        conn.close()
    return fila["contrasena"] if fila else None


def existe_vendedor(nombre):
    return obtener_contrasena_vendedor(nombre) is not None


def obtener_vendedores():
    conn = conectar()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre, contrasena FROM vendedores")
        filas = cursor.fetchall()
    finally:
        conn.close()
    return {f["nombre"]: f["contrasena"] for f in filas}


def crear_vendedor(nombre, contrasena):
    # id_rol usa su valor por defecto (1 = Vendedor)
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO vendedores (nombre, contrasena) VALUES (%s, %s)",
            (nombre, contrasena)
        )
        conn.commit()
    finally:
        conn.close()


def crear_vendedor_con_rol(nombre, contrasena, rol):
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO vendedores (nombre, contrasena, id_rol)
               VALUES (%s, %s, (SELECT id_rol FROM roles WHERE nombre = %s))""",
            (nombre, contrasena, rol)
        )
        conn.commit()
    finally:
        conn.close()


def eliminar_vendedor(nombre):
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vendedores WHERE nombre = %s", (nombre,))
        conn.commit()
    finally:
        conn.close()


def actualizar_password_vendedor(nombre, nueva_contrasena):
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE vendedores SET contrasena = %s WHERE nombre = %s",
            (nueva_contrasena, nombre)
        )
        conn.commit()
    finally:
        conn.close()


def obtener_rol_vendedor(nombre):
    """Devuelve el nombre del rol del usuario (por defecto 'Vendedor')."""
    try:
        conn = conectar()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT r.nombre AS rol
                   FROM vendedores v
                   JOIN roles r ON r.id_rol = v.id_rol
                   WHERE v.nombre = %s""",
                (nombre,)
            )
            fila = cursor.fetchone()
        finally:
            conn.close()
    except mysql.connector.Error:
        return "Vendedor"
    return fila["rol"] if fila else "Vendedor"