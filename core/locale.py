# -*- coding: utf-8 -*-
import os
import json
import sys

_translations = {}

def load_locale():
    global _translations
    # Пытаемся определить путь к en.json (включая работу в скомпилированном PyInstaller виде)
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    locale_path = os.path.join(base_path, "locales", "en.json")
    
    # Резервный поиск в папке рядом с exe
    exe_dir = os.path.dirname(sys.executable) if hasattr(sys, 'frozen') else os.getcwd()
    external_locale_path = os.path.join(exe_dir, "locales", "en.json")
    
    path_to_load = locale_path
    if os.path.exists(external_locale_path):
        path_to_load = external_locale_path
        
    try:
        with open(path_to_load, "r", encoding="utf-8") as f:
            _translations = json.load(f)
    except Exception as e:
        print(f"Error loading localization: {e}")
        _translations = {}

def tr(key, **kwargs):
    text = _translations.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            pass
    return text

# Загружаем при первом импорте
load_locale()
