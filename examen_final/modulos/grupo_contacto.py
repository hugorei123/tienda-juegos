from nucleo.modulo_config import ConfiguracionModulo
from nucleo.campo_config import ConfiguracionCampo

configuracion_grupo_contacto = ConfiguracionModulo(
    titulo="tipos de contacto",
    tabla="grupo_contacto",
    clave_primaria="codigo",
    calcular_siguiente_codigo=False,
    campos=[
        ConfiguracionCampo(nombre="codigo", etiqueta="Código", tipo=str, obligatorio=True, longitud=5),
        ConfiguracionCampo(nombre="descripcion", etiqueta="Descripción", tipo=str, obligatorio=True, longitud=100)
    ]
)