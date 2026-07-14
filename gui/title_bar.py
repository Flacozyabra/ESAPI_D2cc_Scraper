# -*- coding: utf-8 -*-
import sys
import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent, QPixmap
from .themes.dark import COLOR_HEADER, COLOR_TEXT, COLOR_SURFACE

class TitleBar(QWidget):
    def __init__(self, parent=None, title="ESAPI D2cc Scraper"):
        super().__init__(parent)
        self.parent = parent
        self.title = title
        
        self.init_ui()
        
        # Переменные для перетаскивания окна
        self.drag_position = QPoint()

    def init_ui(self):
        # Настройка высоты заголовка
        self.setFixedHeight(40)
        
        # Стилизация заголовка
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_HEADER};
                border-bottom: 1px solid #2d2d2d;
            }}
            QLabel {{
                color: {COLOR_TEXT};
                font-size: 13px;
                font-weight: bold;
                border: none;
                background-color: transparent;
            }}
            QLabel#TitleLabel {{
                padding-left: 0px;
            }}
            QLabel#IconLabel {{
                padding-left: 10px;
                padding-right: 5px;
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {COLOR_TEXT};
                font-size: 14px;
                width: 40px;
                height: 40px;
            }}
            QPushButton:hover {{
                background-color: #323232;
            }}
            QPushButton#CloseButton:hover {{
                background-color: #e81123;
                color: white;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Иконка приложения в заголовке
        self.icon_label = QLabel(self)
        self.icon_label.setObjectName("IconLabel")
        
        # Определяем путь к логотипу (поддерживаем PyInstaller _MEIPASS)
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(base_path, "src", "Eclipse_logo.png")
        
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        layout.addWidget(self.icon_label)
        
        # Название окна
        self.title_label = QLabel(self.title, self)
        self.title_label.setObjectName("TitleLabel")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Кнопка настроек в заголовке
        self.btn_settings = QPushButton("⚙", self)
        self.btn_settings.setToolTip("Settings" if "en" in logo_path else "Настройки")
        layout.addWidget(self.btn_settings)
        
        # Кнопка Свернуть
        self.btn_minimize = QPushButton("—", self)
        self.btn_minimize.clicked.connect(self.minimize_parent)
        layout.addWidget(self.btn_minimize)
        
        # Кнопка Закрыть
        self.btn_close = QPushButton("✕", self)
        self.btn_close.setObjectName("CloseButton")
        self.btn_close.clicked.connect(self.close_parent)
        layout.addWidget(self.btn_close)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def minimize_parent(self):
        self.parent.showMinimized()

    def close_parent(self):
        self.parent.close()
