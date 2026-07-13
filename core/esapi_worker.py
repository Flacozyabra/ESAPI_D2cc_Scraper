# -*- coding: utf-8 -*-
import os
import sys
import ctypes
from PyQt6.QtCore import QThread, pyqtSignal
from core.config import load_config

# Глобальный флаг инициализации CLR
_ESAPI_INITIALIZED = False
_app = None

def init_esapi():
    """Динамически подключает DLL Eclipse ESAPI на основе настроек."""
    global _ESAPI_INITIALIZED, _app
    if _ESAPI_INITIALIZED:
        return True

    config = load_config()
    eclipse_path = config.get("eclipse_bin_path", "")

    if not os.path.exists(eclipse_path):
        raise Exception(f"Путь к DLL ESAPI '{eclipse_path}' не существует. Укажите верный путь в настройках.")

    # Добавляем путь в sys.path и PATH
    if eclipse_path not in sys.path:
        sys.path.append(eclipse_path)
    os.environ["PATH"] = eclipse_path + os.pathsep + os.environ["PATH"]

    try:
        # Инициализируем COM в режиме Single-Threaded Apartment (STA)
        try:
            ctypes.windll.ole32.CoInitializeEx(None, 2)
        except Exception:
            pass

        import clr
        clr.AddReference("VMS.TPS.Common.Model.API")
        clr.AddReference("VMS.TPS.Common.Model.Types")
        _ESAPI_INITIALIZED = True
        return True
    except Exception as e:
        raise Exception(f"Не удалось загрузить библиотеки ESAPI: {e}")

class EsapiWorker(QThread):
    # Сигналы для передачи результатов в главный поток GUI
    connection_status = pyqtSignal(bool, str)
    patient_search_results = pyqtSignal(list, bool)  # (results, search_by_id)
    patient_data_loaded = pyqtSignal(str, str, list, list)  # (patient_id, patient_name, plans, structures)
    calculation_completed = pyqtSignal(dict)  # {struct_type: {"id": str, "dose": str, "status": str, "is_valid": bool}}
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.action = None
        self.params = {}

    def run(self):
        """Точка входа потока."""
        try:
            init_esapi()
        except Exception as e:
            self.connection_status.emit(False, str(e))
            self.error_occurred.emit(str(e))
            return

        # Выполняем запрошенное действие
        if self.action == "connect":
            self._connect()
        elif self.action == "search_patients":
            self._search_patients(self.params.get("query"), self.params.get("by_id", True))
        elif self.action == "load_patient":
            self._load_patient(self.params.get("patient_id_or_name"), self.params.get("is_id", True))
        elif self.action == "calculate":
            self._calculate(
                self.params.get("patient_id"),
                self.params.get("plan_id"),
                self.params.get("organs_mapping"),
                self.params.get("volume", 2.0)
            )

    def request_action(self, action, **kwargs):
        """Запрашивает выполнение действия в потоке."""
        if self.isRunning():
            self.wait()  # Ожидаем завершения предыдущего действия, если оно идет
        self.action = action
        self.params = kwargs
        self.start()

    def _connect(self):
        """Проверяет подключение к ESAPI и инициализирует Application."""
        global _app
        try:
            from VMS.TPS.Common.Model.API import CustomScriptExecutable
            if _app is None:
                _app = CustomScriptExecutable.CreateApplication("d2cc_scraper")
            self.connection_status.emit(True, "Подключение к ESAPI успешно установлено.")
        except Exception as e:
            self.connection_status.emit(False, f"Ошибка подключения к ESAPI: {e}")

    def _search_patients(self, query, by_id=True):
        """Ищет пациентов по ID или фамилии."""
        global _app
        try:
            from VMS.TPS.Common.Model.API import CustomScriptExecutable
            if _app is None:
                _app = CustomScriptExecutable.CreateApplication("d2cc_scraper")
            
            query_lower = query.lower()
            results = []
            
            # Получаем краткую сводку по пациентам
            summaries = _app.PatientSummaries
            for summary in summaries:
                pid = str(summary.Id)
                plast = str(summary.LastName)
                pfirst = str(summary.FirstName)
                full_name = f"{plast} {pfirst}".strip()
                
                if by_id:
                    if query_lower in pid.lower():
                        results.append({"id": pid, "name": full_name})
                else:
                    if query_lower in full_name.lower():
                        results.append({"id": pid, "name": full_name})
                        
                # Ограничиваем количество предложений для производительности
                if len(results) >= 15:
                    break
                    
            self.patient_search_results.emit(results, by_id)
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при поиске пациента: {e}")

    def _load_patient(self, patient_id_or_name, is_id=True):
        """Загружает данные пациента: ФИО, список планов (исключая курс QA) и список всех структур первого плана."""
        global _app
        try:
            from VMS.TPS.Common.Model.API import CustomScriptExecutable
            if _app is None:
                _app = CustomScriptExecutable.CreateApplication("d2cc_scraper")
            
            patient_id = patient_id_or_name
            if not is_id:
                # Если передан Name, найдем сначала ID через summaries
                summaries = _app.PatientSummaries
                for s in summaries:
                    full_name = f"{s.LastName} {s.FirstName}".strip()
                    if full_name.lower() == patient_id_or_name.lower():
                        patient_id = s.Id
                        break
            
            # Закрываем предыдущего пациента и открываем нового
            patient = _app.OpenPatientById(patient_id)
            if patient is None:
                self.error_occurred.emit(f"Пациент с ID '{patient_id}' не найден в базе данных.")
                return
            
            patient_name = f"{patient.LastName} {patient.FirstName}".strip()
            
            # Перебираем планы во всех курсах, кроме курсов с именем "QA"
            plans = []
            all_structures = set()
            
            for course in patient.Courses:
                course_id = str(course.Id)
                if "QA" in course_id.upper():
                    continue  # Исключаем QA курсы
                    
                for plan in course.PlanSetups:
                    plan_id = str(plan.Id)
                    plans.append(plan_id)
                    
                    # Собираем структуры со всех планов для выпадающих списков
                    if plan.StructureSet is not None:
                        for struct in plan.StructureSet.Structures:
                            all_structures.add(str(struct.Id))
            
            self.patient_data_loaded.emit(
                str(patient.Id),
                patient_name,
                list(sorted(plans)),
                list(sorted(all_structures))
            )
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при загрузке данных пациента: {e}")

    def _calculate(self, patient_id, plan_id, organs_mapping, volume=2.0):
        """Выполняет расчет D2cc (или дозы на другой объем) для структур плана."""
        global _app
        results = {}
        try:
            from VMS.TPS.Common.Model.API import CustomScriptExecutable
            from VMS.TPS.Common.Model.Types import VolumePresentation, DoseValuePresentation
            
            if _app is None:
                _app = CustomScriptExecutable.CreateApplication("d2cc_scraper")
            
            patient = _app.OpenPatientById(patient_id)
            if patient is None:
                self.error_occurred.emit("Пациент не найден перед началом расчета.")
                return
                
            # Поиск плана по курсам (исключая QA)
            plan = None
            for course in patient.Courses:
                if "QA" in str(course.Id).upper():
                    continue
                for p in course.PlanSetups:
                    if str(p.Id).lower() == plan_id.lower():
                        plan = p
                        break
                if plan is not None:
                    break
                    
            if plan is None:
                self.error_occurred.emit(f"План '{plan_id}' не найден у пациента.")
                return
                
            if plan.StructureSet is None:
                self.error_occurred.emit("У выбранного плана отсутствует набор структур (StructureSet).")
                return

            # Получаем все структуры плана
            structures = {str(s.Id).lower(): s for s in plan.StructureSet.Structures}
            
            # Получаем количество фракций
            num_fractions = plan.NumberOfFractions
            
            # Выполняем расчет для каждого органа
            for organ_type, target_struct_id in organs_mapping.items():
                if not target_struct_id:
                    results[organ_type] = {"id": "", "sd": "-", "td": "-", "is_valid": False, "error_msg": "Не выбрано"}
                    continue
                    
                struct = structures.get(target_struct_id.lower())
                if struct is None:
                    results[organ_type] = {"id": target_struct_id, "sd": "-", "td": "-", "is_valid": False, "error_msg": "Не найдено"}
                    continue
                
                # Проверка объема структуры
                struct_vol = struct.Volume
                if struct_vol < volume:
                    results[organ_type] = {
                        "id": str(struct.Id),
                        "sd": "-",
                        "td": "-",
                        "is_valid": False,
                        "error_msg": f"Объем < {volume} cc"
                    }
                    continue
                
                try:
                    # Фиктивный (dummy) вызов для инициализации DVH данных
                    _ = plan.GetDVHCumulativeData(
                        struct, 
                        DoseValuePresentation.Absolute, 
                        VolumePresentation.AbsoluteCm3, 
                        0.1
                    )
                    
                    # Расчет дозы на заданный объем
                    dose_value = plan.GetDoseAtVolume(
                        struct, 
                        float(volume), 
                        VolumePresentation.AbsoluteCm3, 
                        DoseValuePresentation.Absolute
                    )
                    
                    is_undefined = dose_value.IsUndefined() if callable(dose_value.IsUndefined) else dose_value.IsUndefined
                    
                    if dose_value is None or is_undefined:
                        results[organ_type] = {
                            "id": str(struct.Id),
                            "sd": "-",
                            "td": "-",
                            "is_valid": False,
                            "error_msg": "Нет дозы"
                        }
                    else:
                        dose_val = dose_value.Dose
                        unit_str = str(dose_value.Unit)
                        
                        if "cGy" in unit_str:
                            dose_val = dose_val / 100.0
                            unit_str = "Gy"
                        elif "Gy" not in unit_str:
                            unit_str = "Gy"
                            
                        # Рассчитываем разовую дозу SD (Single Dose)
                        sd_val = None
                        if num_fractions is not None and num_fractions > 0:
                            sd_val = dose_val / num_fractions
                            
                        sd_str = f"{sd_val:.2f} {unit_str}" if sd_val is not None else "-"
                        td_str = f"{dose_val:.2f} {unit_str}"
                        
                        results[organ_type] = {
                            "id": str(struct.Id),
                            "sd": sd_str,
                            "td": td_str,
                            "is_valid": True
                        }
                except Exception as ex:
                    results[organ_type] = {
                        "id": str(struct.Id),
                        "sd": "-",
                        "td": "-",
                        "is_valid": False,
                        "error_msg": f"Ошибка: {ex}"
                    }
            
            self.calculation_completed.emit(results)
        except Exception as e:
            self.error_occurred.emit(f"Критическая ошибка при расчете: {e}")
