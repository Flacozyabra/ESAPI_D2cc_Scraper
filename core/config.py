# -*- coding: utf-8 -*-
import os
import json

VERSION = "1.0.0"

# Получаем путь к AppData/Local
LOCAL_APP_DATA = os.environ.get("LOCALAPPDATA")
if not LOCAL_APP_DATA:
    LOCAL_APP_DATA = os.path.expanduser("~")

CONFIG_DIR = os.path.join(LOCAL_APP_DATA, "ESAPI_D2cc_Scraper")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "eclipse_bin_path": r"C:\Program Files (x86)\Varian\RTM\17.0\esapi\API",
    "default_volume": 2.0,
    "check_updates_at_startup": True
}

def load_config():
    """Загружает конфигурацию из файла config.json."""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Дозаполняем отсутствующие ключи дефолтными
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception as e:
        print(f"[WARNING] Ошибка загрузки config.json: {e}. Используются настройки по умолчанию.")
        return DEFAULT_CONFIG

def save_config(config):
    """Сохраняет конфигурацию в файл config.json."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Не удалось сохранить конфигурацию: {e}")
        return False
