# -*- coding: utf-8 -*-
import os
import sys
import json
import urllib.request
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QProgressDialog, QMessageBox, QApplication
from core.config import CONFIG_DIR, VERSION, save_config
from core.locale import tr

_active_workers = set()

def apply_dark_title_bar(widget):
    if sys.platform == "win32":
        import ctypes
        try:
            hwnd = int(widget.winId())
            # Immersive Dark Mode
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
            )
            # Caption Color (#2b2b2b)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 35, ctypes.byref(ctypes.c_int(0x002b2b2b)), ctypes.sizeof(ctypes.c_int)
            )
            # Text Color (White)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 36, ctypes.byref(ctypes.c_int(0x00ffffff)), ctypes.sizeof(ctypes.c_int)
            )
        except Exception:
            pass

class UpdateCheckWorker(QThread):
    finished = pyqtSignal(str, str, dict)

    def run(self):
        url = "https://api.github.com/repos/Flacozyabra/ESAPI_D2cc_Scraper/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'ESAPI_D2cc_Scraper'})
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                tag_name = data.get('tag_name', '')
                html_url = data.get('html_url', 'https://github.com/Flacozyabra/ESAPI_D2cc_Scraper/releases')
                
                assets_dict = {}
                for asset in data.get('assets', []):
                    name = asset.get('name', '')
                    download_url = asset.get('browser_download_url', '')
                    if name and download_url:
                        assets_dict[name] = download_url
                        
                self.finished.emit(tag_name or "", html_url or "", assets_dict or {})
        except Exception as e:
            print(f"Error checking for updates: {e}")
            self.finished.emit("", "", {})

class FileDownloadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'ESAPI_D2cc_Scraper-Updater'})
            with urllib.request.urlopen(req, timeout=15) as response:
                total_size = int(response.info().get('Content-Length', 0))
                bytes_downloaded = 0
                block_size = 1024 * 8
                
                with open(self.dest_path, 'wb') as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        bytes_downloaded += len(buffer)
                        f.write(buffer)
                        if total_size > 0:
                            percent = int((bytes_downloaded / total_size) * 100)
                            self.progress.emit(percent)
                            
            self.progress.emit(100)
            self.finished.emit(self.dest_path)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit("")

def is_newer_version(current_version, latest_version):
    if not latest_version:
        return False
    curr = current_version.lower().lstrip('v')
    late = latest_version.lower().lstrip('v')
    try:
        curr_parts = [int(p) for p in curr.split('.')]
        late_parts = [int(p) for p in late.split('.')]
        max_len = max(len(curr_parts), len(late_parts))
        curr_parts += [0] * (max_len - len(curr_parts))
        late_parts += [0] * (max_len - len(late_parts))
        return late_parts > curr_parts
    except ValueError:
        return late > curr

def run_auto_update(parent, latest_version, assets):
    is_frozen = hasattr(sys, "frozen")
    
    if not is_frozen:
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(tr("update_available_title"))
        msg.setText(tr("update_error_source", version=latest_version))
        apply_dark_title_bar(msg)
        msg.exec()
        return

    # Ищем подходящий ассет (.exe файл)
    download_url = None
    asset_name = ""
    for name, url in assets.items():
        if name.lower().endswith(".exe"):
            download_url = url
            asset_name = name
            break
            
    if not download_url:
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(tr("update_error_title"))
        msg.setText(tr("update_error_no_build", version=latest_version))
        apply_dark_title_bar(msg)
        msg.exec()
        return

    # Запрашиваем подтверждение
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setWindowTitle(tr("update_available_title"))
    msg.setText(tr("update_available_msg", version=latest_version))
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg.setDefaultButton(QMessageBox.StandardButton.Yes)
    apply_dark_title_bar(msg)
    
    if msg.exec() != QMessageBox.StandardButton.Yes:
        return

    # Начинаем скачивание в папку LOCAL_APP_DATA
    temp_exe_path = os.path.join(CONFIG_DIR, "update_new.exe")
    
    progress_dialog = QProgressDialog(
        tr("update_downloading"),
        tr("btn_cancel"),
        0, 100, parent
    )
    progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
    apply_dark_title_bar(progress_dialog)
    progress_dialog.setValue(0)
    progress_dialog.show()

    worker = FileDownloadWorker(download_url, temp_exe_path)
    _active_workers.add(worker)
    worker.progress.connect(progress_dialog.setValue)
    
    def on_finished(path):
        progress_dialog.close()
        _active_workers.discard(worker)
        if not path or not os.path.exists(path):
            return
            
        current_exe_path = sys.executable
        updater_bat_path = os.path.join(CONFIG_DIR, "updater.bat")
        
        # Создаем bat-сценарий для замены EXE-файла после его закрытия
        bat_content = f"""@echo off
chcp 65001 > nul
echo ========================================================
echo  ESAPI D2cc Scraper Update -^> {latest_version}
echo ========================================================
echo {tr("update_waiting_exit")}
timeout /t 2 /nobreak > nul

echo {tr("update_replacing")}
copy /y "{temp_exe_path}" "{current_exe_path}"
if errorlevel 1 (
    echo.
    echo {tr("update_error_replace")}
    echo {tr("update_error_replace_desc")}
    echo.
    pause
    exit
)

echo {tr("update_cleaning")}
del "{temp_exe_path}"

echo {tr("update_launching")}
start "" "{current_exe_path}"

:: Самоудаление батника
(goto) 2^>nul ^& del "%~f0"
"""
        try:
            with open(updater_bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)
                
            os.startfile(updater_bat_path)
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(
                parent,
                tr("update_error_title"),
                tr("update_script_err", error=str(e))
            )

    def on_error(err_msg):
        _active_workers.discard(worker)
        QMessageBox.critical(
            parent,
            tr("update_error_title"),
            tr("update_download_err", error=str(err_msg))
        )

    def on_cancel():
        worker.terminate()
        _active_workers.discard(worker)

    worker.finished.connect(on_finished)
    worker.error.connect(on_error)
    progress_dialog.canceled.connect(on_cancel)
    
    worker.start()
