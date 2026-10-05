import re
import sys
import threading
import unicodedata
from datetime import date, datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox,
    QCheckBox, QListWidget, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QFrame, QHeaderView, QAbstractSpinBox, QCalendarWidget, QScrollArea
)
from PySide6.QtCore import Qt, QObject, Signal, QRegularExpression, QDate
from PySide6.QtGui import QColor, QRegularExpressionValidator, QTextCharFormat
import db
import correo

# Cuántos días hacia adelante se puede reservar (cámbialo si quieres)
DIAS_ADELANTE = 60
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

/* ---------- Campo de fecha ---------- */
QPushButton#campoFecha {
    background-color: #16213e;
    border: 1px solid #2c2f4a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e0e0e0;
    text-align: left;
}
QPushButton#campoFecha:hover {
    border: 1px solid #00d4ff;
    background-color: #1c2745;
}

/* ---------- Calendario ---------- */
QCalendarWidget QWidget {
    background-color: #16213e;
    color: #e0e0e0;
}
QCalendarWidget QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    selection-background-color: #007bff;
    selection-color: #ffffff;
}

/* ---------- Campos de entrada ---------- */
QLineEdit, QComboBox, QSpinBox, QDateEdit {
    background-color: #16213e;
    border: 1px solid #2c2f4a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e0e0e0;
}

QComboBox {
    combobox-popup: 0;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {
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

/* ---------- Botones de filtro (activo) ---------- */
QPushButton:checked {
    background-color: #007bff;
    color: #ffffff;
    border: 1px solid #00d4ff;
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

/* ---------- Campo de fecha ---------- */
QPushButton#campoFecha {
    background-color: #f5f7fb;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1c2333;
    text-align: left;
}
QPushButton#campoFecha:hover {
    border: 1px solid #0d6efd;
    background-color: #ffffff;
}

/* ---------- Calendario ---------- */
QCalendarWidget QWidget {
    background-color: #f5f7fb;
    color: #1c2333;
}
QCalendarWidget QAbstractItemView {
    background-color: #f5f7fb;
    color: #1c2333;
    selection-background-color: #0d6efd;
    selection-color: #ffffff;
}

/* ---------- Campos de entrada ---------- */
QLineEdit, QComboBox, QSpinBox, QDateEdit {
    background-color: #f5f7fb;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1c2333;
}

QComboBox {
    combobox-popup: 0;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {
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

/* ---------- Botones de filtro (activo) ---------- */
QPushButton:checked {
    background-color: #0d6efd;
    color: #ffffff;
    border: 1px solid #0a58ca;
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


class SelectorFecha(QPushButton):
    """Campo de fecha: al hacer clic en cualquier parte del campo se despliega el calendario."""

    def __init__(self, parent, minimo, maximo, inicial):
        super().__init__(parent)
        self.setObjectName("campoFecha")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fecha = inicial

        self._calendario = QCalendarWidget(self)
        self._calendario.setWindowFlags(Qt.WindowType.Popup)
        self._calendario.setMinimumDate(minimo)
        self._calendario.setMaximumDate(maximo)
        self._calendario.setSelectedDate(inicial)
        self._calendario.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self._calendario.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self._calendario.clicked.connect(self._elegir)
        self._calendario.activated.connect(self._elegir)

        self.clicked.connect(self._abrir)
        self._actualizar_texto()

    def date(self):
        return self._fecha

    def calendarWidget(self):
        return self._calendario

    def _actualizar_texto(self):
        self.setText(self._fecha.toString("dd/MM/yyyy") + "   \u25be")

    def _abrir(self):
        self._calendario.setSelectedDate(self._fecha)
        self._calendario.move(self.mapToGlobal(self.rect().bottomLeft()))
        self._calendario.show()

    def _elegir(self, fecha):
        self._fecha = fecha
        self._actualizar_texto()
        self._calendario.hide()


class NotificadorCorreo(QObject):
    """Permite avisar a la ventana, desde el hilo del correo, si el envío salió bien o mal."""
    terminado = Signal(bool, str)


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

        self.vendedor_actual = ""
        self.rol_actual = "Vendedor"

        self.notificador = NotificadorCorreo()
        self.notificador.terminado.connect(self._al_terminar_envio_correo)

        self.mostrar_menu_principal()

    def keyPressEvent(self, event):
        # Esc = salida de emergencia en pantalla completa
        if event.key() == Qt.Key.Key_Escape:
            self.salir_app()
            return
        super().keyPressEvent(event)

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

    def validar_correo(self, texto):
        return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", texto) is not None

    def validar_telefono(self, texto):
        """Opcional: vacío es válido. Si se escribe, solo dígitos, espacios, + y -, entre 8 y 15 dígitos."""
        if not texto:
            return True
        if not re.fullmatch(r"[0-9+\-\s]+", texto):
            return False
        return 8 <= len(re.sub(r"\D", "", texto)) <= 15

    def validar_numero_personas(self, num):
        try:
            n = int(num)
            return n > 0
        except:
            return False

    def validar_dia(self, dia):
        dia = dia.strip().capitalize()
        return dia in self.dias_semana and dia != "Lunes"

    # ---------- Fechas ----------
    def _nombre_dia(self, fecha):
        return self.dias_semana[fecha.weekday()]

    def _texto_fecha(self, res, largo=False):
        """Reservas nuevas: 'Mar 07/10/2026' (largo: 'Martes 07/10/2026'). Viejas sin fecha: solo el día."""
        fecha = res.get("fecha")
        if not fecha:
            return res["dia"] if largo else f"{res['dia']} (sin fecha)"
        nombre = self._nombre_dia(fecha)
        if not largo:
            nombre = nombre[:3]
        return f"{nombre} {fecha.strftime('%d/%m/%Y')}"

    def _esta_vencida(self, res):
        fecha = res.get("fecha")
        return bool(fecha) and fecha < date.today()

    def _misma_fecha(self, a, b):
        fa, fb = a.get("fecha"), b.get("fecha")
        if fa and fb:
            return fa == fb
        if not fa and not fb:
            return a["dia"] == b["dia"]
        return False

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
        self.main_layout.addWidget(self._label("Restaurante Don bigote", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        lbl_sub = self._label("Aplicacion escritorio en gestionamiento de Reservas", "lblSubHeader", Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addWidget(lbl_sub)
        self.main_layout.addSpacing(20)

        col = QVBoxLayout()
        col.setSpacing(10)
        col.addWidget(self._boton(" Registrar reserva", self.mostrar_menu_cliente, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Consultar reservas", self.mostrar_reservas_pendientes_publico, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Gestión de reservas", self.mostrar_login_vendedor, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Administración general", self.mostrar_login_admin, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addLayout(col)
        self.main_layout.addStretch()

        # ---------- Fila inferior: Cerrar (izquierda) y selector de tema (derecha) ----------
        tema_layout = QHBoxLayout()
        tema_layout.addWidget(self._boton(" Cerrar", self.salir_app, "btnDanger", min_width=120))
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
        self.main_layout.addWidget(self._label("Registrar reserva", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
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

        # Correo (obligatorio) y teléfono (opcional)
        self.entry_correo = QLineEdit()
        self.entry_correo.setPlaceholderText("ejemplo@gmail.com")
        form.addRow("Correo electrónico:", self.entry_correo)

        self.entry_telefono = QLineEdit()
        self.entry_telefono.setPlaceholderText("Opcional (solo números)")
        self.entry_telefono.setMaxLength(15)
        # Solo permite escribir dígitos (las letras y símbolos no se pueden teclear ni pegar)
        self.entry_telefono.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]*")))
        form.addRow("Teléfono (opcional):", self.entry_telefono)

        # Personas
        self.spin_personas = QSpinBox()
        self.spin_personas.setRange(1, self.limite_personas)
        self.spin_personas.setValue(1)
        self.spin_personas.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        form.addRow(f"Número de personas (máx {self.limite_personas}):", self.spin_personas)

        # Fecha (calendario)
        hoy = QDate.currentDate()
        self.date_fecha = SelectorFecha(
            self, hoy, hoy.addDays(DIAS_ADELANTE),
            hoy.addDays(1) if hoy.dayOfWeek() == 1 else hoy
        )

        # Los lunes (cerrado) se ven en gris en el calendario
        formato_cerrado = QTextCharFormat()
        formato_cerrado.setForeground(QColor("#888888"))
        calendario = self.date_fecha.calendarWidget()
        for i in range(DIAS_ADELANTE + 1):
            d = hoy.addDays(i)
            if d.dayOfWeek() == 1:
                calendario.setDateTextFormat(d, formato_cerrado)

        form.addRow("Fecha de la reserva (lunes cerrado):", self.date_fecha)

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
        qfecha = self.date_fecha.date()
        fecha = date(qfecha.year(), qfecha.month(), qfecha.day())
        dia = self.dias_semana[fecha.weekday()]

        if not self.validar_nombre(nombre):
            QMessageBox.critical(self, "Error", "Nombre inválido. Solo letras y mínimo 2 caracteres.")
            return
        correo_cliente = self.entry_correo.text().strip()
        telefono = self.entry_telefono.text().strip()
        if not correo_cliente:
            QMessageBox.critical(self, "Error", "El correo electrónico es obligatorio.")
            return
        if not self.validar_correo(correo_cliente):
            QMessageBox.critical(self, "Error", "Correo inválido. Use el formato ejemplo@gmail.com")
            return
        if not self.validar_telefono(telefono):
            QMessageBox.critical(self, "Error", "Teléfono inválido. Use solo números (mínimo 8 dígitos).")
            return
        if not self.validar_numero_personas(num_personas):
            QMessageBox.critical(self, "Error", "Número de personas inválido.")
            return
        if int(num_personas) > self.limite_personas:
            QMessageBox.critical(self, "Error", f"No puede superar el límite de {self.limite_personas} personas.")
            return
        if fecha < date.today():
            QMessageBox.critical(self, "Error", "No se puede reservar en una fecha que ya pasó.")
            return
        if (fecha - date.today()).days > DIAS_ADELANTE:
            QMessageBox.critical(self, "Error", f"Solo se puede reservar hasta {DIAS_ADELANTE} días hacia adelante.")
            return
        if not self.validar_dia(dia):
            QMessageBox.critical(self, "Error", "El restaurante está cerrado los lunes. Elija otra fecha.")
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
        if fecha == date.today():
            ahora = datetime.now()
            if inicio_min <= ahora.hour * 60 + ahora.minute:
                QMessageBox.critical(self, "Error", "Para hoy, la hora de inicio debe ser posterior a la hora actual.")
                return

        # Guardar valores para usar al registrar
        self.reserva_temp = {
            "nombre": nombre,
            "correo": correo_cliente,
            "telefono": telefono if telefono else None,
            "personas": int(num_personas),
            "dia": dia,
            "fecha": fecha,
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

        reservas_dia = db.obtener_reservas_por_fecha(fecha)

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
            mesas_seleccionadas,
            self.reserva_temp["telefono"],
            self.reserva_temp["correo"],
            self.reserva_temp["fecha"]
        )
        QMessageBox.information(self, "Éxito", "Reserva solicitada y pendiente de aprobación por vendedor.")
        self.mostrar_menu_cliente()

    # ---------- Ver estado de mi reserva ----------
    def _normalizar(self, texto):
        """Minúsculas y sin tildes, para buscar 'perez' y encontrar 'Pérez'."""
        texto = unicodedata.normalize("NFD", str(texto).lower())
        return "".join(c for c in texto if unicodedata.category(c) != "Mn")

    def _ocultar_correo(self, correo):
        """juanperez@gmail.com -> juan***@gmail.com (nunca muestra más de la mitad del nombre)."""
        correo = (correo or "").strip()
        if "@" not in correo:
            return ""
        local, dominio = correo.rsplit("@", 1)
        visibles = min(4, max(1, len(local) // 2))
        return f"{local[:visibles]}***@{dominio}"

    def _ocultar_telefono(self, telefono):
        """88887777 -> ****7777"""
        digitos = re.sub(r"\D", "", telefono or "")
        if not digitos:
            return ""
        return "****" + digitos[-4:] if len(digitos) > 4 else "****"

    def _estado_amigable(self, res):
        """Devuelve (texto para el cliente, color)."""
        estado = res["estado"]
        pasada = self._esta_vencida(res)
        if estado == "Aceptada":
            if pasada:
                return "Finalizada", "#888888"
            return "Confirmada. ¡Te esperamos!", "#28a745"
        if estado == "Pendiente":
            if pasada:
                return "Vencida: la fecha pasó sin ser aprobada", "#888888"
            return "En espera de aprobación", "#d39e00"
        if "conflicto" in estado:
            return "Sin disponibilidad en ese horario. Puede reservar otro.", "#dc3545"
        return "Rechazada", "#dc3545"

    def _clave_busqueda(self, res):
        """Próximas primero (la más cercana arriba), luego las pasadas y al final las viejas sin fecha."""
        fecha = res.get("fecha")
        if not fecha:
            return (2, 0, res["inicio_min"], res["id"])
        if fecha >= date.today():
            return (0, fecha.toordinal(), res["inicio_min"], res["id"])
        return (1, -fecha.toordinal(), res["inicio_min"], res["id"])

    def mostrar_consulta_reserva(self):
        self.limpiar_frame()

        self.main_layout.addWidget(self._label("Consultar Estado de Reserva", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QHBoxLayout()
        self.entry_consulta = QLineEdit()
        self.entry_consulta.setMinimumWidth(260)
        self.entry_consulta.setPlaceholderText("Ej: Juan")
        self.entry_consulta.returnPressed.connect(self.buscar_reserva)
        form.addStretch()
        form.addWidget(QLabel("Nombre de la reserva:"))
        form.addWidget(self.entry_consulta)
        form.addWidget(self._boton("Buscar", self.buscar_reserva, "btnAccent"))
        form.addStretch()
        self.main_layout.addLayout(form)

        # Resultados con scroll
        contenedor = QWidget()
        self.resultado_frame = QVBoxLayout(contenedor)
        self.resultado_frame.setContentsMargins(0, 0, 0, 0)
        self.resultado_frame.setSpacing(10)
        self.resultado_frame.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMinimumHeight(260)
        scroll.setWidget(contenedor)
        self.main_layout.addWidget(scroll, 1)

        self.main_layout.addLayout(self._fila_botones(
            [self._boton(" Volver", self.mostrar_menu_cliente)]
        ))

    def buscar_reserva(self):
        texto = self.entry_consulta.text().strip()
        self._limpiar_layout(self.resultado_frame)

        if len(texto) < 2:
            self.resultado_frame.addWidget(self._label("Escriba el nombre de la reserva (mínimo 2 letras).", "lblWarning"))
            return

        buscado = self._normalizar(texto)
        resultados = [r for r in db.obtener_todas_las_reservas() if buscado in self._normalizar(r["nombre"])]
        resultados.sort(key=self._clave_busqueda)

        if not resultados:
            self.resultado_frame.addWidget(self._label("No se encontró ninguna reserva con ese nombre.", "lblError"))
            return

        n = len(resultados)
        self.resultado_frame.addWidget(QLabel("Se encontró 1 reserva:" if n == 1 else f"Se encontraron {n} reservas:"))

        for res in resultados:
            mesas_str = ", ".join(map(str, res["mesas"]))
            estado_texto, estado_color = self._estado_amigable(res)

            correo_oculto = self._ocultar_correo(res.get("correo"))
            telefono_oculto = self._ocultar_telefono(res.get("telefono"))
            contacto = f"Correo: {correo_oculto}" if correo_oculto else "Correo: no registrado"
            if telefono_oculto:
                contacto += f"  |  Tel: {telefono_oculto}"

            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(15, 10, 15, 10)
            card_layout.setSpacing(4)

            lbl_nombre = QLabel(f"Reserva: {res['nombre']}")
            lbl_nombre.setObjectName("cardTitulo")
            lbl_contacto = QLabel(contacto)
            lbl_contacto.setObjectName("cardTexto")
            lbl_horario = QLabel(f"Fecha: {self._texto_fecha(res, True)}  |  Horario: {res['inicio_str']} a {res['fin_str']}")
            lbl_horario.setObjectName("cardTexto")
            lbl_mesas = QLabel(f"Mesas: {mesas_str}  |  Personas: {res['personas']}")
            lbl_mesas.setObjectName("cardTexto")
            lbl_estado = QLabel(f"\u25cf {estado_texto}")
            lbl_estado.setStyleSheet(f"color: {estado_color}; font-size: 12pt; font-weight: bold;")

            card_layout.addWidget(lbl_nombre)
            card_layout.addWidget(lbl_contacto)
            card_layout.addWidget(lbl_horario)
            card_layout.addWidget(lbl_mesas)
            card_layout.addWidget(lbl_estado)

            self.resultado_frame.addWidget(card)

    # ==================== Vendedor ====================
    def mostrar_login_vendedor(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(30)
        self.main_layout.addWidget(self._label("Gestión de reservas", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
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
        self.rol_actual = db.obtener_rol_vendedor(nombre)

        if self.rol_actual == "Consultar reservas":
            # Perfil de solo consulta: ve únicamente la pantalla de consulta
            self._mostrar_lista_pendientes(self.mostrar_menu_principal, texto_volver=" Cerrar Sesión")
        else:
            self.mostrar_menu_vendedor()

    def mostrar_menu_vendedor(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self._label(f"Gestión de reservas ({self.vendedor_actual})", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(30)

        col = QVBoxLayout()
        col.setSpacing(10)
        col.addWidget(self._boton(" Ver Reservas Pendientes", self.mostrar_reservas_pendientes_vendedor, min_width=260), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Gestionar Reservas", self.mostrar_gestion_reservas, min_width=260), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addSpacing(10)
        col.addWidget(self._boton(" Cerrar Sesión", self.mostrar_menu_principal, min_width=260), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addLayout(col)
        self.main_layout.addStretch()

    # ---------- Consultar reservas (todas, con filtros y buscador) ----------
    FILTROS_CONSULTA = ["Todas", "Aceptadas", "Rechazadas", "En espera"]

    def _clave_cronologica(self, res):
        """Orden: día de la semana (Martes -> Domingo) y luego hora de inicio."""
        fecha = res.get("fecha")
        if fecha:
            return (0, fecha.toordinal(), res["inicio_min"], res["id"])
        # Reservas viejas sin fecha: al final, ordenadas por día de la semana
        dia = str(res["dia"]).strip().capitalize()
        try:
            idx_dia = self.dias_semana.index(dia)
        except ValueError:
            idx_dia = len(self.dias_semana)
        return (1, idx_dia, res["inicio_min"], res["id"])

    def _coincide_filtro(self, estado):
        f = self._consulta_filtro
        if f == "Todas":
            return True
        if f == "Aceptadas":
            return estado == "Aceptada"
        if f == "Rechazadas":
            return estado.startswith("Rechazada")
        if f == "En espera":
            return estado == "Pendiente"
        return True

    def _mostrar_lista_pendientes(self, callback_volver, texto_volver=" Volver", completo=False):
        """completo=True (solo admin): muestra correo y teléfono completos. Si no, el correo va parcial y sin teléfono."""
        self.limpiar_frame()
        self._consulta_completo = completo

        self.main_layout.addWidget(self._label("Consultar Reservas", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(6)

        self._consulta_filtro = "Todas"
        self._consulta_reservas = sorted(db.obtener_todas_las_reservas(), key=self._clave_cronologica)

        # ---------- Buscador por nombre ----------
        fila_busqueda = QHBoxLayout()
        fila_busqueda.addWidget(QLabel("Buscar:"))
        self.entry_busqueda = QLineEdit()
        self.entry_busqueda.setPlaceholderText("Escriba un nombre...")
        self.entry_busqueda.setClearButtonEnabled(True)
        fila_busqueda.addWidget(self.entry_busqueda)
        self.main_layout.addLayout(fila_busqueda)

        # ---------- Botones de filtro ----------
        self._botones_filtro = {}
        fila_filtros = QHBoxLayout()
        fila_filtros.addStretch()
        for nombre_filtro in self.FILTROS_CONSULTA:
            btn = QPushButton(nombre_filtro)
            btn.setCheckable(True)
            btn.setMinimumWidth(130)
            btn.clicked.connect(lambda _=False, n=nombre_filtro: self._cambiar_filtro_consulta(n))
            self._botones_filtro[nombre_filtro] = btn
            fila_filtros.addWidget(btn)
        fila_filtros.addStretch()
        self.main_layout.addLayout(fila_filtros)

        # ---------- Tabla ----------
        if completo:
            columns = ("Nombre", "Correo", "Teléfono", "Fecha", "Inicio", "Fin", "Mesas", "Personas", "Estado")
        else:
            columns = ("Nombre", "Correo", "Fecha", "Inicio", "Fin", "Mesas", "Personas", "Estado")
        self.tree_consulta = QTreeWidget()
        self.tree_consulta.setHeaderLabels(columns)
        self.tree_consulta.setRootIsDecorated(False)
        self.tree_consulta.setAlternatingRowColors(True)
        self.tree_consulta.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tree_consulta.setMinimumHeight(260)
        self.main_layout.addWidget(self.tree_consulta, 1)

        # ---------- Contador ----------
        self.lbl_contador = QLabel("")
        self.main_layout.addWidget(self.lbl_contador)

        self.main_layout.addLayout(self._fila_botones(
            [self._boton(texto_volver, callback_volver)]
        ))

        self.entry_busqueda.textChanged.connect(self._refrescar_consulta)
        self._cambiar_filtro_consulta("Todas")

    def _cambiar_filtro_consulta(self, nombre_filtro):
        self._consulta_filtro = nombre_filtro
        for n, btn in self._botones_filtro.items():
            btn.setChecked(n == nombre_filtro)
        self._refrescar_consulta()

    def _refrescar_consulta(self):
        texto = self.entry_busqueda.text().strip().lower()
        self.tree_consulta.clear()

        colores_estado = {
            "Aceptada": QColor("#28a745"),
            "Rechazada": QColor("#dc3545"),
            "Pendiente": QColor("#d39e00"),
        }

        mostradas = 0
        for res in self._consulta_reservas:
            estado = res["estado"]
            if not self._coincide_filtro(estado):
                continue
            if texto and texto not in res["nombre"].lower():
                continue

            mesas_str = ", ".join(map(str, res["mesas"]))
            if estado == "Pendiente":
                estado_visible = "En espera (vencida)" if self._esta_vencida(res) else "En espera"
            else:
                estado_visible = estado
            correo_res = (res.get("correo") or "").strip()
            if self._consulta_completo:
                columnas_fila = [
                    res["nombre"], correo_res or "no registrado", res.get("telefono") or "-",
                    self._texto_fecha(res), res["inicio_str"], res["fin_str"],
                    mesas_str, str(res["personas"]), estado_visible
                ]
            else:
                columnas_fila = [
                    res["nombre"], self._ocultar_correo(correo_res) or "no registrado",
                    self._texto_fecha(res), res["inicio_str"], res["fin_str"],
                    mesas_str, str(res["personas"]), estado_visible
                ]
            item = QTreeWidgetItem(self.tree_consulta, columnas_fila)
            clave_color = "Rechazada" if estado.startswith("Rechazada") else estado
            if clave_color in colores_estado:
                item.setForeground(len(columnas_fila) - 1, colores_estado[clave_color])
            mostradas += 1

        if mostradas == 0:
            QTreeWidgetItem(self.tree_consulta, ["No se encontraron reservas"])

        self.lbl_contador.setText(f"Mostrando {mostradas} de {len(self._consulta_reservas)} reservas")

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
            marca = " (VENCIDA)" if self._esta_vencida(res) else ""
            listbox.addItem(f"{idx+1}. {res['nombre']} | {self._texto_fecha(res)} {res['inicio_str']}-{res['fin_str']} | Mesas: {mesas_str}{marca}")
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

    def _enviar_correo_aceptada(self, res):
        """Lanza el envío en un hilo aparte. Devuelve False si la reserva no tiene correo."""
        destino = (res.get("correo") or "").strip()
        if not destino:
            return False

        fecha_texto = self._texto_fecha(res, True)

        def tarea():
            ok, mensaje = correo.enviar_correo_reserva_aceptada(
                destino, res["nombre"], fecha_texto, res["inicio_str"],
                res["fin_str"], res["mesas"], res["personas"]
            )
            self.notificador.terminado.emit(ok, mensaje)

        threading.Thread(target=tarea, daemon=True).start()
        return True

    def _al_terminar_envio_correo(self, ok, mensaje):
        if not ok:
            QMessageBox.warning(
                self, "Correo no enviado",
                f"La reserva se aceptó, pero no se pudo enviar el correo al cliente.\n\n{mensaje}"
            )

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

        # No se puede aceptar una reserva cuya fecha ya pasó
        if accion == "aceptar" and self._esta_vencida(res):
            QMessageBox.warning(self, "Reserva vencida",
                                "La fecha de esta reserva ya pasó, no se puede aceptar. Puede rechazarla.")
            return

        # Verificar conflicto automático contra reservas ya aceptadas
        reservas_aceptadas = db.obtener_reservas_por_estado("Aceptada")
        conflicto = False
        for acept in reservas_aceptadas:
            if self._misma_fecha(res, acept):
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
            texto = "Reserva aceptada correctamente."
            if self._enviar_correo_aceptada(res):
                texto += "\nSe está enviando el correo de confirmación al cliente."
            else:
                texto += "\nEsta reserva no tiene correo registrado, no se envió confirmación."
            QMessageBox.information(self, "Éxito", texto)
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
        self.main_layout.addWidget(self._label("Administración general", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
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
        col.addWidget(self._boton(" Consultar Reservas", self.mostrar_consulta_admin, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Gestionar Reservas Pendientes", self.mostrar_gestion_reservas_admin, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Crear Vendedor", self.mostrar_crear_vendedor, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Eliminar Vendedor", self.mostrar_eliminar_vendedor, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Actualizar Contraseña Vendedor", self.mostrar_actualizar_vendedor, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addSpacing(10)
        col.addWidget(self._boton(" Cerrar Sesión", self.mostrar_menu_principal, min_width=300), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addLayout(col)
        self.main_layout.addStretch()

    def mostrar_consulta_admin(self):
        self._mostrar_lista_pendientes(self.mostrar_menu_admin, completo=True)

    def mostrar_crear_vendedor(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self._label("Crear Vendedor", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QFormLayout()
        self.entry_new_vend_nombre = QLineEdit()
        self.entry_new_vend_pass = QLineEdit()
        self.combo_new_vend_rol = QComboBox()
        self.combo_new_vend_rol.addItems(["Vendedor", "Consultar reservas"])
        self.entry_new_vend_nombre.returnPressed.connect(self.crear_vendedor)
        self.entry_new_vend_pass.returnPressed.connect(self.crear_vendedor)
        form.addRow("Nombre:", self.entry_new_vend_nombre)
        form.addRow("Contraseña:", self.entry_new_vend_pass)
        form.addRow("Rol:", self.combo_new_vend_rol)
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

        rol = self.combo_new_vend_rol.currentText()
        if rol == "Vendedor":
            db.crear_vendedor(nombre, contrasena)
        else:
            db.crear_vendedor_con_rol(nombre, contrasena, rol)
        QMessageBox.information(self, "Éxito", f"Usuario '{nombre}' creado correctamente con el rol '{rol}'.")
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
    ventana.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()