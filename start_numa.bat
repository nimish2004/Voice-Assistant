@echo off
cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] No virtual environment found. Run setup.bat first.
    echo Trying system Python...
)

python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Numa crashed. See error above.
    pause
)
