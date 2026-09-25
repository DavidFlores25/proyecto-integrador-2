import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox,
    QCheckBox, QListWidget, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QFrame, QHeaderView, QAbstractSpinBox
)
from PySide6.QtCore import Qt
import db
# ==================== Sistema de Reservas (GUI) - PySide6 ====================
# Migración de tkinter/ttk a PySide6. Toda la lógica de negocio (validaciones,
# reglas de conflicto de horario, estructura de datos de reservas) se mantiene
# idéntica al archivo original; solo cambia la capa de interfaz gráfica.


# -----------------------------------------------------------------------------
# HOJAS DE ESTILOS QSS - Tema Oscuro y Tema Claro (mismo lenguaje visual original)
# -----------------------------------------------------------------------------
QSS_TEMA_OSCURO = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Segoe UI", sans-serif;
    font-size: 11pt;
}

/* ---------- Encabezados ---------- */
QLabel#lblHeader {
    font-size: 18pt;
    font-weight: bold;
    color: #00d4ff;
}

QLabel#lblSubHeader {
    font-size: 13pt;
    font-weight: bold;
    color: #ffcc00;
}

QLabel#lblWarning {
    color: #ffcc00;
    font-size: 13pt;
}

QLabel#lblError {
    color: #ff6b6b;
}

/* ---------- Campos de entrada ---------- */
QLineEdit, QComboBox, QSpinBox {
    background-color: #16213e;
    border: 1px solid #2c2f4a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e0e0e0;
}

QComboBox {
    combobox-popup: 0;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #00d4ff;
    background-color: #1c2745;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    border: 1px solid #00d4ff;
    border-radius: 4px;
    padding: 4px;
    color: #e0e0e0;
    selection-background-color: #007bff;
    selection-color: #ffffff;
    outline: none;
}

QComboBox QAbstractItemView::item {
    min-height: 26px;
    padding: 2px 8px;
    border-radius: 4px;
}

/* ---------- Botones ---------- */
QPushButton {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2c2f4a;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #0056b3;
    color: #ffffff;
    border: 1px solid #007bff;
}

QPushButton:pressed {
    background-color: #003d80;
}

QPushButton:disabled {
    background-color: #14172a;
    color: #5a5f77;
    border: 1px solid #22263f;
}

QPushButton#btnAccent {
    background-color: #007bff;
    color: #ffffff;
    border: none;
}
QPushButton#btnAccent:hover { background-color: #0056b3; }
QPushButton#btnAccent:pressed { background-color: #003d80; }

QPushButton#btnSuccess {
    background-color: #28a745;
    color: #ffffff;
    border: none;
}
QPushButton#btnSuccess:hover { background-color: #218838; }
QPushButton#btnSuccess:pressed { background-color: #1a6e2c; }

QPushButton#btnDanger {
    background-color: #dc3545;
    color: #ffffff;
    border: none;
}
QPushButton#btnDanger:hover { background-color: #bb2d3b; }
QPushButton#btnDanger:pressed { background-color: #9a2530; }

/* ---------- Checkbuttons de mesas ---------- */
QCheckBox {
    padding: 4px;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
}
QCheckBox:disabled {
    color: #5a5f77;
}

/* ---------- Listas y árboles ---------- */
QListWidget, QTreeWidget {
    background-color: #16213e;
    border: 1px solid #2c2f4a;
    border-radius: 6px;
    color: #e0e0e0;
    alternate-background-color: #1c2745;
}

QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #007bff;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #2c2f4a;
    color: #00d4ff;
    padding: 6px;
    font-weight: bold;
    border: none;
}

/* ---------- Tarjeta de resultado de consulta ---------- */
QFrame#card {
    background-color: #16213e;
    border: 1px solid #2c2f4a;
    border-radius: 8px;
}

QLabel#cardTitulo {
    color: #00d4ff;
    font-size: 13pt;
    font-weight: bold;
}

QLabel#cardTexto {
    color: #e0e0e0;
}

/* ---------- Cuadros de diálogo ---------- */
QMessageBox {
    background-color: #1a1a2e;
}

QMessageBox QLabel {
    color: #e0e0e0;
    font-size: 11pt;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 6px 14px;
}
"""


QSS_TEMA_CLARO = """
QMainWindow, QWidget {
    background-color: #e7ebf4;
    color: #1c2333;
    font-family: "Segoe UI", sans-serif;
    font-size: 11pt;
}

/* ---------- Encabezados ---------- */
QLabel#lblHeader {
    font-size: 18pt;
    font-weight: bold;
    color: #0d6efd;
}

QLabel#lblSubHeader {
    font-size: 13pt;
    font-weight: bold;
    color: #b36a00;
}

QLabel#lblWarning {
    color: #b36a00;
    font-size: 13pt;
}

QLabel#lblError {
    color: #dc3545;
}

/* ---------- Campos de entrada ---------- */
QLineEdit, QComboBox, QSpinBox {
    background-color: #f5f7fb;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1c2333;
}

QComboBox {
    combobox-popup: 0;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #0d6efd;
    background-color: #f4f8ff;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #f5f7fb;
    border: 1px solid #0d6efd;
    border-radius: 4px;
    padding: 4px;
    color: #1c2333;
    selection-background-color: #0d6efd;
    selection-color: #ffffff;
    outline: none;
}

QComboBox QAbstractItemView::item {
    min-height: 26px;
    padding: 2px 8px;
    border-radius: 4px;
}

/* ---------- Botones ---------- */
QPushButton {
    background-color: #f5f7fb;
    color: #1c2333;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #0b5ed7;
    color: #ffffff;
    border: 1px solid #0d6efd;
}

QPushButton:pressed {
    background-color: #084298;
}

QPushButton:disabled {
    background-color: #e9ecef;
    color: #9aa1ad;
    border: 1px solid #dee2e6;
}

QPushButton#btnAccent {
    background-color: #0d6efd;
    color: #ffffff;
    border: none;
}
QPushButton#btnAccent:hover { background-color: #0b5ed7; }
QPushButton#btnAccent:pressed { background-color: #084298; }

QPushButton#btnSuccess {
    background-color: #198754;
    color: #ffffff;
    border: none;
}
QPushButton#btnSuccess:hover { background-color: #157347; }
QPushButton#btnSuccess:pressed { background-color: #12603c; }

QPushButton#btnDanger {
    background-color: #dc3545;
    color: #ffffff;
    border: none;
}
QPushButton#btnDanger:hover { background-color: #bb2d3b; }
QPushButton#btnDanger:pressed { background-color: #9a2530; }

/* ---------- Checkbuttons de mesas ---------- */
QCheckBox {
    padding: 4px;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
}
QCheckBox:disabled {
    color: #9aa1ad;
}

/* ---------- Listas y árboles ---------- */
QListWidget, QTreeWidget {
    background-color: #f5f7fb;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    color: #1c2333;
    alternate-background-color: #f4f6fb;
}

QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #0d6efd;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #e9ecef;
    color: #0d6efd;
    padding: 6px;
    font-weight: bold;
    border: none;
}

/* ---------- Tarjeta de resultado de consulta ---------- */
QFrame#card {
    background-color: #f5f7fb;
    border: 1px solid #ccd0da;
    border-radius: 8px;
}

QLabel#cardTitulo {
    color: #0d6efd;
    font-size: 13pt;
    font-weight: bold;
}

QLabel#cardTexto {
    color: #1c2333;
}

/* ---------- Cuadros de diálogo ---------- */
QMessageBox {
    background-color: #e7ebf4;
}

QMessageBox QLabel {
    color: #1c2333;
    font-size: 11pt;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 6px 14px;
}
"""


class CoverOSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Reservas")
        self.resize(950, 700)

        # ---------- Datos Iniciales ----------
        self.mesas_disponibles = list(range(1, 11))
        self.limite_personas = 10
        self.es_tema_oscuro = True
        self.dias_semana = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        self.dias_validos = [d for d in self.dias_semana if d != "Lunes"]

        # ---------- Contenedor Principal ----------
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(14)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.mostrar_menu_principal()

    # ==================== Utilidades ====================
    def limpiar_frame(self):
        self._limpiar_layout(self.main_layout)

    def _limpiar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._limpiar_layout(sub_layout)

    def validar_nombre(self, nombre):
        return nombre.replace(" ", "").isalpha() and len(nombre) > 1

    def validar_numero_personas(self, num):
        try:
            n = int(num)
            return n > 0
        except:
            return False

    def validar_dia(self, dia):
        dia = dia.strip().capitalize()
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

    # ---------- Helpers de construcción de UI ----------
    def _label(self, texto, object_name=None, align=None):
        lbl = QLabel(texto)
        if object_name:
            lbl.setObjectName(object_name)
        if align is not None:
            lbl.setAlignment(align)
        return lbl

    def _boton(self, texto, comando, object_name=None, min_width=None):
        btn = QPushButton(texto)
        btn.clicked.connect(comando)
        if object_name:
            btn.setObjectName(object_name)
        if min_width:
            btn.setMinimumWidth(min_width)
        return btn

    def _fila_botones(self, botones, centrado=True):
        contenedor = QHBoxLayout()
        if centrado:
            contenedor.addStretch()
        for btn in botones:
            contenedor.addWidget(btn)
        if centrado:
            contenedor.addStretch()
        return contenedor

    def salir_app(self):
        QApplication.instance().quit()

    def cambiar_tema(self, nombre_tema):
        """Alterna dinámicamente la hoja de estilo QSS de toda la aplicación."""
        self.es_tema_oscuro = "Oscuro" in nombre_tema
        QApplication.instance().setStyleSheet(QSS_TEMA_OSCURO if self.es_tema_oscuro else QSS_TEMA_CLARO)

    # ==================== Menú Principal ====================
    def mostrar_menu_principal(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(30)
        self.main_layout.addWidget(self._label("integrador II", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        lbl_sub = self._label("Aplicacion escritorio en gestionamiento de Reservas", "lblSubHeader", Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addWidget(lbl_sub)
        self.main_layout.addSpacing(20)

        col = QVBoxLayout()
        col.setSpacing(10)
        col.addWidget(self._boton(" Cliente", self.mostrar_menu_cliente, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Reservas Pendientes", self.mostrar_reservas_pendientes_publico, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Vendedor", self.mostrar_login_vendedor, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Administrador", self.mostrar_login_admin, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Salir", self.salir_app, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addLayout(col)
        self.main_layout.addStretch()

        # ---------- Selector de tema, abajo a la derecha ----------
        tema_layout = QHBoxLayout()
        tema_layout.addStretch()
        tema_layout.addWidget(QLabel("Tema Visual:"))
        self.combo_tema = QComboBox()
        self.combo_tema.addItems(["Tema Oscuro", "Tema Claro"])
        self.combo_tema.setCurrentText("Tema Oscuro" if self.es_tema_oscuro else "Tema Claro")
        self.combo_tema.setMinimumWidth(150)
        self.combo_tema.currentTextChanged.connect(self.cambiar_tema)
        tema_layout.addWidget(self.combo_tema)
        self.main_layout.addLayout(tema_layout)

    # ==================== Cliente ====================
    def mostrar_menu_cliente(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self._label("Menú Cliente", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(30)

        col = QVBoxLayout()
        col.setSpacing(10)
        col.addWidget(self._boton(" Hacer una Reserva", self.mostrar_formulario_reserva, min_width=260), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Ver Estado de mi Reserva", self.mostrar_consulta_reserva, min_width=260), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addSpacing(10)
        col.addWidget(self._boton(" Volver", self.mostrar_menu_principal, min_width=260), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addLayout(col)
        self.main_layout.addStretch()

    def mostrar_formulario_reserva(self):
        self.limpiar_frame()

        self.main_layout.addWidget(self._label("Solicitar Reserva", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)

        # Nombre
        self.entry_nombre = QLineEdit()
        self.entry_nombre.returnPressed.connect(self.verificar_mesas)
        form.addRow("Nombre de la reserva:", self.entry_nombre)

        # Personas
        self.spin_personas = QSpinBox()
        self.spin_personas.setRange(1, self.limite_personas)
        self.spin_personas.setValue(1)
        self.spin_personas.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        form.addRow(f"Número de personas (máx {self.limite_personas}):", self.spin_personas)

        # Día
        self.combo_dia = QComboBox()
        self.combo_dia.addItems(self.dias_validos)
        form.addRow("Día de la reserva:", self.combo_dia)

        # Horario Inicio
        hora_inicio_widget = QWidget()
        hora_inicio_frame = QHBoxLayout(hora_inicio_widget)
        hora_inicio_frame.setContentsMargins(0, 0, 0, 0)
        self.combo_h_inicio = QComboBox()
        self.combo_h_inicio.addItems([str(i) for i in range(1, 13)])
        self.combo_h_inicio.setCurrentText("8")
        self.combo_h_inicio.setMinimumWidth(60)
        self.combo_h_inicio.view().setTextElideMode(Qt.TextElideMode.ElideNone)
        self.combo_m_inicio = QComboBox()
        self.combo_m_inicio.addItems(["00", "15", "30", "45"])
        self.combo_ampm_inicio = QComboBox()
        self.combo_ampm_inicio.addItems(["AM", "PM"])
        hora_inicio_frame.addWidget(self.combo_h_inicio)
        hora_inicio_frame.addWidget(QLabel(":"))
        hora_inicio_frame.addWidget(self.combo_m_inicio)
        hora_inicio_frame.addWidget(self.combo_ampm_inicio)
        hora_inicio_frame.addStretch()
        form.addRow("Hora de inicio:", hora_inicio_widget)

        # Horario Fin
        hora_fin_widget = QWidget()
        hora_fin_frame = QHBoxLayout(hora_fin_widget)
        hora_fin_frame.setContentsMargins(0, 0, 0, 0)
        self.combo_h_fin = QComboBox()
        self.combo_h_fin.addItems([str(i) for i in range(1, 13)])
        self.combo_h_fin.setCurrentText("10")
        self.combo_h_fin.setMinimumWidth(60)
        self.combo_h_fin.view().setTextElideMode(Qt.TextElideMode.ElideNone)
        self.combo_m_fin = QComboBox()
        self.combo_m_fin.addItems(["00", "15", "30", "45"])
        self.combo_ampm_fin = QComboBox()
        self.combo_ampm_fin.addItems(["AM", "PM"])
        hora_fin_frame.addWidget(self.combo_h_fin)
        hora_fin_frame.addWidget(QLabel(":"))
        hora_fin_frame.addWidget(self.combo_m_fin)
        hora_fin_frame.addWidget(self.combo_ampm_fin)
        hora_fin_frame.addStretch()
        form.addRow("Hora de fin:", hora_fin_widget)

        self.main_layout.addLayout(form)

        # Botón verificar mesas
        self.main_layout.addLayout(self._fila_botones(
            [self._boton(" Verificar Mesas Disponibles", self.verificar_mesas, "btnAccent")]
        ))

        # Frame para mesas
        self.frame_mesas = QVBoxLayout()
        self.main_layout.addLayout(self.frame_mesas)

        self.mesas_vars = {}
        self.mesas_checkbuttons = []

        # Botones inferiores
        self.btn_reservar = self._boton(" Solicitar Reserva", self.registrar_reserva, "btnSuccess")
        self.btn_reservar.setEnabled(False)
        btn_volver = self._boton(" Volver", self.mostrar_menu_cliente)
        self.main_layout.addLayout(self._fila_botones([self.btn_reservar, btn_volver]))

        self.mesas_validas = []
        self.main_layout.addStretch()

    def verificar_mesas(self):
        nombre = self.entry_nombre.text().strip()
        num_personas = str(self.spin_personas.value())
        dia = self.combo_dia.currentText().strip()

        if not self.validar_nombre(nombre):
            QMessageBox.critical(self, "Error", "Nombre inválido. Solo letras y mínimo 2 caracteres.")
            return
        if not self.validar_numero_personas(num_personas):
            QMessageBox.critical(self, "Error", "Número de personas inválido.")
            return
        if int(num_personas) > self.limite_personas:
            QMessageBox.critical(self, "Error", f"No puede superar el límite de {self.limite_personas} personas.")
            return
        if not self.validar_dia(dia):
            QMessageBox.critical(self, "Error", "Día inválido o restaurante cerrado (Lunes).")
            return

        h_i = self.combo_h_inicio.currentText()
        m_i = self.combo_m_inicio.currentText()
        ampm_i = self.combo_ampm_inicio.currentText()
        h_f = self.combo_h_fin.currentText()
        m_f = self.combo_m_fin.currentText()
        ampm_f = self.combo_ampm_fin.currentText()

        hora_inicio_str = self.formato_hora(int(h_i), int(m_i), ampm_i)
        hora_fin_str = self.formato_hora(int(h_f), int(m_f), ampm_f)

        try:
            inicio_min = self.hora_a_minutos(hora_inicio_str)
            fin_min = self.hora_a_minutos(hora_fin_str)
        except:
            QMessageBox.critical(self, "Error", "Formato de hora inválido.")
            return

        apertura = self.hora_a_minutos("8:00 AM")
        cierre = self.hora_a_minutos("11:00 PM")

        if inicio_min < apertura:
            QMessageBox.critical(self, "Error", "El restaurante abre a las 8:00 AM.")
            return
        if fin_min > cierre:
            QMessageBox.critical(self, "Error", "El restaurante cierra a las 11:00 PM.")
            return
        if inicio_min >= fin_min:
            QMessageBox.critical(self, "Error", "La hora de fin debe ser mayor que la de inicio.")
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
        self._limpiar_layout(self.frame_mesas)
        self.mesas_vars = {}
        self.mesas_checkbuttons = []

        self.frame_mesas.addWidget(self._label("Seleccione las mesas disponibles:", "lblSubHeader"))

        filas_mesas = QVBoxLayout()
        self.frame_mesas.addLayout(filas_mesas)

        reservas_dia = db.obtener_reservas_por_dia(dia)

        self.mesas_validas = []
        col = 0
        fila_actual = None
        for m in self.mesas_disponibles:
            ocupado = False
            for res in reservas_dia:
                if m in res["mesas"]:
                    if not (fin_min <= res["inicio_min"] or inicio_min >= res["fin_min"]):
                        ocupado = True
                        break

            estado = "Ocupada" if ocupado else "Libre"

            if col == 0:
                fila_actual = QHBoxLayout()
                filas_mesas.addLayout(fila_actual)

            cb = QCheckBox(f"Mesa {m} - {estado}")
            cb.setEnabled(not ocupado)
            self.mesas_vars[m] = cb
            fila_actual.addWidget(cb)
            self.mesas_checkbuttons.append(cb)
            if not ocupado:
                self.mesas_validas.append(m)

            col += 1
            if col >= 5:
                col = 0

        if not self.mesas_validas:
            QMessageBox.warning(self, "Sin disponibilidad", "No hay mesas disponibles en ese horario.")
            self.btn_reservar.setEnabled(False)
        else:
            self.btn_reservar.setEnabled(True)

    def registrar_reserva(self):
        mesas_seleccionadas = [m for m, var in self.mesas_vars.items() if var.isChecked()]

        if not mesas_seleccionadas:
            QMessageBox.critical(self, "Error", "Debe seleccionar al menos una mesa.")
            return

        if not all(m in self.mesas_validas for m in mesas_seleccionadas):
            QMessageBox.critical(self, "Error", "Mesas inválidas o ocupadas seleccionadas.")
            return

        db.crear_reserva(
            self.reserva_temp["nombre"],
            self.reserva_temp["personas"],
            self.reserva_temp["dia"],
            self.reserva_temp["inicio_str"],
            self.reserva_temp["fin_str"],
            self.reserva_temp["inicio_min"],
            self.reserva_temp["fin_min"],
            mesas_seleccionadas
        )
        QMessageBox.information(self, "Éxito", "Reserva solicitada y pendiente de aprobación por vendedor.")
        self.mostrar_menu_cliente()

    def mostrar_consulta_reserva(self):
        self.limpiar_frame()

        self.main_layout.addWidget(self._label("Consultar Estado de Reserva", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QHBoxLayout()
        self.entry_consulta = QLineEdit()
        self.entry_consulta.setMinimumWidth(260)
        self.entry_consulta.returnPressed.connect(self.buscar_reserva)
        form.addStretch()
        form.addWidget(QLabel("Ingrese el nombre de su reserva:"))
        form.addWidget(self.entry_consulta)
        form.addWidget(self._boton("Buscar", self.buscar_reserva, "btnAccent"))
        form.addStretch()
        self.main_layout.addLayout(form)

        # Resultado
        self.resultado_frame = QVBoxLayout()
        self.main_layout.addLayout(self.resultado_frame)

        self.main_layout.addLayout(self._fila_botones(
            [self._boton(" Volver", self.mostrar_menu_cliente)]
        ))
        self.main_layout.addStretch()

    def buscar_reserva(self):
        nombre = self.entry_consulta.text().strip()

        self._limpiar_layout(self.resultado_frame)

        resultados = db.obtener_reservas_por_nombre(nombre)

        if not resultados:
            self.resultado_frame.addWidget(self._label("No se encontró ninguna reserva con ese nombre.", "lblError"))
            return

        for res in resultados:
            mesas_str = ", ".join(map(str, res["mesas"]))
            estado_color = "#28a745" if res["estado"] == "Aceptada" else ("#ffc107" if res["estado"] == "Pendiente" else "#dc3545")

            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(15, 10, 15, 10)
            card_layout.setSpacing(4)

            lbl_nombre = QLabel(f"Reserva: {res['nombre']}")
            lbl_nombre.setObjectName("cardTitulo")
            lbl_horario = QLabel(f"Día: {res['dia']}  |  Horario: {res['inicio_str']} a {res['fin_str']}")
            lbl_horario.setObjectName("cardTexto")
            lbl_mesas = QLabel(f"Mesas: {mesas_str}  |  Personas: {res['personas']}")
            lbl_mesas.setObjectName("cardTexto")
            lbl_estado = QLabel(f"Estado: {res['estado']}")
            lbl_estado.setStyleSheet(f"color: {estado_color}; font-size: 12pt; font-weight: bold;")

            card_layout.addWidget(lbl_nombre)
            card_layout.addWidget(lbl_horario)
            card_layout.addWidget(lbl_mesas)
            card_layout.addWidget(lbl_estado)

            self.resultado_frame.addWidget(card)

    # ==================== Vendedor ====================
    def mostrar_login_vendedor(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(30)
        self.main_layout.addWidget(self._label("Login Vendedor", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QFormLayout()
        self.entry_vendedor_nombre = QLineEdit()
        self.entry_vendedor_pass = QLineEdit()
        self.entry_vendedor_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.entry_vendedor_nombre.returnPressed.connect(self.login_vendedor)
        self.entry_vendedor_pass.returnPressed.connect(self.login_vendedor)
        form.addRow("Nombre:", self.entry_vendedor_nombre)
        form.addRow("Contraseña:", self.entry_vendedor_pass)
        self.main_layout.addLayout(form)

        self.main_layout.addLayout(self._fila_botones(
            [self._boton("Ingresar", self.login_vendedor, "btnAccent")]
        ))
        self.main_layout.addLayout(self._fila_botones(
            [self._boton(" Volver", self.mostrar_menu_principal)]
        ))
        self.main_layout.addStretch()

    def login_vendedor(self):
        nombre = self.entry_vendedor_nombre.text().strip()
        contrasena = self.entry_vendedor_pass.text().strip()

        vendedores = db.obtener_vendedores()

        if nombre not in vendedores:
            QMessageBox.critical(self, "Error", "Nombre inválido.")
            return
        if contrasena != vendedores[nombre]:
            QMessageBox.critical(self, "Error", "Contraseña incorrecta.")
            return

        self.vendedor_actual = nombre
        self.mostrar_menu_vendedor()

    def mostrar_menu_vendedor(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self._label(f"Menú Vendedor ({self.vendedor_actual})", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(30)

        col = QVBoxLayout()
        col.setSpacing(10)
        col.addWidget(self._boton(" Ver Reservas Pendientes", self.mostrar_reservas_pendientes_vendedor, min_width=260), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Gestionar Reservas", self.mostrar_gestion_reservas, min_width=260), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addSpacing(10)
        col.addWidget(self._boton(" Cerrar Sesión", self.mostrar_menu_principal, min_width=260), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addLayout(col)
        self.main_layout.addStretch()

    def _mostrar_lista_pendientes(self, callback_volver):
        self.limpiar_frame()

        self.main_layout.addWidget(self._label("Reservas Pendientes", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        columns = ("Nombre", "Día", "Inicio", "Fin", "Mesas", "Personas", "Estado")
        tree = QTreeWidget()
        tree.setHeaderLabels(columns)
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(True)
        tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tree.setMinimumHeight(260)

        reservas_pendientes = db.obtener_reservas_pendientes()

        if not reservas_pendientes:
            QTreeWidgetItem(tree, ["No hay reservas pendientes", "", "", "", "", "", ""])
        else:
            for res in reservas_pendientes:
                mesas_str = ", ".join(map(str, res["mesas"]))
                QTreeWidgetItem(tree, [res["nombre"], res["dia"], res["inicio_str"], res["fin_str"], mesas_str, str(res["personas"]), res["estado"]])

        self.main_layout.addWidget(tree)

        self.main_layout.addLayout(self._fila_botones(
            [self._boton(" Volver", callback_volver)]
        ))

    def mostrar_reservas_pendientes_vendedor(self):
        self._mostrar_lista_pendientes(self.mostrar_menu_vendedor)

    def mostrar_reservas_pendientes_publico(self):
        self._mostrar_lista_pendientes(self.mostrar_menu_principal)

    def _mostrar_gestion_reservas(self, callback_volver, es_admin=False):
        self.limpiar_frame()

        titulo = "Gestionar Reservas (Admin)" if es_admin else "Gestionar Reservas"
        self.main_layout.addWidget(self._label(titulo, "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        reservas_pendientes = db.obtener_reservas_pendientes()

        if es_admin:
            self.admin_reservas_pendientes = reservas_pendientes
        else:
            self.reservas_pendientes_gestion = reservas_pendientes

        if not reservas_pendientes:
            self.main_layout.addWidget(self._label("No hay reservas pendientes.", "lblWarning", Qt.AlignmentFlag.AlignHCenter))
            self.main_layout.addLayout(self._fila_botones(
                [self._boton(" Volver", callback_volver)]
            ))
            self.main_layout.addStretch()
            return

        listbox = QListWidget()
        listbox.setMinimumHeight(220)
        indices = []
        for idx, res in enumerate(reservas_pendientes):
            mesas_str = ", ".join(map(str, res["mesas"]))
            listbox.addItem(f"{idx+1}. {res['nombre']} | {res['dia']} {res['inicio_str']}-{res['fin_str']} | Mesas: {mesas_str}")
            indices.append(idx)

        if es_admin:
            self.admin_gestion_listbox = listbox
            self.admin_gestion_indices = indices
        else:
            self.gestion_listbox = listbox
            self.gestion_indices = indices

        self.main_layout.addWidget(listbox)

        self.main_layout.addLayout(self._fila_botones([
            self._boton(" Aceptar", lambda: self._procesar_reserva("aceptar", es_admin), "btnSuccess"),
            self._boton(" Rechazar", lambda: self._procesar_reserva("rechazar", es_admin), "btnDanger"),
            self._boton(" Volver", callback_volver),
        ]))

    def mostrar_gestion_reservas(self):
        self._mostrar_gestion_reservas(self.mostrar_menu_vendedor, es_admin=False)

    def mostrar_gestion_reservas_admin(self):
        self._mostrar_gestion_reservas(self.mostrar_menu_admin, es_admin=True)

    def _procesar_reserva(self, accion, es_admin=False):
        listbox = self.admin_gestion_listbox if es_admin else self.gestion_listbox
        indices = self.admin_gestion_indices if es_admin else self.gestion_indices
        reservas_pendientes = self.admin_reservas_pendientes if es_admin else self.reservas_pendientes_gestion

        seleccion = listbox.currentRow()
        if seleccion < 0:
            QMessageBox.warning(self, "Atención", "Seleccione una reserva de la lista.")
            return

        idx = indices[seleccion]
        res = reservas_pendientes[idx]

        # Verificar conflicto automático contra reservas ya aceptadas
        reservas_aceptadas = db.obtener_reservas_por_estado("Aceptada")
        conflicto = False
        for acept in reservas_aceptadas:
            if res["dia"] == acept["dia"]:
                for m in res["mesas"]:
                    if m in acept["mesas"]:
                        if not (res["fin_min"] <= acept["inicio_min"] or res["inicio_min"] >= acept["fin_min"]):
                            conflicto = True
                            break

        if conflicto:
            db.actualizar_estado_reserva(res["id"], "Rechazada - Horario en conflicto")
            QMessageBox.information(self, "Conflicto", "Reserva rechazada automáticamente por conflicto de horario.")
        elif accion == "aceptar":
            db.actualizar_estado_reserva(res["id"], "Aceptada")
            QMessageBox.information(self, "Éxito", "Reserva aceptada correctamente.")
        else:
            db.actualizar_estado_reserva(res["id"], "Rechazada")
            QMessageBox.information(self, "Éxito", "Reserva rechazada correctamente.")

        if es_admin:
            self.mostrar_gestion_reservas_admin()
        else:
            self.mostrar_gestion_reservas()

    # ==================== Administrador ====================
    def mostrar_login_admin(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(30)
        self.main_layout.addWidget(self._label("Login Administrador", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QFormLayout()
        self.entry_admin_pass = QLineEdit()
        self.entry_admin_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.entry_admin_pass.returnPressed.connect(self.login_admin)
        form.addRow("Contraseña:", self.entry_admin_pass)
        self.main_layout.addLayout(form)

        self.main_layout.addLayout(self._fila_botones(
            [self._boton("Ingresar", self.login_admin, "btnAccent")]
        ))
        self.main_layout.addLayout(self._fila_botones(
            [self._boton(" Volver", self.mostrar_menu_principal)]
        ))
        self.main_layout.addStretch()

    def login_admin(self):
        if self.entry_admin_pass.text().strip() != "123":
            QMessageBox.critical(self, "Error", "Contraseña incorrecta.")
            return
        self.mostrar_menu_admin()

    def mostrar_menu_admin(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self._label("Menú Administrador", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(30)

        col = QVBoxLayout()
        col.setSpacing(8)
        col.addWidget(self._boton(" Gestionar Reservas Pendientes", self.mostrar_gestion_reservas_admin, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Crear Vendedor", self.mostrar_crear_vendedor, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Eliminar Vendedor", self.mostrar_eliminar_vendedor, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Actualizar Contraseña Vendedor", self.mostrar_actualizar_vendedor, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addSpacing(10)
        col.addWidget(self._boton(" Cerrar Sesión", self.mostrar_menu_principal, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addLayout(col)
        self.main_layout.addStretch()

    def mostrar_crear_vendedor(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self._label("Crear Vendedor", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QFormLayout()
        self.entry_new_vend_nombre = QLineEdit()
        self.entry_new_vend_pass = QLineEdit()
        self.entry_new_vend_nombre.returnPressed.connect(self.crear_vendedor)
        self.entry_new_vend_pass.returnPressed.connect(self.crear_vendedor)
        form.addRow("Nombre:", self.entry_new_vend_nombre)
        form.addRow("Contraseña:", self.entry_new_vend_pass)
        self.main_layout.addLayout(form)

        self.main_layout.addLayout(self._fila_botones(
            [self._boton("Crear", self.crear_vendedor, "btnAccent")]
        ))
        self.main_layout.addLayout(self._fila_botones(
            [self._boton(" Volver", self.mostrar_menu_admin)]
        ))
        self.main_layout.addStretch()

    def crear_vendedor(self):
        nombre = self.entry_new_vend_nombre.text().strip()
        contrasena = self.entry_new_vend_pass.text().strip()

        if not nombre or not contrasena:
            QMessageBox.critical(self, "Error", "Complete todos los campos.")
            return

        vendedores = db.obtener_vendedores()
        if any(nombre.lower() == v.lower() for v in vendedores):
            QMessageBox.critical(self, "Error", f"Ya existe un vendedor con el nombre '{nombre}'.")
            return

        db.crear_vendedor(nombre, contrasena)
        QMessageBox.information(self, "Éxito", f"Vendedor '{nombre}' creado correctamente.")
        self.mostrar_menu_admin()

    def mostrar_eliminar_vendedor(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self._label("Eliminar Vendedor", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QFormLayout()
        self.combo_del_vend = QComboBox()
        self.combo_del_vend.addItems(list(db.obtener_vendedores().keys()))
        form.addRow("Seleccione vendedor:", self.combo_del_vend)
        self.main_layout.addLayout(form)

        self.main_layout.addLayout(self._fila_botones(
            [self._boton("Eliminar", self.eliminar_vendedor, "btnDanger")]
        ))
        self.main_layout.addLayout(self._fila_botones(
            [self._boton(" Volver", self.mostrar_menu_admin)]
        ))
        self.main_layout.addStretch()

    def eliminar_vendedor(self):
        nombre = self.combo_del_vend.currentText()
        if not nombre:
            QMessageBox.critical(self, "Error", "Seleccione un vendedor.")
            return

        respuesta = QMessageBox.question(
            self, "Confirmar", f"¿Eliminar al vendedor '{nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            db.eliminar_vendedor(nombre)
            QMessageBox.information(self, "Éxito", "Vendedor eliminado.")
            self.mostrar_menu_admin()

    def mostrar_actualizar_vendedor(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self._label("Actualizar Contraseña", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QFormLayout()
        self.combo_upd_vend = QComboBox()
        self.combo_upd_vend.addItems(list(db.obtener_vendedores().keys()))
        self.entry_upd_vend_pass = QLineEdit()
        self.entry_upd_vend_pass.returnPressed.connect(self.actualizar_vendedor)
        form.addRow("Seleccione vendedor:", self.combo_upd_vend)
        form.addRow("Nueva contraseña:", self.entry_upd_vend_pass)
        self.main_layout.addLayout(form)

        self.main_layout.addLayout(self._fila_botones(
            [self._boton("Actualizar", self.actualizar_vendedor, "btnAccent")]
        ))
        self.main_layout.addLayout(self._fila_botones(
            [self._boton(" Volver", self.mostrar_menu_admin)]
        ))
        self.main_layout.addStretch()

    def actualizar_vendedor(self):
        nombre = self.combo_upd_vend.currentText()
        contrasena = self.entry_upd_vend_pass.text().strip()

        if not nombre:
            QMessageBox.critical(self, "Error", "Seleccione un vendedor.")
            return
        if not contrasena:
            QMessageBox.critical(self, "Error", "Ingrese una nueva contraseña.")
            return

        db.actualizar_password_vendedor(nombre, contrasena)
        QMessageBox.information(self, "Éxito", "Contraseña actualizada.")
        self.mostrar_menu_admin()


# ==================== Ejecución ====================
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS_TEMA_OSCURO)

    ventana = CoverOSApp()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()