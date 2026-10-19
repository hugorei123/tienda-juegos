from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from modulos.usuarios import configuracion_usuarios  # type: ignore[reportMissingImports]
from nucleo.mensajes import Mensajes
from nucleo.repositorio_generico import RepositorioGenerico
from nucleo.seguridad import verificar_clave


class VentanaLogin(QDialog):
    """
    Control de acceso al sistema: pide login y clave.
    La clave se verifica contra el valor encriptado guardado en la base
    (nunca se compara en texto plano).
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acceso al Sistema")
        self.setFixedWidth(360)
        self.repository = RepositorioGenerico(configuracion_usuarios)
        self.usuario = None  # registro del usuario que ingreso, si corresponde

        self._crear_widgets()
        self._crear_atajos()
        self.txt_login.installEventFilter(self)
        self.txt_clave.installEventFilter(self)
        self.txt_login.setFocus()

    def _crear_widgets(self):
        formulario = QFormLayout()
        formulario.setSpacing(8)

        titulo = QLabel("SISTEMA DE GESTION")
        titulo.setObjectName("lbl_titulo_login")
        formulario.addRow(titulo)

        self.txt_login = QLineEdit()
        self.txt_login.setPlaceholderText("Usuario")
        formulario.addRow(QLabel("Login:"), self.txt_login)

        self.txt_clave = QLineEdit()
        self.txt_clave.setPlaceholderText("Clave de acceso")
        self.txt_clave.setEchoMode(QLineEdit.Password)
        self.txt_clave.returnPressed.connect(self._ingresar)
        formulario.addRow(QLabel("Clave:"), self.txt_clave)

        self.btn_ingresar = QPushButton("Ingresar")
        self.btn_ingresar.setObjectName("btn_guardar")
        self.btn_ingresar.clicked.connect(self._ingresar)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        botonera = QHBoxLayout()
        botonera.setSpacing(6)
        botonera.addStretch()
        botonera.addWidget(self.btn_ingresar)
        botonera.addWidget(self.btn_cancelar)

        contenedor = QVBoxLayout(self)
        contenedor.setContentsMargins(20, 20, 20, 20)
        contenedor.addLayout(formulario)
        contenedor.addSpacing(8)
        contenedor.addLayout(botonera)

    def _crear_atajos(self):
        QShortcut(QKeySequence("Ctrl+G"), self, self._ingresar)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.reject)

    def eventFilter(self, objeto, evento):
        if evento.type() == QEvent.KeyPress and evento.key() in (Qt.Key_Return, Qt.Key_Enter):
            if objeto is self.txt_login:
                if self.txt_login.text().strip():
                    self.txt_clave.setFocus()
                    self.txt_clave.selectAll()
                else:
                    self.txt_login.setFocus()
                return True

            if objeto is self.txt_clave:
                if not self.txt_login.text().strip() or not self.txt_clave.text():
                    Mensajes.advertencia(self, "Acceso", "Ingrese el login y la clave.")
                    if not self.txt_login.text().strip():
                        self.txt_login.setFocus()
                    else:
                        self.txt_clave.setFocus()
                    return True
                self._ingresar()
                return True

        return super().eventFilter(objeto, evento)

    def _ingresar(self):
        """Valida login y clave contra la base de datos."""
        login = self.txt_login.text().strip()
        clave = self.txt_clave.text()
        if not login or not clave:
            Mensajes.advertencia(
                self, "Acceso", "Ingrese el login y la clave."
            )
            return

        try:
            registros = self.repository.buscar_exacto(login, "login")
        except Exception as error:
            Mensajes.error(self, error)
            return

        if not registros or not verificar_clave(clave, registros[0]["clave_acceso"]):
            Mensajes.advertencia(
                self, "Acceso", "Login o clave incorrectos."
            )
            self.txt_clave.clear()
            self.txt_clave.setFocus()
            return

        self.usuario = registros[0]
        self.accept()
