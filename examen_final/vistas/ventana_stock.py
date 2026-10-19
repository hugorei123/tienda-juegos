from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nucleo.mensajes import Mensajes
from nucleo.stock_repository import StockRepository
from nucleo.tema import COLOR_TEXTO


class VentanaStock(QMainWindow):
    """Consulta de existencias y acceso al historial de movimientos."""

    def __init__(self, padre=None):
        super().__init__(padre)
        self.repository = StockRepository()
        self.items = []
        self._filas_visibles = []
        self.setWindowTitle("Stock")
        self.resize(900, 540)
        self._crear_interfaz()
        self._recargar()

    def _crear_interfaz(self):
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por descripción...")
        self.txt_buscar.textChanged.connect(self._filtrar)

        self.btn_movimientos = QPushButton("Ver movimientos")
        self.btn_movimientos.clicked.connect(self._ver_movimientos)
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.clicked.connect(self.close)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(
            ["Código", "Descripción", "Categoría", "Stock actual", "Precio"]
        )
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.cellDoubleClicked.connect(lambda *_: self._ver_movimientos())

        barra = QHBoxLayout()
        barra.addWidget(self.btn_movimientos)
        barra.addStretch()
        barra.addWidget(self.btn_cerrar)

        layout = QVBoxLayout()
        layout.addWidget(self.txt_buscar)
        layout.addLayout(barra)
        layout.addWidget(self.tabla, 1)
        contenedor = QWidget()
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

        QShortcut(QKeySequence("F10"), self, self.close)

    def _recargar(self):
        try:
            self.items = self.repository.listar_items()
        except Exception as error:
            Mensajes.error(self, error)
            return
        self._filtrar()

    def _filtrar(self, *_):
        texto = self.txt_buscar.text().strip().casefold()
        filas = [
            item for item in self.items
            if not texto or texto in str(item["descripcion"] or "").casefold()
        ]
        self._filas_visibles = filas
        self.tabla.setRowCount(len(filas))
        for numero_fila, item in enumerate(filas):
            valores = (
                item["codigo"],
                item["descripcion"],
                item["categoria"],
                item["stock_actual"],
                item["precio"],
            )
            color = None
            if item["stock_actual"] <= 0:
                color = QColor("#F4CCCC")
            elif item["stock_actual"] <= 3:
                color = QColor("#FFF2CC")

            for columna, valor in enumerate(valores):
                texto_celda = (
                    f"{valor:.2f}"
                    if isinstance(valor, (Decimal, float))
                    else str(valor if valor is not None else "")
                )
                celda = QTableWidgetItem(texto_celda)
                if columna in (0, 3, 4):
                    celda.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if color is not None:
                    celda.setBackground(color)
                    celda.setForeground(QColor(COLOR_TEXTO))
                self.tabla.setItem(numero_fila, columna, celda)

    def _ver_movimientos(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            Mensajes.advertencia(self, "Stock", "Seleccione un ítem de la lista.")
            return

        item = self._filas_visibles[fila]
        try:
            movimientos = self.repository.listar_movimientos(item["codigo"])
            ventana = VentanaMovimientosStock(
                item["descripcion"], movimientos, self
            )
            ventana.exec()
        except Exception as error:
            Mensajes.error(self, error)


class VentanaMovimientosStock(QDialog):
    """Historial de movimientos de un ítem, en modo de solo lectura."""

    def __init__(self, descripcion, movimientos, padre=None):
        super().__init__(padre)
        self.setWindowTitle(f"Movimientos - {descripcion}")
        self.resize(900, 460)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            [
                "Fecha", "Tipo", "Cantidad", "Stock resultante",
                "Usuario", "Referencia",
            ]
        )
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setRowCount(len(movimientos))

        for numero_fila, movimiento in enumerate(movimientos):
            valores = (
                movimiento["fecha"],
                movimiento["tipo"],
                movimiento["cantidad"],
                movimiento["stock_resultante"],
                movimiento["usuario"],
                movimiento["referencia_codigo"],
            )
            for columna, valor in enumerate(valores):
                texto = str(valor if valor is not None else "")
                celda = QTableWidgetItem(texto)
                if columna in (2, 3, 5):
                    celda.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla.setItem(numero_fila, columna, celda)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        barra = QHBoxLayout()
        barra.addStretch()
        barra.addWidget(btn_cerrar)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabla, 1)
        layout.addLayout(barra)
        QShortcut(QKeySequence("Esc"), self, self.reject)
