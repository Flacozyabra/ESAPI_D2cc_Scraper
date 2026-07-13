# -*- coding: utf-8 -*-
import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

DEFAULT_CONFIG = {
    "eclipse_bin_path": r"C:\Program Files (x86)\Varian\RTM\17.0\esapi\API",
    "default_volume": 2.0
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
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Не удалось сохранить конфигурацию: {e}")
        return False
