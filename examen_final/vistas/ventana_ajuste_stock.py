from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from modulos.config_item import configuracion_items
from nucleo.mensajes import Mensajes
from nucleo.sesion import obtener_usuario
from nucleo.stock_repository import StockRepository
from vistas.ventana_seleccion import VentanaSeleccion


class VentanaAjusteStock(QMainWindow):
    """Registra entradas y salidas manuales de existencias."""

    def __init__(self, padre=None):
        super().__init__(padre)
        self.repository = StockRepository()
        self.item_seleccionado = None
        self.setWindowTitle("Ajuste de stock")
        self.resize(520, 280)
        self._crear_interfaz()

    def _crear_interfaz(self):
        self.lbl_item = QLabel("Ningún juego seleccionado")
        self.lbl_stock = QLabel("-")
        self.btn_seleccionar = QPushButton("Seleccionar juego")
        self.btn_seleccionar.clicked.connect(self._seleccionar_item)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Compra / entrada de mercadería", "COMPRA")
        self.combo_tipo.addItem("Ajuste de entrada", "AJUSTE_ENTRADA")
        self.combo_tipo.addItem("Ajuste de salida", "AJUSTE_SALIDA")

        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 1_000_000_000)

        self.txt_motivo = QLineEdit()
        self.txt_motivo.setPlaceholderText(
            "Obligatorio para ajustes; opcional para compras"
        )

        formulario = QFormLayout()
        formulario.addRow("Juego:", self.lbl_item)
        formulario.addRow("", self.btn_seleccionar)
        formulario.addRow("Stock actual:", self.lbl_stock)
        formulario.addRow("Tipo:", self.combo_tipo)
        formulario.addRow("Cantidad:", self.spn_cantidad)
        formulario.addRow("Motivo:", self.txt_motivo)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.clicked.connect(self.close)

        barra = QHBoxLayout()
        barra.addStretch()
        barra.addWidget(self.btn_guardar)
        barra.addWidget(self.btn_cerrar)

        layout = QVBoxLayout()
        layout.addLayout(formulario)
        layout.addStretch()
        layout.addLayout(barra)
        contenedor = QWidget()
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

        QShortcut(QKeySequence("Ctrl+G"), self, self._guardar)
        QShortcut(QKeySequence("F10"), self, self.close)

    def _seleccionar_item(self):
        self.ventana_seleccion = VentanaSeleccion(
            configuracion_items, self._establecer_item
        )
        self.ventana_seleccion.show()

    def _establecer_item(self, item):
        self.item_seleccionado = item
        self.lbl_item.setText(f"{item['codigo']} - {item['descripcion']}")
        self.lbl_stock.setText(str(item["stock_actual"]))

    def _guardar(self):
        if self.item_seleccionado is None:
            Mensajes.advertencia(self, "Ajuste de stock", "Seleccione un juego.")
            return

        tipo = self.combo_tipo.currentData()
        motivo = self.txt_motivo.text().strip()
        if tipo in ("AJUSTE_ENTRADA", "AJUSTE_SALIDA") and not motivo:
            Mensajes.advertencia(
                self, "Ajuste de stock", "Ingrese el motivo del ajuste."
            )
            self.txt_motivo.setFocus()
            return

        usuario = obtener_usuario()
        if usuario is None or usuario.get("idusuario") is None:
            Mensajes.advertencia(
                self,
                "Ajuste de stock",
                "No se pudo identificar al usuario de la sesión.",
            )
            return

        try:
            stock_resultante = self.repository.ajustar_stock(
                self.item_seleccionado["codigo"],
                self.spn_cantidad.value(),
                tipo,
                motivo,
                usuario["idusuario"],
            )
        except Exception as error:
            Mensajes.error(self, error)
            return

        self.lbl_stock.setText(str(stock_resultante))
        self.item_seleccionado["stock_actual"] = stock_resultante
        Mensajes.informacion(
            self,
            "Ajuste de stock",
            f"Movimiento registrado. Nuevo stock: {stock_resultante}.",
        )
