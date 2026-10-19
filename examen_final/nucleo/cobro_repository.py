from decimal import Decimal, InvalidOperation

from configuracion.base_datos import obtener_conexion


class CobroRepository:
    """Consultas y operaciones transaccionales de cobros."""

    @staticmethod
    def _a_decimal(valor):
        return valor if isinstance(valor, Decimal) else Decimal(str(valor))

    @staticmethod
    def _validar_monto(valor):
        try:
            monto = CobroRepository._a_decimal(valor)
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValueError("Ingrese un monto válido para el cobro.") from error
        if not monto.is_finite() or monto <= 0:
            raise ValueError("El monto del cobro debe ser mayor a 0.")
        return monto

    def saldo_pedido(self, codigo_pedido):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT p.total,
                              COALESCE(SUM(c.monto), 0)
                       FROM pedidos_venta p
                       LEFT JOIN cobros c
                         ON c.codigo_pedido = p.codigo
                        AND c.anulado IS FALSE
                       WHERE p.codigo = %s
                       GROUP BY p.codigo, p.total""",
                    (codigo_pedido,),
                )
                fila = cursor.fetchone()
                if fila is None:
                    raise ValueError("El pedido no existe.")
                total = self._a_decimal(fila[0])
                cobrado = self._a_decimal(fila[1])
            conexion.commit()
            return {
                "total": total,
                "cobrado": cobrado,
                "saldo": total - cobrado,
            }
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def listar_cobros_pedido(self, codigo_pedido):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT c.codigo, mp.descripcion, c.monto, c.fecha,
                              u.nombre_apellido, c.anulado, c.referencia,
                              c.observacion
                       FROM cobros c
                       LEFT JOIN medios_pago mp
                         ON mp.codigo = c.codigo_medio_pago
                       LEFT JOIN usuarios u
                         ON u.idusuario = c.idusuario
                       WHERE c.codigo_pedido = %s
                       ORDER BY c.fecha DESC, c.codigo DESC""",
                    (codigo_pedido,),
                )
                columnas = (
                    "codigo", "medio_pago", "monto", "fecha", "usuario",
                    "anulado", "referencia", "observacion",
                )
                cobros = [
                    dict(zip(columnas, fila)) for fila in cursor.fetchall()
                ]
            conexion.commit()
            return cobros
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def registrar_cobro(
        self, codigo_pedido, codigo_medio_pago, monto, referencia, idusuario
    ):
        monto = self._validar_monto(monto)
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT estado, total
                       FROM pedidos_venta
                       WHERE codigo = %s
                       FOR UPDATE""",
                    (codigo_pedido,),
                )
                pedido = cursor.fetchone()
                if pedido is None:
                    raise ValueError("El pedido no existe.")
                if pedido[0] != "CONFIRMADO":
                    raise ValueError("Solo se pueden cobrar pedidos confirmados.")

                cursor.execute(
                    """SELECT codigo
                       FROM cajas_sesiones
                       WHERE estado = 'ABIERTA'
                       ORDER BY codigo DESC
                       LIMIT 1
                       FOR UPDATE"""
                )
                sesion = cursor.fetchone()
                if sesion is None:
                    raise ValueError("Abrí la caja para cobrar.")
                codigo_sesion = sesion[0]

                cursor.execute(
                    """SELECT codigo
                       FROM medios_pago
                       WHERE codigo = %s AND activo IS TRUE
                       FOR SHARE""",
                    (codigo_medio_pago,),
                )
                if cursor.fetchone() is None:
                    raise ValueError("El medio de pago no existe o está inactivo.")

                cursor.execute(
                    """SELECT COALESCE(SUM(monto), 0)
                       FROM cobros
                       WHERE codigo_pedido = %s AND anulado IS FALSE""",
                    (codigo_pedido,),
                )
                cobrado = self._a_decimal(cursor.fetchone()[0])
                saldo = self._a_decimal(pedido[1]) - cobrado
                if monto > saldo:
                    raise ValueError("El cobro supera el saldo pendiente")

                cursor.execute(
                    """INSERT INTO cobros
                       (fecha, codigo_pedido, codigo_sesion, codigo_medio_pago,
                        monto, referencia, idusuario, anulado)
                       VALUES (now(), %s, %s, %s, %s, %s, %s, FALSE)
                       RETURNING codigo""",
                    (
                        codigo_pedido, codigo_sesion, codigo_medio_pago,
                        monto, referencia, idusuario,
                    ),
                )
                codigo_cobro = cursor.fetchone()[0]
            conexion.commit()
            return codigo_cobro
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def anular_cobro(self, codigo_cobro, idusuario, motivo):
        motivo = str(motivo or "").strip()
        if not motivo:
            raise ValueError("El motivo de anulación es obligatorio.")
        if idusuario is None:
            raise ValueError("No se pudo identificar al usuario de la sesión.")

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT codigo_sesion, anulado
                       FROM cobros
                       WHERE codigo = %s
                       FOR UPDATE""",
                    (codigo_cobro,),
                )
                cobro = cursor.fetchone()
                if cobro is None:
                    raise ValueError("El cobro no existe.")
                if cobro[1]:
                    raise ValueError("El cobro ya está anulado.")

                cursor.execute(
                    """SELECT codigo
                       FROM cajas_sesiones
                       WHERE estado = 'ABIERTA'
                       ORDER BY codigo DESC
                       LIMIT 1
                       FOR UPDATE"""
                )
                sesion = cursor.fetchone()
                if sesion is None or sesion[0] != cobro[0]:
                    raise ValueError(
                        "No se puede anular un cobro de una caja cerrada"
                    )

                cursor.execute(
                    """UPDATE cobros
                       SET anulado = TRUE, observacion = %s
                       WHERE codigo = %s AND anulado IS FALSE""",
                    (motivo, codigo_cobro),
                )
                if cursor.rowcount == 0:
                    raise ValueError("El cobro ya está anulado.")
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def listar_medios_pago(self):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT codigo, descripcion
                       FROM medios_pago
                       WHERE activo IS TRUE
                       ORDER BY descripcion"""
                )
                medios = [
                    {"codigo": fila[0], "descripcion": fila[1]}
                    for fila in cursor.fetchall()
                ]
            conexion.commit()
            return medios
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()
