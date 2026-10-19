from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QMainWindow

from configuracion.base_datos import CONFIG
from modulos.configuracion_sistema import MODULOS, NOMBRE_MENU_PROCESOS, PROCESOS
from nucleo.mensajes import Mensajes
from vistas.ventana_caja import VentanaCaja
from vistas.ventana_navegacion import VentanaNavegacion
from vistas.ventana_ajuste_stock import VentanaAjusteStock
from vistas.ventana_stock import VentanaStock


class VentanaPrincipal(QMainWindow):
    """
    Ventana raiz del sistema: menu que abre cualquier modulo registrado.
    Para agregar un mantenimiento nuevo solo se anade UNA entrada en
    MODULOS (modulos/configuracion_sistema.py).
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion de Juegos de mesa")
        self.resize(760, 440)

        # Guarda las ventanas abiertas para que no las recoja el GC.
        self.ventanas_abiertas = []
        self.ventanas_procesos = []

        self._crear_menu()
        self._crear_contenido()
        self._mostrar_estado_conexion()
        self._centrar_en_pantalla()

    def _centrar_en_pantalla(self):
        """La ventana principal tambien se abre siempre centrada."""
        pantalla = self.screen()
        if pantalla is None:
            return
        geometria = pantalla.availableGeometry()
        self.move(geometria.center() - self.rect().center())

    def _crear_menu(self):
        """Construye el menu a partir del registro de modulos.
        Cada grupo puede tener un submenu (ej: Registros > Items > Categorias)."""
        grupos_por_menu = {}
        for grupo in MODULOS:
            grupos_por_menu.setdefault(grupo["menu"], []).append(grupo)

        for nombre_menu, grupos in grupos_por_menu.items():
            menu = self.menuBar().addMenu(nombre_menu)
            for grupo in grupos:
                destino = menu
                if grupo.get("submenu"):
                    destino = menu.addMenu(grupo["submenu"])
                for titulo, configuracion in grupo["items"]:
                    accion = QAction(titulo, self)
                    # configuracion se captura para cada accion del menu.
                    accion.triggered.connect(
                        lambda marcado=False, c=configuracion: self._abrir_modulo(c)
                    )
                    destino.addAction(accion)

        menu_procesos = self.menuBar().addMenu(NOMBRE_MENU_PROCESOS)
        for titulo, ventana_clase in PROCESOS:
            accion = QAction(titulo, self)
            accion.triggered.connect(
                lambda marcado=False, clase=ventana_clase: self._abrir_proceso(clase)
            )
            menu_procesos.addAction(accion)

        menu_consultas = self.menuBar().addMenu("Consultas")
        accion_stock = QAction("Stock", self)
        accion_stock.triggered.connect(
            lambda marcado=False: self._abrir_proceso(VentanaStock)
        )
        menu_consultas.addAction(accion_stock)
        accion_ajuste_stock = QAction("Ajuste de stock", self)
        accion_ajuste_stock.triggered.connect(
            lambda marcado=False: self._abrir_proceso(VentanaAjusteStock)
        )
        menu_consultas.addAction(accion_ajuste_stock)
        accion_caja = QAction("Caja", self)
        accion_caja.triggered.connect(
            lambda marcado=False: self._abrir_proceso(VentanaCaja)
        )
        menu_consultas.addAction(accion_caja)

        menu_herramientas = self.menuBar().addMenu("Herramientas")

        accion_acerca = QAction("Acerca de...", self)
        accion_acerca.triggered.connect(self._acerca_de)
        menu_herramientas.addAction(accion_acerca)

        menu_salir = self.menuBar().addMenu("Salir")
        accion_salir = QAction("Salir del sistema", self)
        accion_salir.triggered.connect(self.close)
        menu_salir.addAction(accion_salir)

    def _crear_contenido(self):
        etiqueta = QLabel("Sistema de Gestion de Juegos de mesa")
        etiqueta.setObjectName("bienvenida")
        etiqueta.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(etiqueta)

    def _abrir_modulo(self, configuracion):
        ventana = VentanaNavegacion(configuracion)
        self.ventanas_abiertas.append(ventana)
        ventana.show()
        ventana.raise_()

    def _abrir_proceso(self, ventana_clase):
        ventana = ventana_clase(self)
        self.ventanas_procesos.append(ventana)
        ventana.show()
        ventana.raise_()

    def _acerca_de(self):
        Mensajes.informacion(
            self,
            "Acerca de",
            "Plantilla base de desarrollo - Lenguaje de Programacion II\n"
            "PySide6 + PostgreSQL + Psycopg 3 - Hecho por: Hugo, Javier, Guido, Leonel",
        )

    def _mostrar_estado_conexion(self):
        """Estado basico de la conexion, sin exponer la contrasena."""
        self.statusBar().showMessage(
            f"Servidor: {CONFIG['host']} | BD: {CONFIG['dbname']} | "
            f"Usuario: {CONFIG['user']}"
        )