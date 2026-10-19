from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from nucleo.caja_repository import CajaRepository
from nucleo.cobro_repository import CobroRepository
from nucleo.mensajes import Mensajes
from nucleo.sesion import obtener_usuario


def _formatear_monto(monto):
    return f"{monto:.2f}"


class VentanaCobro(QDialog):
    """Registro y consulta de los cobros de un pedido confirmado."""

    def __init__(self, pedido, padre=None):
        super().__init__(padre)
        self.pedido = pedido
        self.repository = CobroRepository()
        self.caja_repository = CajaRepository()
        self.saldo = None
        self.sesion_caja = None
        self.setWindowTitle(f"Cobros del pedido {pedido['codigo']}")
        self.resize(850, 560)
        self._crear_interfaz()
        self._recargar()

    def _crear_interfaz(self):
        formulario_pedido = QFormLayout()
        self.lbl_cliente = QLabel(str(self.pedido.get("cliente") or ""))
        self.lbl_total = QLabel("-")
        self.lbl_cobrado = QLabel("-")
        self.lbl_saldo = QLabel("-")
        formulario_pedido.addRow("Cliente:", self.lbl_cliente)
        formulario_pedido.addRow("Total:", self.lbl_total)
        formulario_pedido.addRow("Cobrado:", self.lbl_cobrado)
        formulario_pedido.addRow("Saldo pendiente:", self.lbl_saldo)

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(
            ["N.º", "Fecha", "Medio de pago", "Monto", "Usuario", "Estado", "Referencia"]
        )
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.itemSelectionChanged.connect(self._actualizar_acciones)

        self.combo_medio = QComboBox()
        self.txt_monto = QLineEdit()
        self.txt_monto.setPlaceholderText("0.00")
        self.txt_referencia = QLineEdit()
        self.txt_referencia.setPlaceholderText("Opcional")
        formulario_cobro = QFormLayout()
        formulario_cobro.addRow("Medio de pago:", self.combo_medio)
        formulario_cobro.addRow("Monto:", self.txt_monto)
        formulario_cobro.addRow("Referencia:", self.txt_referencia)

        self.btn_cobrar = QPushButton("Cobrar")
        self.btn_anular = QPushButton("Anular cobro")
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cobrar.clicked.connect(self._cobrar)
        self.btn_anular.clicked.connect(self._anular)
        self.btn_cerrar.clicked.connect(self.close)
        barra = QHBoxLayout()
        barra.addWidget(self.btn_cobrar)
        barra.addWidget(self.btn_anular)
        barra.addStretch()
        barra.addWidget(self.btn_cerrar)

        layout = QVBoxLayout(self)
        layout.addLayout(formulario_pedido)
        layout.addWidget(self.tabla, 1)
        layout.addLayout(formulario_cobro)
        layout.addLayout(barra)

    def _recargar(self):
        try:
            self.saldo = self.repository.saldo_pedido(self.pedido["codigo"])
            cobros = self.repository.listar_cobros_pedido(self.pedido["codigo"])
            medios = self.repository.listar_medios_pago()
            self.sesion_caja = self.caja_repository.obtener_sesion_abierta()
        except Exception as error:
            Mensajes.error(self, error)
            self.btn_cobrar.setEnabled(False)
            self.btn_anular.setEnabled(False)
            return

        self.lbl_total.setText(_formatear_monto(self.saldo["total"]))
        self.lbl_cobrado.setText(_formatear_monto(self.saldo["cobrado"]))
        self.lbl_saldo.setText(_formatear_monto(self.saldo["saldo"]))
        self._cargar_medios(medios)
        self._cargar_cobros(cobros)
        self.txt_monto.setText(_formatear_monto(self.saldo["saldo"]))
        self.btn_cobrar.setEnabled(
            self.sesion_caja is not None and self.saldo["saldo"] > 0 and bool(medios)
        )
        if self.sesion_caja is None:
            Mensajes.advertencia(self, "Cobros", "Abrí la caja para cobrar")
        self._actualizar_acciones()

    def _cargar_medios(self, medios):
        medio_actual = self.combo_medio.currentData()
        self.combo_medio.clear()
        for medio in medios:
            self.combo_medio.addItem(medio["descripcion"], medio["codigo"])
        indice = self.combo_medio.findData(medio_actual)
        if indice >= 0:
            self.combo_medio.setCurrentIndex(indice)

    def _cargar_cobros(self, cobros):
        self.tabla.setRowCount(len(cobros))
        for fila, cobro in enumerate(cobros):
            valores = (
                cobro["codigo"],
                cobro["fecha"],
                cobro["medio_pago"] or "",
                _formatear_monto(Decimal(str(cobro["monto"]))),
                cobro["usuario"] or "",
                "Anulado" if cobro["anulado"] else "Vigente",
                cobro["referencia"] or "",
            )
            for columna, valor in enumerate(valores):
                celda = QTableWidgetItem(str(valor))
                if columna == 0:
                    celda.setData(Qt.UserRole, cobro["codigo"])
                if columna == 3:
                    celda.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if columna == 5 and cobro["anulado"] and cobro["observacion"]:
                    celda.setToolTip(cobro["observacion"])
                self.tabla.setItem(fila, columna, celda)

    def _cobro_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            return None
        item = self.tabla.item(fila, 0)
        return item.data(Qt.UserRole) if item is not None else None

    def _actualizar_acciones(self):
        fila = self.tabla.currentRow()
        seleccionado_anulable = False
        if fila >= 0:
            estado = self.tabla.item(fila, 5)
            seleccionado_anulable = estado is not None and estado.text() == "Vigente"
        self.btn_anular.setEnabled(
            self.sesion_caja is not None and seleccionado_anulable
        )

    def _usuario_id(self):
        usuario = obtener_usuario()
        if usuario is None or usuario.get("idusuario") is None:
            raise ValueError("No se pudo identificar al usuario de la sesión.")
        return usuario["idusuario"]

    def _cobrar(self):
        try:
            monto = Decimal(self.txt_monto.text().strip().replace(",", "."))
            if not monto.is_finite() or monto <= 0:
                raise ValueError("El monto del cobro debe ser mayor a 0.")
            codigo_medio = self.combo_medio.currentData()
            if codigo_medio is None:
                raise ValueError("No hay medios de pago activos.")
            self.repository.registrar_cobro(
                self.pedido["codigo"],
                codigo_medio,
                monto,
                self.txt_referencia.text().strip() or None,
                self._usuario_id(),
            )
        except (InvalidOperation, ValueError) as error:
            Mensajes.advertencia(self, "Cobro", str(error))
            return
        except Exception as error:
            Mensajes.error(self, error)
            return

        Mensajes.informacion(self, "Cobro", "El cobro se registró correctamente.")
        self._recargar()

    def _anular(self):
        codigo_cobro = self._cobro_seleccionado()
        if codigo_cobro is None:
            Mensajes.advertencia(self, "Cobros", "Seleccione un cobro de la lista.")
            return
        motivo, aceptado = QInputDialog.getText(
            self, "Anular cobro", "Motivo de la anulación:"
        )
        if not aceptado:
            return
        if not motivo.strip():
            Mensajes.advertencia(
                self, "Anular cobro", "El motivo de anulación es obligatorio."
            )
            return
        if not Mensajes.confirmar(
            self,
            "Confirmar anulación",
            f"¿Anular el cobro {codigo_cobro}?",
        ):
            return

        try:
            self.repository.anular_cobro(
                codigo_cobro, self._usuario_id(), motivo.strip()
            )
        except Exception as error:
            Mensajes.error(self, error)
            return
        Mensajes.informacion(self, "Cobro", "El cobro se anuló correctamente.")
        self._recargar()
