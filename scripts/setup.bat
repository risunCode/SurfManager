@echo off
echo ===============================================
echo   SurfManager Setup Script
echo ===============================================
echo.
echo This will install all required dependencies.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment!
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install some dependencies!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   Setup Complete!
echo ===============================================
echo.
echo To run SurfManager in development mode:
echo   1. Run: venv\Scripts\activate.bat
echo   2. Run: python app\main.py
echo.
echo To build executable:
echo   1. Run: build.bat
echo.
pause
