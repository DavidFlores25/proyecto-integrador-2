from flask import Flask, request, jsonify
from flask_cors import CORS
import db

app = Flask(__name__)
CORS(app)

@app.route("/reservas", methods=["POST"])
def nueva_reserva():
    datos = request.json
    try:
        id_reserva = db.crear_reserva(
            datos["nombre"],
            datos["personas"],
            datos["dia"],
            datos["inicio_str"],
            datos["fin_str"],
            datos["inicio_min"],
            datos["fin_min"],
            datos["mesas"]
        )
        return jsonify({"mensaje": "Reserva creada", "id": id_reserva}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/reservas/<nombre>", methods=["GET"])
def ver_estado(nombre):
    resultado = db.obtener_reservas_por_nombre(nombre)
    return jsonify(resultado)

@app.route("/mesas-disponibles", methods=["GET"])
def mesas_disponibles():
    dia = request.args.get("dia")
    inicio_min = int(request.args.get("inicio_min"))
    fin_min = int(request.args.get("fin_min"))

    reservas_dia = db.obtener_reservas_por_dia(dia)
    mesas_todas = list(range(1, 11))
    ocupadas = set()

    for res in reservas_dia:
        if not (fin_min <= res["inicio_min"] or inicio_min >= res["fin_min"]):
            for m in res["mesas"]:
                ocupadas.add(m)

    disponibles = [m for m in mesas_todas if m not in ocupadas]
    return jsonify({"disponibles": disponibles})

if __name__ == "__main__":
    app.run(debug=True)