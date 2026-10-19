from decimal import Decimal

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from nucleo.mensajes import Mensajes
from nucleo.pedido_venta_repository import PedidoVentaRepository
from nucleo.sesion import obtener_usuario


class VentanaPedidoVenta(QDialog):
    """Captura de cabecera y detalle, manteniendo las lineas en memoria."""

    def __init__(self, pedido=None, padre=None):
        super().__init__(padre)
        self.repository = PedidoVentaRepository()
        self.pedido_original = pedido
        self.detalles = []
        self.items_disponibles = {}
        self.setWindowTitle("Pedido de Venta")
        self.resize(900, 580)

        self._crear_interfaz()
        self._cargar_catalogos()
        
        if pedido is None:
            # CORRECCIÓN 1: Escudo protector para el QSpinBox al crear un nuevo pedido
            siguiente_codigo = self.repository.obtener_siguiente_codigo()
            self.spn_codigo.setValue(int(siguiente_codigo) if siguiente_codigo is not None else 1)
            
            self.fecha.setDate(QDate.currentDate())
            self.lbl_estado.setText("BORRADOR")
        else:
            self._cargar_pedido(pedido)

        self._configurar_atajos()
        if pedido and pedido["estado"] != "BORRADOR":
            self._establecer_solo_lectura()

    def _crear_interfaz(self):
        formulario = QFormLayout()
        self.spn_codigo = QSpinBox()
        self.spn_codigo.setRange(1, 2_000_000_000)
        self.spn_codigo.setReadOnly(True)
        self.fecha = QDateEdit()
        self.fecha.setCalendarPopup(True)
        self.fecha.setDisplayFormat("dd/MM/yyyy")
        self.combo_cliente = QComboBox()
        self.lbl_estado = QLabel()
        formulario.addRow("Pedido N.º:", self.spn_codigo)
        formulario.addRow("Fecha:", self.fecha)
        formulario.addRow("Cliente:", self.combo_cliente)
        formulario.addRow("Estado:", self.lbl_estado)

        self.combo_item = QComboBox()
        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 1_000_000)
        self.spn_precio = QDoubleSpinBox()
        self.spn_precio.setRange(0, 99_999_999_999)
        self.spn_precio.setDecimals(2)
        self.spn_precio.setReadOnly(True)
        self.btn_agregar = QPushButton("Agregar ítem")
        self.btn_quitar = QPushButton("Quitar línea")
        self.btn_agregar.clicked.connect(self._agregar_detalle)
        self.btn_quitar.clicked.connect(self._quitar_detalle)
        self.combo_item.currentIndexChanged.connect(self._actualizar_precio_item)

        barra_detalle = QHBoxLayout()
        barra_detalle.addWidget(self.combo_item, 1)
        barra_detalle.addWidget(QLabel("Cantidad:"))
        barra_detalle.addWidget(self.spn_cantidad)
        barra_detalle.addWidget(QLabel("Precio:"))
        barra_detalle.addWidget(self.spn_precio)
        barra_detalle.addWidget(self.btn_agregar)

        self.tabla_detalle = QTableWidget(0, 7)
        self.tabla_detalle.setHorizontalHeaderLabels(
            ["Código", "Descripción", "Cantidad", "Precio", "IVA %", "Subtotal", "Total"]
        )
        self.tabla_detalle.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_detalle.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_detalle.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_detalle.horizontalHeader().setStretchLastSection(True)

        self.lbl_subtotal = QLabel("0.00")
        self.lbl_iva = QLabel("0.00")
        self.lbl_total = QLabel("0.00")
        totales = QFormLayout()
        totales.addRow("Subtotal:", self.lbl_subtotal)
        totales.addRow("IVA:", self.lbl_iva)
        totales.addRow("Total:", self.lbl_total)

        self.btn_guardar = QPushButton("Guardar borrador")
        self.btn_cancelar = QPushButton("Cerrar")
        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_cancelar.clicked.connect(self.reject)
        botones = QHBoxLayout()
        botones.addWidget(self.btn_quitar)
        botones.addStretch()
        botones.addWidget(self.btn_guardar)
        botones.addWidget(self.btn_cancelar)

        layout = QVBoxLayout(self)
        layout.addLayout(formulario)
        layout.addLayout(barra_detalle)
        layout.addWidget(self.tabla_detalle, 1)
        layout.addLayout(totales)
        layout.addLayout(botones)

    def _cargar_catalogos(self):
        clientes = self.repository.listar_clientes()
        for cliente in clientes:
            self.combo_cliente.addItem(
                f"{cliente['cto_cod']} - {cliente['cto_razonsocial']}",
                cliente["cto_cod"],
            )
        for item in self.repository.listar_items():
            self.items_disponibles[item["codigo"]] = item
            self.combo_item.addItem(
                f"{item['codigo']} - {item['descripcion']}", item["codigo"]
            )
        self._actualizar_precio_item()

    def _cargar_pedido(self, pedido):
        # CORRECCIÓN 2: Escudo protector al cargar un pedido existente
        codigo_pedido = pedido.get("codigo")
        self.spn_codigo.setValue(int(codigo_pedido) if codigo_pedido is not None else 0)
        
        fecha = pedido["fecha"]
        self.fecha.setDate(QDate(fecha.year, fecha.month, fecha.day))
        indice = self.combo_cliente.findData(pedido["cod_cliente"])
        self.combo_cliente.setCurrentIndex(indice)
        self.lbl_estado.setText(pedido["estado"])
        self.detalles = [dict(detalle) for detalle in pedido.get("detalles", [])]
        self._actualizar_tabla()

    def _configurar_atajos(self):
        QShortcut(QKeySequence("Ctrl+G"), self, self._guardar)
        QShortcut(QKeySequence("Esc"), self, self.reject)

    def _actualizar_precio_item(self, *_):
        codigo = self.combo_item.currentData()
        item = self.items_disponibles.get(codigo)
        self.spn_precio.setValue(float(item["precio"] or 0) if item else 0)

    def _agregar_detalle(self):
        codigo = self.combo_item.currentData()
        item = self.items_disponibles.get(codigo)
        if item is None:
            Mensajes.advertencia(self, "Pedido", "No hay ítems disponibles para agregar.")
            return
        cantidad = Decimal(self.spn_cantidad.value())
        precio = Decimal(str(item["precio"] or 0))
        porcentaje_iva = Decimal(str(item["porcentaje_iva"] or 0))
        subtotal = cantidad * precio
        monto_iva = subtotal * porcentaje_iva / Decimal("100")
        self.detalles.append(
            {
                "codigo_item": codigo,
                "descripcion": item["descripcion"],
                "cantidad": cantidad,
                "precio_unitario": precio,
                "porcentaje_iva": porcentaje_iva,
                "subtotal": subtotal,
                "monto_iva": monto_iva,
                "total": subtotal + monto_iva,
            }
        )
        self._actualizar_tabla()

    def _quitar_detalle(self):
        fila = self.tabla_detalle.currentRow()
        if fila < 0:
            Mensajes.advertencia(self, "Pedido", "Seleccione una línea para quitar.")
            return
        self.detalles.pop(fila)
        self._actualizar_tabla()

    def _actualizar_tabla(self):
        self.tabla_detalle.setRowCount(len(self.detalles))
        for fila, detalle in enumerate(self.detalles):
            valores = (
                detalle["codigo_item"], detalle["descripcion"], detalle["cantidad"],
                detalle["precio_unitario"], detalle["porcentaje_iva"],
                detalle["subtotal"], detalle["total"],
            )
            for columna, valor in enumerate(valores):
                texto = f"{valor:.2f}" if isinstance(valor, (Decimal, float)) else str(valor)
                celda = QTableWidgetItem(texto)
                if columna != 1:
                    celda.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_detalle.setItem(fila, columna, celda)

        subtotal = sum((Decimal(str(linea["subtotal"])) for linea in self.detalles), Decimal(0))
        monto_iva = sum((Decimal(str(linea["monto_iva"])) for linea in self.detalles), Decimal(0))
        self.lbl_subtotal.setText(f"{subtotal:.2f}")
        self.lbl_iva.setText(f"{monto_iva:.2f}")
        self.lbl_total.setText(f"{subtotal + monto_iva:.2f}")

    def _guardar(self):
        if not self.detalles:
            Mensajes.advertencia(self, "Pedido", "Agregue al menos un ítem al pedido.")
            return
        cod_cliente = self.combo_cliente.currentData()
        if cod_cliente is None:
            Mensajes.advertencia(self, "Pedido", "Seleccione un cliente.")
            return
        usuario = obtener_usuario()
        
        # CORRECCIÓN 3: Limpiamos los datos del diccionario para que coincidan con lo que pide la Base de Datos.
        pedido = {
            "codigo": self.spn_codigo.value(),
            "fecha": self.fecha.date().toPython(),
            "cod_cliente": cod_cliente,
            "idusuario": (
                self.pedido_original["idusuario"] if self.pedido_original
                else usuario["idusuario"] if usuario else None
            ),
            "total": Decimal(self.lbl_total.text()),
        }
        
        try:
            self.repository.guardar(
                pedido,
                self.detalles,
                codigo_original=pedido["codigo"] if self.pedido_original else None,
            )
        except Exception as error:
            Mensajes.error(self, error)
            return
        self.accept()

    def _establecer_solo_lectura(self):
        for control in (
            self.fecha, self.combo_cliente, self.combo_item, self.spn_cantidad,
            self.spn_precio, self.btn_agregar, self.btn_quitar, self.btn_guardar,
        ):
            control.setEnabled(False)
        estado = self.pedido_original["estado"]
        self.lbl_estado.setText(f"{estado} - SOLO LECTURA")
        self.setWindowTitle(f"Pedido de Venta - {estado} - Solo lectura")