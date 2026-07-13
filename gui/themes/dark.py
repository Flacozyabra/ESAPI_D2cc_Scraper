# -*- coding: utf-8 -*-

# Палитра темной темы
COLOR_BACKGROUND = "#1e1e1e"
COLOR_HEADER = "#121212"
COLOR_SURFACE = "#2d2d2d"
COLOR_BORDER = "#3e3e42"
COLOR_BORDER_FOCUS = "#007acc"
COLOR_TEXT = "#e1e1e1"
COLOR_TEXT_MUTED = "#808080"
COLOR_ACCENT = "#007acc"
COLOR_ACCENT_HOVER = "#1c97ea"
COLOR_ERROR = "#d13438"  # Красный для ненайденных органов

DARK_THEME_STYLE = f"""
QMainWindow {{
    background-color: {COLOR_BACKGROUND};
    color: {COLOR_TEXT};
}}

QWidget {{
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
    color: {COLOR_TEXT};
}}

/* Заголовки и метки */
QLabel {{
    color: {COLOR_TEXT};
}}

QLabel#TitleLabel {{
    font-size: 15px;
    font-weight: bold;
    color: {COLOR_TEXT};
}}

/* Поля ввода и комбобоксы */
QLineEdit {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    color: {COLOR_TEXT};
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_BORDER_FOCUS};
}}

QComboBox {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
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
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
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

/* Таблицы */
QTableWidget {{
    background-color: {COLOR_BACKGROUND};
    border: 1px solid {COLOR_BORDER};
    gridline-color: {COLOR_BORDER};
    border-radius: 4px;
}}

QTableWidget::item {{
    padding: 5px;
}}

QTableWidget::item:selected {{
    background-color: {COLOR_ACCENT};
    color: white;
}}

QHeaderView::section {{
    background-color: {COLOR_HEADER};
    color: {COLOR_TEXT};
    padding: 6px;
    border: 1px solid {COLOR_BORDER};
    font-weight: bold;
}}

/* Кнопки */
QPushButton {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 500;
    color: {COLOR_TEXT};
}}

QPushButton:hover {{
    background-color: #3e3e42;
    border: 1px solid #5e5e62;
}}

QPushButton:pressed {{
    background-color: #1c1c1c;
}}

QPushButton#CalculateButton {{
    background-color: {COLOR_ACCENT};
    border: 1px solid {COLOR_ACCENT};
    color: white;
    font-weight: bold;
    font-size: 14px;
}}

QPushButton#CalculateButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton#CalculateButton:pressed {{
    background-color: #005a9e;
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

/* Списки (например, в настройках) */
QListWidget {{
    background-color: {COLOR_HEADER};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
}}

QListWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {COLOR_BORDER};
}}

QListWidget::item:selected {{
    background-color: {COLOR_ACCENT};
    color: white;
}}

/* Скроллбары */
QScrollBar:vertical {{
    border: none;
    background: {COLOR_BACKGROUND};
    width: 10px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: #505054;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
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
