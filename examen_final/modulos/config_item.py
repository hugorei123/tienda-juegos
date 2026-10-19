"""
Configuracion del catalogo de juegos de mesa.
"""

import datetime

from nucleo.campo_config import ConfiguracionCampo
from nucleo.modulo_config import ConfiguracionModulo
from nucleo.referencia_config import ConfiguracionReferencia
from modulos.categorias import configuracion_categorias
from modulos.editoriales import configuracion_editoriales
from modulos.mecanicas import configuracion_mecanicas


configuracion_items = ConfiguracionModulo(
    titulo="Items",
    tabla="item",
    clave_primaria="codigo",
    calcular_siguiente_codigo=True,
    buscar_por="descripcion",
    orden_por="descripcion",
    tamano_navegacion=(800, 560),
    tamano_edicion=(700, 700),
    campos=[
        ConfiguracionCampo(
            nombre="codigo",
            etiqueta="Codigo",
            tipo=int,
            obligatorio=True,
            longitud=10,
            ancho=90,
            alineacion="derecha",
        ),
        ConfiguracionCampo(
            nombre="descripcion",
            etiqueta="Descripcion",
            tipo=str,
            obligatorio=True,
            longitud=120,
            ancho=300,
        ),
        ConfiguracionCampo(
            nombre="codigo_categoria",
            etiqueta="Categoria",
            tipo=int,
            obligatorio=True,
            referencia=ConfiguracionReferencia(
                modulo=configuracion_categorias,
                campo_clave="codigo",
            ),
        ),
        ConfiguracionCampo(
            nombre="codigo_editorial",
            etiqueta="Editorial",
            tipo=int,
            obligatorio=True,
            referencia=ConfiguracionReferencia(
                modulo=configuracion_editoriales,
                campo_clave="codigo",
            ),
        ),
        ConfiguracionCampo(
            nombre="codigo_mecanica",
            etiqueta="Mecanica",
            tipo=int,
            obligatorio=True,
            referencia=ConfiguracionReferencia(
                modulo=configuracion_mecanicas,
                campo_clave="codigo",
            ),
        ),
        ConfiguracionCampo(
            nombre="cantidad_min_jugadores",
            etiqueta="Cantidad minima de jugadores",
            tipo=int,
            obligatorio=True,
        ),
        ConfiguracionCampo(
            nombre="cantidad_max_jugadores",
            etiqueta="Cantidad maxima de jugadores",
            tipo=int,
            obligatorio=True,
        ),
        ConfiguracionCampo(
            nombre="edad_minima",
            etiqueta="Edad minima",
            tipo=int,
            obligatorio=True,
        ),
        ConfiguracionCampo(
            nombre="duracion_minutos",
            etiqueta="Duracion (minutos)",
            tipo=int,
            obligatorio=True,
        ),
        ConfiguracionCampo(
            nombre="idioma_dependencia",
            etiqueta="Dependencia del idioma",
            tipo=str,
            obligatorio=True,
            longitud=100,
        ),
        ConfiguracionCampo(
            nombre="stock_actual",
            etiqueta="Stock actual",
            tipo=int,
            obligatorio=True,
        ),
        ConfiguracionCampo(
            nombre="activo",
            etiqueta="Activo",
            tipo=bool,
        ),
        ConfiguracionCampo(
            nombre="precio",
            etiqueta="Precio",
            tipo=float,
            obligatorio=True,
            alineacion="derecha",
        ),
        ConfiguracionCampo(
            nombre="porcentaje_iva",
            etiqueta="Porcentaje IVA",
            tipo=float,
            obligatorio=True,
            alineacion="derecha",
        ),
        ConfiguracionCampo(
            nombre="fecha_alta",
            etiqueta="Fecha de Alta",
            tipo=datetime.date,
            obligatorio=True,
        ),
    ],
)
