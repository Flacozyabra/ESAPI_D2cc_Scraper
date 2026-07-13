#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ESAPI D2cc Scraper
A standalone Python script to extract D2cc dose values for OARs (rectum, bladder, sigmoid, bowel)
from Varian Eclipse ESAPI using pythonnet.
"""

import os
import sys
import ctypes

# Enforce COM Single-Threaded Apartment (STA) mode for ESAPI COM components
try:
    # COINIT_APARTMENTTHREADED = 0x2
    ctypes.windll.ole32.CoInitializeEx(None, 2)
except Exception as e:
    print(f"[WARNING] Не удалось инициализировать COM STA: {e}")

def safe_exit(code=0):
    try:
        input("\nPress Enter to exit...")
    except (KeyboardInterrupt, EOFError):
        pass
    sys.exit(code)

# ==============================================================================
# НАСТРОЙКА ПУТЕЙ К DLL ECLIPSE ESAPI
# Для Eclipse v17.0 и выше стандартные DLL лежат в папке esapi/API.
# Примеры путей для разных версий:
# - C:\Program Files\Varian\RTM\17.0\esapi\API
# - C:\Program Files (x86)\Varian\RTM\17.0\esapi\API
# - C:\Program Files\Varian\ProductLine\Planning\PhysicalClinical\Bin
# ==============================================================================
ECLIPSE_BIN_PATH = r"C:\Program Files (x86)\Varian\RTM\17.0\esapi\API"

# Добавляем пути в sys.path и PATH для корректной работы pythonnet и загрузки нативных DLL
if os.path.exists(ECLIPSE_BIN_PATH):
    sys.path.append(ECLIPSE_BIN_PATH)
    # Нативные DLL Eclipse загружаются стандартным загрузчиком Windows.
    # Добавляем папку со сборками в переменную окружения PATH.
    os.environ["PATH"] = ECLIPSE_BIN_PATH + os.pathsep + os.environ["PATH"]
else:
    print(f"[WARNING] Путь '{ECLIPSE_BIN_PATH}' не найден.")
    print("Пожалуйста, убедитесь, что путь ECLIPSE_BIN_PATH в начале скрипта указан верно.")

# Подключаем pythonnet CLR
try:
    import clr
except ImportError:
    print("[ERROR] Библиотека 'pythonnet' не установлена.")
    print("Установите её с помощью команды: pip install pythonnet")
    safe_exit(1)

# Добавляем ссылки на стандартные DLL ESAPI (используются как в плагинах, так и в standalone приложениях)
required_dlls = [
    "VMS.TPS.Common.Model.API",
    "VMS.TPS.Common.Model.Types"
]

for dll in required_dlls:
    try:
        clr.AddReference(dll)
    except Exception as e:
        print(f"[WARNING] Не удалось загрузить сборку '{dll}': {e}")

# Импортируем типы из пространств имен VMS.TPS
try:
    from VMS.TPS.Common.Model.API import Application, CustomScriptExecutable
    from VMS.TPS.Common.Model.Types import VolumePresentation, DoseValuePresentation
except ImportError as e:
    print(f"[ERROR] Не удалось импортировать классы из ESAPI: {e}")
    print("Проверьте правильность путей и наличие лицензий/сборок.")
    safe_exit(1)


def find_structure(structures, target_name):
    """
    Ищет структуру в коллекции structures.
    Сначала ищет точное совпадение (без учета регистра),
    если не найдено - ищет по вхождению подстроки.
    """
    target_lower = target_name.lower()
    
    # 1. Точное совпадение
    for struct in structures:
        if struct.Id.lower() == target_lower:
            return struct
            
    # 2. Поиск по подстроке
    for struct in structures:
        if target_lower in struct.Id.lower():
            return struct
            
    return None


def calculate_d2cc(patient_id, course_id, plan_id):
    """
    Основная функция подключения к Eclipse, загрузки плана и расчета D2cc.
    """
    app = None
    try:
        print("\nИнициализация приложения Eclipse ESAPI...")
        # Создаем приложение через CustomScriptExecutable для поддержки unmanaged окружения (Python/EXE)
        app = CustomScriptExecutable.CreateApplication("d2cc_scraper")
        print("Подключение успешно установлено.")
        
        print(f"Открытие пациента: '{patient_id}'...")
        patient = app.OpenPatientById(patient_id)
        if patient is None:
            print(f"[ERROR] Пациент с ID '{patient_id}' не найден.")
            return

        print(f"Поиск курса: '{course_id}'...")
        course = None
        for c in patient.Courses:
            if c.Id.lower() == course_id.lower():
                course = c
                break
                
        if course is None:
            print(f"[ERROR] Курс '{course_id}' не найден для пациента '{patient_id}'.")
            return

        print(f"Поиск плана: '{plan_id}'...")
        plan = None
        for p in course.PlanSetups:
            if p.Id.lower() == plan_id.lower():
                plan = p
                break

        if plan is None:
            print(f"[ERROR] План '{plan_id}' не найден в курсе '{course_id}'.")
            return

        # Проверка типа плана (поддерживается только ExternalPlanSetup)
        plan_type = plan.GetType().Name
        if "ExternalPlanSetup" not in plan_type:
            print(f"[ERROR] План '{plan_id}' имеет тип '{plan_type}'. Поддерживается только ExternalPlanSetup.")
            return

        # Проверка наличия контура структур
        if plan.StructureSet is None:
            print(f"[ERROR] В плане '{plan_id}' отсутствует набор структур (StructureSet).")
            return

        structures = list(plan.StructureSet.Structures)
        target_structures = ['rectum', 'bladder', 'sigmoid', 'bowel']
        

        
        print("\n" + "="*50)
        print(f"Результаты расчета D2cc для плана: {plan.Id}")
        print("="*50)
        
        for target in target_structures:
            struct = find_structure(structures, target)
            if struct is None:
                print(f"{target.capitalize():<10} | Структура не найдена")
                continue
                
            # Расчет D2cc (доза на объем 2.0 cc)
            try:
                struct_vol = struct.Volume
                if struct_vol < 2.0:
                    print(f"{struct.Id:<10} | объем структуры < 2 cc")
                    continue
                
                # Фиктивный (dummy) вызов для инициализации DVH данных и загрузки Dose Matrix в память
                _ = plan.GetDVHCumulativeData(
                    struct, 
                    DoseValuePresentation.Absolute, 
                    VolumePresentation.AbsoluteCm3, 
                    0.1
                )
                
                # GetDoseAtVolume принимает: Structure, Volume, VolumePresentation, DoseValuePresentation
                dose_value = plan.GetDoseAtVolume(
                    struct, 
                    2.0, 
                    VolumePresentation.AbsoluteCm3, 
                    DoseValuePresentation.Absolute
                )
                
                is_undefined = dose_value.IsUndefined() if callable(dose_value.IsUndefined) else dose_value.IsUndefined
                if dose_value is None or is_undefined:
                    print(f"{struct.Id:<10} | нет дозы")
                else:
                    # Приводим к Gy, если доза вернулась в cGy
                    dose_val = dose_value.Dose
                    unit_str = str(dose_value.Unit)
                    
                    if "cGy" in unit_str:
                        dose_val = dose_val / 100.0
                        unit_str = "Gy"
                    elif "Gy" not in unit_str:
                        # Если доза в процентах или неизвестна, но мы просили Absolute, выводим как есть
                        unit_str = "Gy" # Безопасное допущение для абсолютной дозы
                        
                    print(f"{struct.Id:<10} | D2cc = {dose_val:.2f} {unit_str}")
            except Exception as ex:
                print(f"{struct.Id:<10} | Ошибка расчета: {ex}")
                
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"[ERROR] Произошла ошибка во время выполнения: {e}")
    finally:
        if app is not None:
            print("Закрытие сессии Eclipse...")
            try:
                app.Dispose()
                print("Сессия успешно закрыта.")
            except Exception as e:
                print(f"[ERROR] Не удалось закрыть сессию корректно: {e}")


if __name__ == "__main__":
    # Параметры по умолчанию (пользователь может переопределить их)
    default_patient_id = "PATIENT_ID"
    default_course_id = "COURSE_ID"
    default_plan_id = "PLAN_ID"

    print("=== ESAPI D2cc Scraper ===")
    
    # Запрос данных у пользователя
    try:
        patient_id = input(f"Введите Patient ID [{default_patient_id}]: ").strip()
        if not patient_id:
            patient_id = default_patient_id
            
        course_id = input(f"Введите Course ID [{default_course_id}]: ").strip()
        if not course_id:
            course_id = default_course_id
            
        plan_id = input(f"Введите Plan ID [{default_plan_id}]: ").strip()
        if not plan_id:
            plan_id = default_plan_id

        calculate_d2cc(patient_id, course_id, plan_id)
        safe_exit(0)
    except KeyboardInterrupt:
        print("\nВыполнение прервано пользователем.")
        safe_exit(0)
    except Exception as e:
        print(f"[ERROR] Непредвиденная ошибка: {e}")
        safe_exit(1)
