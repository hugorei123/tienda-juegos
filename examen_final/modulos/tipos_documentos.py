"""
Configuracion del modulo TIPOS DE DOCUMENTOS.
Mantenimiento simple de tipos de documentos.
"""

from nucleo.campo_config import ConfiguracionCampo
from nucleo.modulo_config import ConfiguracionModulo
from nucleo.tema import COLOR_CELDA

configuracion_tipos_documentos = ConfiguracionModulo(
    titulo="Tipos de Documentos",
    tabla="tipos_documentos",
    clave_primaria="codigo",
    calcular_siguiente_codigo=True,
    buscar_por="descripcion",
    orden_por="descripcion",
    tamano_navegacion=(400, 400),
    tamano_edicion=(420, 200),
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
            tooltip="Solo numeros. Identificador unico",
        ),
        ConfiguracionCampo(
            nombre="descripcion",
            etiqueta="Descripcion",
            tipo=str,
            obligatorio=True,
            longitud=80,
            ancho=260,
            color_celda=COLOR_CELDA,
            tooltip="Descripcion del tipo de documento",
        ),
        ConfiguracionCampo(
            nombre="abreviatura",
            etiqueta="Abreviatura",
            tipo=str,
            obligatorio=True,
            longitud=10,
            ancho=100,
            tooltip="Sigla del tipo de documento (ej: FAC)",
        ),
        ConfiguracionCampo(
            nombre="activo",
            etiqueta="Activo",
            tipo=bool,
            tooltip="Marque si el tipo de documento esta activo",
        ),
    ],
)