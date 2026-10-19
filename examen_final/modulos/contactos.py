from nucleo.campo_config import ConfiguracionCampo
from nucleo.modulo_config import ConfiguracionModulo
from nucleo.referencia_config import ConfiguracionReferencia


configuracion_contactos = ConfiguracionModulo(
    titulo="Contactos",
    tabla="contactos",
    clave_primaria="cto_cod",
    buscar_por="cto_razonsocial",
    orden_por="cto_razonsocial",
    campos=[
        ConfiguracionCampo(
            nombre="cto_cod", etiqueta="Código", tipo=int, obligatorio=True
        ),
        ConfiguracionCampo(
            nombre="cto_razonsocial", etiqueta="Razón social", obligatorio=True
        ),
        ConfiguracionCampo(nombre="cto_ruc", etiqueta="RUC"),
        ConfiguracionCampo(
            nombre="cto_direccion", etiqueta="Dirección", visible_navegacion=False
        ),
        ConfiguracionCampo(
            nombre="cto_telef", etiqueta="Teléfono", visible_navegacion=False
        ),
        ConfiguracionCampo(
            nombre="gcto_cod", etiqueta="Grupo", tipo=int, visible_navegacion=False
        ),
    ],
)

referencia_clientes = ConfiguracionReferencia(
    modulo=configuracion_contactos,
    campo_clave="cto_cod",
    campos_retorno={"cliente_razonsocial": "cto_razonsocial"},
    filtro={"gcto_cod": 1},
)