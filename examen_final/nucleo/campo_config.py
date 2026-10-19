import datetime


class ConfiguracionCampo:
    """
    Describe UN campo de un mantenimiento (una columna de la tabla).
    Todas las ventanas genericas leen esta configuracion para saber
    como dibujar, validar y guardar el campo.
    """

    def __init__(
        self,
        nombre,
        etiqueta,
        tipo=str,
        obligatorio=False,
        editable=True,
        longitud=None,
        ancho=None,
        guardar=True,
        visible_navegacion=True,
        visible_edicion=True,
        alineacion="izquierda",
        tooltip="",
        valor_predeterminado=None,
        autocompletar=False,
        referencia=None,
        tipo_control=None,
        color_celda=None,
    ):
        self.nombre = nombre
        self.etiqueta = etiqueta
        self.tipo = tipo
        self.obligatorio = obligatorio
        self.editable = editable
        self.longitud = longitud
        self.ancho = ancho
        self.guardar = guardar
        self.visible_navegacion = visible_navegacion
        self.visible_edicion = visible_edicion
        self.alineacion = alineacion
        self.tooltip = tooltip
        self.valor_predeterminado = valor_predeterminado
        self.autocompletar = autocompletar
        self.referencia = referencia
        # Color de fondo opcional de la columna en la navegacion.
        self.color_celda = color_celda
        # Control visual derivado del tipo, si no se indico uno explicito.
        self.tipo_control = tipo_control or self._control_por_tipo()

    def _control_por_tipo(self):
        if self.referencia:
            return "referencia"
        if self.tipo is bool:
            return "checkbox"
        if self.tipo is int:
            return "entero"
        if self.tipo is float:
            return "decimal"
        if self.tipo is datetime.date:
            return "fecha"
        return "texto"