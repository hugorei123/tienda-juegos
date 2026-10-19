from PySide6.QtWidgets import QApplication, QStyle
from PySide6.QtGui import QIcon


def icono_estandar(nombre_tema, pixmap_fallback=None):
    """
    Icono reutilizable para botones y acciones.
    Busca primero el icono en el tema del sistema (Linux/Windows suelen
    tenerlos); si no existe, usa un icono estandar de Qt como alternativa
    (funciona en cualquier plataforma, incluido macOS).
    """
    icono = QIcon.fromTheme(nombre_tema)
    if icono.isNull() and pixmap_fallback is not None:
        icono = QApplication.style().standardIcon(pixmap_fallback)
    return icono


# Iconos usados por la plantilla (por nombre de tema o estandar de Qt).
ICONO_NUEVO = lambda: icono_estandar("document-new", QStyle.StandardPixmap.SP_FileIcon)
ICONO_EDITAR = lambda: icono_estandar("document-open", QStyle.StandardPixmap.SP_FileDialogDetailedView)
ICONO_ELIMINAR = lambda: icono_estandar("edit-delete", QStyle.StandardPixmap.SP_TrashIcon)
ICONO_IMPRIMIR = lambda: icono_estandar("document-print", QStyle.StandardPixmap.SP_DialogSaveButton)
ICONO_CERRAR = lambda: icono_estandar("window-close", QStyle.StandardPixmap.SP_DialogCloseButton)
ICONO_ACEPTAR = lambda: icono_estandar("dialog-ok", QStyle.StandardPixmap.SP_DialogOkButton)
ICONO_CANCELAR = lambda: icono_estandar("dialog-cancel", QStyle.StandardPixmap.SP_DialogCancelButton)
ICONO_BUSCAR = lambda: icono_estandar("edit-find", QStyle.StandardPixmap.SP_FileDialogContentsView)
ICONO_LIMPIAR = lambda: icono_estandar("edit-clear", QStyle.StandardPixmap.SP_LineEditClearButton)
ICONO_VALIDO = lambda: icono_estandar("dialog-apply", QStyle.StandardPixmap.SP_DialogApplyButton)