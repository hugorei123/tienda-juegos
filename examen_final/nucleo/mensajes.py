from PySide6.QtWidgets import QMessageBox


class Mensajes:
    """
    Utilidad unica de mensajes: evita repetir codigo de QMessageBox
    en cada modulo o ventana.
    """

    @staticmethod
    def informacion(padre, titulo, texto):
        QMessageBox.information(padre, titulo, texto)

    @staticmethod
    def advertencia(padre, titulo, texto):
        QMessageBox.warning(padre, titulo, texto)

    @staticmethod
    def error(padre, error):
        # El detalle tecnico queda en consola (para desarrollo) y el
        # usuario final ve un mensaje claro sin traceback completo.
        print("ERROR:", error)
        QMessageBox.critical(padre, "Error", str(error))

    @staticmethod
    def confirmar(padre, titulo, pregunta, texto_detalle=""):
        """Pregunta de confirmacion; devuelve True si el usuario acepta."""
        mensaje = f"{pregunta}\n\n{texto_detalle}" if texto_detalle else pregunta
        respuesta = QMessageBox.question(padre, titulo, mensaje)
        return respuesta == QMessageBox.Yes