import tkinter as tk
from tkinter import ttk, messagebox

# ==================== Sistema de Reservas (GUI) ====================

class CoverOSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cover OS - Sistema de Reservas")
        self.root.geometry("950x700")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(True, True)

        # ---------- Estilos ----------
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#1a1a2e")
        self.style.configure("TLabel", background="#1a1a2e", foreground="#e0e0e0", font=("Segoe UI", 11))
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=6)
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#00d4ff")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 13, "bold"), foreground="#ffcc00")
        self.style.configure("Success.TButton", foreground="#ffffff", background="#28a745")
        self.style.configure("Danger.TButton", foreground="#ffffff", background="#dc3545")
        self.style.configure("Accent.TButton", foreground="#ffffff", background="#007bff")
        self.style.map("TButton", background=[("active", "#0056b3")])

        # ---------- Datos Iniciales ----------
        self.mesas_disponibles = list(range(1, 11))
        self.reservas_pendientes = []
        self.reservas_aceptadas = []
        self.reservas_rechazadas = []
        self.vendedores = {"Eliezer": "Romero", "Darwin": "Eduardo"}
        self.limite_personas = 4
        self.dias_semana = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        self.dias_validos = [d for d in self.dias_semana if d != "Lunes"]

        # ---------- Contenedor Principal ----------
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.mostrar_menu_principal()

    # ==================== Utilidades ====================
    def limpiar_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def validar_nombre(self, nombre):
        return nombre.replace(" ", "").isalpha() and len(nombre) > 1

    def validar_numero_personas(self, num):
        try:
            n = int(num)
            return n > 0
        except:
            return False

    def validar_dia(self, dia):
        return dia in self.dias_semana and dia != "Lunes"

    def hora_a_minutos(self, hora_str):
        hora_str = hora_str.strip().upper()
        tiempo, meridiano = hora_str[:-2], hora_str[-2:]
        h, m = map(int, tiempo.split(":"))
        if meridiano == "PM" and h != 12:
            h += 12
        if meridiano == "AM" and h == 12:
            h = 0
        return h * 60 + m

    def formato_hora(self, h, m, meridiano):
        return f"{h}:{m:02d} {meridiano}"

    # ==================== Menú Principal ====================
    def mostrar_menu_principal(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="integrador II", style="Header.TLabel").pack(pady=(30, 5))
        ttk.Label(self.main_frame, text="Aplicacion escritorio en gestionamiento de Reservas", style="SubHeader.TLabel").pack(pady=(0, 40))

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text=" Cliente", width=25, command=self.mostrar_menu_cliente).pack(pady=10)
        ttk.Button(btn_frame, text=" Vendedor", width=25, command=self.mostrar_login_vendedor).pack(pady=10)
        ttk.Button(btn_frame, text=" Administrador", width=25, command=self.mostrar_login_admin).pack(pady=10)
        ttk.Button(btn_frame, text=" Salir", width=25, command=self.root.quit).pack(pady=10)

    # ==================== Cliente ====================
    def mostrar_menu_cliente(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Menú Cliente", style="Header.TLabel").pack(pady=(20, 30))

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text=" Hacer una Reserva", width=30, command=self.mostrar_formulario_reserva).pack(pady=10)
        ttk.Button(btn_frame, text=" Ver Estado de mi Reserva", width=30, command=self.mostrar_consulta_reserva).pack(pady=10)
        ttk.Button(btn_frame, text=" Volver", width=30, command=self.mostrar_menu_principal).pack(pady=20)

    def mostrar_formulario_reserva(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Solicitar Reserva", style="Header.TLabel").pack(pady=(10, 20))

        form = ttk.Frame(self.main_frame)
        form.pack(pady=10)

        # Nombre
        ttk.Label(form, text="Nombre de la reserva:").grid(row=0, column=0, sticky="w", padx=10, pady=8)
        self.entry_nombre = ttk.Entry(form, width=30, font=("Segoe UI", 11))
        self.entry_nombre.grid(row=0, column=1, padx=10, pady=8)

        # Personas
        ttk.Label(form, text=f"Número de personas (máx {self.limite_personas}):").grid(row=1, column=0, sticky="w", padx=10, pady=8)
        self.spin_personas = ttk.Spinbox(form, from_=1, to=self.limite_personas, width=10, font=("Segoe UI", 11))
        self.spin_personas.set(1)
        self.spin_personas.grid(row=1, column=1, sticky="w", padx=10, pady=8)

        # Día
        ttk.Label(form, text="Día de la reserva:").grid(row=2, column=0, sticky="w", padx=10, pady=8)
        self.combo_dia = ttk.Combobox(form, values=self.dias_validos, state="readonly", width=15, font=("Segoe UI", 11))
        self.combo_dia.set(self.dias_validos[0])
        self.combo_dia.grid(row=2, column=1, sticky="w", padx=10, pady=8)

        # Horario Inicio
        ttk.Label(form, text="Hora de inicio:").grid(row=3, column=0, sticky="w", padx=10, pady=8)
        hora_inicio_frame = ttk.Frame(form)
        hora_inicio_frame.grid(row=3, column=1, sticky="w", padx=10, pady=8)
        self.combo_h_inicio = ttk.Combobox(hora_inicio_frame, values=[str(i) for i in range(1, 13)], state="readonly", width=5, font=("Segoe UI", 11))
        self.combo_h_inicio.set("8")
        self.combo_h_inicio.pack(side="left", padx=(0, 5))
        ttk.Label(hora_inicio_frame, text=":").pack(side="left")
        self.combo_m_inicio = ttk.Combobox(hora_inicio_frame, values=["00", "15", "30", "45"], state="readonly", width=5, font=("Segoe UI", 11))
        self.combo_m_inicio.set("00")
        self.combo_m_inicio.pack(side="left", padx=5)
        self.combo_ampm_inicio = ttk.Combobox(hora_inicio_frame, values=["AM", "PM"], state="readonly", width=5, font=("Segoe UI", 11))
        self.combo_ampm_inicio.set("AM")
        self.combo_ampm_inicio.pack(side="left", padx=5)

        # Horario Fin
        ttk.Label(form, text="Hora de fin:").grid(row=4, column=0, sticky="w", padx=10, pady=8)
        hora_fin_frame = ttk.Frame(form)
        hora_fin_frame.grid(row=4, column=1, sticky="w", padx=10, pady=8)
        self.combo_h_fin = ttk.Combobox(hora_fin_frame, values=[str(i) for i in range(1, 13)], state="readonly", width=5, font=("Segoe UI", 11))
        self.combo_h_fin.set("10")
        self.combo_h_fin.pack(side="left", padx=(0, 5))
        ttk.Label(hora_fin_frame, text=":").pack(side="left")
        self.combo_m_fin = ttk.Combobox(hora_fin_frame, values=["00", "15", "30", "45"], state="readonly", width=5, font=("Segoe UI", 11))
        self.combo_m_fin.set("00")
        self.combo_m_fin.pack(side="left", padx=5)
        self.combo_ampm_fin = ttk.Combobox(hora_fin_frame, values=["AM", "PM"], state="readonly", width=5, font=("Segoe UI", 11))
        self.combo_ampm_fin.set("AM")
        self.combo_ampm_fin.pack(side="left", padx=5)

        # Botón verificar mesas
        ttk.Button(self.main_frame, text=" Verificar Mesas Disponibles", command=self.verificar_mesas).pack(pady=15)

        # Frame para mesas
        self.frame_mesas = ttk.Frame(self.main_frame)
        self.frame_mesas.pack(pady=10)

        self.mesas_vars = {}
        self.mesas_checkbuttons = []

        # Botones inferiores
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=20)
        self.btn_reservar = ttk.Button(btn_frame, text=" Solicitar Reserva", command=self.registrar_reserva, state="disabled")
        self.btn_reservar.pack(side="left", padx=10)
        ttk.Button(btn_frame, text=" Volver", command=self.mostrar_menu_cliente).pack(side="left", padx=10)

        self.mesas_validas = []

    def verificar_mesas(self):
        nombre = self.entry_nombre.get().strip()
        num_personas = self.spin_personas.get().strip()
        dia = self.combo_dia.get().strip()

        if not self.validar_nombre(nombre):
            messagebox.showerror("Error", "Nombre inválido. Solo letras y mínimo 2 caracteres.")
            return
        if not self.validar_numero_personas(num_personas):
            messagebox.showerror("Error", "Número de personas inválido.")
            return
        if int(num_personas) > self.limite_personas:
            messagebox.showerror("Error", f"No puede superar el límite de {self.limite_personas} personas.")
            return
        if not self.validar_dia(dia):
            messagebox.showerror("Error", "Día inválido o restaurante cerrado (Lunes).")
            return

        h_i = self.combo_h_inicio.get()
        m_i = self.combo_m_inicio.get()
        ampm_i = self.combo_ampm_inicio.get()
        h_f = self.combo_h_fin.get()
        m_f = self.combo_m_fin.get()
        ampm_f = self.combo_ampm_fin.get()

        hora_inicio_str = self.formato_hora(int(h_i), int(m_i), ampm_i)
        hora_fin_str = self.formato_hora(int(h_f), int(m_f), ampm_f)

        try:
            inicio_min = self.hora_a_minutos(hora_inicio_str)
            fin_min = self.hora_a_minutos(hora_fin_str)
        except:
            messagebox.showerror("Error", "Formato de hora inválido.")
            return

        apertura = self.hora_a_minutos("8:00 AM")
        cierre = self.hora_a_minutos("11:00 PM")

        if inicio_min < apertura:
            messagebox.showerror("Error", "El restaurante abre a las 8:00 AM.")
            return
        if fin_min > cierre:
            messagebox.showerror("Error", "El restaurante cierra a las 11:00 PM.")
            return
        if inicio_min >= fin_min:
            messagebox.showerror("Error", "La hora de fin debe ser mayor que la de inicio.")
            return

        # Guardar valores para usar al registrar
        self.reserva_temp = {
            "nombre": nombre,
            "personas": int(num_personas),
            "dia": dia,
            "inicio_str": hora_inicio_str,
            "fin_str": hora_fin_str,
            "inicio_min": inicio_min,
            "fin_min": fin_min
        }

        # Limpiar frame de mesas anterior
        for widget in self.frame_mesas.winfo_children():
            widget.destroy()
        self.mesas_vars = {}
        self.mesas_checkbuttons = []

        ttk.Label(self.frame_mesas, text="Seleccione las mesas disponibles:", style="SubHeader.TLabel").pack(pady=(0, 10))

        mesas_frame = ttk.Frame(self.frame_mesas)
        mesas_frame.pack()

        self.mesas_validas = []
        col = 0
        row = 0
        for m in self.mesas_disponibles:
            ocupado = False
            for res in self.reservas_aceptadas + self.reservas_pendientes:
                if m in res["mesas"] and res["dia"] == dia:
                    if not (fin_min <= res["inicio_min"] or inicio_min >= res["fin_min"]):
                        ocupado = True
                        break

            estado = "Ocupada" if ocupado else "Libre"
            var = tk.BooleanVar(value=False)
            self.mesas_vars[m] = var

            cb = ttk.Checkbutton(mesas_frame, text=f"Mesa {m} - {estado}", variable=var, state="disabled" if ocupado else "normal")
            cb.grid(row=row, column=col, sticky="w", padx=10, pady=5)
            self.mesas_checkbuttons.append(cb)
            if not ocupado:
                self.mesas_validas.append(m)

            col += 1
            if col >= 5:
                col = 0
                row += 1

        if not self.mesas_validas:
            messagebox.showwarning("Sin disponibilidad", "No hay mesas disponibles en ese horario.")
            self.btn_reservar.config(state="disabled")
        else:
            self.btn_reservar.config(state="normal")

    def registrar_reserva(self):
        mesas_seleccionadas = [m for m, var in self.mesas_vars.items() if var.get()]

        if not mesas_seleccionadas:
            messagebox.showerror("Error", "Debe seleccionar al menos una mesa.")
            return

        if not all(m in self.mesas_validas for m in mesas_seleccionadas):
            messagebox.showerror("Error", "Mesas inválidas o ocupadas seleccionadas.")
            return

        reserva = {
            "nombre": self.reserva_temp["nombre"],
            "personas": self.reserva_temp["personas"],
            "dia": self.reserva_temp["dia"],
            "inicio_str": self.reserva_temp["inicio_str"],
            "fin_str": self.reserva_temp["fin_str"],
            "inicio_min": self.reserva_temp["inicio_min"],
            "fin_min": self.reserva_temp["fin_min"],
            "mesas": mesas_seleccionadas,
            "estado": "Pendiente"
        }

        self.reservas_pendientes.append(reserva)
        messagebox.showinfo("Éxito", "Reserva solicitada y pendiente de aprobación por vendedor.")
        self.mostrar_menu_cliente()

    def mostrar_consulta_reserva(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Consultar Estado de Reserva", style="Header.TLabel").pack(pady=(20, 20))

        form = ttk.Frame(self.main_frame)
        form.pack(pady=10)

        ttk.Label(form, text="Ingrese el nombre de su reserva:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_consulta = ttk.Entry(form, width=30, font=("Segoe UI", 11))
        self.entry_consulta.grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(form, text="Buscar", command=self.buscar_reserva).grid(row=0, column=2, padx=10, pady=10)

        # Resultado
        self.resultado_frame = ttk.Frame(self.main_frame)
        self.resultado_frame.pack(pady=20, fill="both", expand=True)

        ttk.Button(self.main_frame, text=" Volver", command=self.mostrar_menu_cliente).pack(pady=10)

    def buscar_reserva(self):
        nombre = self.entry_consulta.get().strip()

        for widget in self.resultado_frame.winfo_children():
            widget.destroy()

        encontrado = False
        for res in self.reservas_aceptadas + self.reservas_pendientes + self.reservas_rechazadas:
            if res["nombre"].lower() == nombre.lower():
                encontrado = True
                mesas_str = ", ".join(map(str, res["mesas"]))
                estado_color = "#28a745" if res["estado"] == "Aceptada" else ("#ffc107" if res["estado"] == "Pendiente" else "#dc3545")

                card = tk.Frame(self.resultado_frame, bg="#16213e", bd=2, relief="groove")
                card.pack(pady=10, padx=20, fill="x")

                tk.Label(card, text=f"Reserva: {res['nombre']}", bg="#16213e", fg="#00d4ff", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=15, pady=(10, 2))
                tk.Label(card, text=f"Día: {res['dia']}  |  Horario: {res['inicio_str']} a {res['fin_str']}", bg="#16213e", fg="#e0e0e0", font=("Segoe UI", 11)).pack(anchor="w", padx=15, pady=2)
                tk.Label(card, text=f"Mesas: {mesas_str}  |  Personas: {res['personas']}", bg="#16213e", fg="#e0e0e0", font=("Segoe UI", 11)).pack(anchor="w", padx=15, pady=2)
                tk.Label(card, text=f"Estado: {res['estado']}", bg="#16213e", fg=estado_color, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(2, 10))

        if not encontrado:
            ttk.Label(self.resultado_frame, text="No se encontró ninguna reserva con ese nombre.", foreground="#ff6b6b").pack(pady=20)

    # ==================== Vendedor ====================
    def mostrar_login_vendedor(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Login Vendedor", style="Header.TLabel").pack(pady=(30, 20))

        form = ttk.Frame(self.main_frame)
        form.pack(pady=10)

        ttk.Label(form, text="Nombre:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.entry_vendedor_nombre = ttk.Entry(form, width=25, font=("Segoe UI", 11))
        self.entry_vendedor_nombre.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(form, text="Contraseña:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.entry_vendedor_pass = ttk.Entry(form, width=25, font=("Segoe UI", 11), show="*")
        self.entry_vendedor_pass.grid(row=1, column=1, padx=10, pady=10)

        ttk.Button(form, text="Ingresar", command=self.login_vendedor).grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(self.main_frame, text=" Volver", command=self.mostrar_menu_principal).pack(pady=10)

    def login_vendedor(self):
        nombre = self.entry_vendedor_nombre.get().strip()
        contrasena = self.entry_vendedor_pass.get().strip()

        if nombre not in self.vendedores:
            messagebox.showerror("Error", "Nombre inválido.")
            return
        if contrasena != self.vendedores[nombre]:
            messagebox.showerror("Error", "Contraseña incorrecta.")
            return

        self.vendedor_actual = nombre
        self.mostrar_menu_vendedor()

    def mostrar_menu_vendedor(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text=f"Menú Vendedor ({self.vendedor_actual})", style="Header.TLabel").pack(pady=(20, 30))

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text=" Ver Reservas Pendientes", width=30, command=self.mostrar_reservas_pendientes_vendedor).pack(pady=10)
        ttk.Button(btn_frame, text=" Gestionar Reservas", width=30, command=self.mostrar_gestion_reservas).pack(pady=10)
        ttk.Button(btn_frame, text=" Cerrar Sesión", width=30, command=self.mostrar_menu_principal).pack(pady=20)

    def mostrar_reservas_pendientes_vendedor(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Reservas Pendientes", style="Header.TLabel").pack(pady=(10, 20))

        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(pady=10, fill="both", expand=True, padx=20)

        columns = ("Nombre", "Día", "Inicio", "Fin", "Mesas", "Personas", "Estado")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        if not self.reservas_pendientes:
            tree.insert("", "end", values=("No hay reservas pendientes", "", "", "", "", "", ""))
        else:
            for res in self.reservas_pendientes:
                mesas_str = ", ".join(map(str, res["mesas"]))
                tree.insert("", "end", values=(res["nombre"], res["dia"], res["inicio_str"], res["fin_str"], mesas_str, res["personas"], res["estado"]))

        ttk.Button(self.main_frame, text=" Volver", command=self.mostrar_menu_vendedor).pack(pady=15)

    def mostrar_gestion_reservas(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Gestionar Reservas", style="Header.TLabel").pack(pady=(10, 20))

        if not self.reservas_pendientes:
            ttk.Label(self.main_frame, text="No hay reservas pendientes.", foreground="#ffcc00", font=("Segoe UI", 13)).pack(pady=30)
            ttk.Button(self.main_frame, text=" Volver", command=self.mostrar_menu_vendedor).pack(pady=10)
            return

        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(pady=10, fill="both", expand=True, padx=20)

        self.gestion_listbox = tk.Listbox(list_frame, font=("Segoe UI", 11), bg="#16213e", fg="#e0e0e0", selectbackground="#007bff", height=10)
        self.gestion_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.gestion_listbox.yview)
        self.gestion_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.gestion_indices = []
        for idx, res in enumerate(self.reservas_pendientes):
            mesas_str = ", ".join(map(str, res["mesas"]))
            self.gestion_listbox.insert("end", f"{idx+1}. {res['nombre']} | {res['dia']} {res['inicio_str']}-{res['fin_str']} | Mesas: {mesas_str}")
            self.gestion_indices.append(idx)

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text=" Aceptar", command=lambda: self.procesar_reserva("aceptar")).pack(side="left", padx=10)
        ttk.Button(btn_frame, text=" Rechazar", command=lambda: self.procesar_reserva("rechazar")).pack(side="left", padx=10)
        ttk.Button(btn_frame, text=" Volver", command=self.mostrar_menu_vendedor).pack(side="left", padx=10)

    def procesar_reserva(self, accion):
        seleccion = self.gestion_listbox.curselection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione una reserva de la lista.")
            return

        idx = self.gestion_indices[seleccion[0]]
        res = self.reservas_pendientes[idx]

        # Verificar conflicto automático
        conflicto = False
        for acept in self.reservas_aceptadas:
            if res["dia"] == acept["dia"]:
                for m in res["mesas"]:
                    if m in acept["mesas"]:
                        if not (res["fin_min"] <= acept["inicio_min"] or res["inicio_min"] >= acept["fin_min"]):
                            conflicto = True
                            break

        if conflicto:
            res["estado"] = "Rechazada - Horario en conflicto"
            self.reservas_pendientes.pop(idx)
            self.reservas_rechazadas.append(res)
            messagebox.showinfo("Conflicto", "Reserva rechazada automáticamente por conflicto de horario.")
            self.mostrar_gestion_reservas()
            return

        if accion == "aceptar":
            res["estado"] = "Aceptada"
            self.reservas_aceptadas.append(res)
            self.reservas_pendientes.pop(idx)
            messagebox.showinfo("Éxito", "Reserva aceptada correctamente.")
        else:
            res["estado"] = "Rechazada"
            self.reservas_pendientes.pop(idx)
            self.reservas_rechazadas.append(res)
            messagebox.showinfo("Éxito", "Reserva rechazada correctamente.")

        self.mostrar_gestion_reservas()

    # ==================== Administrador ====================
    def mostrar_login_admin(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Login Administrador", style="Header.TLabel").pack(pady=(30, 20))

        form = ttk.Frame(self.main_frame)
        form.pack(pady=10)

        ttk.Label(form, text="Contraseña:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.entry_admin_pass = ttk.Entry(form, width=25, font=("Segoe UI", 11), show="*")
        self.entry_admin_pass.grid(row=0, column=1, padx=10, pady=10)

        ttk.Button(form, text="Ingresar", command=self.login_admin).grid(row=1, column=0, columnspan=2, pady=20)
        ttk.Button(self.main_frame, text=" Volver", command=self.mostrar_menu_principal).pack(pady=10)

    def login_admin(self):
        if self.entry_admin_pass.get().strip() != "1234":
            messagebox.showerror("Error", "Contraseña incorrecta.")
            return
        self.mostrar_menu_admin()

    def mostrar_menu_admin(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Menú Administrador", style="Header.TLabel").pack(pady=(20, 30))

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text=" Gestionar Reservas Pendientes", width=35, command=self.mostrar_gestion_reservas_admin).pack(pady=8)
        ttk.Button(btn_frame, text=" Crear Vendedor", width=35, command=self.mostrar_crear_vendedor).pack(pady=8)
        ttk.Button(btn_frame, text=" Eliminar Vendedor", width=35, command=self.mostrar_eliminar_vendedor).pack(pady=8)
        ttk.Button(btn_frame, text=" Actualizar Contraseña Vendedor", width=35, command=self.mostrar_actualizar_vendedor).pack(pady=8)
        ttk.Button(btn_frame, text=" Cerrar Sesión", width=35, command=self.mostrar_menu_principal).pack(pady=15)

    def mostrar_gestion_reservas_admin(self):
        # Reutiliza la misma lógica de gestión de vendedor pero con vuelta al menú admin
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Gestionar Reservas (Admin)", style="Header.TLabel").pack(pady=(10, 20))

        if not self.reservas_pendientes:
            ttk.Label(self.main_frame, text="No hay reservas pendientes.", foreground="#ffcc00", font=("Segoe UI", 13)).pack(pady=30)
            ttk.Button(self.main_frame, text=" Volver", command=self.mostrar_menu_admin).pack(pady=10)
            return

        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(pady=10, fill="both", expand=True, padx=20)

        self.admin_gestion_listbox = tk.Listbox(list_frame, font=("Segoe UI", 11), bg="#16213e", fg="#e0e0e0", selectbackground="#007bff", height=10)
        self.admin_gestion_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.admin_gestion_listbox.yview)
        self.admin_gestion_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.admin_gestion_indices = []
        for idx, res in enumerate(self.reservas_pendientes):
            mesas_str = ", ".join(map(str, res["mesas"]))
            self.admin_gestion_listbox.insert("end", f"{idx+1}. {res['nombre']} | {res['dia']} {res['inicio_str']}-{res['fin_str']} | Mesas: {mesas_str}")
            self.admin_gestion_indices.append(idx)

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text=" Aceptar", command=lambda: self.procesar_reserva_admin("aceptar")).pack(side="left", padx=10)
        ttk.Button(btn_frame, text=" Rechazar", command=lambda: self.procesar_reserva_admin("rechazar")).pack(side="left", padx=10)
        ttk.Button(btn_frame, text=" Volver", command=self.mostrar_menu_admin).pack(side="left", padx=10)

    def procesar_reserva_admin(self, accion):
        seleccion = self.admin_gestion_listbox.curselection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione una reserva de la lista.")
            return

        idx = self.admin_gestion_indices[seleccion[0]]
        res = self.reservas_pendientes[idx]

        conflicto = False
        for acept in self.reservas_aceptadas:
            if res["dia"] == acept["dia"]:
                for m in res["mesas"]:
                    if m in acept["mesas"]:
                        if not (res["fin_min"] <= acept["inicio_min"] or res["inicio_min"] >= acept["fin_min"]):
                            conflicto = True
                            break

        if conflicto:
            res["estado"] = "Rechazada - Horario en conflicto"
            self.reservas_pendientes.pop(idx)
            self.reservas_rechazadas.append(res)
            messagebox.showinfo("Conflicto", "Reserva rechazada automáticamente por conflicto de horario.")
            self.mostrar_gestion_reservas_admin()
            return

        if accion == "aceptar":
            res["estado"] = "Aceptada"
            self.reservas_aceptadas.append(res)
            self.reservas_pendientes.pop(idx)
            messagebox.showinfo("Éxito", "Reserva aceptada correctamente.")
        else:
            res["estado"] = "Rechazada"
            self.reservas_pendientes.pop(idx)
            self.reservas_rechazadas.append(res)
            messagebox.showinfo("Éxito", "Reserva rechazada correctamente.")

        self.mostrar_gestion_reservas_admin()

    def mostrar_crear_vendedor(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Crear Vendedor", style="Header.TLabel").pack(pady=(20, 20))

        form = ttk.Frame(self.main_frame)
        form.pack(pady=10)

        ttk.Label(form, text="Nombre:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.entry_new_vend_nombre = ttk.Entry(form, width=25, font=("Segoe UI", 11))
        self.entry_new_vend_nombre.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(form, text="Contraseña:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.entry_new_vend_pass = ttk.Entry(form, width=25, font=("Segoe UI", 11))
        self.entry_new_vend_pass.grid(row=1, column=1, padx=10, pady=10)

        ttk.Button(form, text="Crear", command=self.crear_vendedor).grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(self.main_frame, text=" Volver", command=self.mostrar_menu_admin).pack(pady=10)

    def crear_vendedor(self):
        nombre = self.entry_new_vend_nombre.get().strip()
        contrasena = self.entry_new_vend_pass.get().strip()

        if not nombre or not contrasena:
            messagebox.showerror("Error", "Complete todos los campos.")
            return

        self.vendedores[nombre] = contrasena
        messagebox.showinfo("Éxito", f"Vendedor '{nombre}' creado correctamente.")
        self.mostrar_menu_admin()

    def mostrar_eliminar_vendedor(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Eliminar Vendedor", style="Header.TLabel").pack(pady=(20, 20))

        form = ttk.Frame(self.main_frame)
        form.pack(pady=10)

        ttk.Label(form, text="Seleccione vendedor:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.combo_del_vend = ttk.Combobox(form, values=list(self.vendedores.keys()), state="readonly", width=23, font=("Segoe UI", 11))
        self.combo_del_vend.grid(row=0, column=1, padx=10, pady=10)

        ttk.Button(form, text="Eliminar", command=self.eliminar_vendedor).grid(row=1, column=0, columnspan=2, pady=20)
        ttk.Button(self.main_frame, text=" Volver", command=self.mostrar_menu_admin).pack(pady=10)

    def eliminar_vendedor(self):
        nombre = self.combo_del_vend.get()
        if not nombre:
            messagebox.showerror("Error", "Seleccione un vendedor.")
            return

        if messagebox.askyesno("Confirmar", f"¿Eliminar al vendedor '{nombre}'?"):
            del self.vendedores[nombre]
            messagebox.showinfo("Éxito", "Vendedor eliminado.")
            self.mostrar_menu_admin()

    def mostrar_actualizar_vendedor(self):
        self.limpiar_frame()

        ttk.Label(self.main_frame, text="Actualizar Contraseña", style="Header.TLabel").pack(pady=(20, 20))

        form = ttk.Frame(self.main_frame)
        form.pack(pady=10)

        ttk.Label(form, text="Seleccione vendedor:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.combo_upd_vend = ttk.Combobox(form, values=list(self.vendedores.keys()), state="readonly", width=23, font=("Segoe UI", 11))
        self.combo_upd_vend.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(form, text="Nueva contraseña:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.entry_upd_vend_pass = ttk.Entry(form, width=25, font=("Segoe UI", 11))
        self.entry_upd_vend_pass.grid(row=1, column=1, padx=10, pady=10)

        ttk.Button(form, text="Actualizar", command=self.actualizar_vendedor).grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(self.main_frame, text=" Volver", command=self.mostrar_menu_admin).pack(pady=10)

    def actualizar_vendedor(self):
        nombre = self.combo_upd_vend.get()
        contrasena = self.entry_upd_vend_pass.get().strip()

        if not nombre:
            messagebox.showerror("Error", "Seleccione un vendedor.")
            return
        if not contrasena:
            messagebox.showerror("Error", "Ingrese una nueva contraseña.")
            return

        self.vendedores[nombre] = contrasena
        messagebox.showinfo("Éxito", "Contraseña actualizada.")
        self.mostrar_menu_admin()


# ==================== Ejecución ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = CoverOSApp(root)
    root.mainloop()
