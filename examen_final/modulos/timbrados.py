"""
Configuracion del modulo TIMBRADOS.

Practica las reglas de negocio en Python: la funcion validar_timbrado
se define en este archivo y se registra como 'validacion' del modulo.
La ventana de edicion la ejecuta antes de guardar (sin CHECK en la BD).

Reglas:
- fechas: fecha_fin >= fecha_inicio
- numeros: numero_desde > 0 y numero_hasta >= numero_desde
- numeracion: ultimo_numero <= numero_hasta
- formatos: establecimiento y punto_expedicion con 3 digitos (001)
"""

import datetime
import re

from modulos.tipos_documentos import configuracion_tipos_documentos
from nucleo.campo_config import ConfiguracionCampo
from nucleo.modulo_config import ConfiguracionModulo
from nucleo.referencia_config import ConfiguracionReferencia
from nucleo.tema import COLOR_CELDA

# Solo tres digitos: 001, 002, ...
_FORMATO_TRES_DIGITOS = re.compile(r"^\d{3}$")


def validar_timbrado(datos):
    """Valida las reglas de negocio de un timbrado.

    Devuelve ``(True, "")`` cuando los datos son validos o
    ``(False, mensaje)`` cuando se incumple alguna regla.
    """
    fecha_inicio = _convertir_fecha(datos["fecha_inicio"])
    fecha_fin = _convertir_fecha(datos["fecha_fin"])
    if fecha_inicio is None or fecha_fin is None:
        return False, "Las fechas deben ser validas."

    if fecha_fin < fecha_inicio:
        return False, "La fecha fin no puede ser anterior a la fecha inicio."

    numero_desde = datos["numero_desde"]
    numero_hasta = datos["numero_hasta"]
    ultimo_numero = datos["ultimo_numero"]

    if numero_hasta < numero_desde:
        return False, "El numero hasta debe ser mayor o igual al numero desde."

    if numero_desde <= 0:
        return False, "El numero desde debe ser mayor que cero."

    if ultimo_numero < 0:
        return False, "El ultimo numero no puede ser negativo."
    if ultimo_numero > 0 and ultimo_numero > numero_hasta:
        return False, "El ultimo numero no puede superar el numero hasta."

    for campo, etiqueta in (
        ("establecimiento", "establecimiento"),
        ("punto_expedicion", "punto de expedicion"),
    ):
        valor = datos[campo]
        if not isinstance(valor, str) or not _FORMATO_TRES_DIGITOS.fullmatch(valor):
            return False, (
                f"El {etiqueta} debe tener exactamente 3 digitos (ej: 001)."
            )

    return True, ""


def _convertir_fecha(valor):
    """Convierte una fecha o cadena ISO (YYYY-MM-DD) a date."""
    if isinstance(valor, datetime.datetime):
        return valor.date()
    if isinstance(valor, datetime.date):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.date.fromisoformat(valor)
        except ValueError:
            return None
    return None


configuracion_timbrados = ConfiguracionModulo(
    titulo="Timbrados",
    tabla="timbrados",
    clave_primaria="codigo",
    calcular_siguiente_codigo=True,
    buscar_por="numero_timbrado",
    orden_por="numero_timbrado",
    validacion=validar_timbrado,  # reglas de negocio en Python
    tamano_navegacion=(700, 460),
    tamano_edicion=(620, 360),
    campos=[
        ConfiguracionCampo(
            nombre="codigo",
            etiqueta="Codigo",
            tipo=int,
            obligatorio=True,
            longitud=10,
            ancho=70,
            alineacion="derecha",
            color_celda=COLOR_CELDA,
            tooltip="Solo numeros. Identificador unico",
        ),
        ConfiguracionCampo(
            nombre="numero_timbrado",
            etiqueta="Numero Timbrado",
            tipo=int,
            obligatorio=True,
            longitud=10,
            ancho=110,
            tooltip="Numero de timbrado otorgado por la SET",
        ),
        ConfiguracionCampo(
            nombre="codigo_tipo_documento",
            etiqueta="Tipo Documento",
            tipo=int,
            obligatorio=True,
            ancho=110,
            tooltip="Elija el tipo de documento con Buscar o Ctrl+Enter",
            referencia=ConfiguracionReferencia(
                modulo=configuracion_tipos_documentos,
                campo_clave="codigo",
                campos_retorno={"tipo_documento_descripcion": "descripcion"},
            ),
        ),
        ConfiguracionCampo(
            nombre="tipo_documento_descripcion",
            etiqueta="Tipo Documento",
            tipo=str,
            guardar=False,  # no se guarda: se pega desde la referencia
            editable=False,
            ancho=180,
            tooltip="Descripcion del tipo de documento (se pega al elegir)",
        ),
        ConfiguracionCampo(
            nombre="fecha_inicio",
            etiqueta="Fecha Inicio",
            tipo=datetime.date,
            obligatorio=True,
            tooltip="Desde que fecha es valido el timbrado",
        ),
        ConfiguracionCampo(
            nombre="fecha_fin",
            etiqueta="Fecha Fin",
            tipo=datetime.date,
            obligatorio=True,
            tooltip="Hasta que fecha es valido el timbrado",
        ),
        ConfiguracionCampo(
            nombre="establecimiento",
            etiqueta="Establecimiento",
            tipo=str,
            obligatorio=True,
            longitud=3,
            ancho=90,
            tooltip="Codigo del establecimiento, 3 digitos (ej: 001)",
        ),
        ConfiguracionCampo(
            nombre="punto_expedicion",
            etiqueta="Punto Expedicion",
            tipo=str,
            obligatorio=True,
            longitud=3,
            ancho=90,
            tooltip="Codigo del punto de expedicion, 3 digitos (ej: 001)",
        ),
        ConfiguracionCampo(
            nombre="numero_desde",
            etiqueta="Numero Desde",
            tipo=int,
            obligatorio=True,
            longitud=10,
            ancho=100,
            tooltip="Primer numero autorizado del rango",
        ),
        ConfiguracionCampo(
            nombre="numero_hasta",
            etiqueta="Numero Hasta",
            tipo=int,
            obligatorio=True,
            longitud=10,
            ancho=100,
            tooltip="Ultimo numero autorizado del rango",
        ),
        ConfiguracionCampo(
            nombre="ultimo_numero",
            etiqueta="Ultimo Numero",
            tipo=int,
            obligatorio=True,
            longitud=10,
            ancho=100,
            tooltip="Ultimo numero usado (arranca en 0)",
        ),
        ConfiguracionCampo(
            nombre="activo",
            etiqueta="Activo",
            tipo=bool,
            tooltip="Marque si el timbrado esta activo",
        ),
    ],
)