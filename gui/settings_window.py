# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QStackedWidget, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt6.QtCore import Qt
from .title_bar import TitleBar
from .theme import DARK_THEME_STYLE, COLOR_BACKGROUND
from core.config import load_config, save_config

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Загрузка текущих настроек
        self.config = load_config()
        
        self.init_ui()

    def init_ui(self):
        # Настройка окна: темная тема, безрамочность
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(DARK_THEME_STYLE)
        self.resize(550, 300)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)  # 1px граница окна
        main_layout.setSpacing(0)
        
        # Верхний заголовок
        self.title_bar = TitleBar(self, title="Настройки")
        # Скрываем кнопку настроек в окне настроек
        self.title_bar.btn_settings.hide()
        main_layout.addWidget(self.title_bar)
        
        # Центральный контейнер
        content_widget = QWidget(self)
        content_widget.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        
        # Левая панель - список разделов
        self.list_sections = QListWidget(self)
        self.list_sections.setFixedWidth(120)
        self.list_sections.addItem("General")
        self.list_sections.setCurrentRow(0)
        content_layout.addWidget(self.list_sections)
        
        # Правая панель - содержимое
        self.stacked_widget = QStackedWidget(self)
        
        # Раздел General
        self.general_widget = QWidget(self)
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
        
        main_layout.addWidget(content_widget)
        
        # Нижняя панель с кнопками
        buttons_widget = QWidget(self)
        buttons_widget.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
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
        save_config(self.config)
        self.accept()
