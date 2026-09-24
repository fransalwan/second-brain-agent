@echo off
REM Startup script untuk Second Brain Ambient Watcher + Global Quick Capture

echo.
echo ========================================
echo  Second Brain Ambient Watcher Launcher
echo ========================================
echo.

REM Check if config.json exists
if not exist "config.json" (
    echo ERROR: config.json tidak ditemukan!
    echo Silakan buat file config.json terlebih dahulu.
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python tidak ditemukan di PATH!
    echo Silakan install Python 3.11+ terlebih dahulu.
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import pynput" >nul 2>&1
if errorlevel 1 (
    echo Installing pynput...
    pip install pynput
)

echo.
echo Starting Ambient Watcher + Global Quick Capture...
echo Hotkey: Ctrl+Shift+Space
echo Press Ctrl+C to stop.
echo.

python ambient_watcher.py

pause
