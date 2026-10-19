import datetime
from decimal import Decimal, ROUND_HALF_UP
from xml.sax.saxutils import escape

from PySide6.QtCore import QDir, QUrl
from PySide6.QtGui import QDesktopServices
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from configuracion import datos_negocio
from nucleo.tema import COLOR_ENCABEZADO_TABLA


class ReportePDF:
    """
    Servicio de impresion: genera un PDF del listado actual y lo abre
    en el visor PDF del sistema mediante QDesktopServices.
    """

    def __init__(self, configuracion):
        self.configuracion = configuracion
        self._estilos = getSampleStyleSheet()
        for estilo in self._estilos.byName.values():
            estilo.textColor = colors.black

    def generar(self, filas, abrir=True):
        """Genera el PDF y devuelve la ruta del archivo creado."""
        nombre = (
            f"reporte_{self.configuracion.tabla}_"
            f"{datetime.datetime.now():%Y%m%d_%H%M%S}.pdf"
        )
        ruta = QDir.tempPath() + "/" + nombre

        documento = SimpleDocTemplate(
            ruta,
            pagesize=landscape(A4),
            title=self.configuracion.titulo,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        titulo = Paragraph(
            f"Listado de {self.configuracion.titulo}", self._estilos["Title"]
        )
        total = Paragraph(f"Total de registros: {len(filas)}", self._estilos["Normal"])
        tabla = self._armar_tabla(filas)

        documento.build(
            [titulo, total, Spacer(1, 16), tabla],
            onFirstPage=self._encabezado_pie,
            onLaterPages=self._encabezado_pie,
        )

        if abrir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
        return ruta

    def generar_pedido(self, pedido, abrir=True):
        """Genera el comprobante PDF de un pedido, con detalle y total."""
        nombre = (
            f"pedido_venta_{pedido['codigo']}_"
            f"{datetime.datetime.now():%Y%m%d_%H%M%S}.pdf"
        )
        ruta = QDir.tempPath() + "/" + nombre
        documento = SimpleDocTemplate(
            ruta,
            pagesize=A4,
            title=f"Pedido de Venta {pedido['codigo']}",
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40,
        )
        estilos = self._estilos
        story = [
            Paragraph(f"Pedido de Venta N.º {pedido['codigo']}", estilos["Title"]),
            Spacer(1, 10),
            Paragraph(f"Cliente: {escape(str(pedido.get('cliente') or ''))}", estilos["Normal"]),
            Paragraph(f"Fecha: {escape(str(pedido.get('fecha') or ''))}", estilos["Normal"]),
            Paragraph(f"Estado: {escape(str(pedido.get('estado') or ''))}", estilos["Normal"]),
            Spacer(1, 16),
        ]
        filas = [["Código", "Descripción", "Cantidad", "Precio", "IVA %", "Total"]]
        for detalle in pedido.get("detalles", []):
            filas.append([
                escape(str(detalle.get("codigo_item", ""))),
                Paragraph(escape(str(detalle.get("descripcion", ""))), estilos["Normal"]),
                str(detalle.get("cantidad", "")),
                f"{detalle.get('precio_unitario', 0):.2f}",
                f"{detalle.get('porcentaje_iva', 0):.2f}",
                f"{detalle.get('total', 0):.2f}",
            ])
        tabla = Table(filas, repeatRows=1, colWidths=[55, 200, 60, 70, 55, 70])
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_ENCABEZADO_TABLA)),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ]))
        story.extend([
            tabla,
            Spacer(1, 16),
            Paragraph(f"Subtotal: {pedido.get('subtotal', 0):.2f}", estilos["Normal"]),
            Paragraph(f"IVA: {pedido.get('monto_iva', 0):.2f}", estilos["Normal"]),
            Paragraph(f"<b>TOTAL: {pedido.get('total', 0):.2f}</b>", estilos["Heading2"]),
        ])
        documento.build(
            story,
            onFirstPage=self._encabezado_pie,
            onLaterPages=self._encabezado_pie,
        )
        if abrir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
        return ruta

    def generar_ticket(self, pedido, cobros, abrir=True):
        """Genera un ticket de compra de 80 mm con el alto ajustado al contenido."""
        nombre = (
            f"ticket_pedido_{pedido['codigo']}_"
            f"{datetime.datetime.now():%Y%m%d_%H%M%S}.pdf"
        )
        ruta = QDir.tempPath() + "/" + nombre
        ancho = 80 * mm
        margen = 4 * mm
        estilos = {
            "normal": ParagraphStyle(
                "TicketNormal", fontName="Helvetica", fontSize=7.5,
                leading=9, textColor=colors.black,
            ),
            "centrado": ParagraphStyle(
                "TicketCentrado", fontName="Helvetica", fontSize=7.5,
                leading=9, alignment=1, textColor=colors.black,
            ),
            "titulo": ParagraphStyle(
                "TicketTitulo", fontName="Helvetica-Bold", fontSize=10,
                leading=12, alignment=1, textColor=colors.black,
            ),
            "seccion": ParagraphStyle(
                "TicketSeccion", fontName="Helvetica-Bold", fontSize=8,
                leading=10, textColor=colors.black,
            ),
            "derecha": ParagraphStyle(
                "TicketDerecha", fontName="Helvetica", fontSize=7,
                leading=8, alignment=2, textColor=colors.black,
            ),
            "tabla": ParagraphStyle(
                "TicketTabla", fontName="Helvetica", fontSize=6.5,
                leading=7.5, textColor=colors.black,
            ),
            "tabla_derecha": ParagraphStyle(
                "TicketTablaDerecha", fontName="Helvetica", fontSize=6.5,
                leading=7.5, alignment=2, textColor=colors.black,
            ),
        }
        story = [
            Paragraph(escape(datos_negocio.NOMBRE), estilos["titulo"]),
            Paragraph(f"RUC: {escape(datos_negocio.RUC)}", estilos["centrado"]),
            Paragraph(escape(datos_negocio.DIRECCION), estilos["centrado"]),
            Paragraph(f"Tel.: {escape(datos_negocio.TELEFONO)}", estilos["centrado"]),
            Spacer(1, 5),
            Paragraph("TICKET DE COMPRA", estilos["titulo"]),
            Spacer(1, 5),
            Paragraph(
                f"N.º de ticket: {escape(str(pedido.get('codigo') or ''))}",
                estilos["normal"],
            ),
            Paragraph(
                f"Fecha: {escape(str(pedido.get('fecha') or ''))}",
                estilos["normal"],
            ),
            Paragraph(
                f"Estado: {escape(str(pedido.get('estado') or ''))}",
                estilos["normal"],
            ),
            Paragraph(
                f"Cliente: {escape(str(pedido.get('cliente') or ''))}",
                estilos["normal"],
            ),
            Paragraph(
                f"RUC cliente: {escape(str(pedido.get('cto_ruc') or ''))}",
                estilos["normal"],
            ),
            Paragraph(
                f"Atendió: {escape(str(pedido.get('usuario') or ''))}",
                estilos["normal"],
            ),
            Spacer(1, 5),
            Paragraph("Detalle", estilos["seccion"]),
        ]

        ancho_contenido = ancho - 2 * margen - 12
        anchos_columnas = [
            ancho_contenido * 0.12,
            ancho_contenido * 0.38,
            ancho_contenido * 0.24,
            ancho_contenido * 0.26,
        ]
        filas_detalle = [[
            Paragraph("<b>Cant.</b>", estilos["tabla"]),
            Paragraph("<b>Descripción</b>", estilos["tabla"]),
            Paragraph("<b>Precio unit.</b>", estilos["tabla_derecha"]),
            Paragraph("<b>Total</b>", estilos["tabla_derecha"]),
        ]]
        subtotal = Decimal("0")
        iva_5 = Decimal("0")
        iva_10 = Decimal("0")
        for detalle in pedido.get("detalles", []):
            cantidad = self._decimal(detalle.get("cantidad"))
            precio = self._decimal(detalle.get("precio_unitario"))
            porcentaje_iva = self._decimal(detalle.get("porcentaje_iva"))
            importe = cantidad * precio
            monto_iva = importe * porcentaje_iva / Decimal("100")
            total_linea = importe + monto_iva
            subtotal += importe
            if porcentaje_iva == Decimal("5"):
                iva_5 += monto_iva
            elif porcentaje_iva == Decimal("10"):
                iva_10 += monto_iva
            filas_detalle.append([
                Paragraph(escape(str(detalle.get("cantidad") or "")), estilos["tabla"]),
                Paragraph(
                    escape(str(detalle.get("descripcion") or "")), estilos["tabla"]
                ),
                Paragraph(self._formatear_monto(precio), estilos["tabla_derecha"]),
                Paragraph(
                    self._formatear_monto(total_linea), estilos["tabla_derecha"]
                ),
            ])
        tabla_detalle = Table(
            filas_detalle, colWidths=anchos_columnas, repeatRows=1
        )
        tabla_detalle.setStyle(TableStyle([
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
            ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.extend([
            tabla_detalle,
            Spacer(1, 5),
            Paragraph(
                f"Subtotal: {self._formatear_monto(subtotal)}",
                estilos["derecha"],
            ),
            Paragraph(f"IVA 5%: {self._formatear_monto(iva_5)}", estilos["derecha"]),
            Paragraph(
                f"IVA 10%: {self._formatear_monto(iva_10)}", estilos["derecha"]
            ),
            Paragraph(
                f"<b>TOTAL: {self._formatear_monto(self._decimal(pedido.get('total')))}</b>",
                estilos["derecha"],
            ),
            Spacer(1, 7),
            Paragraph("Pagos", estilos["seccion"]),
        ])

        total_cobrado = Decimal("0")
        cobros_vigentes = [cobro for cobro in cobros if not cobro.get("anulado")]
        for cobro in cobros_vigentes:
            monto = self._decimal(cobro.get("monto"))
            total_cobrado += monto
            story.append(
                Paragraph(
                    f"{escape(str(cobro.get('medio_pago') or ''))}: "
                    f"{self._formatear_monto(monto)}",
                    estilos["normal"],
                )
            )
        total_pedido = self._decimal(pedido.get("total"))
        saldo = total_pedido - total_cobrado
        story.extend([
            Paragraph(
                f"Total cobrado: {self._formatear_monto(total_cobrado)}",
                estilos["derecha"],
            ),
            Paragraph(
                "<b>PAGADO</b>" if saldo == 0 else
                f"Saldo pendiente: {self._formatear_monto(saldo)}",
                estilos["derecha"],
            ),
            Spacer(1, 8),
            Paragraph(escape(datos_negocio.LEYENDA_PIE), estilos["centrado"]),
            Paragraph(
                "Ticket de compra - no válido como factura", estilos["centrado"]
            ),
        ])

        altura_contenido = sum(
            flujo.wrap(ancho_contenido, 100000)[1]
            + flujo.getSpaceBefore()
            + flujo.getSpaceAfter()
            for flujo in story
        )
        alto = altura_contenido + 2 * margen + 12
        documento = SimpleDocTemplate(
            ruta,
            pagesize=(ancho, alto),
            title=f"Ticket de Compra {pedido['codigo']}",
            leftMargin=margen,
            rightMargin=margen,
            topMargin=margen,
            bottomMargin=margen,
        )
        documento.build(story, onFirstPage=self._fondo_blanco_ticket)
        if abrir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
        return ruta

    @staticmethod
    def _decimal(valor):
        return valor if isinstance(valor, Decimal) else Decimal(str(valor or 0))

    @classmethod
    def _formatear_monto(cls, monto):
        entero = cls._decimal(monto).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"{entero:,}".replace(",", ".")

    @staticmethod
    def _fondo_blanco_ticket(canvas, documento):
        canvas.saveState()
        ancho, alto = documento.pagesize
        canvas.setFillColor(colors.white)
        canvas.rect(0, 0, ancho, alto, fill=1, stroke=0)
        canvas.restoreState()

    def _armar_tabla(self, filas):
        """Encabezados y datos del PDF a partir de la configuracion."""
        campos = self.configuracion.campos_visibles_navegacion()
        encabezados = [campo.etiqueta for campo in campos]
        datos = [
            [self._texto(campo, fila.get(campo.nombre)) for campo in campos]
            for fila in filas
        ]

        tabla = Table([encabezados] + datos, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_ENCABEZADO_TABLA)),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ]))
        return tabla

    @staticmethod
    def _texto(campo, valor):
        if campo.tipo is bool:
            return "Si" if valor else "No"
        if valor is None:
            return ""
        return str(valor)

    def _encabezado_pie(self, canvas, documento):
        """Numero de pagina y fecha en cada hoja."""
        canvas.saveState()
        ancho, alto = documento.pagesize
        canvas.setFillColor(colors.white)
        canvas.rect(0, 0, ancho, alto, fill=1, stroke=0)
        canvas.setFillColor(colors.black)
        canvas.setFont("Helvetica", 9)
        canvas.drawCentredString(ancho / 2, 18, f"Pagina {documento.page}")
        canvas.drawString(
            40, 18, f"Generado: {datetime.datetime.now():%d/%m/%Y %H:%M}"
        )
        canvas.restoreState()