@echo off
cd /d "%~dp0"
echo ===================================================
echo Building ESAPI D2cc Scraper into EXE file
echo ===================================================

:: Step 1: Install dependencies
echo [1/3] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b %ERRORLEVEL%
)

:: Step 2: Build EXE with PyInstaller
echo [2/3] Running PyInstaller...
python -m PyInstaller --onefile --noconsole --name "d2cc_scraper" main.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed.
    pause
    exit /b %ERRORLEVEL%
)

:: Step 3: Clean up temporary files
echo [3/3] Cleaning up temporary build files...
if exist build rmdir /s /q build
if exist d2cc_scraper.spec del /f /q d2cc_scraper.spec

echo ===================================================
echo Build completed successfully!
echo Executable is located in: dist\d2cc_scraper.exe
echo ===================================================
pause
