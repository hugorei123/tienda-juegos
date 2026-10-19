from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette


COLOR_FONDO_VENTANA = "#F4F7F4"
COLOR_FONDO_CONTROLES = "#FFFFFF"
COLOR_FILA_ALTERNA = "#EEF3EE"
COLOR_TEXTO = "#2B3A33"
COLOR_ACENTO = "#4A7A62"
COLOR_ACENTO_HOVER = "#3F6B55"
COLOR_ACENTO_PRESSED = "#355B49"
COLOR_ENCABEZADO_TABLA = "#DCEBE1"
COLOR_CELDA = COLOR_ENCABEZADO_TABLA
COLOR_SELECCION = "#CFE3D6"
COLOR_TEXTO_SELECCION = "#1F2D26"
COLOR_BORDE = "#C5D3C9"
COLOR_TEXTO_DESHABILITADO = "#8A9A91"


def aplicar_tema(app):
    app.setStyle("Fusion")

    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(COLOR_FONDO_VENTANA))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(COLOR_TEXTO))
    paleta.setColor(QPalette.ColorRole.Base, QColor(COLOR_FONDO_CONTROLES))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor(COLOR_FILA_ALTERNA))
    paleta.setColor(QPalette.ColorRole.Text, QColor(COLOR_TEXTO))
    paleta.setColor(QPalette.ColorRole.Button, QColor(COLOR_ACENTO))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(COLOR_FONDO_CONTROLES))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(COLOR_SELECCION))
    paleta.setColor(
        QPalette.ColorRole.HighlightedText, QColor(COLOR_TEXTO_SELECCION)
    )
    paleta.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLOR_FONDO_CONTROLES))
    paleta.setColor(QPalette.ColorRole.ToolTipText, QColor(COLOR_TEXTO))
    for rol in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        paleta.setColor(
            QPalette.ColorGroup.Disabled, rol, QColor(COLOR_TEXTO_DESHABILITADO)
        )
    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Button,
        QColor(COLOR_FILA_ALTERNA),
    )
    app.setPalette(paleta)

    familia = (
        "Segoe UI"
        if QFontDatabase.hasFamily("Segoe UI")
        else app.font().family()
    )
    app.setFont(QFont(familia, 10))
    app.setStyleSheet(
        f"""
        QWidget {{
            color: {COLOR_TEXTO};
        }}
        QWidget:disabled {{
            color: {COLOR_TEXTO_DESHABILITADO};
        }}
        QMainWindow, QDialog, QMessageBox {{
            background-color: {COLOR_FONDO_VENTANA};
        }}
        QPushButton {{
            color: {COLOR_FONDO_CONTROLES};
            background-color: {COLOR_ACENTO};
            border: 1px solid {COLOR_ACENTO};
            border-radius: 4px;
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_ACENTO_HOVER};
            border-color: {COLOR_ACENTO_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_ACENTO_PRESSED};
            border-color: {COLOR_ACENTO_PRESSED};
        }}
        QPushButton:disabled {{
            color: {COLOR_TEXTO_DESHABILITADO};
            background-color: {COLOR_FILA_ALTERNA};
            border-color: {COLOR_BORDE};
        }}
        QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit {{
            color: {COLOR_TEXTO};
            background-color: {COLOR_FONDO_CONTROLES};
            border: 1px solid {COLOR_BORDE};
            border-radius: 4px;
            padding: 5px 7px;
            selection-background-color: {COLOR_SELECCION};
            selection-color: {COLOR_TEXTO_SELECCION};
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus,
        QTextEdit:focus {{
            border-color: {COLOR_ACENTO};
        }}
        QTableWidget {{
            color: {COLOR_TEXTO};
            background-color: {COLOR_FONDO_CONTROLES};
            alternate-background-color: {COLOR_FILA_ALTERNA};
            border: 1px solid {COLOR_BORDE};
            gridline-color: {COLOR_BORDE};
            selection-background-color: {COLOR_SELECCION};
            selection-color: {COLOR_TEXTO_SELECCION};
        }}
        QHeaderView::section {{
            color: {COLOR_TEXTO};
            background-color: {COLOR_ENCABEZADO_TABLA};
            border: 1px solid {COLOR_BORDE};
            padding: 5px 7px;
        }}
        QMenuBar {{
            color: {COLOR_TEXTO};
            background-color: {COLOR_FONDO_VENTANA};
        }}
        QMenuBar::item:selected, QMenu::item:selected {{
            color: {COLOR_TEXTO_SELECCION};
            background-color: {COLOR_SELECCION};
        }}
        QMenu {{
            color: {COLOR_TEXTO};
            background-color: {COLOR_FONDO_CONTROLES};
            border: 1px solid {COLOR_BORDE};
        }}
        QMenu::item {{
            padding: 5px 24px 5px 8px;
        }}
        QGroupBox {{
            border: 1px solid {COLOR_BORDE};
            border-radius: 4px;
            margin-top: 8px;
            padding: 8px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
        }}
        QTabWidget::pane {{
            border: 1px solid {COLOR_BORDE};
        }}
        QTabBar::tab {{
            color: {COLOR_TEXTO};
            background-color: {COLOR_FILA_ALTERNA};
            border: 1px solid {COLOR_BORDE};
            padding: 6px 10px;
        }}
        QTabBar::tab:selected {{
            background-color: {COLOR_ENCABEZADO_TABLA};
        }}
        """
    )
