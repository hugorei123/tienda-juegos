from PySide6.QtCore import Qt

from vistas.ventana_navegacion import VentanaNavegacion


class VentanaSeleccion(VentanaNavegacion):
    """
    Misma navegacion, pero en modo "pegar":
    el usuario elige UNA fila (Enter o doble clic) y el registro
    se entrega al formulario que pidio la busqueda.

    Uso:
        ventana = VentanaSeleccion(configuracion_categorias, al_elegir)
        ventana.show()

    La ventana bloquea el formulario padre (modalidad de ventana).
    """

    def __init__(self, configuracion, al_seleccionar, filtro=None):
        super().__init__(configuracion, al_seleccionar=al_seleccionar, filtro=filtro)
        # No permite interactuar con el formulario hasta elegir o cerrar.
        self.setWindowModality(Qt.WindowModal)