import datetime

from psycopg.errors import ForeignKeyViolation
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nucleo.iconos import (
    ICONO_CERRAR,
    ICONO_ELIMINAR,
    ICONO_EDITAR,
    ICONO_IMPRIMIR,
    ICONO_NUEVO,
)
from nucleo.mensajes import Mensajes
from nucleo.repositorio_generico import RepositorioGenerico
from servicios.reporte_pdf import ReportePDF
from vistas.ventana_edicion import VentanaEdicion


class VentanaNavegacion(QMainWindow):
    """
    Ventana generica de listado y acciones del CRUD.
    Se construye SOLA a partir de una ConfiguracionModulo:
        VentanaNavegacion(configuracion_editoriales)
    Si al_seleccionar no es None, funciona en modo "seleccion":
    Enter o doble clic devuelven el registro elegido (filosofia "pegar").
    """

    def __init__(self, configuracion, al_seleccionar=None, filtro=None):
        super().__init__()
        self.configuracion = configuracion
        self.repository = RepositorioGenerico(configuracion, filtro=filtro)
        self.al_seleccionar = al_seleccionar
        self.filas_actuales = []

        self.setWindowTitle(configuracion.titulo)
        self.resize(*configuracion.tamano_navegacion)

        self._crear_widgets()
        self._crear_layout()
        self._conectar_senales()
        self._configurar_atajos()
        if al_seleccionar:
            self.setWindowTitle(f"Buscar {configuracion.titulo} - seleccione una fila")

        # La ventana se abre centrada en la pantalla.
        self._centrar_en_pantalla()

        # Carga inicial de todos los registros.
        self._recargar()

    def _centrar_en_pantalla(self):
        """Centra la ventana en la pantalla primaria."""
        pantalla = self.screen()
        if pantalla is None:
            return
        geometria = pantalla.availableGeometry()
        self.move(
            geometria.center() - self.rect().center()
        )

    # ---------------------------------------------------------------
    #   Construccion de la interfaz
    # ---------------------------------------------------------------
    def _crear_widgets(self):
        configuracion = self.configuracion

        self.lbl_titulo = QLabel(configuracion.titulo.upper())
        self.lbl_titulo.setObjectName("lbl_titulo")

        # Barra de atajos siempre visible.
        self.lbl_atajos = QLabel(
            "F2: Nuevo   |   F3: Editar   |   F8: Eliminar   |   "
            "F9: Imprimir   |   F10: Cerrar"
        )
        self.lbl_atajos.setObjectName("lbl_atajos")

        # Barra de acciones (los botones se ocultan en modo seleccion).
        self.btn_nuevo = QPushButton(ICONO_NUEVO(), "Nuevo")
        self.btn_editar = QPushButton(ICONO_EDITAR(), "Editar")
        self.btn_eliminar = QPushButton(ICONO_ELIMINAR(), "Eliminar")
        self.btn_duplicar = QPushButton("Duplicar")
        self.btn_imprimir = QPushButton(ICONO_IMPRIMIR(), "Imprimir")
        self.btn_cerrar = QPushButton(ICONO_CERRAR(), "Cerrar")

        self.btn_nuevo.setVisible(configuracion.permitir_nuevo)
        self.btn_editar.setVisible(configuracion.permitir_editar)
        self.btn_eliminar.setVisible(configuracion.permitir_eliminar)
        self.btn_duplicar.setVisible(configuracion.permitir_duplicar)
        self.btn_imprimir.setVisible(configuracion.permitir_imprimir)

        # Tooltips de ayuda amigables por accion.
        self.btn_nuevo.setToolTip(f"Nuevo registro de {configuracion.titulo} (F2)")
        self.btn_editar.setToolTip("Seleccione una fila y edite el registro (F3)")
        self.btn_eliminar.setToolTip("Seleccione una fila y elimine el registro (F8)")
        self.btn_duplicar.setToolTip("Copia la fila seleccionada como registro nuevo")
        self.btn_imprimir.setToolTip(f"Imprimir el listado actual de {configuracion.titulo} (F9)")
        self.btn_cerrar.setToolTip("Cerrar esta ventana (F10)")

        # Zona de busqueda: campo de texto unico (mas aire para la tabla).
        # El criterio se cambia haciendo clic en el encabezado de la tabla.
        self.txt_buscar = QLineEdit()
        self.campo_busqueda = configuracion.buscar_por
        self._actualizar_placeholder_busqueda()
        self.txt_buscar.setToolTip(
            "Escriba para filtrar. Haga clic en un encabezado de columna "
            "para cambiar el campo de busqueda"
        )

        # Tabla generica: una columna por campo visible en navegacion.
        self.tabla = QTableWidget(0, len(configuracion.campos_visibles_navegacion()))
        self.tabla.setHorizontalHeaderLabels(
            [c.etiqueta for c in configuracion.campos_visibles_navegacion()]
        )
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(30)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla.installEventFilter(self)

        for indice, campo in enumerate(configuracion.campos_visibles_navegacion()):
            if campo.ancho:
                self.tabla.setColumnWidth(indice, campo.ancho)

    def _crear_layout(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        # Margenes finos para un diseno compacto.
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        layout.addWidget(self.lbl_titulo, 0, Qt.AlignCenter)
        layout.addWidget(self.lbl_atajos, 0, Qt.AlignCenter)

        # Botonera: botones juntos a la izquierda con espacio minimo (3 px).
        barra_botones = QHBoxLayout()
        barra_botones.setSpacing(3)
        barra_botones.setContentsMargins(2, 2, 2, 2)
        for boton in (self.btn_nuevo, self.btn_editar, self.btn_eliminar,
                      self.btn_duplicar, self.btn_imprimir, self.btn_cerrar):
            barra_botones.addWidget(boton)
        layout.addLayout(barra_botones)

        barra_busqueda = QHBoxLayout()
        barra_busqueda.addWidget(self.txt_buscar, 1)
        layout.addLayout(barra_busqueda)

        layout.addWidget(self.tabla, 1)
        self.setCentralWidget(contenedor)

    def _conectar_senales(self):
        self.btn_nuevo.clicked.connect(self.nuevo)
        self.btn_editar.clicked.connect(self.editar)
        self.btn_eliminar.clicked.connect(self.eliminar)
        self.btn_duplicar.clicked.connect(self.duplicar)
        self.btn_imprimir.clicked.connect(self.imprimir)
        self.btn_cerrar.clicked.connect(self.close)

        self.txt_buscar.textChanged.connect(self._buscar)

        # Click en el encabezado de una columna: esa columna pasa a ser
        # el criterio de busqueda actual (filosofia del proyecto antiguo).
        self.tabla.horizontalHeader().sectionClicked.connect(
            self._cambiar_campo_busqueda
        )
        self.tabla.cellDoubleClicked.connect(self._accion_fila_actual)
        self.tabla.customContextMenuRequested.connect(self._menu_contextual)

    def _configurar_atajos(self):
        QShortcut(QKeySequence("F2"), self, self.nuevo)
        QShortcut(QKeySequence("F3"), self, self.editar)
        QShortcut(QKeySequence("F8"), self, self.eliminar)
        QShortcut(QKeySequence("F9"), self, self.imprimir)
        QShortcut(QKeySequence("F10"), self, self.close)

    # ---------------------------------------------------------------
    #   Acciones del CRUD
    # ---------------------------------------------------------------
    def nuevo(self):
        """Abre la edicion en modo NUEVO (con siguiente codigo sugerido)."""
        if self.al_seleccionar:
            return
        self._abrir_edicion("nuevo", None)

    def editar(self):
        """Abre la edicion con los datos de la fila seleccionada."""
        if self.al_seleccionar:
            return
        valores = self._valores_fila_actual()
        if valores is not None:
            self._abrir_edicion("editar", valores)

    def eliminar(self):
        """Confirma y elimina el registro de la fila seleccionada."""
        if self.al_seleccionar:
            return
        valores = self._valores_fila_actual()
        if valores is None:
            return
        configuracion = self.configuracion

        detalle = "\n".join(
            f"{campo.etiqueta}: {valores.get(campo.nombre, '')}"
            for campo in configuracion.campos_visibles_navegacion()
        )
        if not Mensajes.confirmar(
            self,
            "Confirmar eliminacion",
            "Esta accion eliminara el registro:\n\n" + detalle,
        ):
            return

        try:
            self.repository.eliminar(valores[configuracion.clave_primaria])
        except ForeignKeyViolation:
            Mensajes.advertencia(
                self,
                "No se puede eliminar",
                "No se puede eliminar este registro porque está siendo utilizado "
                "por otros elementos del sistema.",
            )
            return
        except Exception as error:
            Mensajes.error(self, error)
            return
        Mensajes.informacion(self, "Exito", "Registro eliminado correctamente.")
        self._recargar()

    def duplicar(self):
        """Copia la fila seleccionada y la abre como registro NUEVO."""
        if self.al_seleccionar:
            return
        valores = self._valores_fila_actual()
        if valores is None:
            return
        self._abrir_edicion("duplicar", valores)

    def imprimir(self):
        """Genera un PDF del listado actualmente mostrado."""
        ReportePDF(self.configuracion).generar(self.filas_actuales)

    def _abrir_edicion(self, modo, valores):
        ventana = VentanaEdicion(self.configuracion, modo, valores, padre=self)
        if ventana.exec() == VentanaEdicion.Accepted:
            self._recargar()

    # ---------------------------------------------------------------
    #   Seleccion de registros (modo "pegar")
    # ---------------------------------------------------------------
    def _accion_fila_actual(self, *args):
        """Enter o doble clic: editar (normal) o elegir registro (seleccion)."""
        if self.al_seleccionar is not None:
            self._elegir_registro()
        else:
            self.editar()

    def _elegir_registro(self):
        """Devuelve el registro elegido al formulario que lo pidio."""
        valores = self._valores_fila_actual()
        if valores is None:
            return
        self.al_seleccionar(valores)
        self.close()

    # ---------------------------------------------------------------
    #   Busqueda y datos en la tabla
    # ---------------------------------------------------------------
    def _cambiar_campo_busqueda(self, indice_columna):
        """Al hacer clic en el encabezado, esa columna pasa a filtrar."""
        campos = self.configuracion.campos_visibles_navegacion()
        if 0 <= indice_columna < len(campos):
            self.campo_busqueda = campos[indice_columna].nombre
            self._actualizar_placeholder_busqueda()
            self._buscar()

    def _actualizar_placeholder_busqueda(self):
        """Muestra en el campo cual es el criterio de busqueda actual."""
        campo = self.configuracion.obtener_campo(self.campo_busqueda)
        etiqueta = campo.etiqueta if campo else self.campo_busqueda
        self.txt_buscar.setPlaceholderText(f"Filtrar por {etiqueta}...")

    def _campo_busqueda_activo(self):
        return self.campo_busqueda

    def _buscar(self):
        """Filtra en PostgreSQL (never carga todo para filtrar en memoria)."""
        texto = self.txt_buscar.text()
        try:
            filas = self.repository.buscar(texto, self._campo_busqueda_activo())
        except Exception as error:
            Mensajes.error(self, error)
            return
        self._filas_a_tabla(filas)

    def _recargar(self):
        try:
            filas = self.repository.listar()
        except Exception as error:
            Mensajes.error(self, error)
            return
        self._filas_a_tabla(filas)

    def _filas_a_tabla(self, filas):
        """Vuelca la lista de dicts al QTableWidget."""
        self.filas_actuales = filas
        campos = self.configuracion.campos_visibles_navegacion()

        self.tabla.setSortingEnabled(False)
        self.tabla.setRowCount(0)
        for numero_fila, fila in enumerate(filas):
            self.tabla.insertRow(numero_fila)
            for numero_columna, campo in enumerate(campos):
                item = self._crear_item(campo, fila.get(campo.nombre))
                self.tabla.setItem(numero_fila, numero_columna, item)
        self.tabla.setSortingEnabled(True)

        cantidad = len(filas)
        palabra = "registro" if cantidad == 1 else "registros"
        self.statusBar().showMessage(f"{cantidad} {palabra} encontrados")
        self._actualizar_botones_segun_registros(cantidad)

    def _actualizar_botones_segun_registros(self, cantidad):
        """Editar/Eliminar/Imprimir solo tienen sentido si hay registros."""
        if self.al_seleccionar is not None:
            return
        hay_registros = cantidad > 0
        self.btn_editar.setEnabled(hay_registros)
        self.btn_eliminar.setEnabled(hay_registros)
        self.btn_imprimir.setEnabled(hay_registros)

    def _crear_item(self, campo, valor):
        # Los campos booleanos se muestran como checkbox en la tabla.
        if campo.tipo is bool:
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setCheckState(Qt.Checked if valor else Qt.Unchecked)
        else:
            item = QTableWidgetItem(self._formatear(campo, valor))
            if campo.alineacion == "derecha":
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Color de fondo opcional de la celda.
        if campo.color_celda:
            item.setBackground(QColor(campo.color_celda))
        return item

    @staticmethod
    def _formatear(campo, valor):
        if campo.tipo is bool:
            return "Si" if valor else "No"
        if valor is None:
            return ""
        return str(valor)

    def _valores_fila_actual(self):
        """Devuelve la fila seleccionada como dict {campo: valor} o None."""
        fila = self.tabla.currentRow()
        if fila < 0:
            Mensajes.advertencia(self, "Aviso", "Primero seleccione una fila en la tabla.")
            return None
        valores = {}
        for numero_columna, campo in enumerate(
            self.configuracion.campos_visibles_navegacion()
        ):
            item = self.tabla.item(fila, numero_columna)
            if campo.tipo is bool:
                # El checkbox de la columna es la fuente del valor.
                valores[campo.nombre] = item.checkState() == Qt.Checked
            else:
                valores[campo.nombre] = self._convertir(campo, item.text())
        return valores

    @staticmethod
    def _convertir(campo, texto):
        if campo.tipo is int:
            return int(texto) if texto else None
        if campo.tipo is float:
            return float(texto) if texto else None
        if campo.tipo is bool:
            return texto == "Si"
        if campo.tipo is datetime.date:
            return texto
        return texto

    # ---------------------------------------------------------------
    #   Menú contextual y teclado
    # ---------------------------------------------------------------
    def _menu_contextual(self, posicion):
        menu = QMenu(self)
        menu.addAction("Editar", self.editar)
        menu.addSeparator()
        menu.addAction("Duplicar", self.duplicar)
        menu.addSeparator()
        menu.addAction("Eliminar", self.eliminar)
        menu.exec(self.tabla.mapToGlobal(posicion))

    def eventFilter(self, objeto, evento):
        """Enter sobre la tabla: Editar o elegir registro segun el modo."""
        if objeto is self.tabla and evento.type() == QEvent.KeyPress:
            tecla = evento.key()
            if tecla in (Qt.Key_Return, Qt.Key_Enter):
                self._accion_fila_actual()
                return True
        return super().eventFilter(objeto, evento)