# Sistema de gestión - Tienda de juegos de mesa

Aplicación de escritorio para administrar una tienda de juegos de mesa
de una sola sucursal. Proyecto del examen final de Lenguaje de Programación II.

## Funcionalidades

- **Catálogo de juegos:** categoría, editorial, mecánica, cantidad de jugadores,
  edad mínima, duración, dependencia del idioma, precio e IVA.
- **Pedidos de venta:** borrador, confirmación, anulación y cálculo de IVA.
- **Stock:** consulta con alertas, historial de movimientos (kardex) y ajustes.
- **Caja y cobros:** apertura, cobros en efectivo, tarjeta, transferencia o QR,
  y cierre con arqueo.
- **Ticket de compra** en formato de 80 mm.
- **Maestros:** contactos, usuarios, tipos de documentos y timbrados.

## Tecnologías

Python, PySide6, PostgreSQL y ReportLab.

## Cómo ejecutarlo

1. Crear la base de datos y ejecutar `tienda_juegos.sql`.
2. Instalar las dependencias: `pip install -r requirements.txt`
3. Configurar la conexión en `configuracion/base_datos.py`.
4. Ejecutar: `python main.py`