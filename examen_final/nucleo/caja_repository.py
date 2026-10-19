from decimal import Decimal, InvalidOperation

from psycopg.errors import UniqueViolation

from configuracion.base_datos import obtener_conexion


class CajaRepository:
    """Consultas y operaciones transaccionales de caja."""

    @staticmethod
    def _a_decimal(valor):
        return valor if isinstance(valor, Decimal) else Decimal(str(valor))

    @staticmethod
    def _validar_monto(valor, etiqueta):
        try:
            monto = CajaRepository._a_decimal(valor)
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValueError(f"Ingrese un monto válido para {etiqueta}.") from error
        if not monto.is_finite() or monto < 0:
            raise ValueError(
                f"El monto de {etiqueta} debe ser mayor o igual a 0."
            )
        return monto

    @staticmethod
    def _resumen_con_cursor(cursor, codigo_sesion, monto_apertura):
        cursor.execute(
            """SELECT mp.codigo, mp.descripcion, mp.es_efectivo,
                      COALESCE(SUM(c.monto), 0)
               FROM medios_pago mp
               LEFT JOIN cobros c
                 ON c.codigo_medio_pago = mp.codigo
                AND c.codigo_sesion = %s
                AND c.anulado IS FALSE
               GROUP BY mp.codigo, mp.descripcion, mp.es_efectivo
               ORDER BY mp.descripcion""",
            (codigo_sesion,),
        )
        medios = [
            {
                "codigo": fila[0],
                "descripcion": fila[1],
                "es_efectivo": fila[2],
                "total": CajaRepository._a_decimal(fila[3]),
            }
            for fila in cursor.fetchall()
        ]
        efectivo = sum(
            (medio["total"] for medio in medios if medio["es_efectivo"]),
            Decimal("0"),
        )
        apertura = CajaRepository._a_decimal(monto_apertura)
        return {
            "por_medio_pago": medios,
            "efectivo": efectivo,
            "esperado": apertura + efectivo,
        }

    def obtener_sesion_abierta(self):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT c.codigo, c.fecha_apertura, c.idusuario_apertura,
                              u.nombre_apellido, c.monto_apertura, c.observacion
                       FROM cajas_sesiones c
                       LEFT JOIN usuarios u
                         ON u.idusuario = c.idusuario_apertura
                       WHERE c.estado = 'ABIERTA'
                       ORDER BY c.codigo DESC
                       LIMIT 1"""
                )
                fila = cursor.fetchone()
                sesion = (
                    dict(
                        zip(
                            (
                                "codigo", "fecha_apertura", "idusuario_apertura",
                                "usuario_apertura", "monto_apertura", "observacion",
                            ),
                            fila,
                        )
                    )
                    if fila is not None
                    else None
                )
            conexion.commit()
            return sesion
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def abrir_caja(self, monto_apertura, idusuario):
        monto_apertura = self._validar_monto(monto_apertura, "apertura")

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM cajas_sesiones WHERE estado = 'ABIERTA' LIMIT 1"
                )
                if cursor.fetchone() is not None:
                    raise ValueError("Ya hay una caja abierta.")
                cursor.execute(
                    """INSERT INTO cajas_sesiones
                       (fecha_apertura, idusuario_apertura, monto_apertura, estado)
                       VALUES (now(), %s, %s, 'ABIERTA')
                       RETURNING codigo""",
                    (idusuario, monto_apertura),
                )
                codigo = cursor.fetchone()[0]
            conexion.commit()
            return codigo
        except UniqueViolation as error:
            conexion.rollback()
            raise ValueError("Ya hay una caja abierta.") from error
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def resumen_sesion(self, codigo_sesion):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT monto_apertura FROM cajas_sesiones
                       WHERE codigo = %s""",
                    (codigo_sesion,),
                )
                fila = cursor.fetchone()
                if fila is None:
                    raise ValueError("La sesión de caja no existe.")
                resumen = self._resumen_con_cursor(
                    cursor, codigo_sesion, fila[0]
                )
            conexion.commit()
            return resumen
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def cerrar_caja(self, codigo_sesion, monto_contado, idusuario, observacion):
        monto_contado = self._validar_monto(monto_contado, "contado")

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT estado, monto_apertura
                       FROM cajas_sesiones
                       WHERE codigo = %s
                       FOR UPDATE""",
                    (codigo_sesion,),
                )
                sesion = cursor.fetchone()
                if sesion is None or sesion[0] != "ABIERTA":
                    raise ValueError("La sesión de caja no está abierta.")

                resumen = self._resumen_con_cursor(
                    cursor, codigo_sesion, sesion[1]
                )
                esperado = resumen["esperado"]
                cursor.execute(
                    """UPDATE cajas_sesiones
                       SET fecha_cierre = now(), idusuario_cierre = %s,
                           monto_contado = %s, observacion = %s,
                           estado = 'CERRADA'
                       WHERE codigo = %s AND estado = 'ABIERTA'""",
                    (idusuario, monto_contado, observacion, codigo_sesion),
                )
                if cursor.rowcount == 0:
                    raise ValueError("La sesión de caja ya no está abierta.")
            conexion.commit()
            return {
                "esperado": esperado,
                "contado": monto_contado,
                "diferencia": monto_contado - esperado,
            }
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def listar_sesiones(self, limite=30):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT s.codigo, s.estado, s.fecha_apertura,
                              ua.nombre_apellido, s.monto_apertura,
                              s.fecha_cierre, uc.nombre_apellido,
                              s.monto_contado, s.observacion,
                              COALESCE(SUM(
                                  CASE WHEN mp.es_efectivo IS TRUE
                                       THEN cb.monto ELSE 0 END
                              ), 0)
                       FROM cajas_sesiones s
                       LEFT JOIN usuarios ua
                         ON ua.idusuario = s.idusuario_apertura
                       LEFT JOIN usuarios uc
                         ON uc.idusuario = s.idusuario_cierre
                       LEFT JOIN cobros cb
                         ON cb.codigo_sesion = s.codigo
                        AND cb.anulado IS FALSE
                       LEFT JOIN medios_pago mp
                         ON mp.codigo = cb.codigo_medio_pago
                       GROUP BY s.codigo, ua.nombre_apellido, uc.nombre_apellido
                       ORDER BY s.fecha_apertura DESC, s.codigo DESC
                       LIMIT %s""",
                    (limite,),
                )
                sesiones = []
                for fila in cursor.fetchall():
                    apertura = self._a_decimal(fila[4])
                    esperado = apertura + self._a_decimal(fila[9])
                    contado = (
                        self._a_decimal(fila[7])
                        if fila[7] is not None
                        else None
                    )
                    sesiones.append(
                        {
                            "codigo": fila[0],
                            "estado": fila[1],
                            "fecha_apertura": fila[2],
                            "usuario_apertura": fila[3],
                            "monto_apertura": apertura,
                            "fecha_cierre": fila[5],
                            "usuario_cierre": fila[6],
                            "esperado": esperado,
                            "contado": contado,
                            "diferencia": (
                                contado - esperado if contado is not None else None
                            ),
                            "observacion": fila[8],
                        }
                    )
            conexion.commit()
            return sesiones
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()
