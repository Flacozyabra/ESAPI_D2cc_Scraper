# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QStackedWidget, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QGraphicsDropShadowEffect, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from .title_bar import TitleBar
from .themes.dark import DARK_THEME_STYLE

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Загрузка текущих настроек
        self.config = self.parent.config if parent else {}
        
        self.init_ui()

    def init_ui(self):
        # Настройка безрамочного окна и прозрачного фона.
        # Важно: добавляем Qt.WindowType.Window, чтобы окно не обрезалось границами родительского окна и могло перемещаться в любое место экрана.
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setStyleSheet(DARK_THEME_STYLE)
        self.resize(560, 310)
        
        # Внешний layout для отступа под тень
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(5, 5, 5, 5)
        outer_layout.setSpacing(0)
        
        # Главный контейнер (для QSS границы и прямых углов)
        self.window_widget = QWidget(self)
        self.window_widget.setObjectName("SettingsWindowWidget")
        outer_layout.addWidget(self.window_widget)
        
        # Тень для эффекта глубины
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 0)
        self.window_widget.setGraphicsEffect(shadow)
        
        # Внутренний layout главного контейнера
        main_layout = QVBoxLayout(self.window_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        # Верхний заголовок
        self.title_bar = TitleBar(self, title="Настройки")
        # Скрываем кнопку настроек в окне настроек
        self.title_bar.btn_settings.hide()
        main_layout.addWidget(self.title_bar)
        
        # Центральный контейнер
        content_container = QWidget(self.window_widget)
        content_container_layout = QVBoxLayout(content_container)
        content_container_layout.setContentsMargins(15, 15, 15, 10)
        
        # Оборачиваем настройки в рамку SettingsGroup
        settings_group = QFrame(content_container)
        settings_group.setObjectName("SettingsGroup")
        content_container_layout.addWidget(settings_group)
        
        content_layout = QHBoxLayout(settings_group)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(15)
        
        # Левая панель - список разделов
        self.list_sections = QListWidget(settings_group)
        self.list_sections.setFixedWidth(120)
        self.list_sections.addItem("General")
        self.list_sections.setCurrentRow(0)
        content_layout.addWidget(self.list_sections)
        
        # Правая панель - содержимое
        self.stacked_widget = QStackedWidget(settings_group)
        
        # Раздел General
        self.general_widget = QWidget(settings_group)
        gen_layout = QVBoxLayout(self.general_widget)
        gen_layout.setContentsMargins(0, 0, 0, 0)
        gen_layout.setSpacing(10)
        
        lbl_path = QLabel("Путь к DLL Eclipse ESAPI:", self.general_widget)
        gen_layout.addWidget(lbl_path)
        
        path_box_layout = QHBoxLayout()
        self.txt_path = QLineEdit(self.config.get("eclipse_bin_path", ""), self.general_widget)
        path_box_layout.addWidget(self.txt_path)
        
        btn_browse = QPushButton("Обзор...", self.general_widget)
        btn_browse.clicked.connect(self.browse_folder)
        path_box_layout.addWidget(btn_browse)
        
        gen_layout.addLayout(path_box_layout)
        gen_layout.addStretch()
        
        self.stacked_widget.addWidget(self.general_widget)
        content_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(content_container)
        
        # Нижняя панель с кнопками
        buttons_widget = QWidget(self.window_widget)
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(15, 0, 15, 15)
        buttons_layout.addStretch()
        
        self.btn_save = QPushButton("Сохранить", self)
        self.btn_save.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.btn_save)
        
        self.btn_cancel = QPushButton("Отмена", self)
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)
        
        main_layout.addWidget(buttons_widget)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с DLL ESAPI", self.txt_path.text())
        if folder:
            self.txt_path.setText(folder)

    def save_settings(self):
        # Сохранение настроек
        self.config["eclipse_bin_path"] = self.txt_path.text().strip()
        from core.config import save_config
        save_config(self.config)
        self.accept()
