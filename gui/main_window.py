# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, QCompleter, QTextEdit, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QStringListModel
from PyQt6.QtGui import QDoubleValidator, QColor
from .title_bar import TitleBar
from .settings_window import SettingsWindow
from .themes.dark import DARK_THEME_STYLE, get_organ_field_style
from core.esapi_worker import EsapiWorker
from core.config import load_config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.worker = EsapiWorker()
        
        # Синонимы для автопоиска структур
        self.synonyms = {
            "rectum": ["rectum", "anorectum"],
            "bladder": ["bladder"],
            "sigmoid": ["sigma", "sigmoid"],
            "bowel": ["bowel", "bowelbag", "bowel bag", "bowel_bag"]
        }
        
        # Данные пациента и планов
        self.all_structures = []
        self.plans = []
        self.patient_id = ""
        self.patient_name = ""
        
        # Модели для автодополнения
        self.name_completer_model = QStringListModel()
        self.id_completer_model = QStringListModel()
        self.plan_completer_model = QStringListModel()

        # Таймеры для debounce ввода
        self.name_timer = QTimer()
        self.name_timer.setSingleShot(True)
        self.name_timer.timeout.connect(self.search_patients_by_name)
        
        self.id_timer = QTimer()
        self.id_timer.setSingleShot(True)
        self.id_timer.timeout.connect(self.search_patients_by_id)

        self.init_ui()
        self.setup_connections()
        
        # Инициализация ESAPI подключения
        self.write_log("Запуск приложения. Попытка подключения к ESAPI...", "info")
        self.worker.request_action("connect")

    def init_ui(self):
        # Настройка главного окна: безрамочность и прозрачный фон
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(DARK_THEME_STYLE)
        
        # Устанавливаем фиксированную ширину и переключаемую высоту
        self.setFixedWidth(520)
        self.setFixedHeight(550)  # Высота по умолчанию (с открытым логом)
        
        # Внешний layout для отступа под тень
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(5, 5, 5, 5)
        outer_layout.setSpacing(0)
        
        # Главный виджет контейнера (для отрисовки тени и границы)
        self.window_widget = QWidget(self)
        self.window_widget.setObjectName("MainWindowWidget")
        outer_layout.addWidget(self.window_widget)
        
        # Установка тени вокруг окна
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 0)
        self.window_widget.setGraphicsEffect(shadow)
        
        # Устанавливаем центральный виджет
        central_widget = QWidget(self)
        central_widget.setLayout(outer_layout)
        self.setCentralWidget(central_widget)
        
        # Основной layout внутри контейнера
        main_layout = QVBoxLayout(self.window_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        # Заголовок (TitleBar)
        self.title_bar = TitleBar(self, title="ESAPI D2cc Scraper")
        self.title_bar.btn_settings.clicked.connect(self.open_settings)
        main_layout.addWidget(self.title_bar)
        
        # Внутренний контейнер для формы
        content_widget = QWidget(self.window_widget)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 10)
        content_layout.setSpacing(15)
        
        # Сетка ввода (Patient Name, Patient ID, Plan ID, Volume)
        input_grid = QGridLayout()
        input_grid.setSpacing(10)
        
        # Строка 1: Patient Name и Patient ID
        input_grid.addWidget(QLabel("Patient Name:", self), 0, 0)
        self.txt_name = QLineEdit(self)
        self.txt_name.setPlaceholderText("Фамилия Имя...")
        input_grid.addWidget(self.txt_name, 0, 1)
        
        input_grid.addWidget(QLabel("ID:", self), 0, 2)
        self.txt_id = QLineEdit(self)
        self.txt_id.setPlaceholderText("ID пациента...")
        input_grid.addWidget(self.txt_id, 0, 3)
        
        # Строка 2: Plan ID и Volume
        input_grid.addWidget(QLabel("Plan ID:", self), 1, 0)
        self.txt_plan_id = QLineEdit(self)
        self.txt_plan_id.setPlaceholderText("Имя плана...")
        input_grid.addWidget(self.txt_plan_id, 1, 1)
        
        input_grid.addWidget(QLabel("Vol (cc):", self), 1, 2)
        self.txt_volume = QLineEdit(str(self.config.get("default_volume", 2.0)), self)
        volume_validator = QDoubleValidator(0.01, 100.0, 2, self)
        volume_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.txt_volume.setValidator(volume_validator)
        input_grid.addWidget(self.txt_volume, 1, 3)
        
        content_layout.addLayout(input_grid)
        
        # Разделительная линия
        line = QWidget(self)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #2d2d2d;")
        content_layout.addWidget(line)
        
        # Сетка результатов
        results_grid = QGridLayout()
        results_grid.setSpacing(10)
        results_grid.setColumnStretch(0, 3)  # Орган (ComboBox)
        results_grid.setColumnStretch(1, 2)  # SD
        results_grid.setColumnStretch(2, 2)  # TD
        
        # Заголовки колонок
        results_grid.addWidget(QLabel("<b>Орган / Структура</b>", self), 0, 0)
        results_grid.addWidget(QLabel("<b>SD</b>", self), 0, 1)
        results_grid.addWidget(QLabel("<b>TD</b>", self), 0, 2)
        
        self.organ_widgets = {}
        organs = [("rectum", "Rectum"), ("bladder", "Bladder"), ("sigmoid", "Sigmoid"), ("bowel", "Bowel")]
        
        for idx, (organ_key, organ_title) in enumerate(organs, start=1):
            cb = QComboBox(self)
            cb.setEditable(True)
            cb.setPlaceholderText(f"Выбор {organ_title}...")
            results_grid.addWidget(cb, idx, 0)
            
            lbl_sd = QLabel("n/a", self)
            lbl_sd.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_sd.setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; color: #808080;")
            results_grid.addWidget(lbl_sd, idx, 1)
            
            lbl_td = QLabel("n/a", self)
            lbl_td.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_td.setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; color: #808080;")
            results_grid.addWidget(lbl_td, idx, 2)
            
            self.organ_widgets[organ_key] = {
                "combo": cb,
                "sd_label": lbl_sd,
                "td_label": lbl_td,
                "title": organ_title
            }
            
        content_layout.addLayout(results_grid)
        
        # Кнопка расчета
        self.btn_calculate = QPushButton("Рассчитать D2cc", self)
        self.btn_calculate.setObjectName("CalculateButton")
        self.btn_calculate.setEnabled(False)
        self.btn_calculate.clicked.connect(self.start_calculation)
        content_layout.addWidget(self.btn_calculate)
        
        main_layout.addWidget(content_widget)
        
        # --- Секция лога и разделителя-кнопки ---
        # Кнопка-стрелка для сворачивания/разворачивания лога
        self.btn_toggle_log = QPushButton("▲", self)
        self.btn_toggle_log.setObjectName("LogToggleButton")
        self.btn_toggle_log.clicked.connect(self.toggle_log)
        main_layout.addWidget(self.btn_toggle_log)
        
        # Текстовое поле лога
        self.log_view = QTextEdit(self)
        self.log_view.setObjectName("LogView")
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(110)
        main_layout.addWidget(self.log_view)
        
        # Настройка автокомплитеров
        self.name_completer = QCompleter(self)
        self.name_completer.setModel(self.name_completer_model)
        self.name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.name_completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.txt_name.setCompleter(self.name_completer)
        
        self.id_completer = QCompleter(self)
        self.id_completer.setModel(self.id_completer_model)
        self.id_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.id_completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.txt_id.setCompleter(self.id_completer)

        self.plan_completer = QCompleter(self)
        self.plan_completer.setModel(self.plan_completer_model)
        self.plan_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.txt_plan_id.setCompleter(self.plan_completer)

    def setup_connections(self):
        self.worker.connection_status.connect(self.on_connection_status)
        self.worker.patient_search_results.connect(self.on_patient_search_results)
        self.worker.patient_data_loaded.connect(self.on_patient_loaded)
        self.worker.calculation_completed.connect(self.on_calculation_completed)
        self.worker.error_occurred.connect(self.on_error)
        
        self.txt_name.textEdited.connect(self.on_name_edited)
        self.txt_id.textEdited.connect(self.on_id_edited)
        self.txt_plan_id.textEdited.connect(self.check_calculation_readiness)
        
        self.name_completer.activated[str].connect(self.on_name_selected)
        self.id_completer.activated[str].connect(self.on_id_selected)
        self.plan_completer.activated[str].connect(self.on_plan_selected)
        
        self.txt_name.returnPressed.connect(lambda: self.load_patient_by_field(is_id=False))
        self.txt_id.returnPressed.connect(lambda: self.load_patient_by_field(is_id=True))
        self.txt_plan_id.returnPressed.connect(self.on_plan_selected)

    # --- Управление логом ---
    def write_log(self, message, level="info"):
        """Записывает строку лога с цветовым форматированием в нижнее текстовое поле."""
        color_map = {
            "info": "#ebebeb",
            "warning": "#e6a23c",
            "error": "#f56c6c",
            "success": "#67c23a"
        }
        color = color_map.get(level, "#ebebeb")
        self.log_view.append(f'<span style="color: {color};">[{level.upper()}] {message}</span>')

    def toggle_log(self):
        """Сворачивает / разворачивает лог при нажатии на разделитель."""
        if self.log_view.isVisible():
            self.log_view.setVisible(False)
            self.btn_toggle_log.setText("▼")
            self.setFixedHeight(430)  # Стягиваем нижний край вверх (без лога)
        else:
            self.log_view.setVisible(True)
            self.btn_toggle_log.setText("▲")
            self.setFixedHeight(550)  # Растягиваем вниз (с логом)

    # --- Обработка подключения ESAPI ---
    def on_connection_status(self, success, message):
        if success:
            self.write_log(message, "success")
        else:
            self.write_log(f"Не удалось загрузить библиотеки ESAPI: {message}", "error")
            self.write_log("Пожалуйста, откройте настройки (шестеренка вверху) и укажите корректный путь к DLL ESAPI.", "warning")

    # --- Поиск пациентов ---
    def on_name_edited(self, text):
        if len(text) >= 2:
            self.name_timer.start(300)

    def on_id_edited(self, text):
        if len(text) >= 2:
            self.id_timer.start(300)

    def search_patients_by_name(self):
        query = self.txt_name.text().strip()
        if query:
            self.worker.request_action("search_patients", query=query, by_id=False)

    def search_patients_by_id(self):
        query = self.txt_id.text().strip()
        if query:
            self.worker.request_action("search_patients", query=query, by_id=True)

    def on_patient_search_results(self, results, search_by_id):
        suggestions = []
        for r in results:
            if search_by_id:
                suggestions.append(r["id"])
            else:
                suggestions.append(r["name"])
                
        if search_by_id:
            self.id_completer_model.setStringList(suggestions)
        else:
            self.name_completer_model.setStringList(suggestions)

    # --- Загрузка пациента ---
    def on_name_selected(self, name):
        self.write_log(f"Запрос загрузки пациента по имени: {name}...", "info")
        self.worker.request_action("load_patient", patient_id_or_name=name, is_id=False)

    def on_id_selected(self, patient_id):
        self.write_log(f"Запрос загрузки пациента по ID: {patient_id}...", "info")
        self.worker.request_action("load_patient", patient_id_or_name=patient_id, is_id=True)

    def load_patient_by_field(self, is_id=True):
        field_text = self.txt_id.text().strip() if is_id else self.txt_name.text().strip()
        if field_text:
            self.write_log(f"Загрузка пациента: {field_text}...", "info")
            self.worker.request_action("load_patient", patient_id_or_name=field_text, is_id=is_id)

    def on_patient_loaded(self, patient_id, patient_name, plans, structures):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.plans = plans
        self.all_structures = structures
        
        self.txt_id.blockSignals(True)
        self.txt_name.blockSignals(True)
        self.txt_id.setText(patient_id)
        self.txt_name.setText(patient_name)
        self.txt_id.blockSignals(False)
        self.txt_name.blockSignals(False)
        
        self.plan_completer_model.setStringList(plans)
        
        # Сбрасываем старые данные органов
        for widget in self.organ_widgets.values():
            widget["combo"].clear()
            widget["sd_label"].setText("n/a")
            widget["td_label"].setText("n/a")
            widget["sd_label"].setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; color: #808080;")
            widget["td_label"].setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; color: #808080;")
            widget["combo"].setStyleSheet("")
            
        self.txt_plan_id.clear()
        self.txt_plan_id.setFocus()
        self.write_log(f"Пациент {patient_name} (ID: {patient_id}) загружен. Найдено планов: {len(plans)}.", "success")
        self.check_calculation_readiness()

    # --- Обработка планов и органов ---
    def on_plan_selected(self, plan_id=""):
        plan_id = self.txt_plan_id.text().strip()
        if not plan_id or plan_id not in self.plans:
            return
            
        self.write_log(f"Выбран план: '{plan_id}'. Выполняется автопоиск структур...", "info")
        
        # Заполняем комбобоксы всеми структурами плана
        for organ_key, widget in self.organ_widgets.items():
            cb = widget["combo"]
            cb.clear()
            cb.addItems(self.all_structures)
            
            # Автопоиск по синонимам
            matched_structure = self.find_structure_match(organ_key)
            if matched_structure:
                cb.setCurrentText(matched_structure)
                cb.setStyleSheet(get_organ_field_style(is_valid=True))
                cb.setToolTip("Структура успешно найдена автопоиском.")
                self.write_log(f"[{widget['title']}] Автоподстановка: '{matched_structure}'", "info")
            else:
                cb.setStyleSheet(get_organ_field_style(is_valid=False))
                cb.setToolTip("Структура не найдена. Выберите её вручную из списка.")
                self.write_log(f"[{widget['title']}] Структура автопоиском не найдена. Выберите вручную.", "warning")
                
            cb.currentTextChanged.connect(lambda text, key=organ_key: self.validate_organ_field(key, text))
            
        self.check_calculation_readiness()

    def find_structure_match(self, organ_key):
        targets = self.synonyms[organ_key]
        for target in targets:
            for s in self.all_structures:
                if s.lower() == target.lower():
                    return s
        for target in targets:
            for s in self.all_structures:
                if target.lower() in s.lower():
                    return s
        return None

    def validate_organ_field(self, organ_key, text):
        widget = self.organ_widgets[organ_key]
        cb = widget["combo"]
        if text.strip() in self.all_structures:
            cb.setStyleSheet(get_organ_field_style(is_valid=True))
            cb.setToolTip("Выбрано вручную.")
        else:
            cb.setStyleSheet(get_organ_field_style(is_valid=False))
            cb.setToolTip("Выбранная структура отсутствует в плане.")
        self.check_calculation_readiness()

    # --- Логика расчета ---
    def check_calculation_readiness(self):
        has_patient = bool(self.patient_id)
        has_plan = self.txt_plan_id.text().strip() in self.plans
        has_volume = bool(self.txt_volume.text().strip())
        self.btn_calculate.setEnabled(has_patient and has_plan and has_volume)

    def start_calculation(self):
        plan_id = self.txt_plan_id.text().strip()
        volume = self.txt_volume.text().replace(",", ".").strip()
        
        # Формируем карту сопоставления органов
        organs_mapping = {}
        for organ_key, widget in self.organ_widgets.items():
            organs_mapping[organ_key] = widget["combo"].currentText().strip()
            widget["sd_label"].setText("n/a")
            widget["td_label"].setText("...")
            widget["sd_label"].setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; color: #808080;")
            widget["td_label"].setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; color: #808080;")
            
        self.write_log(f"Запущен расчет D2cc на объем {volume} cc для плана '{plan_id}'...", "info")
        self.btn_calculate.setEnabled(False)
        
        self.worker.request_action(
            "calculate",
            patient_id=self.patient_id,
            plan_id=plan_id,
            organs_mapping=organs_mapping,
            volume=float(volume)
        )

    def on_calculation_completed(self, results):
        for organ_key, res in results.items():
            widget = self.organ_widgets[organ_key]
            
            if res["is_valid"]:
                widget["sd_label"].setText(res["sd"])
                widget["td_label"].setText(res["td"])
                widget["sd_label"].setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; color: #4CAF50; font-weight: bold;")
                widget["td_label"].setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; color: #4CAF50; font-weight: bold;")
                self.write_log(f"[{widget['title']}] Расчет успешен. SD: {res['sd']}, TD: {res['td']}", "success")
            else:
                widget["sd_label"].setText("n/a")
                widget["td_label"].setText(res.get("error_msg", "Ошибка"))
                widget["sd_label"].setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; color: #f44336;")
                widget["td_label"].setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; color: #f44336; font-size: 11px;")
                self.write_log(f"[{widget['title']}] Ошибка расчета: {res.get('error_msg')}", "error")
                
        self.write_log("Расчет успешно завершен.", "success")
        self.check_calculation_readiness()

    # --- Вспомогательные методы ---
    def open_settings(self):
        settings_dialog = SettingsWindow(self)
        if settings_dialog.exec():
            self.config = load_config()
            self.write_log("Путь к DLL обновлен. Переподключение к ESAPI...", "info")
            self.worker.request_action("connect")

    def on_error(self, message):
        self.write_log(message, "error")
        self.check_calculation_readiness()
