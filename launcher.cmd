@echo off
REM SurfManager Launcher CMD
REM Handles admin elevation, venv setup, dependency checking, and GUI launch

cd /d "%~dp0"

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :run
) else (
    goto :elevate
)

:elevate
echo Requesting administrator privileges...
echo.

REM Create temporary VBS script for elevation
set "tempVBS=%temp%\elevate_%random%.vbs"
echo Set UAC = CreateObject("Shell.Application") > "%tempVBS%"
echo UAC.ShellExecute "cmd.exe", "/c ""%~f0""", "", "runas", 1 >> "%tempVBS%"

REM Execute the VBS script
cscript //nologo "%tempVBS%"
del "%tempVBS%"
exit /b

:run
cls
echo ============================================================
echo     SurfManager Launcher
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    echo.
    pause
    exit /b 1
)

echo [OK] Running with administrator privileges
echo.
echo Checking requirements...
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [*] Creating virtual environment...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        echo.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if required packages are installed
echo Checking dependencies...

python -c "import PyQt6" >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] PyQt6 NOT installed
    set "MISSING_DEPS=1"
) else (
    echo [OK] PyQt6 installed
)

python -c "import psutil" >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] psutil NOT installed
    set "MISSING_DEPS=1"
) else (
    echo [OK] psutil installed
)

echo.

if defined MISSING_DEPS (
    echo ERROR: Missing required packages!
    echo Installing dependencies...
    echo.
    pip install -r requirements.txt
    if %errorLevel% neq 0 (
        echo ERROR: Failed to install dependencies
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencies installed successfully!
    echo.
)

echo ============================================================
echo [OK] All requirements satisfied!
echo.
echo Launching SurfManager GUI...
echo ============================================================
echo.

REM Launch the GUI (hidden console)
python main.py
exit /b %errorLevel%

