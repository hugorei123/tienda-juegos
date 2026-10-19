"""
Configuracion del catalogo de editoriales.
Demuestra que con otra configuracion corta se obtiene otro CRUD completo
sin copiar ventanas ni repositorios.
"""

from nucleo.campo_config import ConfiguracionCampo
from nucleo.modulo_config import ConfiguracionModulo
from nucleo.tema import COLOR_CELDA

configuracion_editoriales = ConfiguracionModulo(
    titulo="Editoriales",
    tabla="editoriales",
    clave_primaria="codigo",
    calcular_siguiente_codigo=True,
    buscar_por="nombre",
    orden_por="nombre",
    tamano_navegacion=(400, 400),   # tamano de la ventana de navegacion
    tamano_edicion=(450, 180),      # tamano de la ventana de edicion
    campos=[
        ConfiguracionCampo(
            nombre="codigo",
            etiqueta="Codigo",
            tipo=int,
            obligatorio=True,
            longitud=10,
            ancho=90,
            alineacion="derecha",
            color_celda=COLOR_CELDA,
            tooltip="Solo numeros. Identificador unico de la editorial",
        ),
        ConfiguracionCampo(
            nombre="nombre",
            etiqueta="Nombre",
            tipo=str,
            obligatorio=True,
            longitud=100,
            ancho=350,
            color_celda=COLOR_CELDA,
            tooltip="Nombre de la editorial (alfanumerico)",
        ),
        ConfiguracionCampo(
            nombre="importado",
            etiqueta="Importado",
            tipo=bool,
            tooltip="Marque si la editorial es importada",
        ),
    ],
)