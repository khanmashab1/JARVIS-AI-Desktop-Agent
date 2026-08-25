@echo off
chcp 65001 >nul
title JARVIS - AI Desktop Agent
color 0B

echo ===================================================
echo             JARVIS - AI Desktop Agent
echo ===================================================
echo.

cd /d "%~dp0"

:: 1. Virtual Environment Activation
if exist ".venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment .venv
    call ".venv\Scripts\activate.bat"
    goto :PYTHON_CHECK
)

if exist "venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment venv
    call "venv\Scripts\activate.bat"
    goto :PYTHON_CHECK
)

echo [*] Using system Python environment

:PYTHON_CHECK
:: 2. Check Python availability
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] ERROR: Python is not found in PATH.
    echo Please install Python 3.11+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 3. Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo [*] Setting up initial .env configuration
        copy ".env.example" ".env" >nul
    )
)

:: 4. Launch JARVIS Desktop GUI
echo [*] Starting JARVIS Desktop Agent...
echo.
python run.py

echo.
echo [*] JARVIS process ended.
pause
