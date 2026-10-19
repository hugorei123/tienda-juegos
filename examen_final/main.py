import sys

from PySide6.QtWidgets import QApplication
from nucleo.sesion import iniciar_sesion
from nucleo.tema import aplicar_tema
from vistas.ventana_login import VentanaLogin
from vistas.ventana_principal import VentanaPrincipal


def main():
    app = QApplication(sys.argv)
    aplicar_tema(app)
    login = VentanaLogin()
    if login.exec() == VentanaLogin.DialogCode.Accepted:
        iniciar_sesion(login.usuario)
        ventana = VentanaPrincipal()
        ventana.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()