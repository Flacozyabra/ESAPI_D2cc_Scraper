#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ESAPI D2cc Scraper - PyQt6 Application Entry Point.
"""

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    # Создаем экземпляр приложения Qt
    app = QApplication(sys.argv)
    
    # Создаем и показываем главное окно программы
    window = MainWindow()
    window.show()
    
    # Запускаем основной цикл событий
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
