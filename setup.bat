@echo off
title Numa Setup
echo.
echo  =============================================
echo   Numa - Personal Voice Assistant - Setup
echo  =============================================
echo.

REM ── Check Python version ──────────────────────────────────────────────────
python --version 2>nul | findstr /C:"3.10" >nul
if errorlevel 1 (
    echo  [ERROR] Python 3.10 is required but not found.
    echo.
    echo  Please download Python 3.10 from:
    echo  https://www.python.org/downloads/release/python-31011/
    echo.
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo  [OK] Python 3.10 found.
echo.

REM ── Check FFmpeg ──────────────────────────────────────────────────────────
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo  [WARNING] FFmpeg not found in PATH.
    echo.
    echo  Whisper requires FFmpeg. Please install it:
    echo  1. Download from: https://ffmpeg.org/download.html
    echo  2. Extract and add the bin/ folder to your PATH
    echo  3. Run this setup again
    echo.
    echo  Or install via winget:
    echo  winget install ffmpeg
    echo.
    pause
    exit /b 1
)

echo  [OK] FFmpeg found.
echo.

REM ── Create virtual environment ─────────────────────────────────────────────
echo  Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo  [OK] Virtual environment created.
) else (
    echo  [OK] Virtual environment already exists.
)
echo.

REM ── Activate venv ─────────────────────────────────────────────────────────
call .venv\Scripts\activate.bat

REM ── Upgrade pip ───────────────────────────────────────────────────────────
echo  Upgrading pip...
python -m pip install --upgrade pip --quiet
echo  [OK] pip upgraded.
echo.

REM ── Install dependencies ───────────────────────────────────────────────────
echo  Installing dependencies (this may take 5-10 minutes)...
echo  Downloading Whisper, PyQt6, and audio libraries...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo  [ERROR] Some packages failed to install.
    echo  Check the errors above and try again.
    pause
    exit /b 1
)

echo.
echo  [OK] All dependencies installed.
echo.

REM ── Check .env file ───────────────────────────────────────────────────────
if not exist ".env" (
    echo  Creating .env file...
    echo GEMINI_API_KEY=your_key_here > .env
    echo.
    echo  [ACTION REQUIRED] Open the .env file and add your Gemini API key.
    echo  Get a free key at: https://aistudio.google.com/apikey
    echo.
) else (
    echo  [OK] .env file found.
)

REM ── Create launch shortcut ────────────────────────────────────────────────
echo  Creating start script...
(
    echo @echo off
    echo cd /d "%~dp0"
    echo call .venv\Scripts\activate.bat
    echo python main.py
) > start_numa.bat

echo  [OK] start_numa.bat created.
echo.

REM ── Done ──────────────────────────────────────────────────────────────────
echo  =============================================
echo   Setup Complete!
echo  =============================================
echo.
echo  Next steps:
echo  1. Add your Gemini API key to the .env file
echo  2. Double-click start_numa.bat to launch
echo  3. The onboarding screen will guide you through setup
echo.
echo  Note: First launch downloads Whisper model (~150MB)
echo  Make sure you have internet connection.
echo.
pause
