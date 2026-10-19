"""
Registro central de modulos: de aqui sale el menu de la aplicacion.
Cada grupo es un menu (y opcionalmente un submenu) con sus items.
Agregar un mantenimiento nuevo = 1 entrada en el grupo correspondiente.
"""

from modulos.contactos import configuracion_contactos
from modulos.categorias import configuracion_categorias
from modulos.config_item import configuracion_items
from modulos.mecanicas import configuracion_mecanicas
from modulos.grupo_contacto import configuracion_grupo_contacto
from modulos.timbrados import configuracion_timbrados
from modulos.tipos_documentos import configuracion_tipos_documentos
from modulos.usuarios import configuracion_usuarios
from vistas.ventana_pedidos_listado import VentanaPedidosListado
from modulos.editoriales import configuracion_editoriales

NOMBRE_MENU_PROCESOS = "Facturación y Ventas"
PROCESOS = [
    ("Pedido de Venta", VentanaPedidosListado),
]

MODULOS = [
    {
        "menu": "Registros",
        "submenu": "Sistema General",
        "items": [
            ("Tipos de Documentos", configuracion_tipos_documentos),
            ("Timbrados", configuracion_timbrados),
            ("Usuarios", configuracion_usuarios),
        ],
    },
    {
        "menu": "Registros",
        "submenu": "Grupo de contactos",
        "items": [
            ("Tipos de contactos", configuracion_grupo_contacto),
            ("Contactos", configuracion_contactos),
        ],
    },
    {
        "menu": "Registros",
        "submenu": "Items",
        "items": [
            ("Categorias", configuracion_categorias),
            ("Editoriales", configuracion_editoriales),
            ("Mecanicas", configuracion_mecanicas),
            ("Items", configuracion_items),
        ],
    },
]