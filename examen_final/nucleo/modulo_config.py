from nucleo.campo_config import ConfiguracionCampo


class ConfiguracionModulo:
    """
    Describe un mantenimiento completo: tabla, campos y comportamientos.
    Con SOLO esta configuracion se construyen las tres ventanas genericas
    (Navegacion, Edicion y Seleccion) y el RepositorioGenerico.
    """

    def __init__(
        self,
        titulo,
        tabla,
        clave_primaria="codigo",
        campos=None,
        buscar_por=None,
        orden_por=None,
        orden_desc=False,
        tamano_navegacion=(900, 520),
        tamano_edicion=(560, 460),
        calcular_siguiente_codigo=False,
        campo_codigo=None,
        campo_secreto=None,  # campo que se encripta al guardar (claves)
        validacion=None,
        permitir_nuevo=True,
        permitir_editar=True,
        permitir_eliminar=True,
        permitir_duplicar=True,
        permitir_imprimir=True,
    ):
        self.titulo = titulo
        self.tabla = tabla
        self.clave_primaria = clave_primaria
        self.campos = campos or []
        self.buscar_por = buscar_por or (self.campos[0].nombre if self.campos else "")
        self.orden_por = orden_por or self.clave_primaria
        self.orden_desc = orden_desc
        self.tamano_navegacion = tamano_navegacion
        self.tamano_edicion = tamano_edicion
        self.calcular_siguiente_codigo = calcular_siguiente_codigo
        self.campo_codigo = campo_codigo
        self.campo_secreto = campo_secreto
        self.validacion = validacion
        self.permitir_nuevo = permitir_nuevo
        self.permitir_editar = permitir_editar
        self.permitir_eliminar = permitir_eliminar
        self.permitir_duplicar = permitir_duplicar
        self.permitir_imprimir = permitir_imprimir

    # --- Helpers usados por las ventanas y el repositorio ---

    def obtener_campo(self, nombre):
        for campo in self.campos:
            if campo.nombre == nombre:
                return campo
        return None

    def campos_que_se_guardan(self):
        return [c for c in self.campos if c.guardar]

    def campos_visibles_navegacion(self):
        return [c for c in self.campos if c.visible_navegacion]

    def campos_visibles_edicion(self):
        return [c for c in self.campos if c.visible_edicion]

    def campo_siguiente_codigo(self):
        """Campo donde se autocompleta el proximo codigo (si esta activo)."""
        if self.campo_codigo:
            return self.obtener_campo(self.campo_codigo)
        return self.obtener_campo(self.clave_primaria)