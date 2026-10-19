from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nucleo.caja_repository import CajaRepository
from nucleo.mensajes import Mensajes
from nucleo.sesion import obtener_usuario


def _formatear_monto(monto):
    return f"{monto:.2f}"


def _leer_monto(campo, etiqueta):
    try:
        monto = Decimal(campo.text().strip().replace(",", "."))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Ingrese un monto válido para {etiqueta}.") from error
    if not monto.is_finite() or monto < 0:
        raise ValueError(f"El monto de {etiqueta} debe ser mayor o igual a 0.")
    return monto


class VentanaCaja(QMainWindow):
    """Apertura, cierre y arqueo de sesiones de caja."""

    def __init__(self, padre=None):
        super().__init__(padre)
        self.repository = CajaRepository()
        self.sesion = None
        self.setWindowTitle("Caja")
        self.resize(900, 620)
        self._crear_interfaz()
        self._recargar()

    def _crear_interfaz(self):
        self.lbl_estado = QLabel("Cargando caja...")
        self.lbl_apertura_usuario = QLabel("-")
        self.lbl_apertura_fecha = QLabel("-")
        self.lbl_monto_apertura = QLabel("-")
        self.lbl_efectivo_esperado = QLabel("-")

        self.txt_monto_apertura = QLineEdit("0.00")
        self.txt_monto_apertura.setPlaceholderText("0.00")
        self.btn_abrir = QPushButton("Abrir caja")
        self.btn_abrir.clicked.connect(self._abrir_caja)

        self.txt_efectivo_contado = QLineEdit()
        self.txt_efectivo_contado.setPlaceholderText("0.00")
        self.txt_observacion = QLineEdit()
        self.txt_observacion.setPlaceholderText("Observación del cierre (opcional)")
        self.btn_cerrar_caja = QPushButton("Cerrar caja")
        self.btn_cerrar_caja.clicked.connect(self._cerrar_caja)

        self.tabla_medios = QTableWidget(0, 2)
        self.tabla_medios.setHorizontalHeaderLabels(["Medio de pago", "Total cobrado"])
        self.tabla_medios.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabla_medios.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_medios.setAlternatingRowColors(True)
        self.tabla_medios.verticalHeader().setVisible(False)
        self.tabla_medios.horizontalHeader().setStretchLastSection(True)

        formulario_apertura = QFormLayout()
        formulario_apertura.addRow("Monto de apertura:", self.txt_monto_apertura)

        formulario_cierre = QFormLayout()
        formulario_cierre.addRow("Abrió:", self.lbl_apertura_usuario)
        formulario_cierre.addRow("Fecha de apertura:", self.lbl_apertura_fecha)
        formulario_cierre.addRow("Monto de apertura:", self.lbl_monto_apertura)
        formulario_cierre.addRow("Efectivo esperado:", self.lbl_efectivo_esperado)
        formulario_cierre.addRow("Efectivo contado:", self.txt_efectivo_contado)
        formulario_cierre.addRow("Observación:", self.txt_observacion)

        self.btn_cerrar_ventana = QPushButton("Cerrar ventana")
        self.btn_cerrar_ventana.clicked.connect(self.close)
        barra_ventana = QHBoxLayout()
        barra_ventana.addStretch()
        barra_ventana.addWidget(self.btn_cerrar_ventana)

        self.btn_abrir.setVisible(False)
        self.txt_monto_apertura.setVisible(False)
        self.txt_efectivo_contado.setVisible(False)
        self.txt_observacion.setVisible(False)
        self.btn_cerrar_caja.setVisible(False)
        self.lbl_apertura_usuario.setVisible(False)
        self.lbl_apertura_fecha.setVisible(False)
        self.lbl_monto_apertura.setVisible(False)
        self.lbl_efectivo_esperado.setVisible(False)
        self.tabla_medios.setVisible(False)

        self.formulario_apertura = formulario_apertura
        self.formulario_cierre = formulario_cierre
        self._contenedor_estado = QWidget()
        self._layout_estado = QVBoxLayout(self._contenedor_estado)
        self._layout_estado.setContentsMargins(0, 0, 0, 0)
        self._layout_estado.addWidget(self.lbl_estado)
        self._layout_estado.addLayout(formulario_apertura)
        self._layout_estado.addWidget(self.btn_abrir)
        self._layout_estado.addLayout(formulario_cierre)
        self.lbl_cobros = QLabel("Cobros por medio de pago:")
        self._layout_estado.addWidget(self.lbl_cobros)
        self._layout_estado.addWidget(self.tabla_medios)
        self._layout_estado.addWidget(self.btn_cerrar_caja)

        self.tabla_historial = QTableWidget(0, 9)
        self.tabla_historial.setHorizontalHeaderLabels(
            [
                "N.º", "Estado", "Apertura", "Usuario apertura",
                "Monto inicial", "Cierre", "Esperado", "Contado", "Diferencia",
            ]
        )
        self.tabla_historial.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabla_historial.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_historial.setAlternatingRowColors(True)
        self.tabla_historial.verticalHeader().setVisible(False)
        self.tabla_historial.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.addWidget(self._contenedor_estado)
        layout.addWidget(QLabel("Historial de sesiones:"))
        layout.addWidget(self.tabla_historial, 1)
        layout.addLayout(barra_ventana)
        contenedor = QWidget()
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

        QShortcut(QKeySequence("F10"), self, self.close)

    def _mostrar_estado(self, abierta):
        for control in (
            self.txt_monto_apertura, self.btn_abrir,
        ):
            control.setVisible(not abierta)
        for control in (
            self.lbl_apertura_usuario,
            self.lbl_apertura_fecha,
            self.lbl_monto_apertura,
            self.lbl_efectivo_esperado,
            self.txt_efectivo_contado,
            self.txt_observacion,
            self.tabla_medios,
            self.btn_cerrar_caja,
        ):
            control.setVisible(abierta)

        self.formulario_apertura.setRowVisible(0, not abierta)
        self.formulario_cierre.setRowVisible(0, abierta)
        self.formulario_cierre.setRowVisible(1, abierta)
        self.formulario_cierre.setRowVisible(2, abierta)
        self.formulario_cierre.setRowVisible(3, abierta)
        self.formulario_cierre.setRowVisible(4, abierta)
        self.formulario_cierre.setRowVisible(5, abierta)
        self.lbl_cobros.setVisible(abierta)
        self.lbl_estado.setText("Caja abierta" if abierta else "Caja cerrada")

    def _recargar(self):
        try:
            self.sesion = self.repository.obtener_sesion_abierta()
            sesiones = self.repository.listar_sesiones()
            resumen = (
                self.repository.resumen_sesion(self.sesion["codigo"])
                if self.sesion is not None
                else None
            )
        except Exception as error:
            Mensajes.error(self, error)
            return

        abierta = self.sesion is not None
        self._mostrar_estado(abierta)
        if abierta:
            self.lbl_apertura_usuario.setText(
                str(self.sesion["usuario_apertura"] or self.sesion["idusuario_apertura"])
            )
            self.lbl_apertura_fecha.setText(str(self.sesion["fecha_apertura"]))
            self.lbl_monto_apertura.setText(
                _formatear_monto(Decimal(str(self.sesion["monto_apertura"])))
            )
            self.lbl_efectivo_esperado.setText(
                _formatear_monto(resumen["esperado"])
            )
            self.txt_efectivo_contado.setText(
                _formatear_monto(resumen["esperado"])
            )
            self._cargar_medios_pago(resumen["por_medio_pago"])

        self._cargar_historial(sesiones)

    def _cargar_medios_pago(self, medios):
        self.tabla_medios.setRowCount(len(medios))
        for fila, medio in enumerate(medios):
            self.tabla_medios.setItem(
                fila, 0, QTableWidgetItem(medio["descripcion"])
            )
            monto = QTableWidgetItem(_formatear_monto(medio["total"]))
            monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_medios.setItem(fila, 1, monto)

    def _cargar_historial(self, sesiones):
        self.tabla_historial.setRowCount(len(sesiones))
        for fila, sesion in enumerate(sesiones):
            valores = (
                sesion["codigo"],
                sesion["estado"],
                sesion["fecha_apertura"],
                sesion["usuario_apertura"],
                sesion["monto_apertura"],
                sesion["fecha_cierre"],
                sesion["esperado"],
                sesion["contado"],
                sesion["diferencia"],
            )
            for columna, valor in enumerate(valores):
                if isinstance(valor, Decimal):
                    texto = _formatear_monto(valor)
                else:
                    texto = str(valor if valor is not None else "")
                celda = QTableWidgetItem(texto)
                if columna in (0, 4, 6, 7, 8):
                    celda.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_historial.setItem(fila, columna, celda)

    def _usuario_id(self):
        usuario = obtener_usuario()
        if usuario is None or usuario.get("idusuario") is None:
            raise ValueError("No se pudo identificar al usuario de la sesión.")
        return usuario["idusuario"]

    def _abrir_caja(self):
        try:
            monto = _leer_monto(self.txt_monto_apertura, "apertura")
            self.repository.abrir_caja(monto, self._usuario_id())
        except Exception as error:
            Mensajes.error(self, error)
            return
        Mensajes.informacion(self, "Caja", "La caja se abrió correctamente.")
        self._recargar()

    def _cerrar_caja(self):
        if self.sesion is None:
            Mensajes.advertencia(self, "Caja", "No hay una caja abierta.")
            return
        try:
            contado = _leer_monto(self.txt_efectivo_contado, "efectivo contado")
            resumen = self.repository.resumen_sesion(self.sesion["codigo"])
            esperado = resumen["esperado"]
            diferencia = contado - esperado
            if diferencia > 0:
                diferencia_texto = f"Sobrante: {_formatear_monto(diferencia)}"
            elif diferencia < 0:
                diferencia_texto = f"Faltante: {_formatear_monto(abs(diferencia))}"
            else:
                diferencia_texto = "Sin diferencia"
            pregunta = (
                f"¿Cerrar la caja?\n"
                f"Efectivo esperado: {_formatear_monto(esperado)}\n"
                f"Efectivo contado: {_formatear_monto(contado)}\n"
                f"Diferencia: {diferencia_texto}"
            )
            if not Mensajes.confirmar(self, "Confirmar cierre de caja", pregunta):
                return
            resultado = self.repository.cerrar_caja(
                self.sesion["codigo"],
                contado,
                self._usuario_id(),
                self.txt_observacion.text().strip(),
            )
        except Exception as error:
            Mensajes.error(self, error)
            return

        Mensajes.informacion(
            self,
            "Caja cerrada",
            f"Caja cerrada correctamente.\n"
            f"Esperado: {_formatear_monto(resultado['esperado'])}\n"
            f"Contado: {_formatear_monto(resultado['contado'])}\n"
            f"Diferencia: {_formatear_monto(resultado['diferencia'])}",
        )
        self._recargar()
