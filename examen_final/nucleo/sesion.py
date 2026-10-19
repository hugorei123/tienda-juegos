_usuario_actual = None


def iniciar_sesion(usuario):
    """Guarda el registro del usuario autenticado durante la ejecucion."""
    global _usuario_actual
    _usuario_actual = usuario


def obtener_usuario():
    """Devuelve el usuario autenticado, o None si no hay sesion activa."""
    return _usuario_actual