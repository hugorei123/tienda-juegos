from nucleo.campo_config import ConfiguracionCampo
from nucleo.modulo_config import ConfiguracionModulo
from nucleo.tema import COLOR_CELDA

configuracion_usuarios = ConfiguracionModulo(
    titulo="Usuarios",
    tabla="usuarios",
    clave_primaria="idusuario",
    calcular_siguiente_codigo=True,
    buscar_por="login",
    orden_por="login",
    campo_secreto="clave_acceso",  # se encripta al guardar
    campos=[
        ConfiguracionCampo(
            nombre="idusuario",
            etiqueta="Codigo",
            tipo=int,
            obligatorio=True,
            longitud=10,
            ancho=90,
            alineacion="derecha",
            color_celda=COLOR_CELDA,
            tooltip="Solo numeros. Identificador unico del usuario",
        ),
        ConfiguracionCampo(
            nombre="nombre_apellido",
            etiqueta="Nombre y Apellido",
            tipo=str,
            obligatorio=True,
            longitud=100,
            ancho=260,
            color_celda=COLOR_CELDA,
            tooltip="Nombre y apellido del usuario",
        ),
        ConfiguracionCampo(
            nombre="login",
            etiqueta="Login",
            tipo=str,
            obligatorio=True,
            longitud=30,
            ancho=120,
            tooltip="Nombre de usuario para entrar al sistema",
        ),
        ConfiguracionCampo(
            nombre="clave_acceso",
            etiqueta="Clave",
            tipo=str,
            obligatorio=True,
            longitud=64,
            ancho=140,
            visible_navegacion=False,  # el hash no se muestra en la lista
            tooltip="Clave de acceso (se guarda encriptada)",
        ),
    ],
)