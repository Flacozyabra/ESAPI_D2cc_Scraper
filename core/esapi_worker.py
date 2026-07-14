# -*- coding: utf-8 -*-
import os
import sys
import ctypes
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from core.config import load_config
from core.locale import tr

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
        raise Exception(tr("log_conn_fail", message=f"Path '{eclipse_path}' does not exist."))

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
        raise Exception(tr("log_conn_fail", message=str(e)))

class EsapiWorker(QObject):
    # Сигналы для передачи результатов в главный поток GUI
    connection_status = pyqtSignal(bool, str)
    patient_search_results = pyqtSignal(list, bool)  # (results, search_by_id)
    patient_data_loaded = pyqtSignal(str, str, list, list)  # (patient_id, patient_name, plans, structures)
    calculation_completed = pyqtSignal(dict)  # {struct_type: {"id": str, "dose": str, "status": str, "is_valid": bool}}
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def request_action(self, action, **kwargs):
        """Выполняет действие в главном STA потоке GUI."""
        QApplication.processEvents()
        try:
            init_esapi()
        except Exception as e:
            self.connection_status.emit(False, str(e))
            self.error_occurred.emit(str(e))
            return

        try:
            if action == "connect":
                self._connect()
            elif action == "search_patients":
                self._search_patients(kwargs.get("query"), kwargs.get("by_id", True))
            elif action == "load_patient":
                self._load_patient(kwargs.get("patient_id_or_name"), kwargs.get("is_id", True))
            elif action == "calculate":
                self._calculate(
                    kwargs.get("patient_id"),
                    kwargs.get("plan_id"),
                    kwargs.get("organs_mapping"),
                    kwargs.get("volume", 2.0)
                )
        except Exception as e:
            self.error_occurred.emit(tr("err_action_failed", action=action, error=str(e)))

    def _connect(self):
        """Проверяет подключение к ESAPI и инициализирует Application."""
        global _app
        try:
            from VMS.TPS.Common.Model.API import CustomScriptExecutable
            if _app is None:
                _app = CustomScriptExecutable.CreateApplication("d2cc_scraper")
            self.connection_status.emit(True, tr("log_conn_success"))
        except Exception as e:
            self.connection_status.emit(False, tr("log_conn_fail", message=str(e)))

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
            self.error_occurred.emit(tr("err_search_patient", error=str(e)))

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
            try:
                _app.ClosePatient()
            except Exception:
                pass
            patient = _app.OpenPatientById(patient_id)
            if patient is None:
                self.error_occurred.emit(tr("err_patient_not_found", id=patient_id))
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
            self.error_occurred.emit(tr("err_load_patient", error=str(e)))

    def _calculate(self, patient_id, plan_id, organs_mapping, volume=2.0):
        """Выполняет расчет D2cc (или дозы на другой объем) для структур плана."""
        global _app
        results = {}
        try:
            from VMS.TPS.Common.Model.API import CustomScriptExecutable
            from VMS.TPS.Common.Model.Types import VolumePresentation, DoseValuePresentation
            
            if _app is None:
                _app = CustomScriptExecutable.CreateApplication("d2cc_scraper")
            try:
                _app.ClosePatient()
            except Exception:
                pass
            patient = _app.OpenPatientById(patient_id)
            if patient is None:
                self.error_occurred.emit(tr("err_patient_not_found_before_calc"))
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
                self.error_occurred.emit(tr("err_plan_not_found", plan_id=plan_id))
                return
                
            if plan.StructureSet is None:
                self.error_occurred.emit(tr("err_no_structure_set"))
                return

            # Получаем все структуры плана
            structures = {str(s.Id).lower(): s for s in plan.StructureSet.Structures}
            
            # Получаем количество фракций
            num_fractions = plan.NumberOfFractions
            
            # Выполняем расчет для каждого органа
            for organ_type, target_struct_id in organs_mapping.items():
                if not target_struct_id:
                    results[organ_type] = {"id": "", "sd": "n/a", "td": "n/a", "is_valid": False, "error_msg": "n/a"}
                    continue
                    
                struct = structures.get(target_struct_id.lower())
                if struct is None:
                    results[organ_type] = {"id": target_struct_id, "sd": "n/a", "td": "n/a", "is_valid": False, "error_msg": "n/a"}
                    continue
                
                # Проверка объема структуры
                struct_vol = struct.Volume
                if struct_vol < volume:
                    results[organ_type] = {
                        "id": str(struct.Id),
                        "sd": "n/a",
                        "td": "n/a",
                        "is_valid": False,
                        "error_msg": tr("err_structure_volume_low", volume=volume)
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
                            "sd": "n/a",
                            "td": "n/a",
                            "is_valid": False,
                            "error_msg": tr("err_no_dose")
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
                            
                        sd_str = f"{sd_val:.2f} {unit_str}" if sd_val is not None else "n/a"
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
                        "sd": "n/a",
                        "td": "n/a",
                        "is_valid": False,
                        "error_msg": tr("err_calculation_failed", error=str(ex))
                    }
            
            self.calculation_completed.emit(results)
        except Exception as e:
            self.error_occurred.emit(tr("err_critical_calc", error=str(e)))
