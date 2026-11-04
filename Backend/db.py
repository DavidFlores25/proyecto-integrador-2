import os
import queue
import threading
import time
import unicodedata
import uuid
from datetime import date, timedelta

import mysql.connector


def _leer(nombre, defecto):
    """Busca el dato en: variable de entorno -> config.py -> valor por defecto."""
    valor = os.environ.get(nombre)
    if valor:
        return valor
    try:
        import config
        valor = getattr(config, nombre, None)
        if valor not in (None, ""):
            return valor
    except ImportError:
        pass
    return defecto


def _abrir():
    host = str(_leer("DB_HOST", "localhost"))
    datos = dict(
        host=host,
        user=str(_leer("DB_USER", "root")),
        password=str(_leer("DB_PASSWORD", "")),
        database=str(_leer("DB_NAME", "restaurante")),
        port=int(_leer("DB_PORT", 3306)),
        # autocommit: las lecturas no dejan transaccion abierta (no hace falta
        # rollback = 1 viaje menos a la nube en cada consulta).
        # Las escrituras multiples usan start_transaction() explicito.
        autocommit=True,
        connection_timeout=10,
    )
    if host != "localhost":
        datos["ssl_disabled"] = False  # la base en la nube exige conexion segura
    return mysql.connector.connect(**datos)


# ---- Pool de conexiones ----
# Cada viaje a la nube cuesta ~100-300 ms y abrir una conexion nueva (TLS) cuesta
# bastante mas. Se guardan conexiones abiertas y se reutilizan desde cualquier hilo
# (si la interfaz crea un hilo nuevo por accion, un "una conexion por hilo" reconectaria siempre).
_MAX_INACTIVAS = 4          # conexiones que se mantienen abiertas
_REVISAR_SI_INACTIVA = 20   # segundos; solo si estuvo inactiva mas que esto se hace ping
_pool = queue.LifoQueue()


class _Conexion:
    def __init__(self, conn):
        self._conn = conn

    def close(self):
        """Devuelve la conexion al pool (sin viajes a la red si no hay transaccion pendiente)."""
        conn = self._conn
        if conn is None:
            return
        self._conn = None
        try:
            if conn.in_transaction:
                conn.rollback()
            if _pool.qsize() < _MAX_INACTIVAS:
                _pool.put((conn, time.monotonic()))
                return
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

    def __getattr__(self, nombre):
        return getattr(self._conn, nombre)


def conectar():
    while True:
        try:
            conn, ultimo_uso = _pool.get_nowait()
        except queue.Empty:
            break
        # Antes se hacia ping en CADA llamada (un viaje de ida y vuelta extra).
        # Ahora solo si la conexion estuvo un rato sin usarse.
        if time.monotonic() - ultimo_uso > _REVISAR_SI_INACTIVA:
            try:
                conn.ping(reconnect=False)
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
                continue
        return _Conexion(conn)
    return _Conexion(_abrir())


def precalentar():
    """Llamar UNA vez al iniciar la app: abre la conexion en segundo plano
    para que la primera accion del usuario ya la encuentre lista."""
    def _tarea():
        try:
            conectar().close()
        except Exception:
            pass
    threading.Thread(target=_tarea, daemon=True).start()


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


# Las mesas vienen en la MISMA consulta (subconsulta con GROUP_CONCAT).
# Antes se hacia una consulta extra por cada reserva (N+1): con 50 reservas = 51 viajes a la nube.
_SELECT_RESERVAS = """
    SELECT r.id, r.nombre, r.personas, r.fecha, r.hora_inicio, r.hora_fin,
           c.correo, c.telefono, e.nombre AS estado,
           (SELECT GROUP_CONCAT(rm.numero_mesa ORDER BY rm.numero_mesa)
              FROM reserva_mesas rm WHERE rm.id_reserva = r.id) AS mesas_txt
    FROM reservas r
    JOIN clientes c ON c.id_cliente = r.id_cliente
    JOIN estados  e ON e.id_estado  = r.id_estado
"""


def _mesa(valor):
    valor = valor.strip()
    try:
        return int(valor)
    except ValueError:
        return valor


def _armar_reservas(filas_reservas):
    """Agrega las claves que el resto del programa espera (dia, minutos, textos, mesas)."""
    for fila in filas_reservas:
        ini = _time_a_min(fila["hora_inicio"])
        fin = _time_a_min(fila["hora_fin"])
        fila["inicio_min"] = ini
        fila["fin_min"] = fin
        fila["inicio_str"] = _min_a_texto(ini)
        fila["fin_str"] = _min_a_texto(fin)
        fila["dia"] = _DIAS[fila["fecha"].weekday()]
        txt = fila.pop("mesas_txt", None)
        fila["mesas"] = [_mesa(m) for m in txt.split(",")] if txt else []
    return filas_reservas


def _consultar(where="", params=()):
    conn = conectar()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(_SELECT_RESERVAS + (" WHERE " + where if where else ""), params)
        return _armar_reservas(cursor.fetchall())
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
        conn.start_transaction()
        cursor = conn.cursor()

        # Buscar-o-crear cliente en UN solo viaje (requiere clientes.correo UNIQUE).
        # LAST_INSERT_ID(id_cliente) hace que lastrowid devuelva el id tanto si inserto como si ya existia.
        cursor.execute(
            """INSERT INTO clientes (correo, telefono) VALUES (%s, %s)
               ON DUPLICATE KEY UPDATE
                   id_cliente = LAST_INSERT_ID(id_cliente),
                   telefono = COALESCE(VALUES(telefono), telefono)""",
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

        # Todas las mesas en un solo INSERT multi-fila
        if mesas:
            cursor.executemany(
                "INSERT INTO reserva_mesas (id_reserva, numero_mesa) VALUES (%s, %s)",
                [(id_reserva, m) for m in mesas]
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
        # autocommit activo: no hace falta commit (un viaje menos)
        cursor.execute(
            """UPDATE reservas
               SET id_estado = (SELECT id_estado FROM estados WHERE nombre = %s)
               WHERE id = %s""",
            (nuevo_estado, id_reserva)
        )
    finally:
        conn.close()


# ==================== Estadisticas (dashboard admin) ====================

def _filtro_sql(desde, hasta, estado=None):
    """WHERE (sobre reservas r + estados e) y sus parametros para rango de fechas y estado."""
    where = "r.fecha BETWEEN %s AND %s"
    params = [desde, hasta]
    if estado == "Rechazada":
        where += " AND e.nombre LIKE 'Rechazada%%'"
    elif estado:
        where += " AND e.nombre = %s"
        params.append(estado)
    return where, params


def reservas_filtradas(desde, hasta, estado=None):
    """Listado de reservas (con mesas) del rango, ordenado por fecha y hora."""
    where, params = _filtro_sql(desde, hasta, estado)
    return _consultar(where + " ORDER BY r.fecha, r.hora_inicio", params)


def estadisticas(desde, hasta, estado=None):
    """Datos del dashboard para reservas con fecha entre desde y hasta.

    estado: None (todos), 'Pendiente', 'Aceptada' o 'Rechazada' (incluye las rechazadas por conflicto).

    Antes: 6 consultas. Ahora: 3 (los conteos por estado/dia/hora/promedio se calculan
    en Python a partir de una sola lectura).
    """
    where, params = _filtro_sql(desde, hasta, estado)

    conn = conectar()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT e.nombre, r.fecha, r.hora_inicio, r.personas "
            "FROM reservas r JOIN estados e ON e.id_estado = r.id_estado "
            f"WHERE {where}", params)
        filas = cur.fetchall()

        cur.execute(
            "SELECT rm.numero_mesa, COUNT(*) FROM reserva_mesas rm "
            "JOIN reservas r ON r.id = rm.id_reserva "
            "JOIN estados e ON e.id_estado = r.id_estado "
            f"WHERE {where} GROUP BY rm.numero_mesa", params)
        mesas = {m: n for m, n in cur.fetchall()}

        cur.execute(
            "SELECT COUNT(*) FROM reservas r JOIN estados e ON e.id_estado = r.id_estado "
            "WHERE e.nombre = 'Pendiente'")
        pendientes_global = cur.fetchone()[0]
    finally:
        conn.close()

    por_estado = {"Pendiente": 0, "Aceptada": 0, "Rechazada": 0}
    por_dia = [0] * 7
    por_hora = {}
    suma_personas = 0
    for nombre, fecha, hora_inicio, personas in filas:
        clave = "Rechazada" if nombre.startswith("Rechazada") else nombre
        por_estado[clave] = por_estado.get(clave, 0) + 1
        por_dia[fecha.weekday()] += 1
        hora = int(hora_inicio.total_seconds() // 3600)
        por_hora[hora] = por_hora.get(hora, 0) + 1
        suma_personas += personas or 0

    total = len(filas)
    return {
        "total": total,
        "promedio_personas": (suma_personas / total) if total else 0.0,
        "por_estado": por_estado,
        "por_dia": por_dia,
        "por_hora": por_hora,
        "mesas": mesas,
        "pendientes_global": pendientes_global,
    }


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
    finally:
        conn.close()


def eliminar_vendedor(nombre):
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vendedores WHERE nombre = %s", (nombre,))
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
    finally:
        conn.close()


def actualizar_vendedor(nombre_actual, nuevo_nombre=None, contrasena=None):
    """Cambia nombre y/o contraseña en un solo UPDATE. Lo que venga en None no se toca."""
    campos, valores = [], []
    if nuevo_nombre:
        campos.append("nombre = %s")
        valores.append(nuevo_nombre)
    if contrasena:
        campos.append("contrasena = %s")
        valores.append(contrasena)
    if not campos:
        return
    valores.append(nombre_actual)
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE vendedores SET {', '.join(campos)} WHERE nombre = %s",
            valores
        )
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