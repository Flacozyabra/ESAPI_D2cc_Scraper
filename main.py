#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ESAPI D2cc Scraper - PyQt6 Application Entry Point.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt

class LoadingSplash(QWidget):
    """Кастомный сплэшскрин с поддержкой прозрачного PNG логотипа Eclipse."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Определяем путь к логотипу (поддерживаем PyInstaller _MEIPASS)
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        logo_path = os.path.join(base_path, "src", "Eclipse_logo.png")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Логотип
        self.logo_label = QLabel(self)
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        layout.addWidget(self.logo_label)
        
        # Текст загрузки
        self.text_label = QLabel("Connecting to ESAPI...", self)
        self.text_label.setStyleSheet("color: #ffffff; font-size: 14px; font-family: 'Segoe UI'; font-weight: bold;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text_label)
        
        self.adjustSize()
        
        # Центрирование сплэшскрина на экране
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            self.move((geom.width() - self.width()) // 2, (geom.height() - self.height()) // 2)

def main():
    app = QApplication(sys.argv)
    
    # Установка иконки по умолчанию для всего приложения
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_path, "src", "Eclipse_logo.png")
    app.setWindowIcon(QIcon(icon_path))
    
    # Показываем сплэшскрин загрузки
    splash = LoadingSplash()
    splash.show()
    app.processEvents()
    
    # Импортируем окно только после показа сплэша (для чистоты таймингов)
    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    # Скрываем сплэшскрин
    splash.close()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
