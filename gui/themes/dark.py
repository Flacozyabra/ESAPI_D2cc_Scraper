# -*- coding: utf-8 -*-

# Палитра темы DICOM WatchDog
COLOR_BACKGROUND = "#202020"
COLOR_HEADER = "#1a1a1a"
COLOR_SURFACE = "#0f0f0f"
COLOR_BORDER = "#3d3d3d"
COLOR_BORDER_FOCUS = "#1f538d"
COLOR_TEXT = "#ffffff"
COLOR_TEXT_MUTED = "#a0a0a0"
COLOR_ACCENT = "#1f538d"
COLOR_ACCENT_HOVER = "#2a69a5"
COLOR_ERROR = "#d13438"

DARK_THEME_STYLE = f"""
QMainWindow {{
    background-color: transparent;
}}

QDialog {{
    background-color: transparent;
}}

/* Главный контейнер окон с рамкой (прямые углы) как в DICOM WatchDog */
#MainWindowWidget, #SettingsWindowWidget {{
    background-color: {COLOR_BACKGROUND};
    border: 1px solid {COLOR_BORDER};
    border-radius: 0px;
}}

QWidget {{
    font-family: "Segoe UI", -apple-system, Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: {COLOR_TEXT};
}}

/* Тонкие светлые рамки вокруг отделов (прямые углы) */
#InputGroup, #ResultsGroup, #SettingsGroup {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 0px;
    background-color: transparent;
}}

/* Заголовки и метки */
QLabel {{
    color: {COLOR_TEXT};
    background-color: transparent;
}}

QLabel#TitleLabel {{
    font-size: 14px;
    font-weight: bold;
    color: {COLOR_TEXT};
}}

/* Поля ввода и комбобоксы */
QLineEdit {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {COLOR_TEXT};
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_BORDER_FOCUS};
}}

QComboBox {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 5px 10px;
    color: {COLOR_TEXT};
    min-width: 60px;
}}

QComboBox:editable {{
    background-color: {COLOR_SURFACE};
}}

QComboBox:focus, QComboBox:on {{
    border: 1px solid {COLOR_BORDER_FOCUS};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
}}

QComboBox::down-arrow {{
    image: url(non_existent_icon.png);
    width: 0; 
    height: 0; 
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLOR_TEXT};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    selection-background-color: {COLOR_ACCENT};
    selection-color: white;
    outline: 0;
}}

/* Кнопки */
QPushButton {{
    background-color: {COLOR_ACCENT};
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: normal;
    color: {COLOR_TEXT};
}}

QPushButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton:pressed {{
    background-color: #1a4675;
}}

QPushButton#CalculateButton {{
    background-color: {COLOR_ACCENT};
    border: none;
    color: white;
    font-weight: bold;
    font-size: 14px;
}}

QPushButton#CalculateButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton#CalculateButton:pressed {{
    background-color: #1a4675;
}}

QPushButton#CalculateButton:disabled {{
    background-color: #26384d;
    color: #709bc1;
}}

QPushButton#SettingsButton {{
    background-color: transparent;
    border: none;
    padding: 5px;
}}

QPushButton#SettingsButton:hover {{
    background-color: {COLOR_SURFACE};
    border-radius: 4px;
}}

/* Поле Лога как QPlainTextEdit в DICOM WatchDog */
QTextEdit#LogView {{
    background-color: #161616;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    color: #ebebeb;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    padding: 5px;
}}

/* QScrollBar полностью из DICOM WatchDog */
QScrollBar:vertical {{
    background-color: #121212;
    width: 10px;
    margin: 0px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: #3e3e3e;
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #525252;
}}

QScrollBar::handle:vertical:pressed {{
    background-color: #686868;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
    height: 0px;
    width: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: #121212;
    height: 10px;
    margin: 0px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: #3e3e3e;
    min-width: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: #525252;
}}

QScrollBar::handle:horizontal:pressed {{
    background-color: #686868;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
    height: 0px;
    width: 0px;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* Списки (например, боковое меню настроек) */
QListWidget {{
    background-color: #141414;
    border: none;
    border-right: 1px solid #282828;
}}

QListWidget::item {{
    padding: 8px 12px;
    margin: 3px 6px;
    border-radius: 5px;
    color: #a0a0a0;
}}

QListWidget::item:hover {{
    background-color: #222222;
    color: {COLOR_TEXT};
}}

QListWidget::item:selected {{
    background-color: {COLOR_ACCENT};
    color: white;
}}
"""

def get_organ_field_style(is_valid=True):
    """Возвращает QSS стиль для поля органа (QLineEdit / QComboBox) в зависимости от валидности."""
    if is_valid:
        return f"""
            QComboBox {{
                border: 1px solid {COLOR_BORDER};
                background-color: {COLOR_SURFACE};
            }}
            QComboBox:focus {{
                border: 1px solid {COLOR_BORDER_FOCUS};
            }}
        """
    else:
        return f"""
            QComboBox {{
                border: 2px solid {COLOR_ERROR};
                background-color: {COLOR_SURFACE};
            }}
            QComboBox:focus {{
                border: 2px solid {COLOR_ERROR};
            }}
        """
