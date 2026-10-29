import io
import os
import re
import sys
import threading
import unicodedata
from datetime import date, datetime
from xml.sax.saxutils import escape
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox,
    QCheckBox, QListWidget, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QFrame, QHeaderView, QAbstractSpinBox, QCalendarWidget, QScrollArea,
    QGridLayout, QMenu, QStackedWidget, QFileDialog
)
from PySide6.QtCharts import (
    QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QPieSeries, QValueAxis
)
from PySide6.QtCore import Qt, QObject, Signal, QRegularExpression, QDate, QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QBrush, QColor, QPainter, QPixmap, QRegularExpressionValidator, QTextCharFormat
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

    def setDate(self, fecha):
        self._fecha = fecha
        self._actualizar_texto()

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


# -----------------------------------------------------------------------------
# PANEL DE ADMINISTRACIÓN (menú lateral + dashboard con filtros y gráficas)
# -----------------------------------------------------------------------------
DIAS_CORTO = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
COLORES_ESTADO = {"Pendiente": "#ffcc00", "Aceptada": "#28a745", "Rechazada": "#dc3545"}

QSS_OSCURO = """
QFrame#sidebar { background-color: #12122a; border-right: 1px solid #2c2f4a; }
QLabel#sideTitulo { background: transparent; color: #00d4ff; font-size: 14pt; font-weight: bold; padding: 6px 4px 14px 4px; }
QPushButton#navBtn {
    background: transparent; border: none; border-left: 3px solid transparent;
    border-radius: 0; text-align: left; padding: 10px 14px; color: #c8c8d8;
}
QPushButton#navBtn:hover { background-color: #16213e; color: #ffffff; border-left: 3px solid #2c2f4a; }
QPushButton#navBtn[activo="true"] { background-color: #16213e; color: #00d4ff; border-left: 3px solid #00d4ff; }
QFrame#card QLabel { background: transparent; }
QLabel#kpiValor { background: transparent; color: #00d4ff; font-size: 22pt; font-weight: bold; }
QLabel#kpiTitulo { background: transparent; color: #a0a4bd; }
"""

QSS_CLARO = """
QFrame#sidebar { background-color: #d5dbe9; border-right: 1px solid #ccd0da; }
QLabel#sideTitulo { background: transparent; color: #0d6efd; font-size: 14pt; font-weight: bold; padding: 6px 4px 14px 4px; }
QPushButton#navBtn {
    background: transparent; border: none; border-left: 3px solid transparent;
    border-radius: 0; text-align: left; padding: 10px 14px; color: #2b3348;
}
QPushButton#navBtn:hover { background-color: #e7ebf4; color: #000000; border-left: 3px solid #ccd0da; }
QPushButton#navBtn[activo="true"] { background-color: #f5f7fb; color: #0d6efd; border-left: 3px solid #0d6efd; }
QFrame#card QLabel { background: transparent; }
QLabel#kpiValor { background: transparent; color: #0d6efd; font-size: 22pt; font-weight: bold; }
QLabel#kpiTitulo { background: transparent; color: #5a6275; }
"""


def _hora_texto(h):
    return f"{h % 12 or 12}{'AM' if h < 12 else 'PM'}"


DIAS_LARGO = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def _texto_filtros(desde, hasta, estado):
    return f"Del {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}  |  Estado: {estado or 'Todos'}"


def _kpis(d):
    """Textos de las 4 tarjetas a partir del resultado de db.estadisticas()."""
    est = d["por_estado"]
    resueltas = est["Aceptada"] + est["Rechazada"]
    return {
        "total": str(d["total"]),
        "pendientes": str(est["Pendiente"]),
        "aceptacion": f"{est['Aceptada'] * 100 / resueltas:.0f}%" if resueltas else "—",
        "personas": f"{d['promedio_personas']:.1f}" if d["total"] else "—",
    }


def _correo_visible(correo):
    return "no registrado" if not correo or correo.startswith("sin_correo_") else correo


class BarraFiltros(QWidget):
    """Fila de filtros reutilizable: Rango rápido, Desde, Hasta y Estado (+ botón opcional)."""

    RANGOS = ["Todo", "Últimos 30 días", "Este mes", "Próximos 30 días"]

    def __init__(self, texto_boton=None, al_aplicar=None):
        super().__init__()
        hoy = QDate.currentDate()
        minimo, maximo = QDate(2020, 1, 1), hoy.addYears(1)

        fila = QHBoxLayout(self)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(10)
        self.combo_rango = QComboBox()
        self.combo_rango.addItems(self.RANGOS)
        self.sel_desde = SelectorFecha(self, minimo, maximo, minimo)
        self.sel_hasta = SelectorFecha(self, minimo, maximo, maximo)
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["Todos", "Pendiente", "Aceptada", "Rechazada"])

        for etiqueta, w in (("Rango:", self.combo_rango), ("Desde:", self.sel_desde),
                            ("Hasta:", self.sel_hasta), ("Estado:", self.combo_estado)):
            fila.addWidget(QLabel(etiqueta))
            fila.addWidget(w)
        if texto_boton:
            btn = QPushButton(texto_boton)
            btn.setObjectName("btnAccent")
            btn.clicked.connect(al_aplicar)
            fila.addWidget(btn)
        fila.addStretch()

        self.combo_rango.activated.connect(lambda _: self._aplicar_rango(al_aplicar))
        for sel in (self.sel_desde, self.sel_hasta):
            sel.calendarWidget().clicked.connect(lambda _=None: self.combo_rango.setCurrentIndex(-1))

    def _aplicar_rango(self, al_aplicar=None):
        hoy = QDate.currentDate()
        rangos = {
            "Todo": (QDate(2020, 1, 1), hoy.addYears(1)),
            "Últimos 30 días": (hoy.addDays(-30), hoy),
            "Este mes": (QDate(hoy.year(), hoy.month(), 1), QDate(hoy.year(), hoy.month(), hoy.daysInMonth())),
            "Próximos 30 días": (hoy, hoy.addDays(30)),
        }
        desde, hasta = rangos[self.combo_rango.currentText()]
        self.sel_desde.setDate(desde)
        self.sel_hasta.setDate(hasta)
        if al_aplicar:
            al_aplicar()

    def valores(self):
        """(desde, hasta, estado o None) — o None (con aviso) si el rango es inválido."""
        desde = self.sel_desde.date().toPython()
        hasta = self.sel_hasta.date().toPython()
        if desde > hasta:
            QMessageBox.warning(self, "Rango inválido", "La fecha 'Desde' no puede ser mayor que 'Hasta'.")
            return None
        estado = self.combo_estado.currentText()
        return desde, hasta, (None if estado == "Todos" else estado)


# -----------------------------------------------------------------------------
# REPORTES (PDF y Excel) - diseño corporativo
# -----------------------------------------------------------------------------
EMPRESA = "Sistema de Reservas"  # nombre que sale en el encabezado de todos los reportes
# Logo opcional: pon un archivo "logo.png" junto a este programa y saldrá en los PDF
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")

# Paleta (hex sin '#')
R_AZUL_OSCURO = "12264A"
R_AZUL = "0D6EFD"
R_VERDE = "1E9E57"
R_AMBAR = "E0A800"
R_ROJO = "D64045"
R_FONDO = "F4F6FA"
R_TEXTO = "5A6275"
R_LINEA = "D9DEE8"
# estado -> (relleno claro, color de texto)
R_ESTADO = {"Aceptada": ("DDF3E4", "1E7B45"), "Pendiente": ("FFF1CC", "8A6100"), "Rechazada": ("FADBD8", "A8262B")}


def _clave_estado(nombre):
    return "Rechazada" if nombre.startswith("Rechazada") else nombre


def _plural(n, palabra):
    return f"{n} {palabra}{'' if n == 1 else 's'}"


def _picos(d):
    """Día, hora y mesas con más y menos movimiento (solo lo que tenga datos)."""
    res = {}
    dias = d["por_dia"]
    if any(dias):
        i = max(range(7), key=lambda k: dias[k])
        res["dia"] = (DIAS_LARGO[i], dias[i])
    if d["por_hora"]:
        h = max(d["por_hora"], key=d["por_hora"].get)
        res["hora"] = (_hora_texto(h), d["por_hora"][h])
    if d["mesas"]:
        mx = max(d["mesas"], key=d["mesas"].get)
        mn = min(d["mesas"], key=d["mesas"].get)
        res["mesa_max"] = (mx, d["mesas"][mx])
        res["mesa_min"] = (mn, d["mesas"][mn])
    return res


def _resumen_ejecutivo(d):
    """Frases automáticas que explican los números del período."""
    if not d["total"]:
        return ["No hay reservas en el período seleccionado."]
    est = d["por_estado"]
    resueltas = est["Aceptada"] + est["Rechazada"]
    frases = [f"Se registraron {_plural(d['total'], 'reserva')}, con un promedio de "
              f"{d['promedio_personas']:.1f} personas por reserva."]
    if resueltas:
        frases.append(f"De las reservas ya resueltas, el {est['Aceptada'] * 100 / resueltas:.0f}% fue aceptada "
                      f"({est['Aceptada']} de {resueltas}).")
    if est["Pendiente"]:
        n = est["Pendiente"]
        frases.append(f"Hay {_plural(n, 'reserva')} pendiente{'' if n == 1 else 's'} de revisión.")
    p = _picos(d)
    if "dia" in p:
        frases.append(f"El día más concurrido es el {p['dia'][0].lower()} ({_plural(p['dia'][1], 'reserva')}).")
    if "hora" in p:
        frases.append(f"La hora pico es {p['hora'][0]} ({_plural(p['hora'][1], 'reserva')}).")
    if "mesa_max" in p:
        t = f"La mesa {p['mesa_max'][0]} es la más usada ({_plural(p['mesa_max'][1], 'uso')})"
        if p["mesa_min"][0] != p["mesa_max"][0]:
            t += f" y la mesa {p['mesa_min'][0]}, la menos usada ({_plural(p['mesa_min'][1], 'uso')})"
        frases.append(t + ".")
    return frases


def _contar_estados(reservas):
    cuenta = {"Aceptada": 0, "Pendiente": 0, "Rechazada": 0}
    for r in reservas:
        cuenta[_clave_estado(r["estado"])] += 1
    return cuenta


# ------------------------------------------------------------------------- PDF
def _lienzo_numerado(titulo_reporte):
    """Canvas de reportlab que dibuja encabezado corporativo y pie 'Página X de Y' en cada hoja."""
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as rl_canvas

    generado = datetime.now()
    margen = 1.7 * cm

    class Lienzo(rl_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._paginas = []

        def showPage(self):
            self._paginas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._paginas)
            for estado in self._paginas:
                self.__dict__.update(estado)
                self._decorar(total)
                super().showPage()
            super().save()

        def _decorar(self, total):
            ancho, alto = self._pagesize
            self.saveState()
            # Banda superior
            self.setFillColor(HexColor("#" + R_AZUL_OSCURO))
            self.rect(0, alto - 2.1 * cm, ancho, 2.1 * cm, stroke=0, fill=1)
            self.setFillColor(HexColor("#" + R_AZUL))
            self.rect(0, alto - 2.2 * cm, ancho, 0.1 * cm, stroke=0, fill=1)
            x = margen
            if os.path.exists(LOGO):
                try:
                    iw, ih = ImageReader(LOGO).getSize()
                    h = 1.4 * cm
                    w = h * iw / ih
                    self.drawImage(LOGO, x, alto - 1.75 * cm, width=w, height=h, mask="auto")
                    x += w + 0.4 * cm
                except Exception:
                    pass
            self.setFillColor(white)
            self.setFont("Helvetica-Bold", 16)
            self.drawString(x, alto - 1.28 * cm, EMPRESA)
            self.setFont("Helvetica", 10)
            self.setFillColor(HexColor("#B8C4DB"))
            self.drawRightString(ancho - margen, alto - 1.25 * cm, titulo_reporte)
            # Pie de página
            self.setStrokeColor(HexColor("#" + R_LINEA))
            self.setLineWidth(0.6)
            self.line(margen, 1.45 * cm, ancho - margen, 1.45 * cm)
            self.setFont("Helvetica", 8)
            self.setFillColor(HexColor("#" + R_TEXTO))
            self.drawString(margen, 0.95 * cm, f"Confidencial   |   {EMPRESA}   |   Generado el {generado:%d/%m/%Y %H:%M}")
            self.drawRightString(ancho - margen, 0.95 * cm, f"Página {self._pageNumber} de {total}")
            self.restoreState()

    return Lienzo


def _pdf_estilos():
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle
    return {
        "titulo": ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=21, leading=26,
                                 textColor=HexColor("#" + R_AZUL_OSCURO), spaceAfter=2),
        "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=10, leading=14, textColor=HexColor("#" + R_TEXTO)),
        "seccion": ParagraphStyle("seccion", fontName="Helvetica-Bold", fontSize=12.5, leading=16, spaceBefore=16,
                                  spaceAfter=3, textColor=HexColor("#" + R_AZUL_OSCURO)),
        "punto": ParagraphStyle("punto", fontName="Helvetica", fontSize=10, leading=15, leftIndent=14,
                                bulletIndent=2, spaceAfter=3, textColor=HexColor("#2b3348")),
        "pie_grafico": ParagraphStyle("pie_grafico", fontName="Helvetica-Oblique", fontSize=8.5, leading=11,
                                      alignment=1, textColor=HexColor("#" + R_TEXTO)),
        "celda": ParagraphStyle("celda", fontName="Helvetica", fontSize=8, leading=10, textColor=HexColor("#2b3348")),
        "celda_enc": ParagraphStyle("celda_enc", fontName="Helvetica-Bold", fontSize=8, leading=10,
                                    textColor=HexColor("#FFFFFF")),
        "total": ParagraphStyle("total", fontName="Helvetica-Bold", fontSize=10, leading=14, alignment=2,
                                textColor=HexColor("#" + R_AZUL_OSCURO)),
    }


def _pdf_seccion(texto, estilos, ancho):
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import HRFlowable, Paragraph
    return [Paragraph(texto, estilos["seccion"]),
            HRFlowable(width=ancho, thickness=1.2, color=HexColor("#" + R_AZUL), spaceAfter=8)]


def _pdf_tarjetas(items, ancho):
    """Tarjetas de indicadores: items = [(valor, etiqueta, color_hex)]."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle
    n, hueco = len(items), 0.35 * cm
    w = (ancho - hueco * (n - 1)) / n
    fila_v, fila_e, anchos = [], [], []
    for i, (valor, etiqueta, _) in enumerate(items):
        if i:
            fila_v.append("")
            fila_e.append("")
            anchos.append(hueco)
        fila_v.append(valor)
        fila_e.append(etiqueta)
        anchos.append(w)
    tabla = Table([fila_v, fila_e], colWidths=anchos, rowHeights=[1.45 * cm, 0.8 * cm])
    estilo = [
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"), ("VALIGN", (0, 1), (-1, 1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 21),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica"), ("FONTSIZE", (0, 1), (-1, 1), 8.5),
        ("TEXTCOLOR", (0, 1), (-1, 1), HexColor("#" + R_TEXTO)),
    ]
    for i, (_, _, color) in enumerate(items):
        c = i * 2
        estilo += [("BACKGROUND", (c, 0), (c, 1), HexColor("#" + R_FONDO)),
                   ("LINEABOVE", (c, 0), (c, 0), 3, HexColor("#" + color)),
                   ("TEXTCOLOR", (c, 0), (c, 0), HexColor("#" + color))]
    tabla.setStyle(TableStyle(estilo))
    return tabla


def generar_pdf_estadisticas(ruta, d, desde, hasta, estado, graficas_png):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    titulo = "Reporte de estadísticas"
    ancho = A4[0] - 3.4 * cm
    estilos = _pdf_estilos()
    doc = SimpleDocTemplate(ruta, pagesize=A4, leftMargin=1.7 * cm, rightMargin=1.7 * cm,
                            topMargin=3.1 * cm, bottomMargin=2.0 * cm, title=titulo, author=EMPRESA)
    k = _kpis(d)
    historia = [
        Paragraph(titulo, estilos["titulo"]),
        Paragraph(f"Período: {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}   |   Estado: {estado or 'Todos'}", estilos["sub"]),
        Spacer(1, 0.5 * cm),
        _pdf_tarjetas([(k["total"], "Reservas", R_AZUL), (k["pendientes"], "Pendientes", R_AMBAR),
                       (k["aceptacion"], "% de aceptación", R_VERDE),
                       (k["personas"], "Personas por reserva", R_AZUL_OSCURO)], ancho),
    ]
    historia += _pdf_seccion("Resumen ejecutivo", estilos, ancho)
    historia += [Paragraph(escape(f), estilos["punto"], bulletText="•") for f in _resumen_ejecutivo(d)]

    # Análisis gráfico: 2 x 2, cada gráfica con una frase corta debajo
    p = _picos(d)
    est = d["por_estado"]
    pies = [
        "Proporción de reservas aceptadas, pendientes y rechazadas." if d["total"] else "Sin datos en el período.",
        f"Día de mayor demanda: {p['dia'][0].lower()}." if "dia" in p else "Sin datos en el período.",
        f"Hora pico: {p['hora'][0]}." if "hora" in p else "Sin datos en el período.",
        f"Mesa más usada: la {p['mesa_max'][0]}." if "mesa_max" in p else "Sin datos en el período.",
    ]
    w_img = 8.5 * cm
    imgs = [Image(io.BytesIO(png), width=w_img, height=w_img * 340 / 540) for png in graficas_png]
    pies_p = [Paragraph(escape(t), estilos["pie_grafico"]) for t in pies]
    historia += _pdf_seccion("Análisis gráfico", estilos, ancho)
    rejilla = Table([imgs[:2], pies_p[:2], imgs[2:], pies_p[2:]], colWidths=[ancho / 2] * 2)
    rejilla.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                 ("BOTTOMPADDING", (0, 1), (-1, 1), 12), ("BOTTOMPADDING", (0, 3), (-1, 3), 4)]))
    historia.append(rejilla)
    doc.build(historia, canvasmaker=_lienzo_numerado(titulo))


def generar_pdf_listado(ruta, reservas, desde, hasta, estado):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    titulo = "Listado de reservas"
    pagina = landscape(A4)
    ancho = pagina[0] - 3.4 * cm
    estilos = _pdf_estilos()
    doc = SimpleDocTemplate(ruta, pagesize=pagina, leftMargin=1.7 * cm, rightMargin=1.7 * cm,
                            topMargin=3.1 * cm, bottomMargin=2.0 * cm, title=titulo, author=EMPRESA)
    cuenta = _contar_estados(reservas)
    historia = [
        Paragraph(titulo, estilos["titulo"]),
        Paragraph(f"Período: {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}   |   Estado: {estado or 'Todos'}", estilos["sub"]),
        Spacer(1, 0.45 * cm),
        _pdf_tarjetas([(str(len(reservas)), "Reservas", R_AZUL), (str(cuenta["Aceptada"]), "Aceptadas", R_VERDE),
                       (str(cuenta["Pendiente"]), "Pendientes", R_AMBAR), (str(cuenta["Rechazada"]), "Rechazadas", R_ROJO)],
                      ancho),
        Spacer(1, 0.5 * cm),
    ]
    if not reservas:
        historia.append(Paragraph("No hay reservas con esos filtros.", estilos["sub"]))
    else:
        c, ce = estilos["celda"], estilos["celda_enc"]
        filas = [[Paragraph(t, ce) for t in ("Nombre", "Correo", "Teléfono", "Fecha", "Horario", "Mesas", "Pers.", "Estado")]]
        for r in reservas:
            color = R_ESTADO[_clave_estado(r["estado"])][1]
            filas.append([
                Paragraph(escape(r["nombre"]), c),
                Paragraph(escape(_correo_visible(r["correo"])), c),
                Paragraph(r.get("telefono") or "-", c),
                Paragraph(f"{r['fecha']:%d/%m/%Y}", c),
                Paragraph(f"{r['inicio_str']} - {r['fin_str']}", c),
                Paragraph(", ".join(map(str, r["mesas"])), c),
                Paragraph(str(r["personas"]), c),
                Paragraph(f'<font color="#{color}"><b>{escape(r["estado"])}</b></font>', c),
            ])
        anchos = [4.5 * cm, 5.3 * cm, 2.4 * cm, 2.2 * cm, 3.4 * cm, 2.4 * cm, 1.3 * cm]
        anchos.append(ancho - sum(anchos))
        tabla = Table(filas, repeatRows=1, colWidths=anchos)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#" + R_AZUL_OSCURO)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), HexColor("#" + R_FONDO)]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, HexColor("#" + R_LINEA)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        historia.append(tabla)
        personas = sum(r["personas"] for r in reservas if _clave_estado(r["estado"]) == "Aceptada")
        historia += [Spacer(1, 0.3 * cm),
                     Paragraph(f"Total: {_plural(len(reservas), 'reserva')}   |   Personas en reservas aceptadas: {personas}",
                               estilos["total"])]
    doc.build(historia, canvasmaker=_lienzo_numerado(titulo))


# ----------------------------------------------------------------------- Excel
def _xl_banner(ws, titulo, ultima_col, info):
    """Banner azul con el nombre de la empresa y el título; luego las líneas de información."""
    from openpyxl.styles import Alignment, Font, PatternFill
    ws.sheet_view.showGridLines = False
    azul = PatternFill("solid", fgColor=R_AZUL_OSCURO)
    for fila in (1, 2):
        for c in range(1, ultima_col + 1):
            ws.cell(row=fila, column=c).fill = azul
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ultima_col)
    for c in range(1, ultima_col + 1):
        ws.cell(row=3, column=c).fill = PatternFill("solid", fgColor=R_AZUL)
    ws["A1"] = EMPRESA.upper()
    ws["A1"].font = Font(bold=True, size=10, color="9FB4D9")
    ws["A1"].alignment = Alignment(vertical="bottom", indent=1)
    ws["A2"] = titulo
    ws["A2"].font = Font(bold=True, size=20, color="FFFFFF")
    ws["A2"].alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = 24
    ws.row_dimensions[2].height = 36
    ws.row_dimensions[3].height = 5
    for i, texto in enumerate(info, start=4):
        celda = ws.cell(row=i, column=1, value=texto)
        celda.font = Font(italic=True, size=10, color=R_TEXTO)
        celda.alignment = Alignment(indent=1)


def _xl_encabezado(celdas):
    from openpyxl.styles import Alignment, Font, PatternFill
    for c in celdas:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=R_AZUL_OSCURO)
        c.alignment = Alignment(horizontal="center", vertical="center")


def _xl_impresion(ws, repetir_filas=None):
    from openpyxl.worksheet.properties import PageSetupProperties
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.4
    ws.oddFooter.left.text = "Confidencial"
    ws.oddFooter.center.text = EMPRESA
    ws.oddFooter.right.text = "Página &P de &N"
    if repetir_filas:
        ws.print_title_rows = repetir_filas


def _xl_grafico(datos, col, n, titulo, colores=None):
    """Gráfica de barras (o de pastel si se dan colores) sobre una tabla de la hoja Datos."""
    from openpyxl.chart import BarChart, PieChart, Reference
    from openpyxl.chart.label import DataLabelList
    from openpyxl.chart.series import DataPoint
    pastel = colores is not None
    g = PieChart() if pastel else BarChart()
    g.title = titulo
    g.add_data(Reference(datos, min_col=col + 1, min_row=3, max_row=3 + n), titles_from_data=True)
    g.set_categories(Reference(datos, min_col=col, min_row=4, max_row=3 + n))
    g.dataLabels = DataLabelList()
    g.dataLabels.showVal = True
    for atributo in ("showSerName", "showCatName", "showLegendKey", "showPercent"):
        setattr(g.dataLabels, atributo, False)
    serie = g.series[0]
    if pastel:
        for i, color in enumerate(colores):
            punto = DataPoint(idx=i)
            punto.graphicalProperties.solidFill = color
            serie.dPt.append(punto)
        g.legend.position = "r"
    else:
        serie.graphicalProperties.solidFill = R_AZUL
        serie.graphicalProperties.line.solidFill = R_AZUL
        g.legend = None
        g.gapWidth = 60
        g.x_axis.delete = False
        g.y_axis.delete = False
        g.y_axis.numFmt = "0"
    g.width, g.height = 14.2, 7.6
    return g


def generar_excel_estadisticas(ruta, d, desde, hasta, estado):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.worksheet.pagebreak import Break

    wb = Workbook()
    wb.properties.title = "Reporte de estadísticas"
    wb.properties.creator = EMPRESA
    ws = wb.active
    ws.title = "Resumen"
    columnas = 12
    for c in range(1, columnas + 1):
        ws.column_dimensions[ws.cell(row=1, column=c).column_letter].width = 13
    _xl_banner(ws, "Reporte de estadísticas", columnas, [
        f"Período: {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}   |   Estado: {estado or 'Todos'}",
        f"Generado el {datetime.now():%d/%m/%Y %H:%M}"])

    # Tarjetas de indicadores (3 columnas cada una, con "hueco" blanco entre ellas)
    k = _kpis(d)
    tarjetas = [("Reservas", k["total"], R_AZUL), ("Pendientes", k["pendientes"], R_AMBAR),
                ("% de aceptación", k["aceptacion"], R_VERDE), ("Personas por reserva", k["personas"], R_AZUL_OSCURO)]
    blanco = Side(style="thick", color="FFFFFF")
    ws.row_dimensions[7].height = 22
    ws.row_dimensions[8].height = 44
    for i, (etiqueta, valor, color) in enumerate(tarjetas):
        c1 = i * 3 + 1
        for fila in (7, 8):
            ws.merge_cells(start_row=fila, start_column=c1, end_row=fila, end_column=c1 + 2)
            for c in range(c1, c1 + 3):
                celda = ws.cell(row=fila, column=c)
                celda.fill = PatternFill("solid", fgColor=R_FONDO)
                celda.border = Border(top=Side(style="thick", color=color) if fila == 7 else None,
                                      left=blanco if c == c1 else None, right=blanco if c == c1 + 2 else None)
        ws.cell(row=7, column=c1, value=etiqueta).font = Font(size=10, color=R_TEXTO)
        ws.cell(row=7, column=c1).alignment = Alignment(horizontal="center", vertical="bottom")
        ws.cell(row=8, column=c1, value=valor).font = Font(size=26, bold=True, color=color)
        ws.cell(row=8, column=c1).alignment = Alignment(horizontal="center", vertical="center")

    def encabezado_seccion(fila, texto):
        ws.cell(row=fila, column=1, value=texto).font = Font(bold=True, size=13, color=R_AZUL_OSCURO)
        for c in range(1, columnas + 1):
            ws.cell(row=fila, column=c).border = Border(bottom=Side(style="medium", color=R_AZUL))
        ws.row_dimensions[fila].height = 22

    encabezado_seccion(10, "Resumen ejecutivo")
    fila = 11
    for frase in _resumen_ejecutivo(d):
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=columnas)
        ws.cell(row=fila, column=1, value="•  " + frase).alignment = Alignment(indent=1, vertical="center", wrap_text=True)
        ws.cell(row=fila, column=1).font = Font(size=11, color="2B3348")
        ws.row_dimensions[fila].height = 21
        fila += 1

    # Hoja de datos (de aquí salen las gráficas)
    datos = wb.create_sheet("Datos")
    datos.sheet_view.showGridLines = False
    datos["A1"] = "Datos de las gráficas"
    datos["A1"].font = Font(bold=True, size=14, color=R_AZUL_OSCURO)
    estados_con_datos = [(e, n) for e, n in d["por_estado"].items() if n]
    tablas = [
        (1, "Estado", estados_con_datos),
        (4, "Día", list(zip(DIAS_LARGO, d["por_dia"]))),
        (7, "Hora", [(_hora_texto(h), n) for h, n in sorted(d["por_hora"].items())]),
        (10, "Mesa", [(f"Mesa {m}", n) for m, n in sorted(d["mesas"].items())]),
    ]
    linea = Side(style="thin", color=R_LINEA)
    for col, etiqueta, filas in tablas:
        datos.cell(row=3, column=col, value=etiqueta)
        datos.cell(row=3, column=col + 1, value="Reservas")
        _xl_encabezado([datos.cell(row=3, column=col), datos.cell(row=3, column=col + 1)])
        datos.column_dimensions[datos.cell(row=3, column=col).column_letter].width = 16
        datos.column_dimensions[datos.cell(row=3, column=col + 1).column_letter].width = 11
        for i, (nombre, n) in enumerate(filas):
            for j, v in enumerate((nombre, n)):
                celda = datos.cell(row=4 + i, column=col + j, value=v)
                celda.border = Border(bottom=linea)
                celda.alignment = Alignment(horizontal="left" if j == 0 else "center")
                if i % 2:
                    celda.fill = PatternFill("solid", fgColor=R_FONDO)
    for letra in ("C", "F", "I"):
        datos.column_dimensions[letra].width = 4

    # Gráficas en 2 x 2 bajo el resumen
    fila += 1
    ws.row_breaks.append(Break(id=fila - 1))  # al imprimir, las gráficas empiezan en hoja nueva
    encabezado_seccion(fila, "Análisis gráfico")
    inicio = fila + 1
    vivos = {"Aceptada": R_VERDE, "Pendiente": R_AMBAR, "Rechazada": R_ROJO}
    colores_pastel = [vivos[_clave_estado(e)] for e, _ in estados_con_datos]
    pedidos = [
        (tablas[0], "Reservas por estado", colores_pastel, "A", 0),
        (tablas[1], "Reservas por día de la semana", None, "G", 0),
        (tablas[2], "Horas más pedidas", None, "A", 1),
        (tablas[3], "Mesas más usadas", None, "G", 1),
    ]
    for (col, _, filas), titulo, colores, ancla, bloque in pedidos:
        if any(n for _, n in filas):
            ws.add_chart(_xl_grafico(datos, col, len(filas), titulo, colores), f"{ancla}{inicio + bloque * 17}")

    _xl_impresion(ws)
    _xl_impresion(datos)
    wb.save(ruta)


def generar_excel_listado(ruta, reservas, desde, hasta, estado):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    wb = Workbook()
    wb.properties.title = "Listado de reservas"
    wb.properties.creator = EMPRESA
    ws = wb.active
    ws.title = "Reservas"
    columnas = ["Nombre", "Correo", "Teléfono", "Fecha", "Inicio", "Fin", "Mesas", "Personas", "Estado"]
    for letra, ancho in zip("ABCDEFGHI", (26, 32, 14, 13, 10, 10, 14, 10, 32)):
        ws.column_dimensions[letra].width = ancho

    cuenta = _contar_estados(reservas)
    _xl_banner(ws, "Listado de reservas", len(columnas), [
        f"Período: {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}   |   Estado: {estado or 'Todos'}",
        f"Generado el {datetime.now():%d/%m/%Y %H:%M}   |   Total: {len(reservas)}   |   Aceptadas: {cuenta['Aceptada']}"
        f"   |   Pendientes: {cuenta['Pendiente']}   |   Rechazadas: {cuenta['Rechazada']}"])

    fila_enc = 7
    for c, nombre in enumerate(columnas, start=1):
        ws.cell(row=fila_enc, column=c, value=nombre)
    _xl_encabezado(ws[fila_enc])
    ws.row_dimensions[fila_enc].height = 24

    linea = Side(style="thin", color=R_LINEA)
    for i, r in enumerate(reservas):
        fila = fila_enc + 1 + i
        valores = [r["nombre"], _correo_visible(r["correo"]), r.get("telefono") or "-", r["fecha"],
                   r["inicio_str"], r["fin_str"], ", ".join(map(str, r["mesas"])), r["personas"], r["estado"]]
        for c, v in enumerate(valores, start=1):
            celda = ws.cell(row=fila, column=c, value=v)
            celda.border = Border(bottom=linea)
            celda.alignment = Alignment(horizontal="center" if c in (4, 5, 6, 7, 8) else "left", vertical="center")
            if i % 2:
                celda.fill = PatternFill("solid", fgColor=R_FONDO)
        ws.cell(row=fila, column=4).number_format = "DD/MM/YYYY"
        relleno, texto = R_ESTADO[_clave_estado(r["estado"])]
        estado_celda = ws.cell(row=fila, column=9)
        estado_celda.fill = PatternFill("solid", fgColor=relleno)
        estado_celda.font = Font(bold=True, color=texto)

    if reservas:
        ultima = fila_enc + len(reservas)
        ws.auto_filter.ref = f"A{fila_enc}:I{ultima}"
        fila_total = ultima + 2
        ws.cell(row=fila_total, column=1, value=f"Total: {_plural(len(reservas), 'reserva')}").font = Font(bold=True, color=R_AZUL_OSCURO)
        personas = sum(r["personas"] for r in reservas if _clave_estado(r["estado"]) == "Aceptada")
        ws.cell(row=fila_total, column=2, value=f"Personas en reservas aceptadas: {personas}").font = Font(bold=True, color=R_AZUL_OSCURO)
        for c in range(1, len(columnas) + 1):
            ws.cell(row=fila_total, column=c).border = Border(top=Side(style="medium", color=R_AZUL_OSCURO))
    ws.freeze_panes = f"A{fila_enc + 1}"
    _xl_impresion(ws, f"{fila_enc}:{fila_enc}")
    wb.save(ruta)


class PanelAdmin(QWidget):
    """Panel de administración: sidebar a la izquierda y, a la derecha, un QStackedWidget
    (Estadísticas y Reportes). `app` es la ventana principal; el panel usa sus métodos
    mostrar_* para las secciones que todavía son pantallas completas."""

    TIPOS = {
        "Estadísticas": "Resumen del período: tarjetas (total, pendientes, % de aceptación, personas "
                        "por reserva) y las 4 gráficas.",
        "Listado de reservas": "Tabla con todas las reservas del período, una por fila: nombre, correo, "
                               "teléfono, fecha, hora, mesas, personas y estado.",
    }

    def __init__(self, app, oscuro=True):
        super().__init__()
        self.app = app
        self.oscuro = oscuro
        self.setStyleSheet(QSS_OSCURO if oscuro else QSS_CLARO)

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(self._crear_sidebar())

        self.paginas = QStackedWidget()
        self.paginas.addWidget(self._crear_dashboard())
        self.paginas.addWidget(self._crear_reportes())
        raiz.addWidget(self.paginas, 1)

        self.refrescar()

    # ------------------------------------------------------------------ sidebar
    def _nav(self, texto, comando=None, activo=False):
        btn = QPushButton(texto)
        btn.setObjectName("navBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("activo", "true" if activo else "false")
        if comando:
            btn.clicked.connect(comando)
        return btn

    def _crear_sidebar(self):
        barra = QFrame()
        barra.setObjectName("sidebar")
        barra.setFixedWidth(230)
        col = QVBoxLayout(barra)
        col.setContentsMargins(0, 14, 0, 14)
        col.setSpacing(2)

        titulo = QLabel("Administración")
        titulo.setObjectName("sideTitulo")
        titulo.setContentsMargins(14, 0, 0, 0)
        col.addWidget(titulo)

        self.btn_stats = self._nav("Estadísticas", lambda: self._ir_a(0), activo=True)
        col.addWidget(self.btn_stats)
        col.addWidget(self._nav("Reservas", self.app.mostrar_consulta_admin))
        self.btn_pendientes = self._nav("Pendientes", self.app.mostrar_gestion_reservas_admin)
        col.addWidget(self.btn_pendientes)
        self.btn_reportes = self._nav("Reportes", lambda: self._ir_a(1))
        col.addWidget(self.btn_reportes)

        # Vendedores: un solo botón con submenú (luego pasará a una sección con pestañas)
        btn_vend = self._nav("Vendedores  ▾")
        menu = QMenu(btn_vend)
        menu.addAction("Crear vendedor", self.app.mostrar_crear_vendedor)
        menu.addAction("Eliminar vendedor", self.app.mostrar_eliminar_vendedor)
        menu.addAction("Actualizar vendedor", self.app.mostrar_actualizar_vendedor)
        btn_vend.clicked.connect(lambda: menu.exec(btn_vend.mapToGlobal(btn_vend.rect().bottomLeft())))
        col.addWidget(btn_vend)

        col.addStretch()
        col.addWidget(self._nav("Cerrar sesión", self.app.mostrar_menu_principal))
        return barra

    def _ir_a(self, indice):
        """Cambia de página en el panel derecho y marca el botón activo del menú."""
        self.paginas.setCurrentIndex(indice)
        for i, btn in enumerate((self.btn_stats, self.btn_reportes)):
            btn.setProperty("activo", "true" if i == indice else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ---------------------------------------------------------------- dashboard
    def _crear_dashboard(self):
        contenido = QWidget()
        col = QVBoxLayout(contenido)
        col.setContentsMargins(20, 18, 20, 18)
        col.setSpacing(14)

        encabezado = QLabel("Estadísticas")
        encabezado.setObjectName("lblHeader")
        col.addWidget(encabezado)

        self.filtros = BarraFiltros("Aplicar", self.refrescar)
        col.addWidget(self.filtros)

        # ---- Tarjetas KPI
        kpis = QHBoxLayout()
        kpis.setSpacing(12)
        self.kpi = {}
        for clave, titulo in (("total", "Reservas"), ("pendientes", "Pendientes"),
                              ("aceptacion", "% de aceptación"), ("personas", "Personas por reserva")):
            tarjeta = QFrame()
            tarjeta.setObjectName("card")
            lay = QVBoxLayout(tarjeta)
            valor = QLabel("-")
            valor.setObjectName("kpiValor")
            lbl = QLabel(titulo)
            lbl.setObjectName("kpiTitulo")
            lay.addWidget(valor)
            lay.addWidget(lbl)
            kpis.addWidget(tarjeta, 1)
            self.kpi[clave] = valor
        col.addLayout(kpis)

        # ---- Gráficas (2 x 2)
        grid = QGridLayout()
        grid.setSpacing(12)
        self.vistas = {}
        for i, clave in enumerate(("estado", "dia", "hora", "mesa")):
            vista = QChartView()
            vista.setRenderHint(QPainter.RenderHint.Antialiasing)
            vista.setMinimumHeight(290)
            grid.addWidget(vista, i // 2, i % 2)
            self.vistas[clave] = vista
        col.addLayout(grid)
        col.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(contenido)
        return scroll

    # ------------------------------------------------------------------- datos
    def _graficas(self, d, oscuro=None):
        """Las 4 gráficas (en este orden: estado, día, hora, mesa) a partir de db.estadisticas()."""
        horas, mesas = d["por_hora"], d["mesas"]
        h, m = sorted(horas), sorted(mesas)
        return {
            "estado": self._pastel("Reservas por estado", d["por_estado"], oscuro),
            "dia": self._barras("Reservas por día de la semana", DIAS_CORTO, d["por_dia"], oscuro),
            "hora": self._barras("Horas más pedidas", [_hora_texto(x) for x in h], [horas[x] for x in h], oscuro),
            "mesa": self._barras("Mesas más usadas", [f"M{x}" for x in m], [mesas[x] for x in m], oscuro),
        }

    def refrescar(self):
        valores = self.filtros.valores()
        if valores is None:
            return
        try:
            d = db.estadisticas(*valores)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las estadísticas.\n\n{e}")
            return

        pend = d["pendientes_global"]
        self.btn_pendientes.setText(f"Pendientes  ({pend})" if pend else "Pendientes")

        for clave, texto in _kpis(d).items():
            self.kpi[clave].setText(texto)
        for clave, chart in self._graficas(d).items():
            self.vistas[clave].setChart(chart)

    # ---------------------------------------------------------------- reportes
    def _crear_reportes(self):
        pagina = QWidget()
        col = QVBoxLayout(pagina)
        col.setContentsMargins(20, 18, 20, 18)
        col.setSpacing(14)

        encabezado = QLabel("Reportes")
        encabezado.setObjectName("lblHeader")
        col.addWidget(encabezado)

        self.filtros_rep = BarraFiltros()
        col.addWidget(self.filtros_rep)

        tarjeta = QFrame()
        tarjeta.setObjectName("card")
        tarjeta.setMaximumWidth(780)
        lay = QVBoxLayout(tarjeta)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)

        fila_tipo = QHBoxLayout()
        fila_tipo.addWidget(QLabel("Tipo de reporte:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(list(self.TIPOS))
        fila_tipo.addWidget(self.combo_tipo)
        fila_tipo.addStretch()
        lay.addLayout(fila_tipo)

        self.lbl_desc = QLabel(self.TIPOS["Estadísticas"])
        self.lbl_desc.setObjectName("kpiTitulo")
        self.lbl_desc.setWordWrap(True)
        self.combo_tipo.currentTextChanged.connect(lambda t: self.lbl_desc.setText(self.TIPOS[t]))
        lay.addWidget(self.lbl_desc)

        botones = QHBoxLayout()
        btn_pdf = QPushButton("Exportar PDF")
        btn_pdf.setObjectName("btnDanger")
        btn_pdf.clicked.connect(lambda: self._exportar("pdf"))
        btn_xlsx = QPushButton("Exportar Excel")
        btn_xlsx.setObjectName("btnSuccess")
        btn_xlsx.clicked.connect(lambda: self._exportar("xlsx"))
        botones.addWidget(btn_pdf)
        botones.addWidget(btn_xlsx)
        botones.addStretch()
        lay.addLayout(botones)

        col.addWidget(tarjeta)
        col.addStretch()
        return pagina

    def _exportar(self, formato):
        valores = self.filtros_rep.valores()
        if valores is None:
            return
        desde, hasta, estado = valores
        tipo = self.combo_tipo.currentText()
        es_stats = tipo == "Estadísticas"

        sugerido = f"reporte_{'estadisticas' if es_stats else 'reservas'}_{date.today():%Y-%m-%d}.{formato}"
        filtro = "PDF (*.pdf)" if formato == "pdf" else "Excel (*.xlsx)"
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar reporte", sugerido, filtro)
        if not ruta:
            return
        if not ruta.lower().endswith("." + formato):
            ruta += "." + formato

        try:
            if es_stats:
                datos = db.estadisticas(desde, hasta, estado)
                if formato == "pdf":
                    pngs = [self._grafico_png(g) for g in self._graficas(datos, oscuro=False).values()]
                    generar_pdf_estadisticas(ruta, datos, desde, hasta, estado, pngs)
                else:
                    generar_excel_estadisticas(ruta, datos, desde, hasta, estado)
            else:
                datos = db.reservas_filtradas(desde, hasta, estado)
                (generar_pdf_listado if formato == "pdf" else generar_excel_listado)(ruta, datos, desde, hasta, estado)
        except ImportError as e:
            QMessageBox.warning(self, "Falta una librería",
                                f"Para este reporte hay que instalar '{e.name}'.\n\nEjecuta:  pip install {e.name}")
        except PermissionError:
            QMessageBox.critical(self, "Error", "No se pudo guardar el archivo. ¿Está abierto en otro programa?")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el reporte.\n\n{e}")
        else:
            QMessageBox.information(self, "Reporte generado", f"Reporte guardado en:\n{ruta}")

    # ---- PDF
    def _grafico_png(self, chart):
        vista = QChartView(chart)
        vista.setRenderHint(QPainter.RenderHint.Antialiasing)
        vista.setStyleSheet("QChartView { background: #ffffff; border: none; }")
        vista.resize(540, 340)
        pix = QPixmap(1080, 680)  # doble resolución para que se vea nítido al imprimir
        pix.setDevicePixelRatio(2)
        pix.fill(QColor("#ffffff"))
        QWidget.render(vista, pix)  # (QGraphicsView.render pide un QPainter)
        datos = QByteArray()
        buf = QBuffer(datos)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        pix.save(buf, "PNG")
        buf.close()
        return bytes(datos)

    # ----------------------------------------------------------------- gráficas
    def _base(self, titulo, oscuro=None):
        oscuro = self.oscuro if oscuro is None else oscuro
        chart = QChart()
        chart.setTheme(QChart.ChartTheme.ChartThemeDark if oscuro else QChart.ChartTheme.ChartThemeLight)
        chart.setBackgroundBrush(QBrush(QColor("#16213e" if oscuro else "#f5f7fb")))
        chart.setBackgroundRoundness(8)
        chart.setTitle(titulo)
        chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)
        return chart

    def _pastel(self, titulo, por_estado, oscuro=None):
        chart = self._base(titulo, oscuro)
        if not sum(por_estado.values()):
            chart.setTitle(f"{titulo} — sin datos")
            return chart
        serie = QPieSeries()
        for nombre, n in por_estado.items():
            if n:
                rebanada = serie.append(f"{nombre}: {n}", n)
                rebanada.setColor(QColor(COLORES_ESTADO[nombre]))
                rebanada.setLabelVisible(True)
        chart.addSeries(serie)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        return chart

    def _barras(self, titulo, categorias, valores, oscuro=None):
        oscuro = self.oscuro if oscuro is None else oscuro
        chart = self._base(titulo, oscuro)
        if not any(valores):
            chart.setTitle(f"{titulo} — sin datos")
            chart.legend().hide()
            return chart
        conjunto = QBarSet("Reservas")
        conjunto.append([float(v) for v in valores])
        conjunto.setColor(QColor("#00d4ff" if oscuro else "#0d6efd"))
        serie = QBarSeries()
        serie.append(conjunto)
        serie.setLabelsVisible(True)
        chart.addSeries(serie)
        chart.legend().hide()

        eje_x = QBarCategoryAxis()
        eje_x.append(categorias)
        chart.addAxis(eje_x, Qt.AlignmentFlag.AlignBottom)
        serie.attachAxis(eje_x)

        tope = int(max(valores))
        eje_y = QValueAxis()
        eje_y.setLabelFormat("%d")
        eje_y.setMinorTickCount(0)
        chart.addAxis(eje_y, Qt.AlignmentFlag.AlignLeft)
        serie.attachAxis(eje_y)
        if tope < 8:  # pocos datos: una marca por cada número entero
            eje_y.setRange(0, tope + 1)
            eje_y.setTickCount(tope + 2)
        else:
            eje_y.setRange(0, tope)
            eje_y.applyNiceNumbers()
        return chart


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

    @staticmethod
    def _solo_letras(entry, max_len=50):
        """Bloquea números y símbolos al teclear/pegar (letras con tilde, ñ y espacios sí)."""
        entry.setValidator(QRegularExpressionValidator(QRegularExpression(r"[\p{L} ]*")))
        entry.setMaxLength(max_len)
        return entry

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
        col.addWidget(self._boton(" Registrar Reserva", self.mostrar_menu_cliente, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Consultar reservas", self.mostrar_reservas_pendientes_publico, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(self._boton(" Gestión del Asistente", self.mostrar_login_vendedor, min_width=220), alignment=Qt.AlignmentFlag.AlignHCenter)
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
        self.entry_nombre = self._solo_letras(QLineEdit(), 100)
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
        self.main_layout.addWidget(self._label("Gestión del Asistente", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
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
        """Panel de administración: menú lateral + dashboard con filtros y gráficas."""
        self.limpiar_frame()
        self.main_layout.addWidget(PanelAdmin(self, self.es_tema_oscuro), 1)

    def mostrar_consulta_admin(self):
        self._mostrar_lista_pendientes(self.mostrar_menu_admin, completo=True)

    def mostrar_crear_vendedor(self):
        self.limpiar_frame()

        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self._label("Crear Vendedor", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QFormLayout()
        self.entry_new_vend_nombre = self._solo_letras(QLineEdit())
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
        if not self.validar_nombre(nombre):
            QMessageBox.critical(self, "Error", "Nombre inválido. Solo letras y mínimo 2 caracteres.")
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
        self.main_layout.addWidget(self._label("Actualizar Vendedor", "lblHeader", Qt.AlignmentFlag.AlignHCenter))
        self.main_layout.addSpacing(10)

        form = QFormLayout()
        self.combo_upd_vend = QComboBox()
        self.combo_upd_vend.addItems(list(db.obtener_vendedores().keys()))
        self.entry_upd_vend_nombre = self._solo_letras(QLineEdit())
        self.entry_upd_vend_pass = QLineEdit()
        self.entry_upd_vend_pass.setPlaceholderText("Dejar vacío para no cambiarla")
        self.entry_upd_vend_nombre.returnPressed.connect(self.actualizar_vendedor)
        self.entry_upd_vend_pass.returnPressed.connect(self.actualizar_vendedor)
        # Al elegir un vendedor, su nombre actual aparece listo para editar
        self.combo_upd_vend.currentTextChanged.connect(self.entry_upd_vend_nombre.setText)
        self.entry_upd_vend_nombre.setText(self.combo_upd_vend.currentText())
        form.addRow("Seleccione vendedor:", self.combo_upd_vend)
        form.addRow("Nombre:", self.entry_upd_vend_nombre)
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
        actual = self.combo_upd_vend.currentText()
        nuevo_nombre = self.entry_upd_vend_nombre.text().strip()
        contrasena = self.entry_upd_vend_pass.text().strip()

        if not actual:
            QMessageBox.critical(self, "Error", "Seleccione un vendedor.")
            return
        if not self.validar_nombre(nuevo_nombre):
            QMessageBox.critical(self, "Error", "Nombre inválido. Solo letras y mínimo 2 caracteres.")
            return

        cambia_nombre = nuevo_nombre != actual
        if not cambia_nombre and not contrasena:
            QMessageBox.information(self, "Sin cambios", "Cambie el nombre o escriba una nueva contraseña.")
            return

        if cambia_nombre and any(nuevo_nombre.lower() == v.lower() and v != actual
                                 for v in db.obtener_vendedores()):
            QMessageBox.critical(self, "Error", f"Ya existe un vendedor con el nombre '{nuevo_nombre}'.")
            return

        db.actualizar_vendedor(actual, nuevo_nombre if cambia_nombre else None, contrasena or None)
        QMessageBox.information(self, "Éxito", "Vendedor actualizado correctamente.")
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