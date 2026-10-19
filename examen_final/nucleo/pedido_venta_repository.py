from psycopg.errors import ForeignKeyViolation

from configuracion.base_datos import obtener_conexion
from modulos.contactos import referencia_clientes
from nucleo.repositorio_generico import RepositorioGenerico
from nucleo.ventas import VentaRepository


class PedidoVentaRepository:
    """Acceso a datos especifico para pedidos de venta y sus detalles."""

    def obtener_siguiente_codigo(self):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                # CORRECCIÓN: Llamamos directamente a la secuencia que creaste en DBeaver
                cursor.execute("SELECT nextval('pedidos_venta_codigo_seq')")
                return cursor.fetchone()[0]
        finally:
            conexion.close()

    def listar_clientes(self):
        repositorio = RepositorioGenerico(
            referencia_clientes.modulo,
            filtro=referencia_clientes.filtro,
        )
        return repositorio.listar()

    def listar_items(self):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT codigo, descripcion, precio, porcentaje_iva "
                    "FROM item WHERE activo IS TRUE ORDER BY descripcion"
                )
                return [
                    {
                        "codigo": fila[0],
                        "descripcion": fila[1],
                        "precio": fila[2],
                        "porcentaje_iva": fila[3] or 0,
                    }
                    for fila in cursor.fetchall()
                ]
        finally:
            conexion.close()

    def guardar(self, pedido, detalles, codigo_original=None):
        """Inserta o actualiza cabecera y reemplaza sus líneas en una transacción."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if codigo_original is None:
                    cursor.execute(
                        """INSERT INTO pedidos_venta
                           (codigo, fecha, cod_cliente, idusuario, estado, observacion, total)
                           VALUES (%s, %s, %s, %s, 'BORRADOR', %s, %s)""",
                        (
                            pedido["codigo"], pedido["fecha"],
                            pedido["cod_cliente"], pedido["idusuario"],
                            pedido.get("observacion", ""), pedido["total"],
                        ),
                    )
                    codigo = pedido["codigo"]
                else:
                    cursor.execute(
                        """UPDATE pedidos_venta
                           SET fecha = %s, cod_cliente = %s,
                               observacion = %s, total = %s
                           WHERE codigo = %s AND estado = 'BORRADOR'""",
                        (
                            pedido["fecha"], pedido["cod_cliente"],
                            pedido.get("observacion", ""), pedido["total"],
                            codigo_original,
                        ),
                    )
                    if cursor.rowcount == 0:
                        raise ValueError(
                            "El pedido no existe o ya fue confirmado; no se puede editar."
                        )
                    codigo = codigo_original
                    cursor.execute(
                        "DELETE FROM pedidos_venta_det WHERE codigo_pedido = %s",
                        (codigo,),
                    )

                for numero_linea, detalle in enumerate(detalles, start=1):
                    cursor.execute(
                        """INSERT INTO pedidos_venta_det
                           (codigo_pedido, nro_item, codigo_item, cantidad, precio_unitario)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (
                            codigo, numero_linea, detalle["codigo_item"],
                            detalle["cantidad"], detalle["precio_unitario"],
                        ),
                    )
            conexion.commit()
            return codigo
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def confirmar(self, codigo, idusuario):
        VentaRepository().confirmar_pedido(codigo, idusuario)

    def anular(self, codigo, idusuario, motivo):
        VentaRepository().anular_pedido(codigo, idusuario, motivo)

    def eliminar(self, codigo):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """DELETE FROM pedidos_venta
                       WHERE codigo = %s AND estado = 'BORRADOR'""",
                    (codigo,),
                )
                if cursor.rowcount == 0:
                    raise ValueError("El pedido no existe o ya fue confirmado.")
            conexion.commit()
        except ForeignKeyViolation:
            conexion.rollback()
            raise
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def listar(self):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT p.codigo, p.fecha, p.cod_cliente,
                              c.cto_razonsocial, p.idusuario, u.nombre_apellido,
                              p.estado, p.observacion, p.total
                       FROM pedidos_venta p
                       LEFT JOIN contactos c ON c.cto_cod = p.cod_cliente
                       LEFT JOIN usuarios u ON u.idusuario = p.idusuario
                       ORDER BY p.codigo DESC"""
                )
                columnas = (
                    "codigo", "fecha", "cod_cliente", "cliente",
                    "idusuario", "usuario", "estado", "observacion", "total",
                )
                return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        finally:
            conexion.close()

    def obtener(self, codigo):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """SELECT p.codigo, p.fecha, p.cod_cliente, p.idusuario,
                              c.cto_razonsocial, c.cto_ruc, u.nombre_apellido,
                              p.estado, p.observacion, p.total
                       FROM pedidos_venta p
                       LEFT JOIN contactos c ON c.cto_cod = p.cod_cliente
                       LEFT JOIN usuarios u ON u.idusuario = p.idusuario
                       WHERE p.codigo = %s""",
                    (codigo,),
                )
                fila = cursor.fetchone()
                if fila is None:
                    return None
                
                pedido = dict(
                    zip(
                        ("codigo", "fecha", "cod_cliente", "idusuario", "cliente",
                         "cto_ruc", "usuario", "estado", "observacion", "total"),
                        fila,
                    )
                )
                
                cursor.execute(
                    """SELECT d.codigo_item, i.descripcion as descripcion_item, d.cantidad,
                              d.precio_unitario, i.porcentaje_iva, 
                              (d.cantidad * d.precio_unitario) as subtotal,
                              0 as monto_iva,
                              (d.cantidad * d.precio_unitario) as total
                       FROM pedidos_venta_det d
                       JOIN item i ON d.codigo_item = i.codigo
                       WHERE d.codigo_pedido = %s 
                       ORDER BY d.nro_item""",
                    (codigo,),
                )
                pedido["detalles"] = [
                    dict(
                        zip(
                            ("codigo_item", "descripcion", "cantidad", "precio_unitario",
                             "porcentaje_iva", "subtotal", "monto_iva", "total"),
                            detalle,
                        )
                    )
                    for detalle in cursor.fetchall()
                ]
                return pedido
        finally:
            conexion.close()