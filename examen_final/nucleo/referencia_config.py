class ConfiguracionReferencia:
    """
    Permite "pegar" un registro de OTRO mantenimiento en este formulario.

    Ejemplo (campo referencia en un catalogo):
        ConfiguracionReferencia(
            modulo=configuracion_categorias,
            campo_clave="codigo",
            campos_retorno={
                "codigo_categoria": "codigo",       # este_formulario: otro_modulo
                "descripcion_categoria": "descripcion",
            },
        )

    Al elegir una categoria en la VentanaSeleccion, el campo de referencia
    guarda la clave y los campos de retorno reciben los valores copiados.
    """

    def __init__(self, modulo, campo_clave="codigo", campos_retorno=None, filtro=None):
        self.modulo = modulo
        self.campo_clave = campo_clave
        self.campos_retorno = campos_retorno or {}
        self.filtro = dict(filtro or {})