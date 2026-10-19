from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from psycopg.errors import ForeignKeyViolation

from nucleo.cobro_repository import CobroRepository
from nucleo.mensajes import Mensajes
from nucleo.pedido_venta_repository import PedidoVentaRepository
from nucleo.sesion import obtener_usuario
from servicios.reporte_pdf import ReportePDF
from vistas.ventana_cobro import VentanaCobro
from vistas.ventana_pedido_venta import VentanaPedidoVenta


class VentanaPedidosListado(QMainWindow):
    """Listado y acciones del proceso de pedidos, separado del CRUD generico."""

    def __init__(self, padre=None):
        super().__init__(padre)
        self.repository = PedidoVentaRepository()
        self.pedidos = []
        self.setWindowTitle("Pedidos de Venta")
        self.resize(1050, 560)
        self._crear_interfaz()
        self._configurar_atajos()
        self._recargar()

    def _crear_interfaz(self):
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Filtrar por número, cliente, usuario o estado...")
        self.txt_buscar.textChanged.connect(self._filtrar)

        self.btn_nuevo = QPushButton("Nuevo (F2)")
        self.btn_editar = QPushButton("Abrir / editar (F3)")
        self.btn_confirmar = QPushButton("Confirmar (F7)")
        self.btn_eliminar = QPushButton("Eliminar (F8)")
        self.btn_ticket = QPushButton("Imprimir ticket (F9)")
        self.btn_anular = QPushButton("Anular")
        self.btn_cobrar = QPushButton("Cobrar")
        self.btn_cerrar = QPushButton("Cerrar (F10)")
        self.btn_nuevo.clicked.connect(self._nuevo)
        self.btn_editar.clicked.connect(self._abrir_seleccionado)
        self.btn_confirmar.clicked.connect(self._confirmar_seleccionado)
        self.btn_eliminar.clicked.connect(self._eliminar_seleccionado)
        self.btn_ticket.clicked.connect(self._imprimir_ticket_seleccionado)
        self.btn_anular.clicked.connect(self._anular_seleccionado)
        self.btn_cobrar.clicked.connect(self._cobrar_seleccionado)
        self.btn_cerrar.clicked.connect(self.close)

        # CORRECCIÓN 1: Cambiamos a 6 columnas y actualizamos los títulos
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["N.º", "Fecha", "Cliente", "Vendedor", "Estado", "Total"]
        )
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.cellDoubleClicked.connect(lambda *_: self._abrir_seleccionado())
        self.tabla.itemSelectionChanged.connect(self._actualizar_acciones)

        barra = QHBoxLayout()
        for boton in (
            self.btn_nuevo, self.btn_editar, self.btn_confirmar,
            self.btn_eliminar, self.btn_anular, self.btn_ticket,
            self.btn_cobrar, self.btn_cerrar,
        ):
            barra.addWidget(boton)
        layout = QVBoxLayout()
        layout.addWidget(self.txt_buscar)
        layout.addLayout(barra)
        layout.addWidget(self.tabla, 1)
        contenedor = QWidget()
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

    def _configurar_atajos(self):
        QShortcut(QKeySequence("F2"), self, self._nuevo)
        QShortcut(QKeySequence("F3"), self, self._abrir_seleccionado)
        QShortcut(QKeySequence("F7"), self, self._confirmar_seleccionado)
        QShortcut(QKeySequence("F8"), self, self._eliminar_seleccionado)
        QShortcut(QKeySequence("F9"), self, self._imprimir_ticket_seleccionado)
        QShortcut(QKeySequence("F10"), self, self.close)

    def _recargar(self):
        try:
            self.pedidos = self.repository.listar()
        except Exception as error:
            Mensajes.error(self, error)
            return
        self._filtrar()

    def _filtrar(self, *_):
        texto = self.txt_buscar.text().strip().casefold()
        filas = [
            pedido for pedido in self.pedidos
            if not texto or texto in " ".join(str(valor or "") for valor in pedido.values()).casefold()
        ]
        self.tabla.setRowCount(len(filas))
        for numero_fila, pedido in enumerate(filas):
            valores = (
                pedido["codigo"], pedido["fecha"], pedido["cliente"], pedido["usuario"],
                pedido["estado"], pedido["total"],
            )
            for columna, valor in enumerate(valores):
                texto_celda = f"{valor:.2f}" if isinstance(valor, (float,)) else str(valor or "")
                celda = QTableWidgetItem(texto_celda)
                # CORRECCIÓN 2: Alineamos a la derecha solo la columna 0 (N.º) y la 5 (Total)
                if columna in (0, 5):
                    celda.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla.setItem(numero_fila, columna, celda)
        self._filas_visibles = filas
        self._actualizar_acciones()

    def _actualizar_acciones(self):
        fila = self.tabla.currentRow()
        pedido = (
            self._filas_visibles[fila]
            if 0 <= fila < len(self._filas_visibles)
            else None
        )
        es_borrador = pedido is not None and pedido["estado"] == "BORRADOR"
        es_confirmado = pedido is not None and pedido["estado"] == "CONFIRMADO"
        self.btn_editar.setEnabled(es_borrador)
        self.btn_confirmar.setEnabled(es_borrador)
        self.btn_eliminar.setEnabled(es_borrador)
        self.btn_anular.setEnabled(es_confirmado)
        self.btn_cobrar.setEnabled(es_confirmado)
        self.btn_ticket.setEnabled(es_confirmado)

    def _pedido_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            Mensajes.advertencia(self, "Pedidos", "Seleccione un pedido de la lista.")
            return None
        return self._filas_visibles[fila]

    def _nuevo(self):
        try:
            ventana = VentanaPedidoVenta(padre=self)
            if ventana.exec() == QDialog.DialogCode.Accepted:
                self._recargar()
        except Exception as error:
            Mensajes.error(
                self,
                RuntimeError(
                    "No se pudo abrir el pedido. Ejecute script_plantilla.sql en "
                    "la base configurada en configuracion/base_datos.py y vuelva "
                    f"a intentarlo. Detalle: {error}"
                ),
            )

    def _abrir_seleccionado(self):
        seleccionado = self._pedido_seleccionado()
        if seleccionado is None:
            return
        if seleccionado["estado"] != "BORRADOR":
            Mensajes.advertencia(
                self, "Pedidos", "Solo se pueden editar pedidos en borrador."
            )
            return
        try:
            pedido = self.repository.obtener(seleccionado["codigo"])
            if pedido is None:
                raise ValueError("El pedido ya no existe.")
            ventana = VentanaPedidoVenta(pedido=pedido, padre=self)
            ventana.exec()
            self._recargar()
        except Exception as error:
            Mensajes.error(self, error)

    def _anular_seleccionado(self):
        pedido = self._pedido_seleccionado()
        if pedido is None:
            return
        if pedido["estado"] != "CONFIRMADO":
            Mensajes.advertencia(
                self, "Pedidos", "Solo se pueden anular pedidos confirmados."
            )
            return

        motivo, aceptado = QInputDialog.getText(
            self, "Anular pedido", "Motivo de la anulación:"
        )
        if not aceptado:
            return
        if not motivo.strip():
            Mensajes.advertencia(
                self, "Anular pedido", "El motivo de anulación es obligatorio."
            )
            return
        if not Mensajes.confirmar(
            self,
            "Confirmar anulación",
            f"¿Anular el pedido {pedido['codigo']}? Se repondrá el stock",
        ):
            return

        try:
            usuario = obtener_usuario()
            if usuario is None or usuario.get("idusuario") is None:
                raise ValueError("No se pudo identificar al usuario de la sesión.")
            self.repository.anular(
                pedido["codigo"], usuario["idusuario"], motivo.strip()
            )
            self._recargar()
            Mensajes.informacion(
                self,
                "Pedido anulado",
                f"El pedido {pedido['codigo']} fue anulado y se repuso el stock.",
            )
        except Exception as error:
            Mensajes.error(self, error)

    def _cobrar_seleccionado(self):
        pedido = self._pedido_seleccionado()
        if pedido is None:
            return
        if pedido["estado"] != "CONFIRMADO":
            Mensajes.advertencia(
                self, "Pedidos", "Solo se pueden cobrar pedidos confirmados."
            )
            return
        try:
            VentanaCobro(pedido=pedido, padre=self).exec()
        except Exception as error:
            Mensajes.error(self, error)

    def _confirmar_seleccionado(self):
        pedido = self._pedido_seleccionado()
        if pedido is None:
            return
        if pedido["estado"] != "BORRADOR":
            Mensajes.advertencia(
                self, "Pedidos", "Solo se pueden confirmar pedidos en borrador."
            )
            return
        if not Mensajes.confirmar(
            self, "Confirmar pedido", f"¿Confirmar el pedido {pedido['codigo']}?"
        ):
            return
        try:
            usuario = obtener_usuario()
            self.repository.confirmar(pedido["codigo"], usuario["idusuario"])
            self._recargar()
        except Exception as error:
            Mensajes.error(self, error)

    def _eliminar_seleccionado(self):
        pedido = self._pedido_seleccionado()
        if pedido is None:
            return
        if pedido["estado"] != "BORRADOR":
            Mensajes.advertencia(self, "Pedidos", "Solo se pueden eliminar pedidos en borrador.")
            return
        respuesta = QMessageBox.question(
            self, "Eliminar pedido", f"¿Eliminar el pedido {pedido['codigo']}?"
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            self.repository.eliminar(pedido["codigo"])
            self._recargar()
        except ForeignKeyViolation:
            Mensajes.advertencia(
                self,
                "No se puede eliminar",
                "No se puede eliminar este registro porque está siendo utilizado "
                "por otros elementos del sistema.",
            )
        except Exception as error:
            Mensajes.error(self, error)

    def _imprimir_ticket_seleccionado(self):
        seleccionado = self._pedido_seleccionado()
        if seleccionado is None:
            return
        if seleccionado["estado"] != "CONFIRMADO":
            Mensajes.advertencia(
                self, "Pedidos", "Solo se pueden imprimir tickets de pedidos confirmados."
            )
            return
        try:
            pedido = self.repository.obtener(seleccionado["codigo"])
            if pedido is None:
                raise ValueError("El pedido ya no existe.")
            cobros = CobroRepository().listar_cobros_pedido(pedido["codigo"])
            ReportePDF(None).generar_ticket(pedido, cobros)
        except Exception as error:
            Mensajes.error(self, error)