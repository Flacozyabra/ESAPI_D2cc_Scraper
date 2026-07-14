# -*- coding: utf-8 -*-
import sys
import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, QCompleter, QTextEdit, QGraphicsDropShadowEffect, QFrame
from PyQt6.QtCore import Qt, QTimer, QStringListModel, QPoint
from PyQt6.QtGui import QDoubleValidator, QColor, QPainter, QPolygon, QBrush, QIcon
from .title_bar import TitleBar
from .settings_window import SettingsWindow
from .themes.dark import DARK_THEME_STYLE, get_organ_field_style
from core.esapi_worker import EsapiWorker
from core.config import load_config
from core.locale import tr

class LogToggleButton(QPushButton):
    """Кастомный сплиттер-кнопка из DICOM WatchDog с тонкой линией и сплюснутой стрелочкой."""
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.is_collapsed = False
        self.setMouseTracking(True)
        self.setObjectName("LogToggleButton")
        self.setFixedHeight(8)

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Рисуем линию по центру (сплиттерная линия, как в DICOM WatchDog)
        w = self.width()
        cy = self.height() // 2
        painter.setPen(QColor("#3F3F46"))
        painter.drawLine(15, cy, w - 15, cy)
        
        cx = w // 2
        
        # Цвет стрелки (серый по умолчанию, синий при наведении как в DICOM WatchDog)
        arrow_color = QColor("#71717A")
        if self.underMouse():
            arrow_color = QColor("#1f538d")
            
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(arrow_color))
        
        # Сплюснутый треугольник (ширина основания 20px, высота 4px)
        if self.is_collapsed:
            p1 = QPoint(cx, cy + 2)
            p2 = QPoint(cx - 10, cy - 2)
            p3 = QPoint(cx + 10, cy - 2)
        else:
            p1 = QPoint(cx, cy - 2)
            p2 = QPoint(cx - 10, cy + 2)
            p3 = QPoint(cx + 10, cy + 2)
            
        poly = QPolygon([p1, p2, p3])
        painter.drawPolygon(poly)


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
        self.write_log(tr("log_conn_start"), "info")
        self.worker.request_action("connect")

    def init_ui(self):
        # Настройка главного окна: безрамочность и прозрачный фон
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(DARK_THEME_STYLE)
        
        # Иконка окна
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.setWindowIcon(QIcon(os.path.join(base_path, "src", "Eclipse_logo.png")))
        
        # Устанавливаем фиксированную ширину (600) и переключаемую высоту
        self.setFixedWidth(600)
        self.setFixedHeight(560)
        
        # Внешний layout для отступа под тень
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(5, 5, 5, 5)
        outer_layout.setSpacing(0)
        
        # Главный виджет контейнера
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
        self.title_bar = TitleBar(self, title=tr("window_title"))
        self.title_bar.btn_settings.clicked.connect(self.open_settings)
        main_layout.addWidget(self.title_bar)
        
        # Внутренний контейнер для формы (высота жестко фиксирована 390px, чтобы не сжиматься при скрытии лога)
        self.content_widget = QWidget(self.window_widget)
        self.content_widget.setFixedHeight(390)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 20, 20, 10)
        content_layout.setSpacing(15)
        
        # --- ОТДЕЛ ВВОДА: в рамке InputGroup ---
        self.input_group = QFrame(self.window_widget)
        self.input_group.setObjectName("InputGroup")
        input_group_layout = QVBoxLayout(self.input_group)
        input_group_layout.setContentsMargins(12, 12, 12, 12)
        
        input_grid = QGridLayout()
        input_grid.setSpacing(10)
        input_grid.setColumnStretch(0, 0)
        input_grid.setColumnStretch(1, 3)  # Поле Patient Name / Plan ID (длиннее)
        input_grid.setColumnStretch(2, 0)
        input_grid.setColumnStretch(3, 2)  # Поле ID / Volume (короче, но в два раза шире чем было)
        
        input_grid.addWidget(QLabel(tr("patient_name"), self), 0, 0)
        self.txt_name = QLineEdit(self)
        self.txt_name.setPlaceholderText(tr("patient_name_placeholder"))
        input_grid.addWidget(self.txt_name, 0, 1)
        
        input_grid.addWidget(QLabel(tr("patient_id"), self), 0, 2)
        self.txt_id = QLineEdit(self)
        self.txt_id.setPlaceholderText(tr("patient_id_placeholder"))
        input_grid.addWidget(self.txt_id, 0, 3)
        
        input_grid.addWidget(QLabel(tr("plan_id"), self), 1, 0)
        self.txt_plan_id = QLineEdit(self)
        self.txt_plan_id.setPlaceholderText(tr("plan_id_placeholder"))
        input_grid.addWidget(self.txt_plan_id, 1, 1)
        
        input_grid.addWidget(QLabel(tr("volume"), self), 1, 2)
        self.txt_volume = QLineEdit(str(self.config.get("default_volume", 2.0)), self)
        self.txt_volume.setMaximumWidth(70)  # Ограничиваем ширину поля объема
        volume_validator = QDoubleValidator(0.01, 100.0, 2, self)
        volume_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.txt_volume.setValidator(volume_validator)
        input_grid.addWidget(self.txt_volume, 1, 3, Qt.AlignmentFlag.AlignLeft)
        
        input_group_layout.addLayout(input_grid)
        content_layout.addWidget(self.input_group)
        
        # --- ОТДЕЛ РЕЗУЛЬТАТОВ: в рамке ResultsGroup ---
        self.results_group = QFrame(self.window_widget)
        self.results_group.setObjectName("ResultsGroup")
        results_group_layout = QVBoxLayout(self.results_group)
        results_group_layout.setContentsMargins(12, 12, 12, 12)
        
        results_grid = QGridLayout()
        results_grid.setSpacing(10)
        results_grid.setColumnStretch(0, 3)  # OAR
        results_grid.setColumnStretch(1, 2)  # SD
        results_grid.setColumnStretch(2, 2)  # TD
        
        # Заголовки колонок центрированы
        lbl_oar = QLabel(f"<b>{tr('patient_name').replace(':', '').strip() if 'OAR' in tr('patient_name') else 'OAR'}</b>", self)
        lbl_oar.setText("<b>OAR</b>")
        lbl_oar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_grid.addWidget(lbl_oar, 0, 0)
        
        lbl_sd_hdr = QLabel("<b>SD</b>", self)
        lbl_sd_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_grid.addWidget(lbl_sd_hdr, 0, 1)
        
        lbl_td_hdr = QLabel("<b>TD</b>", self)
        lbl_td_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_grid.addWidget(lbl_td_hdr, 0, 2)
        
        self.organ_widgets = {}
        organs = [("rectum", "Rectum"), ("bladder", "Bladder"), ("sigmoid", "Sigmoid"), ("bowel", "Bowel")]
        
        for idx, (organ_key, organ_title) in enumerate(organs, start=1):
            cb = QComboBox(self)
            cb.setEditable(True)
            cb.addItem("n/a")
            cb.setCurrentText("n/a")
            results_grid.addWidget(cb, idx, 0)
            
            lbl_sd = QLabel("n/a", self)
            lbl_sd.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_sd.setStyleSheet("background-color: #0f0f0f; border: 1px solid #3d3d3d; border-radius: 6px; padding: 4px; color: #808080; min-height: 24px;")
            results_grid.addWidget(lbl_sd, idx, 1)
            
            lbl_td = QLabel("n/a", self)
            lbl_td.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_td.setStyleSheet("background-color: #0f0f0f; border: 1px solid #3d3d3d; border-radius: 6px; padding: 4px; color: #808080; min-height: 24px;")
            results_grid.addWidget(lbl_td, idx, 2)
            
            self.organ_widgets[organ_key] = {
                "combo": cb,
                "sd_label": lbl_sd,
                "td_label": lbl_td,
                "title": organ_title
            }
            
        results_group_layout.addLayout(results_grid)
        content_layout.addWidget(self.results_group)
        
        # Кнопка расчета
        self.btn_calculate = QPushButton(tr("btn_calculate"), self)
        self.btn_calculate.setObjectName("CalculateButton")
        self.btn_calculate.setEnabled(False)
        self.btn_calculate.clicked.connect(self.start_calculation)
        content_layout.addWidget(self.btn_calculate)
        
        main_layout.addWidget(self.content_widget)
        
        # --- Секция лога и разделителя-кнопки ---
        self.btn_toggle_log = LogToggleButton(parent=self)
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
        self.name_completer.popup().setStyleSheet("background-color: #0f0f0f; color: #ffffff; border: 1px solid #3d3d3d; selection-background-color: #1f538d; selection-color: #ffffff;")
        self.txt_name.setCompleter(self.name_completer)
        
        self.id_completer = QCompleter(self)
        self.id_completer.setModel(self.id_completer_model)
        self.id_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.id_completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.id_completer.popup().setStyleSheet("background-color: #0f0f0f; color: #ffffff; border: 1px solid #3d3d3d; selection-background-color: #1f538d; selection-color: #ffffff;")
        self.txt_id.setCompleter(self.id_completer)

        self.plan_completer = QCompleter(self)
        self.plan_completer.setModel(self.plan_completer_model)
        self.plan_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.plan_completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.plan_completer.popup().setStyleSheet("background-color: #0f0f0f; color: #ffffff; border: 1px solid #3d3d3d; selection-background-color: #1f538d; selection-color: #ffffff;")
        self.txt_plan_id.setCompleter(self.plan_completer)
        self.txt_plan_id.installEventFilter(self)

    def setup_connections(self):
        self.worker.connection_status.connect(self.on_connection_status)
        self.worker.patient_search_results.connect(self.on_patient_search_results)
        self.worker.patient_data_loaded.connect(self.on_patient_loaded)
        self.worker.calculation_completed.connect(self.on_calculation_completed)
        self.worker.error_occurred.connect(self.on_error)
        
        self.txt_name.textEdited.connect(self.on_name_edited)
        self.txt_id.textEdited.connect(self.on_id_edited)
        self.txt_plan_id.textEdited.connect(self.check_calculation_readiness)
        self.btn_toggle_log.clicked.connect(self.toggle_log)
        
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
            self.btn_toggle_log.is_collapsed = True
            self.btn_toggle_log.update()
            self.setFixedHeight(440)  # Стягиваем нижний край вверх
        else:
            self.log_view.setVisible(True)
            self.btn_toggle_log.is_collapsed = False
            self.btn_toggle_log.update()
            self.setFixedHeight(560)  # Растягиваем вниз

    # --- Обработка подключения ESAPI ---
    def on_connection_status(self, success, message):
        if success:
            self.write_log(message, "success")
        else:
            self.write_log(message, "error")

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
        self.write_log(tr("log_loading_patient", query=name), "info")
        self.worker.request_action("load_patient", patient_id_or_name=name, is_id=False)

    def on_id_selected(self, patient_id):
        self.write_log(tr("log_loading_patient", query=patient_id), "info")
        self.worker.request_action("load_patient", patient_id_or_name=patient_id, is_id=True)

    def load_patient_by_field(self, is_id=True):
        field_text = self.txt_id.text().strip() if is_id else self.txt_name.text().strip()
        if field_text:
            self.write_log(tr("log_loading_patient", query=field_text), "info")
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
            cb = widget["combo"]
            cb.blockSignals(True)
            cb.clear()
            cb.addItem("n/a")
            cb.setCurrentText("n/a")
            cb.blockSignals(False)
            
            widget["sd_label"].setText("n/a")
            widget["td_label"].setText("n/a")
            widget["sd_label"].setStyleSheet("background-color: #0f0f0f; border: 1px solid #3d3d3d; border-radius: 6px; padding: 4px; color: #808080; min-height: 24px;")
            widget["td_label"].setStyleSheet("background-color: #0f0f0f; border: 1px solid #3d3d3d; border-radius: 6px; padding: 4px; color: #808080; min-height: 24px;")
            widget["combo"].setStyleSheet("")
            
        self.txt_plan_id.clear()
        self.txt_plan_id.setFocus()
        self.write_log(tr("log_patient_loaded", name=patient_name, id=patient_id, count=len(plans)), "success")
        self.check_calculation_readiness()

    # --- Обработка планов и органов ---
    def on_plan_selected(self, plan_id=""):
        plan_id = self.txt_plan_id.text().strip()
        if not plan_id or plan_id not in self.plans:
            return
            
        self.write_log(tr("log_plan_selected", plan_id=plan_id), "info")
        
        # Заполняем комбобоксы всеми структурами плана
        for organ_key, widget in self.organ_widgets.items():
            cb = widget["combo"]
            cb.blockSignals(True)
            cb.clear()
            cb.addItem("n/a")
            cb.addItems(self.all_structures)
            cb.blockSignals(False)
            
            # Автопоиск по синонимам
            matched_structure = self.find_structure_match(organ_key)
            if matched_structure:
                cb.setCurrentText(matched_structure)
                cb.setStyleSheet(get_organ_field_style(is_valid=True))
                cb.setToolTip("Structure successfully auto-matched.")
                self.write_log(f"[{widget['title']}] Auto-match: '{matched_structure}'", "info")
            else:
                cb.setCurrentText("n/a")
                cb.setStyleSheet(get_organ_field_style(is_valid=False))
                cb.setToolTip("Structure not matched. Select manually.")
                
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
        if text.strip() == "n/a" or not text.strip():
            cb.setStyleSheet(get_organ_field_style(is_valid=False))
            cb.setToolTip("No structure selected.")
        elif text.strip() in self.all_structures:
            cb.setStyleSheet(get_organ_field_style(is_valid=True))
            cb.setToolTip("Manually selected.")
        else:
            cb.setStyleSheet(get_organ_field_style(is_valid=False))
            cb.setToolTip("Selected structure not found in plan.")
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
            val = widget["combo"].currentText().strip()
            if val == "n/a" or not val:
                organs_mapping[organ_key] = ""
            else:
                organs_mapping[organ_key] = val
                
            widget["sd_label"].setText("n/a")
            widget["td_label"].setText("...")
            widget["sd_label"].setStyleSheet("background-color: #0f0f0f; border: 1px solid #3d3d3d; border-radius: 6px; padding: 4px; color: #808080; min-height: 24px;")
            widget["td_label"].setStyleSheet("background-color: #0f0f0f; border: 1px solid #3d3d3d; border-radius: 6px; padding: 4px; color: #808080; min-height: 24px;")
            
        self.write_log(tr("log_calc_start", volume=volume, plan_id=plan_id), "info")
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
                widget["sd_label"].setStyleSheet("background-color: #0f0f0f; border: 1px solid #3d3d3d; border-radius: 6px; padding: 4px; color: #ffffff; min-height: 24px;")
                widget["td_label"].setStyleSheet("background-color: #0f0f0f; border: 1px solid #3d3d3d; border-radius: 6px; padding: 4px; color: #ffffff; min-height: 24px;")
                self.write_log(tr("log_calc_success", organ=widget['title'], sd=res['sd'], td=res['td']), "success")
            else:
                widget["sd_label"].setText("n/a")
                widget["td_label"].setText(res.get("error_msg", "Error"))
                widget["sd_label"].setStyleSheet("background-color: #0f0f0f; border: 1px solid #3d3d3d; border-radius: 6px; padding: 4px; color: #f44336; min-height: 24px;")
                widget["td_label"].setStyleSheet("background-color: #0f0f0f; border: 1px solid #3d3d3d; border-radius: 6px; padding: 4px; color: #f44336; font-size: 11px; min-height: 24px;")
                self.write_log(tr("log_calc_error", organ=widget['title'], error=res.get('error_msg')), "error")
                
        self.write_log(tr("log_calc_finished"), "success")
        self.check_calculation_readiness()

    # --- Вспомогательные методы ---
    def open_settings(self):
        settings_dialog = SettingsWindow(self)
        if settings_dialog.exec():
            self.config = load_config()
            self.write_log(tr("log_updating_dll"), "info")
            self.worker.request_action("connect")

    def on_error(self, message):
        self.write_log(message, "error")
        self.check_calculation_readiness()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj == self.txt_plan_id and event.type() == QEvent.Type.MouseButtonPress:
            if self.txt_plan_id.text().strip() == "":
                self.plan_completer.setCompletionPrefix("")
            self.plan_completer.complete()
        return super().eventFilter(obj, event)
