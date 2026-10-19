import datetime

from PySide6.QtCore import QDate, QEvent, Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nucleo.iconos import (
    ICONO_ACEPTAR,
    ICONO_BUSCAR,
    ICONO_CANCELAR,
    ICONO_LIMPIAR,
    ICONO_VALIDO,
)
from nucleo.mensajes import Mensajes
from nucleo.repositorio_generico import RepositorioGenerico


class VentanaEdicion(QDialog):
    """
    Ventana generica de edicion: genera sus propios campos a partir de
    ConfiguracionModulo. Modos: "nuevo", "editar" y "duplicar".

    Atajos: Ctrl+G = Aceptar, Ctrl+Q = Cancelar, Enter = siguiente campo,
    Ctrl+Enter en un campo con referencia = abrir la busqueda de seleccion.
    """

    def __init__(self, configuracion, modo="nuevo", valores=None, padre=None):
        super().__init__(padre)
        self.configuracion = configuracion
        self.modo = modo
        self.valores_originales = valores or {}
        self.repository = RepositorioGenerico(configuracion)
        self.controles = {}      # nombre_campo -> widget de entrada
        self.acciones_validas = {}  # nombre_campo -> accion de validacion

        self.setWindowTitle(f"{configuracion.titulo} - {modo.capitalize()}")
        self.resize(*configuracion.tamano_edicion)

        self._crear_titulo()
        self._crear_controles()
        self._crear_botones()
        self._cargar_valores()
        self._configurar_atajos()
        self._validar()
        self._centrar_ventana()

    def _centrar_ventana(self):
        """Siempre centrada: sobre la ventana padre si existe, sino pantalla."""
        if self.parentWidget() is not None and self.parentWidget().isVisible():
            geometria = self.parentWidget().geometry()
        else:
            pantalla = self.screen()
            if pantalla is None:
                return
            geometria = pantalla.availableGeometry()
        self.move(geometria.center() - self.rect().center())

    def _crear_titulo(self):
        """Encabezado de la ventana de edicion."""
        self.lbl_titulo_edicion = QLabel(self.configuracion.titulo)
        self.lbl_titulo_edicion.setObjectName("lbl_titulo_edicion")

        self.lbl_mensaje_edicion = QLabel(
            "Ctrl+G: Aceptar   |   Ctrl+Q: Cancelar   |   Enter: siguiente campo"
        )
        self.lbl_mensaje_edicion.setObjectName("lbl_mensaje_edicion")

    # ---------------------------------------------------------------
    #   Construccion dinamica de los campos
    # ---------------------------------------------------------------
    def _crear_controles(self):
        formulario = QFormLayout()
        formulario.setLabelAlignment(Qt.AlignRight)
        formulario.setSpacing(4)  # minimo espacio entre filas

        for campo in self.configuracion.campos_visibles_edicion():
            control = self._crear_control(campo)
            self.controles[campo.nombre] = control

            # Placeholder y burbuja de ayuda (texto del tooltip).
            if isinstance(control, QLineEdit) and campo.tooltip:
                control.setPlaceholderText(campo.tooltip)
            if campo.tooltip:
                control.setToolTip(campo.tooltip)

            fila = control
            if campo.tipo_control == "referencia":
                fila = self._configurar_referencia(campo, control)

            etiqueta = QLabel(campo.etiqueta)
            formulario.addRow(etiqueta, fila)

            # Enter dentro de un control: pasar al siguiente campo.
            control.installEventFilter(self)
            if isinstance(control, QWidget):
                for hijo in control.findChildren(QWidget):
                    hijo.installEventFilter(self)

        # El formulario ocupa todo el espacio de la ventana.
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        # Margenes finos para un diseno compacto.
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        layout.addWidget(self.lbl_titulo_edicion, 0, Qt.AlignCenter)
        layout.addWidget(self.lbl_mensaje_edicion, 0, Qt.AlignCenter)
        layout.addSpacing(4)
        layout.addLayout(formulario)
        layout.addStretch()
        self.setLayout(layout)

    def _crear_control(self, campo):
        """Crea el widget de entrada segun el tipo de control."""
        if campo.tipo_control == "checkbox":
            control = QCheckBox()
            control.setEnabled(campo.editable)
            control.toggled.connect(self._validar)
            return control

        if campo.tipo_control == "fecha":
            control = QDateEdit()
            control.setCalendarPopup(True)
            control.setDisplayFormat("dd/MM/yyyy")
            control.setDate(QDate.currentDate())
            control.setReadOnly(not campo.editable)
            control.dateChanged.connect(self._validar)
            return control

        # QLineEdit para texto, entero, decimal y referencia.
        control = QLineEdit()
        control.setReadOnly(not campo.editable)
        if campo.longitud:
            control.setMaxLength(campo.longitud)
        if campo.tipo_control == "entero":
            control.setValidator(QIntValidator(0, 2147483647))
        elif campo.tipo_control == "decimal":
            control.setValidator(QDoubleValidator(0.0, 1e12, 6))
        control.textChanged.connect(self._validar)

        # El campo de la clave primaria siempre se muestra angosto y los
        # campos con 'ancho' definido respetan ese ancho.
        if campo.ancho:
            control.setFixedWidth(campo.ancho)
        elif campo.nombre == self.configuracion.clave_primaria:
            control.setFixedWidth(120)
        return control

    def _configurar_referencia(self, campo, control):
        """
        Iconos dentro del campo de referencia:
        izquierda = Limpiar, derecha = Buscar (tambien con Ctrl+Enter).
        """
        control.setReadOnly(True)

        accion_limpiar = control.addAction(
            ICONO_LIMPIAR(), QLineEdit.ActionPosition.LeadingPosition
        )
        accion_limpiar.triggered.connect(
            lambda: self._limpiar_referencia(campo, control)
        )
        accion_limpiar.setToolTip("Limpiar esta referencia")

        accion_buscar = control.addAction(
            ICONO_BUSCAR(), QLineEdit.ActionPosition.TrailingPosition
        )
        accion_buscar.triggered.connect(
            lambda: self._buscar_referencia(campo, control)
        )
        accion_buscar.setToolTip("Buscar registro de referencia (Ctrl+Enter)")

        return control

    def _crear_botones(self):
        self.btn_aceptar = QPushButton(ICONO_ACEPTAR(), "Aceptar")
        self.btn_aceptar.setObjectName("btn_guardar")
        self.btn_aceptar.setToolTip("Guardar los cambios (Ctrl+G)")
        self.btn_aceptar.clicked.connect(self._aceptar)

        self.btn_cancelar = QPushButton(ICONO_CANCELAR(), "Cancelar")
        self.btn_cancelar.setToolTip("Cancelar sin guardar (Ctrl+Q)")
        self.btn_cancelar.clicked.connect(self.reject)

        # Botonera al estilo GtkButtonBox (END): a la derecha, espacio minimo.
        botonera = QHBoxLayout()
        botonera.setSpacing(3)
        botonera.setContentsMargins(5, 5, 5, 5)
        botonera.addStretch()
        botonera.addWidget(self.btn_aceptar)
        botonera.addWidget(self.btn_cancelar)
        self.layout().addLayout(botonera)

    def _configurar_atajos(self):
        QShortcut(QKeySequence("Ctrl+G"), self, self._aceptar)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.reject)

    # ---------------------------------------------------------------
    #   Carga de valores y sugerencia de codigo
    # ---------------------------------------------------------------
    def _cargar_valores(self):
        # Nuevo: se sugiere el siguiente codigo si esta configurado.
        if self.modo == "nuevo" and self.configuracion.calcular_siguiente_codigo:
            self._sugerir_codigo()

        for campo in self.configuracion.campos_visibles_edicion():
            valor = self.valores_originales.get(campo.nombre,
                                                campo.valor_predeterminado)
            self._setear_valor(campo, valor)

            # En edicion, la clave primaria no se puede modificar.
            if self.modo == "editar" and campo.nombre == self.configuracion.clave_primaria:
                self.controles[campo.nombre].setReadOnly(True)

        # Las referencias rellenan sus campos de retorno al editar.
        if self.valores_originales:
            self._cargar_referencias_de_retorno()

        # Foco en el primer campo para cargar datos con el teclado.
        primeros = self.configuracion.campos_visibles_edicion()
        if primeros:
            self.controles[primeros[0].nombre].setFocus()

    def _sugerir_codigo(self):
        try:
            siguiente = self.repository.calcular_siguiente_codigo()
        except Exception as error:
            Mensajes.error(self, error)
            return
        campo = self.configuracion.campo_siguiente_codigo()
        if campo is not None:
            self._setear_valor(campo, siguiente)

    def _setear_valor(self, campo, valor):
        control = self.controles.get(campo.nombre)
        if control is None or valor is None:
            return
        if campo.tipo_control == "checkbox":
            control.setChecked(bool(valor))
        elif campo.tipo_control == "fecha":
            fecha = QDate.fromString(str(valor), "yyyy-MM-dd")
            if fecha.isValid():
                control.setDate(fecha)
        else:
            control.setText(str(valor))

    def _cargar_referencias_de_retorno(self):
        """Rellena los campos de retorno de cada referencia al editar."""
        for campo in self.configuracion.campos_visibles_edicion():
            if campo.tipo_control != "referencia":
                continue
            control = self.controles[campo.nombre]
            clave = self.valores_originales.get(campo.nombre)
            if not clave:
                continue
            referencia = campo.referencia
            repositorio = RepositorioGenerico(
                referencia.modulo, filtro=referencia.filtro
            )
            try:
                registro = repositorio.obtener_por_clave(clave)
            except Exception:
                registro = None
            if registro:
                self._pegar_referencia(campo, control, registro)

    # ---------------------------------------------------------------
    #   Referencias / "pegar"
    # ---------------------------------------------------------------
    def _buscar_referencia(self, campo, control):
        """Abre la ventana de seleccion y pega el registro elegido."""
        referencia = campo.referencia

        def al_elegir(registro):
            # La clave de la referencia y los campos de retorno se copian.
            self._pegar_referencia(campo, control, registro)
            self._validar()

        # Import diferido: evita un ciclo de imports entre las ventanas.
        from vistas.ventana_seleccion import VentanaSeleccion

        self.ventana_busqueda = VentanaSeleccion(
            referencia.modulo, al_elegir, filtro=referencia.filtro
        )
        self.ventana_busqueda.show()
    def _pegar_referencia(self, campo, control, registro):
        """Copia la clave y los valores de retorno en el formulario."""
        control.setText(str(registro.get(campo.referencia.campo_clave, "")))
        for campo_destino, campo_origen in campo.referencia.campos_retorno.items():
            control_destino = self.controles.get(campo_destino)
            if control_destino is not None:
                self._setear_valor(
                    self.configuracion.obtener_campo(campo_destino),
                    registro.get(campo_origen),
                )

    def _limpiar_referencia(self, campo, control):
        control.clear()
        for campo_destino in campo.referencia.campos_retorno:
            control_destino = self.controles.get(campo_destino)
            if control_destino is not None:
                control_destino.clear()
        self._validar()

    # ---------------------------------------------------------------
    #   Validacion y guardado
    # ---------------------------------------------------------------
    def _validar(self):
        """Habilita Aceptar solo cuando los obligatorios son validos y
        muestra un icono de "ok" en cada campo valido."""
        valido = True
        for campo in self.configuracion.campos_visibles_edicion():
            if campo.obligatorio and not self._campo_valido(campo):
                valido = False
            self._actualizar_icono_validacion(campo)
        self.btn_aceptar.setEnabled(valido)
        return valido

    def _actualizar_icono_validacion(self, campo):
        """Icono verde de confirmacion en QLineEdit validos (no referencias)."""
        if campo.tipo_control == "referencia":
            return
        control = self.controles[campo.nombre]
        if not isinstance(control, QLineEdit):
            return

        accion = self.acciones_validas.get(campo.nombre)
        cumple = campo.obligatorio and self._campo_valido(campo)
        if cumple and accion is None:
            accion = control.addAction(
                ICONO_VALIDO(), QLineEdit.ActionPosition.TrailingPosition
            )
            accion.setToolTip("Campo valido")
            self.acciones_validas[campo.nombre] = accion
        elif not cumple and accion is not None:
            control.removeAction(accion)
            self.acciones_validas.pop(campo.nombre, None)

    def _campo_valido(self, campo):
        control = self.controles[campo.nombre]
        if campo.tipo_control == "checkbox":
            return control.isChecked()
        texto = control.text().strip()
        if not texto:
            return False
        if campo.tipo_control == "entero":
            return self._es_entero(texto)
        if campo.tipo_control == "decimal":
            return self._es_decimal(texto)
        return True

    @staticmethod
    def _es_entero(texto):
        try:
            int(texto)
            return True
        except ValueError:
            return False

    @staticmethod
    def _es_decimal(texto):
        try:
            float(texto)
            return True
        except ValueError:
            return False

    def _aceptar(self):
        if not self._validar():
            Mensajes.advertencia(
                self, "Validacion", "Complete correctamente los campos obligatorios."
            )
            return

        valores = self._recoger_valores()
        try:
            if self.modo == "editar":
                clave = self.valores_originales[self.configuracion.clave_primaria]
                self.repository.actualizar(clave, valores)
            else:
                self.repository.insertar(valores)
        except Exception as error:
            Mensajes.error(self, error)
            return
        self.accept()

    def _recoger_valores(self):
        """Junta los valores de los controles en un dict {campo: valor}."""
        valores = {}
        for campo in self.configuracion.campos_que_se_guardan():
            control = self.controles.get(campo.nombre)
            if control is None:
                continue
            if campo.tipo_control == "checkbox":
                valores[campo.nombre] = control.isChecked()
            elif campo.tipo_control == "fecha":
                valores[campo.nombre] = control.date().toString("yyyy-MM-dd")
            else:
                texto = control.text().strip()
                if campo.tipo is int:
                    valores[campo.nombre] = int(texto) if texto else None
                elif campo.tipo is float:
                    valores[campo.nombre] = float(texto) if texto else None
                else:
                    valores[campo.nombre] = texto
        return valores

    # ---------------------------------------------------------------
    #   Teclado dentro de los campos
    # ---------------------------------------------------------------
    def eventFilter(self, objeto, evento):
        """Enter: siguiente campo; Ctrl+Enter en referencia: buscar.
        Al enfocar un campo, muestra su ayuda en el label de estado."""
        if evento.type() == QEvent.KeyPress and evento.key() in (Qt.Key_Return, Qt.Key_Enter):
            campo = self._campo_del_control(objeto)
            if campo and campo.tipo_control == "referencia" and evento.modifiers() & Qt.ControlModifier:
                self._buscar_referencia(campo, self.controles[campo.nombre])
                return True
            if self._es_ultimo_campo(objeto):
                # En el ultimo campo, Enter lleva al boton Aceptar.
                self.btn_aceptar.setFocus()
            else:
                self.focusNextChild()
            return True

        if evento.type() == QEvent.FocusIn:
            self._mostrar_ayuda_campo(self._campo_del_control(objeto))
        elif evento.type() == QEvent.FocusOut:
            self._mostrar_ayuda_general()
        return super().eventFilter(objeto, evento)

    def _es_ultimo_campo(self, control):
        ultimo = self.configuracion.campos_visibles_edicion()[-1]
        return self._campo_del_control(control) is ultimo

    def _mostrar_ayuda_campo(self, campo):
        """Ayuda dinamica del campo enfocado."""
        if campo is None:
            self._mostrar_ayuda_general()
            return
        if campo.tipo_control == "referencia":
            self.lbl_mensaje_edicion.setText(
                "Referencia a otro mantenimiento: Ctrl+Enter o icono "
                "Buscar para elegir registro, icono Limpiar para borrar"
            )
            return
        if campo.tipo is int:
            tipo = "entero"
        elif campo.tipo is float:
            tipo = "decimal"
        elif campo.tipo is bool:
            tipo = "Si/No"
        else:
            tipo = "alfanumerico"
        obligatorio = "obligatorio" if campo.obligatorio else "opcional"
        mensaje = f"Tipo {tipo} - {obligatorio}"
        if campo.tooltip:
            mensaje += f" | {campo.tooltip}"
        self.lbl_mensaje_edicion.setText(mensaje)

    def _mostrar_ayuda_general(self):
        self.lbl_mensaje_edicion.setText(
            "Ctrl+G: Aceptar   |   Ctrl+Q: Cancelar   |   Enter: siguiente campo"
        )

    def _campo_del_control(self, control):
        for nombre, candidato in self.controles.items():
            if candidato is control:
                return self.configuracion.obtener_campo(nombre)
            if isinstance(candidato, QWidget) and control in candidato.findChildren(QWidget):
                return self.configuracion.obtener_campo(nombre)
        return None