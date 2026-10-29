"""
Servidor Flask de Don Bigote.

- Sirve la página web (index.html, css, javascript, imágenes).
- Expone una API JSON que usa db.py (la misma base de datos MySQL de la app de escritorio).

Ejecutar:   python app.py      ->   http://localhost:5000
"""
import re
from datetime import date, datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

import db

# ---------- Reglas del negocio (iguales a la app de escritorio) ----------
DIAS_ADELANTE = 60
LIMITE_PERSONAS = 10
MESAS = list(range(1, 11))
APERTURA_MIN = 8 * 60      # 8:00 AM
CIERRE_MIN = 23 * 60       # 11:00 PM

BASE = Path(__file__).resolve().parent.parent / "website"
app = Flask(__name__, static_folder=None)


# ==================== Archivos de la página ====================
@app.route("/")
def inicio():
    return send_from_directory(BASE, "index.html")


# index.html usa Assets/ y assets/ (en Linux importa la mayúscula), css/, javascript/ e img/
@app.route("/<any(css,javascript,Assets,assets,img):carpeta>/<path:archivo>")
def estaticos(carpeta, archivo):
    return send_from_directory(BASE / carpeta, archivo)


# ==================== Validaciones ====================
class ErrorValidacion(ValueError):
    pass


def validar_nombre(nombre):
    return nombre.replace(" ", "").isalpha() and len(nombre) > 1


def validar_correo(texto):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", texto) is not None


def validar_telefono(texto):
    """Opcional. Si se escribe: solo dígitos, espacios, + y -, entre 8 y 15 dígitos."""
    if not texto:
        return True
    if not re.fullmatch(r"[0-9+\-\s]+", texto):
        return False
    return 8 <= len(re.sub(r"\D", "", texto)) <= 15


def hora_a_minutos(texto):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", texto or "")
    if not m or int(m[1]) > 23 or int(m[2]) > 59:
        raise ErrorValidacion("Formato de hora inválido.")
    return int(m[1]) * 60 + int(m[2])


def validar_fecha_y_horario(fecha_txt, inicio_txt, fin_txt):
    """Devuelve (fecha, inicio_min, fin_min) o lanza ErrorValidacion con el mensaje para el cliente."""
    try:
        fecha = date.fromisoformat(fecha_txt or "")
    except ValueError:
        raise ErrorValidacion("Fecha inválida.")

    hoy = date.today()
    if fecha < hoy:
        raise ErrorValidacion("No se puede reservar en una fecha que ya pasó.")
    if (fecha - hoy).days > DIAS_ADELANTE:
        raise ErrorValidacion(f"Solo se puede reservar hasta {DIAS_ADELANTE} días hacia adelante.")
    if fecha.weekday() == 0:
        raise ErrorValidacion("El restaurante está cerrado los lunes. Elija otra fecha.")

    inicio = hora_a_minutos(inicio_txt)
    fin = hora_a_minutos(fin_txt)
    if inicio < APERTURA_MIN:
        raise ErrorValidacion("El restaurante abre a las 8:00 AM.")
    if fin > CIERRE_MIN:
        raise ErrorValidacion("El restaurante cierra a las 11:00 PM.")
    if inicio >= fin:
        raise ErrorValidacion("La hora de fin debe ser mayor que la de inicio.")
    if fecha == hoy:
        ahora = datetime.now()
        if inicio <= ahora.hour * 60 + ahora.minute:
            raise ErrorValidacion("Para hoy, la hora de inicio debe ser posterior a la hora actual.")
    return fecha, inicio, fin


def mesas_ocupadas(fecha, inicio_min, fin_min):
    """Mesas con una reserva ACEPTADA que se cruza con el horario pedido."""
    ocupadas = set()
    for res in db.obtener_reservas_por_fecha(fecha):
        if not (fin_min <= res["inicio_min"] or inicio_min >= res["fin_min"]):
            ocupadas.update(res["mesas"])
    return ocupadas


def respuesta_error(mensaje, codigo=400):
    return jsonify(error=mensaje), codigo


@app.errorhandler(Exception)
def error_inesperado(e):
    # Errores de MySQL u otros: se registran en consola y el cliente ve un mensaje genérico
    if isinstance(e, HTTPException):
        return respuesta_error(e.description, e.code)
    app.logger.exception("Error inesperado")
    return respuesta_error("No pudimos procesar la solicitud. Intente de nuevo en un momento.", 500)


# ==================== API ====================
@app.get("/api/mesas")
def api_mesas():
    """?fecha=2026-10-07&inicio=12:00&fin=14:00  ->  estado de cada mesa en ese horario."""
    try:
        fecha, ini, fin = validar_fecha_y_horario(
            request.args.get("fecha"), request.args.get("inicio"), request.args.get("fin"))
    except ErrorValidacion as e:
        return respuesta_error(str(e))

    ocupadas = mesas_ocupadas(fecha, ini, fin)
    return jsonify(mesas=[{"numero": m, "libre": m not in ocupadas} for m in MESAS])


@app.post("/api/reservas")
def api_crear_reserva():
    datos = request.get_json(silent=True) or {}

    nombre = str(datos.get("nombre", "")).strip()
    correo = str(datos.get("correo", "")).strip()
    telefono = str(datos.get("telefono", "")).strip()

    if not validar_nombre(nombre) or len(nombre) > 100:
        return respuesta_error("Nombre inválido. Solo letras y mínimo 2 caracteres.")
    if not correo:
        return respuesta_error("El correo electrónico es obligatorio.")
    if not validar_correo(correo) or len(correo) > 100:
        return respuesta_error("Correo inválido. Use el formato ejemplo@gmail.com")
    if not validar_telefono(telefono) or len(telefono) > 20:
        return respuesta_error("Teléfono inválido. Use solo números (mínimo 8 dígitos).")

    try:
        personas = int(datos.get("personas"))
    except (TypeError, ValueError):
        return respuesta_error("Número de personas inválido.")
    if personas < 1:
        return respuesta_error("Número de personas inválido.")
    if personas > LIMITE_PERSONAS:
        return respuesta_error(f"No puede superar el límite de {LIMITE_PERSONAS} personas.")

    try:
        fecha, ini, fin = validar_fecha_y_horario(
            datos.get("fecha"), datos.get("inicio"), datos.get("fin"))
    except ErrorValidacion as e:
        return respuesta_error(str(e))

    mesas = datos.get("mesas")
    if not isinstance(mesas, list) or not mesas:
        return respuesta_error("Debe seleccionar al menos una mesa.")
    try:
        mesas = sorted({int(m) for m in mesas})
    except (TypeError, ValueError):
        return respuesta_error("Mesas inválidas.")
    if any(m not in MESAS for m in mesas):
        return respuesta_error("Mesas inválidas.")

    # Se vuelve a verificar aquí: otra persona pudo ocupar la mesa mientras el cliente llenaba el formulario
    if set(mesas) & mesas_ocupadas(fecha, ini, fin):
        return respuesta_error("Alguna de las mesas elegidas ya fue ocupada en ese horario. Verifique de nuevo.", 409)

    # dia, inicio_str y fin_str ya no se usan en db.crear_reserva cuando se manda la fecha
    id_reserva = db.crear_reserva(nombre, personas, "", "", "", ini, fin,
                                  mesas, telefono or None, correo, fecha)

    return jsonify(
        id=id_reserva,
        mensaje="Reserva solicitada. Queda pendiente de aprobación por parte del restaurante."
    ), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)