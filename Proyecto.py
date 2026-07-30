# ==================== Cover OS - Sistema de Reservas ====================

# ---------- Datos Iniciales ----------
mesas_disponibles = list(range(1, 11))  # 10 mesas
reservas_pendientes = []
reservas_aceptadas = []
reservas_rechazadas = []  # <--- NUEVA LISTA PARA GUARDAR RECHAZADAS

vendedores = {
    "Eliezer": "Romero",
    "Darwin": "Eduardo"
}

limite_personas = 4
dias_semana = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

# ==================== Funciones de validación ====================

def validar_nombre(nombre):
    try:
        return nombre.replace(" ", "").isalpha() and len(nombre) > 1
    except:
        return False

def validar_numero_personas(num):
    try:
        n = int(num)
        return n > 0
    except:
        return False

def validar_dia(dia):
    return dia.capitalize() in dias_semana and dia.capitalize() != "Lunes"

def validar_hora(hora):
    try:
        hora = hora.strip().upper()
        if not ("AM" in hora or "PM" in hora):
            return False
        tiempo, meridiano = hora[:-2], hora[-2:]
        h, m = map(int, tiempo.split(":"))
        if meridiano not in ["AM", "PM"]:
            return False
        if not (1 <= h <= 12 and 0 <= m < 60):
            return False
        return True
    except:
        return False

def hora_a_minutos(hora_str):
    hora_str = hora_str.strip().upper()
    tiempo, meridiano = hora_str[:-2], hora_str[-2:]
    h, m = map(int, tiempo.split(":"))
    if meridiano == "PM" and h != 12:
        h += 12
    if meridiano == "AM" and h == 12:
        h = 0
    return h*60 + m

# ==================== Funciones Cliente ====================

def pedir_nombre_reserva():
    while True:
        nombre = input("Ingrese nombre de la reserva: ").strip()
        if validar_nombre(nombre):
            return nombre
        print("Nombre inválido. Solo letras y mínimo 2 caracteres.")

def pedir_numero_personas():
    while True:
        num = input(f"Ingrese número de personas (máx {limite_personas} por mesa): ").strip()
        if validar_numero_personas(num):
            if int(num) <= limite_personas:
                return int(num)
            else:
                print(f"No puede superar el límite de {limite_personas} personas.")
        else:
            print("Número inválido.")

def pedir_dia():
    while True:
        dia = input("Ingrese día de la reserva (no lunes): ").strip().capitalize()
        if validar_dia(dia):
            return dia
        print("Día inválido o restaurante cerrado.")

def pedir_horario():
    while True:
        hora_inicio = input("Ingrese hora de inicio (HH:MM AM/PM): ").strip().upper()
        hora_fin = input("Ingrese hora de fin (HH:MM AM/PM, máximo 11:00 PM): ").strip().upper()

        if not (validar_hora(hora_inicio) and validar_hora(hora_fin)):
            print("Formato de hora inválido. Ejemplo correcto: 8:30 AM o 10:00 PM")
            continue

        inicio_min = hora_a_minutos(hora_inicio)
        fin_min = hora_a_minutos(hora_fin)

        apertura = hora_a_minutos("8:00 AM")
        cierre = hora_a_minutos("11:00 PM")

        # No permitir reservar antes de 8 AM
        if inicio_min < apertura:
            print("El restaurante abre a las 8:00 AM. Seleccione una hora dentro del horario.")
            continue

        # No permitir reservar después del cierre
        if fin_min > cierre:
            print("El restaurante cierra a las 11:00 PM. Ajuste la hora de fin.")
            continue

        # Validar que la hora de fin sea mayor a la de inicio
        if inicio_min >= fin_min:
            print("La hora de fin debe ser mayor que la hora de inicio.")
            continue

        return hora_inicio, hora_fin, inicio_min, fin_min

def registrar_reserva_cliente():
    print("\n=== Solicitar Reserva ===")
    nombre = pedir_nombre_reserva()
    num_personas = pedir_numero_personas()
    dia = pedir_dia()
    hora_inicio_str, hora_fin_str, inicio_min, fin_min = pedir_horario()

    print("\nMesas disponibles para ese horario:")
    mesas_validas = []
    for m in mesas_disponibles:
        ocupado = False
        for res in reservas_aceptadas + reservas_pendientes:
            if m in res["mesas"] and res["dia"] == dia:
                if not (fin_min <= res["inicio_min"] or inicio_min >= res["fin_min"]):
                    ocupado = True
                    break
        estado = "Ocupada" if ocupado else "Libre"
        print(f"Mesa {m} - {estado}")
        if not ocupado:
            mesas_validas.append(m)

    if not mesas_validas:
        print("No hay mesas disponibles en ese horario.")
        return

    while True:
        mesas_seleccionadas = input("Ingrese números de mesas separados por coma: ").strip()
        try:
            mesas = [int(x) for x in mesas_seleccionadas.split(",")]
            if all(m in mesas_validas for m in mesas):
                break
            else:
                print("Mesas inválidas o ocupadas. Seleccione solo mesas disponibles.")
        except:
            print("Formato inválido.")

    reserva = {
        "nombre": nombre,
        "personas": num_personas,
        "dia": dia,
        "inicio_str": hora_inicio_str,
        "fin_str": hora_fin_str,
        "inicio_min": inicio_min,
        "fin_min": fin_min,
        "mesas": mesas,
        "estado": "Pendiente"
    }

    reservas_pendientes.append(reserva)
    print("Reserva solicitada y pendiente de aprobación por vendedor.")

def ver_estado_reserva():
    nombre_reserva = input("Ingrese el nombre de su reserva: ").strip()
    encontrado = False

    # AHORA TAMBIÉN BUSCA EN RESERVAS RECHAZADAS 
    for res in reservas_aceptadas + reservas_pendientes + reservas_rechazadas:
        if res["nombre"].lower() == nombre_reserva.lower():
            mesas_str = ', '.join(map(str, res["mesas"]))
            print(f"Reserva: {res['nombre']} - {res['dia']} {res['inicio_str']} a {res['fin_str']} - Mesas: {mesas_str} - Estado: {res['estado']}")
            encontrado = True

    if not encontrado:
        print("No se encontró ninguna reserva con ese nombre.")

# ==================== Funciones Vendedor ====================

def login_vendedor():
    nombre = input("Ingrese su nombre: ").strip()
    if nombre not in vendedores:
        print("Nombre inválido.")
        return None
    contrasena = input("Ingrese su contraseña: ").strip()
    if contrasena != vendedores[nombre]:
        print("Contraseña incorrecta.")
        return None
    return nombre

def ver_reservas_pendientes_vendedor():
    if not reservas_pendientes:
        print("No hay reservas pendientes.")
        return
    for idx, res in enumerate(reservas_pendientes):
        mesas_str = ', '.join(map(str, res["mesas"]))
        print(f"{idx+1}. {res['nombre']} - {res['dia']} {res['inicio_str']} a {res['fin_str']} - Mesas: {mesas_str} - Estado: {res['estado']}")

def gestionar_reserva_vendedor():
    if not reservas_pendientes:
        print("No hay reservas pendientes.")
        return

    while True:
        ver_reservas_pendientes_vendedor()
        try:
            seleccion = int(input("Ingrese el número de la reserva a gestionar (0 para salir): "))
            if seleccion == 0:
                break
            if 1 <= seleccion <= len(reservas_pendientes):
                res = reservas_pendientes[seleccion-1]

                conflicto = False
                for acept in reservas_aceptadas:
                    if res['dia'] == acept['dia']:
                        for m in res['mesas']:
                            if m in acept['mesas']:
                                if not (res['fin_min'] <= acept['inicio_min'] or res['inicio_min'] >= acept['fin_min']):
                                    conflicto = True
                                    break
                if conflicto:
                    res['estado'] = "Rechazada - Horario en conflicto"
                    reservas_pendientes.remove(res)
                    reservas_rechazadas.append(res)  # <--- Guardada correctamente
                    print("Reserva rechazada automáticamente por conflicto de horario.")
                    continue

                decision = input("Aceptar reserva? (S/N): ").strip().upper()
                if decision == "S":
                    res['estado'] = "Aceptada"
                    reservas_aceptadas.append(res)
                    reservas_pendientes.remove(res)
                else:
                    res['estado'] = "Rechazada"
                    reservas_pendientes.remove(res)
                    reservas_rechazadas.append(res)  # <--- AQUÍ SE GUARDA LA RECHAZADA
            else:
                print("Número inválido.")
        except:
            print("Ingrese un número válido.")

# ==================== Funciones Administrador ====================

def administrador():
    contrasena = input("Ingrese contraseña de administrador: ").strip()
    if contrasena != "admin123":
        print("Contraseña incorrecta.")
        return

    while True:
        print("\n=== Menú Administrador ===")
        print("1. Ver reservas pendientes")
        print("2. Crear vendedor")
        print("3. Eliminar vendedor")
        print("4. Actualizar contraseña vendedor")
        print("0. Salir")
        opcion = input("Ingrese opción: ").strip()

        if opcion == "0":
            break
        elif opcion == "1":
            gestionar_reserva_vendedor()
        elif opcion == "2":
            nombre = input("Ingrese nombre del vendedor: ").strip()
            contrasena = input("Ingrese contraseña: ").strip()
            vendedores[nombre] = contrasena
            print("Vendedor creado.")
        elif opcion == "3":
            nombre = input("Ingrese nombre del vendedor a eliminar: ").strip()
            if nombre in vendedores:
                del vendedores[nombre]
                print("Vendedor eliminado.")
            else:
                print("No existe.")
        elif opcion == "4":
            nombre = input("Ingrese nombre del vendedor: ").strip()
            if nombre in vendedores:
                contrasena = input("Ingrese nueva contraseña: ").strip()
                vendedores[nombre] = contrasena
                print("Contraseña actualizada.")
            else:
                print("No existe.")
        
# ==================== Programa Principal ====================

def main():
    while True:
        print("\n=== Cover OS ===")
        print("1. Cliente")
        print("2. Vendedor")
        print("3. Administrador")
        print("0. Salir")
        opcion = input("Ingrese opción: ").strip()

        if opcion == "0":
            break
        elif opcion == "1":
            while True:
                print("\n--- Menú Cliente ---")
                print("1. Hacer una reserva")
                print("2. Ver estado de mi reserva")
                print("0. Volver")
                opc = input("Ingrese opción: ").strip()
                if opc == "0":
                    break
                elif opc == "1":
                    registrar_reserva_cliente()
                elif opc == "2":
                    ver_estado_reserva()
                else:
                    print("Opción inválida.")
        elif opcion == "2":
            usuario = login_vendedor()
            if usuario:
                while True:
                    print(f"\n--- Menú Vendedor ({usuario}) ---")
                    print("1. Ver reservas pendientes")
                    print("2. Gestionar reservas")
                    print("0. Volver")
                    opc = input("Ingrese opción: ").strip()
                    if opc == "0":
                        break
                    elif opc == "1":
                        ver_reservas_pendientes_vendedor()
                    elif opc == "2":
                        gestionar_reserva_vendedor()
                    else:
                        print("Opción inválida.")
        elif opcion == "3":
            administrador()
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    main()
