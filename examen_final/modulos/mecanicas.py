"""
Configuracion del modulo MECANICAS (primer ejemplo de la plantilla).
Aquí NO se programa la ventana ni el CRUD: solo se describe la tabla.
"""
from nucleo.modulo_config import ConfiguracionModulo
from nucleo.campo_config import ConfiguracionCampo

configuracion_mecanicas = ConfiguracionModulo(
    titulo="Mecanicas",
    tabla="mecanicas",
    clave_primaria="codigo",
    calcular_siguiente_codigo=True,
    campos=[
        ConfiguracionCampo(nombre="codigo", etiqueta="Código", tipo=int, obligatorio=True),
        ConfiguracionCampo(nombre="descripcion", etiqueta="Descripción", tipo=str, obligatorio=True, longitud=100)
    ]
)