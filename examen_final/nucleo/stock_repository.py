from decimal import Decimal, InvalidOperation

from configuracion.base_datos import obtener_conexion


class StockRepository:
    """Consultas de stock y sus movimientos."""

    @staticmethod
    def _cantidad_positiva(cantidad):
        if isinstance(cantidad, bool):
            raise ValueError("La cantidad debe ser un entero mayor a 0.")
        try:
            valor = Decimal(str(cantidad))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValueError(
                "La cantidad debe ser un entero mayor a 0."
            ) from error

        if (
            not valor.is_finite()
            or valor <= 0
            or valor != valor.to_integral_value()
        ):
            raise ValueError("La cantidad debe ser un entero mayor a 0.")
        return int(valor)

    def ajustar_stock(self, codigo_item, cantidad, tipo, motivo, idusuario):
        cantidad = self._cantidad_positiva(cantidad)
        if tipo not in ("COMPRA", "AJUSTE_ENTRADA", "AJUSTE_SALIDA"):
            raise ValueError("Tipo de movimiento no permitido.")
        if tipo in ("AJUSTE_ENTRADA", "AJUSTE_SALIDA") and not str(
            motivo or ""
        ).strip():
            raise ValueError("El motivo es obligatorio para los ajustes.")
        if codigo_item is None:
            raise ValueError("Seleccione un ítem.")

        cantidad_firmada = -cantidad if tipo == "AJUSTE_SALIDA" else cantidad
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """UPDATE item
                       SET stock_actual = stock_actual + %s
                       WHERE codigo = %s AND stock_actual + %s >= 0
                       RETURNING stock_actual""",
                    (cantidad_firmada, codigo_item, cantidad_firmada),
                )
                fila = cursor.fetchone()
                if fila is None:
                    raise ValueError(
                        "Item inexistente o el stock quedaría negativo"
                    )
                stock_resultante = fila[0]
                cursor.execute(
                    """INSERT INTO movimientos_stock
                       (codigo_item, tipo, cantidad, stock_resultante, idusuario,
                        observacion)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        codigo_item,
                        tipo,
                        cantidad_firmada,
                        stock_resultante,
                        idusuario,
                        motivo,
                    ),
                )
            conexion.commit()
            return stock_resultante
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def listar_items(self):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT i.codigo, i.descripcion, c.descripcion,
                              i.stock_actual, i.precio
                       FROM item i
                       JOIN categorias c ON c.codigo = i.codigo_categoria
                       ORDER BY i.descripcion"""
                )
                columnas = (
                    "codigo", "descripcion", "categoria", "stock_actual", "precio"
                )
                return [
                    dict(zip(columnas, fila))
                    for fila in cursor.fetchall()
                ]
        finally:
            conexion.close()

    def listar_movimientos(self, codigo_item):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT m.fecha, m.tipo, m.cantidad, m.stock_resultante,
                              u.nombre_apellido, m.referencia_codigo
                       FROM movimientos_stock m
                       LEFT JOIN usuarios u ON u.idusuario = m.idusuario
                       WHERE m.codigo_item = %s
                       ORDER BY m.fecha DESC""",
                    (codigo_item,),
                )
                columnas = (
                    "fecha", "tipo", "cantidad", "stock_resultante",
                    "usuario", "referencia_codigo",
                )
                return [
                    dict(zip(columnas, fila))
                    for fila in cursor.fetchall()
                ]
        finally:
            conexion.close()
