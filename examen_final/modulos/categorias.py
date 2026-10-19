"""
Configuracion del modulo CATEGORIAS.
Aquí NO se programa la ventana ni el CRUD: solo se describe la tabla.
"""
from nucleo.modulo_config import ConfiguracionModulo
from nucleo.campo_config import ConfiguracionCampo

configuracion_categorias = ConfiguracionModulo(
    titulo="Categorias",
    tabla="categorias",
    clave_primaria="codigo",
    calcular_siguiente_codigo=True,
    campos=[
        ConfiguracionCampo(nombre="codigo", etiqueta="Código", tipo=int, obligatorio=True),
        ConfiguracionCampo(nombre="descripcion", etiqueta="Descripción", tipo=str, obligatorio=True, longitud=100)
    ]
)