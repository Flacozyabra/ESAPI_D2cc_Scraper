# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, QCompleter, QMessageBox
from PyQt6.QtCore import Qt, QTimer, QStringListModel
from PyQt6.QtGui import QDoubleValidator
from .title_bar import TitleBar
from .settings_window import SettingsWindow
from .themes.dark import DARK_THEME_STYLE, COLOR_BACKGROUND, get_organ_field_style
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

        # Таймеры для debounce ввода (задержка поиска при вводе)
        self.name_timer = QTimer()
        self.name_timer.setSingleShot(True)
        self.name_timer.timeout.connect(self.search_patients_by_name)
        
        self.id_timer = QTimer()
        self.id_timer.setSingleShot(True)
        self.id_timer.timeout.connect(self.search_patients_by_id)

        self.init_ui()
        self.setup_connections()
        
        # Инициализация ESAPI подключения
        self.lbl_status.setText("Подключение к ESAPI...")
        self.worker.request_action("connect")

    def init_ui(self):
        # Настройка главного окна: безрамочность и темная тема
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(DARK_THEME_STYLE)
        self.resize(500, 480)
        
        # Главный контейнер
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)  # 1px рамка вокруг окна
        main_layout.setSpacing(0)
        
        # Заголовок (TitleBar)
        self.title_bar = TitleBar(self, title="ESAPI D2cc Scraper")
        self.title_bar.btn_settings.clicked.connect(self.open_settings)
        main_layout.addWidget(self.title_bar)
        
        # Контентная часть
        content_widget = QWidget(self)
        content_widget.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
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
        # Валидатор для чисел с плавающей точкой
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
        
        # Таблица/сетка органов и результатов
        results_grid = QGridLayout()
        results_grid.setSpacing(10)
        results_grid.setColumnStretch(0, 3)  # Орган (ComboBox)
        results_grid.setColumnStretch(1, 2)  # Рассчитанная доза (Value)
        results_grid.setColumnStretch(2, 4)  # Статус/информация
        
        # Заголовки колонок
        results_grid.addWidget(QLabel("<b>Орган / Структура</b>", self), 0, 0)
        results_grid.addWidget(QLabel("<b>Доза (Gy)</b>", self), 0, 1)
        results_grid.addWidget(QLabel("<b>Статус</b>", self), 0, 2)
        
        self.organ_widgets = {}
        organs = [("rectum", "Rectum"), ("bladder", "Bladder"), ("sigmoid", "Sigmoid"), ("bowel", "Bowel")]
        
        for idx, (organ_key, organ_title) in enumerate(organs, start=1):
            # ComboBox для выбора структуры
            cb = QComboBox(self)
            cb.setEditable(True)
            cb.setPlaceholderText(f"Выбор {organ_title}...")
            results_grid.addWidget(cb, idx, 0)
            
            # Метка для вывода значения дозы
            lbl_dose = QLabel("-", self)
            lbl_dose.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_dose.setStyleSheet("background-color: #121212; border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px;")
            results_grid.addWidget(lbl_dose, idx, 1)
            
            # Метка для вывода статуса/ошибки
            lbl_status = QLabel("Ожидание плана", self)
            lbl_status.setStyleSheet("color: #808080;")
            results_grid.addWidget(lbl_status, idx, 2)
            
            self.organ_widgets[organ_key] = {
                "combo": cb,
                "dose_label": lbl_dose,
                "status_label": lbl_status,
                "title": organ_title
            }
            
        content_layout.addLayout(results_grid)
        
        # Кнопка расчета
        self.btn_calculate = QPushButton("Рассчитать D2cc", self)
        self.btn_calculate.setObjectName("CalculateButton")
        self.btn_calculate.setEnabled(False)
        self.btn_calculate.clicked.connect(self.start_calculation)
        content_layout.addWidget(self.btn_calculate)
        
        # Статус-бар внизу
        self.lbl_status = QLabel("Готов к работе", self)
        self.lbl_status.setStyleSheet("color: #808080; font-size: 11px; padding-top: 5px;")
        content_layout.addWidget(self.lbl_status)
        
        main_layout.addWidget(content_widget)
        
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
        # Подключения сигналов воркера
        self.worker.connection_status.connect(self.on_connection_status)
        self.worker.patient_search_results.connect(self.on_patient_search_results)
        self.worker.patient_data_loaded.connect(self.on_patient_loaded)
        self.worker.calculation_completed.connect(self.on_calculation_completed)
        self.worker.error_occurred.connect(self.on_error)
        
        # Отслеживание ввода пользователя
        self.txt_name.textEdited.connect(self.on_name_edited)
        self.txt_id.textEdited.connect(self.on_id_edited)
        self.txt_plan_id.textEdited.connect(self.check_calculation_readiness)
        
        # События завершения выбора в автокомплитере
        self.name_completer.activated[str].connect(self.on_name_selected)
        self.id_completer.activated[str].connect(self.on_id_selected)
        self.plan_completer.activated[str].connect(self.on_plan_selected)
        
        # Событие нажатия Enter
        self.txt_name.returnPressed.connect(lambda: self.load_patient_by_field(is_id=False))
        self.txt_id.returnPressed.connect(lambda: self.load_patient_by_field(is_id=True))
        self.txt_plan_id.returnPressed.connect(self.on_plan_selected)

    # --- Обработка подключения ESAPI ---
    def on_connection_status(self, success, message):
        self.lbl_status.setText(message)
        if success:
            self.lbl_status.setStyleSheet("color: #4CAF50;")  # Зеленый
        else:
            self.lbl_status.setStyleSheet("color: #f44336;")  # Красный
            QMessageBox.critical(self, "Ошибка подключения", message)

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
        # Формируем списки для автокомплитера
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

    # --- Загрузка пациента и его планов ---
    def on_name_selected(self, name):
        self.lbl_status.setText(f"Загрузка пациента по имени: {name}...")
        self.worker.request_action("load_patient", patient_id_or_name=name, is_id=False)

    def on_id_selected(self, patient_id):
        self.lbl_status.setText(f"Загрузка пациента по ID: {patient_id}...")
        self.worker.request_action("load_patient", patient_id_or_name=patient_id, is_id=True)

    def load_patient_by_field(self, is_id=True):
        field_text = self.txt_id.text().strip() if is_id else self.txt_name.text().strip()
        if field_text:
            self.lbl_status.setText(f"Загрузка пациента: {field_text}...")
            self.worker.request_action("load_patient", patient_id_or_name=field_text, is_id=is_id)

    def on_patient_loaded(self, patient_id, patient_name, plans, structures):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.plans = plans
        self.all_structures = structures
        
        # Обновляем текстовые поля без триггера автопоиска
        self.txt_id.blockSignals(True)
        self.txt_name.blockSignals(True)
        self.txt_id.setText(patient_id)
        self.txt_name.setText(patient_name)
        self.txt_id.blockSignals(False)
        self.txt_name.blockSignals(False)
        
        # Обновляем комплитер планов
        self.plan_completer_model.setStringList(plans)
        
        # Сбрасываем старые данные органов
        for widget in self.organ_widgets.values():
            widget["combo"].clear()
            widget["dose_label"].setText("-")
            widget["status_label"].setText("Выберите план лечения")
            widget["status_label"].setStyleSheet("color: #808080;")
            widget["combo"].setStyleSheet("")
            
        self.txt_plan_id.clear()
        self.txt_plan_id.setFocus()
        self.lbl_status.setText(f"Пациент {patient_name} успешно загружен.")
        self.lbl_status.setStyleSheet("color: #e1e1e1;")
        self.check_calculation_readiness()

    # --- Обработка планов и органов ---
    def on_plan_selected(self, plan_id=""):
        plan_id = self.txt_plan_id.text().strip()
        if not plan_id or plan_id not in self.plans:
            return
            
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
                widget["status_label"].setText("Структура найдена")
                widget["status_label"].setStyleSheet("color: #4CAF50;")
            else:
                # Если совпадение не найдено, подсвечиваем поле красным
                cb.setStyleSheet(get_organ_field_style(is_valid=False))
                widget["status_label"].setText("Требуется ручной выбор")
                widget["status_label"].setStyleSheet("color: #d13438; font-weight: bold;")
                
            # Подключаем валидацию рамки при ручном изменении выбора
            cb.currentTextChanged.connect(lambda text, key=organ_key: self.validate_organ_field(key, text))
            
        self.check_calculation_readiness()

    def find_structure_match(self, organ_key):
        """Ищет первое совпадение среди синонимов для конкретного органа."""
        targets = self.synonyms[organ_key]
        # Точное совпадение
        for target in targets:
            for s in self.all_structures:
                if s.lower() == target.lower():
                    return s
        # Совпадение по подстроке
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
            widget["status_label"].setText("Выбрано вручную")
            widget["status_label"].setStyleSheet("color: #007acc;")
        else:
            cb.setStyleSheet(get_organ_field_style(is_valid=False))
            widget["status_label"].setText("Не найдено")
            widget["status_label"].setStyleSheet("color: #d13438;")
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
            widget["dose_label"].setText("-")
            widget["status_label"].setText("Расчет...")
            widget["status_label"].setStyleSheet("color: #808080;")
            
        self.lbl_status.setText("Выполняется расчет...")
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
            
            # Выводим дозу
            if res["dose"]:
                widget["dose_label"].setText(res["dose"])
            else:
                widget["dose_label"].setText("-")
                
            # Выводим статус
            widget["status_label"].setText(res["status"])
            if res["is_valid"]:
                widget["status_label"].setStyleSheet("color: #4CAF50;")  # Зеленый
            else:
                widget["status_label"].setStyleSheet("color: #f44336;")  # Красный
                
        self.lbl_status.setText("Расчет успешно завершен.")
        self.lbl_status.setStyleSheet("color: #4CAF50;")
        self.check_calculation_readiness()

    # --- Вспомогательные методы ---
    def open_settings(self):
        settings_dialog = SettingsWindow(self)
        if settings_dialog.exec():
            # Перезагружаем настройки
            self.config = load_config()
            self.lbl_status.setText("Настройки сохранены. Подключение к ESAPI...")
            self.worker.request_action("connect")

    def on_error(self, message):
        self.lbl_status.setText("Ошибка!")
        self.lbl_status.setStyleSheet("color: #f44336;")
        QMessageBox.warning(self, "Внимание", message)
        self.check_calculation_readiness()
