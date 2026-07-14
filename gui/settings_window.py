# -*- coding: utf-8 -*-
import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QStackedWidget, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QDialogButtonBox
from PyQt6.QtCore import Qt
from .themes.dark import DARK_THEME_STYLE
from core.locale import tr

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumWidth(550)
        self.setFixedHeight(320)
        
        # Применение темного режима заголовка Windows (как в DICOM WatchDog)
        if sys.platform == "win32":
            import ctypes
            try:
                hwnd = int(self.winId())
                # Включение темного режима (Immersive Dark Mode)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
                )
            except Exception:
                try:
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, 19, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
                    )
                except Exception:
                    pass

            # Установка темно-серого цвета #2b2b2b (BGR: 0x002b2b2b) для заголовка Windows 11
            try:
                hwnd = int(self.winId())
                # DWMWA_CAPTION_COLOR = 35
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 35, ctypes.byref(ctypes.c_int(0x002b2b2b)), ctypes.sizeof(ctypes.c_int)
                )
                # DWMWA_TEXT_COLOR = 36 (белый текст)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 36, ctypes.byref(ctypes.c_int(0x00ffffff)), ctypes.sizeof(ctypes.c_int)
                )
            except Exception:
                pass

        # Загрузка текущих настроек
        self.config = self.parent.config if parent else {}
        
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(DARK_THEME_STYLE)
        
        # Основной вертикальный макет диалога
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 10)
        outer_layout.setSpacing(10)
        
        # Горизонтальный макет для контента (боковое меню +stacked widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Левая часть: боковое меню (QListWidget)
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("settingsSidebar")
        self.sidebar.addItem(tr("sidebar_general"))
        self.sidebar.setCurrentRow(0)
        self.sidebar.setFixedWidth(140)
        main_layout.addWidget(self.sidebar)
        
        # Правая часть: stacked widget с контентом (прозрачный, наследует #202020 от рамки)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("QStackedWidget { background-color: transparent; padding: 15px; }")
        
        # Раздел General
        self.general_widget = QWidget()
        gen_layout = QVBoxLayout(self.general_widget)
        gen_layout.setContentsMargins(0, 0, 0, 0)
        gen_layout.setSpacing(10)
        
        lbl_path = QLabel(tr("lbl_dll_path"), self.general_widget)
        gen_layout.addWidget(lbl_path)
        
        path_box_layout = QHBoxLayout()
        self.txt_path = QLineEdit(self.config.get("eclipse_bin_path", ""), self.general_widget)
        path_box_layout.addWidget(self.txt_path)
        
        btn_browse = QPushButton(tr("btn_browse"), self.general_widget)
        btn_browse.clicked.connect(self.browse_folder)
        btn_browse.setFixedWidth(80)
        path_box_layout.addWidget(btn_browse)
        
        gen_layout.addLayout(path_box_layout)
        gen_layout.addStretch()
        
        self.stacked_widget.addWidget(self.general_widget)
        main_layout.addWidget(self.stacked_widget)
        
        outer_layout.addLayout(main_layout)
        
        # Панель кнопок (Save / Cancel) внизу
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.save_settings)
        self.button_box.rejected.connect(self.reject)
        
        # Контейнер для кнопок с правым отступом
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 15, 0)
        button_layout.addStretch()
        button_layout.addWidget(self.button_box)
        outer_layout.addLayout(button_layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr("dlg_select_dll_folder"), self.txt_path.text())
        if folder:
            self.txt_path.setText(folder)

    def save_settings(self):
        # Сохранение настроек
        self.config["eclipse_bin_path"] = self.txt_path.text().strip()
        from core.config import save_config
        save_config(self.config)
        self.accept()
