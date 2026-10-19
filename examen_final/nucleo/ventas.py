from decimal import Decimal, InvalidOperation

from configuracion.base_datos import obtener_conexion


class VentaRepository:
    """Operaciones transaccionales para ventas e inventario."""

    @staticmethod
    def _normalizar_cantidad(valor):
        try:
            cantidad = Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValueError("La cantidad vendida debe ser un entero positivo.") from error

        if (
            not cantidad.is_finite()
            or cantidad <= 0
            or cantidad != cantidad.to_integral_value()
        ):
            raise ValueError("La cantidad vendida debe ser un entero positivo.")
        return int(cantidad)

    @staticmethod
    def _descontar_stock(
        cursor, codigo_item, cantidad, idusuario, referencia_codigo
    ):
        cursor.execute(
            """UPDATE item
               SET stock_actual = stock_actual - %s
               WHERE codigo = %s AND stock_actual >= %s
               RETURNING stock_actual""",
            (cantidad, codigo_item, cantidad),
        )
        fila = cursor.fetchone()
        if fila is None:
            raise ValueError(
                f"No existe el item {codigo_item} o no hay stock suficiente."
            )
        stock_resultante = fila[0]
        cursor.execute(
            """INSERT INTO movimientos_stock
               (codigo_item, tipo, cantidad, stock_resultante, idusuario,
                referencia_codigo)
               VALUES (%s, 'VENTA', %s, %s, %s, %s)""",
            (
                codigo_item,
                -cantidad,
                stock_resultante,
                idusuario,
                referencia_codigo,
            ),
        )

    def registrar_venta(self, venta, detalles):
        """Inserta una venta confirmada y sus lineas, descontando el stock."""
        if not detalles:
            raise ValueError("No se puede registrar una venta sin detalles.")

        cantidades = [
            self._normalizar_cantidad(detalle["cantidad"])
            for detalle in detalles
        ]
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT nextval(pg_get_serial_sequence('pedidos_venta', 'codigo'))"
                )
                codigo = cursor.fetchone()[0]
                cursor.execute(
                    """INSERT INTO pedidos_venta
                       (codigo, fecha, cod_cliente, idusuario, estado, total)
                       VALUES (%s, %s, %s, %s, 'CONFIRMADO', %s)""",
                    (
                        codigo,
                        venta["fecha"],
                        venta["cod_cliente"],
                        venta["idusuario"],
                        venta["total"],
                    ),
                )

                for nro_item, (detalle, cantidad) in enumerate(
                    zip(detalles, cantidades), start=1
                ):
                    self._descontar_stock(
                        cursor,
                        detalle["codigo_item"],
                        cantidad,
                        venta["idusuario"],
                        codigo,
                    )
                    cursor.execute(
                        """INSERT INTO pedidos_venta_det
                           (codigo_pedido, nro_item, codigo_item, cantidad,
                            precio_unitario)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (
                            codigo,
                            nro_item,
                            detalle["codigo_item"],
                            cantidad,
                            detalle["precio_unitario"],
                        ),
                    )
            conexion.commit()
            return codigo
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def confirmar_pedido(self, codigo, idusuario):
        """Confirma un borrador y descuenta stock dentro de una transaccion."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT estado FROM pedidos_venta WHERE codigo = %s FOR UPDATE",
                    (codigo,),
                )
                pedido = cursor.fetchone()
                if pedido is None or pedido[0] != "BORRADOR":
                    raise ValueError("El pedido no existe o ya fue confirmado.")

                cursor.execute(
                    """SELECT codigo_item, cantidad
                       FROM pedidos_venta_det
                       WHERE codigo_pedido = %s ORDER BY nro_item""",
                    (codigo,),
                )
                detalles = cursor.fetchall()
                if not detalles:
                    raise ValueError("No se puede confirmar un pedido sin detalles.")

                for codigo_item, cantidad in detalles:
                    cantidad_entera = self._normalizar_cantidad(cantidad)
                    self._descontar_stock(
                        cursor, codigo_item, cantidad_entera, idusuario, codigo
                    )

                cursor.execute(
                    """UPDATE pedidos_venta SET estado = 'CONFIRMADO'
                       WHERE codigo = %s AND estado = 'BORRADOR'""",
                    (codigo,),
                )
                if cursor.rowcount == 0:
                    raise ValueError("El pedido no existe o ya fue confirmado.")
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def anular_pedido(self, codigo, idusuario, motivo):
        """Anula un pedido confirmado y repone el stock en una transaccion."""
        if not str(motivo or "").strip():
            raise ValueError("El motivo de anulación es obligatorio.")

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT estado FROM pedidos_venta WHERE codigo = %s FOR UPDATE",
                    (codigo,),
                )
                pedido = cursor.fetchone()
                if pedido is None or pedido[0] != "CONFIRMADO":
                    raise ValueError("Solo se pueden anular pedidos confirmados.")

                cursor.execute(
                    """SELECT COUNT(*), COALESCE(SUM(monto), 0)
                       FROM cobros
                       WHERE codigo_pedido = %s AND anulado = FALSE""",
                    (codigo,),
                )
                cantidad_cobros, monto_cobrado = cursor.fetchone()
                if cantidad_cobros > 0:
                    monto_formateado = Decimal(str(monto_cobrado))
                    raise ValueError(
                        "Anulá primero los cobros del pedido "
                        f"(cobrado: {monto_formateado:.2f})."
                    )

                cursor.execute(
                    """SELECT codigo_item, SUM(cantidad)
                       FROM pedidos_venta_det
                       WHERE codigo_pedido = %s
                       GROUP BY codigo_item
                       ORDER BY codigo_item""",
                    (codigo,),
                )
                detalles = cursor.fetchall()
                if not detalles:
                    raise ValueError("No se puede anular un pedido sin detalles.")

                for codigo_item, cantidad in detalles:
                    cantidad_entera = self._normalizar_cantidad(cantidad)
                    cursor.execute(
                        """UPDATE item
                           SET stock_actual = stock_actual + %s
                           WHERE codigo = %s
                           RETURNING stock_actual""",
                        (cantidad_entera, codigo_item),
                    )
                    fila = cursor.fetchone()
                    if fila is None:
                        raise ValueError(f"No existe el item {codigo_item}.")
                    cursor.execute(
                        """INSERT INTO movimientos_stock
                           (codigo_item, tipo, cantidad, stock_resultante,
                            idusuario, referencia_codigo, observacion)
                           VALUES (%s, 'ANULACION', %s, %s, %s, %s, %s)""",
                        (
                            codigo_item,
                            cantidad_entera,
                            fila[0],
                            idusuario,
                            codigo,
                            motivo.strip(),
                        ),
                    )

                cursor.execute(
                    """UPDATE pedidos_venta SET estado = 'ANULADO'
                       WHERE codigo = %s AND estado = 'CONFIRMADO'""",
                    (codigo,),
                )
                if cursor.rowcount == 0:
                    raise ValueError("Solo se pueden anular pedidos confirmados.")
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()
