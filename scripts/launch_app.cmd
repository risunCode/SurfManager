@echo off
REM SurfManager Application Launcher Module
REM This module handles launching the SurfManager application

REM Check if launched from Launcher.cmd
if not defined LAUNCHED_FROM_LAUNCHER (
    echo ============================================================
    echo ERROR: This script must be run from Launcher.cmd
    echo ============================================================
    echo.
    echo Please run Launcher.cmd instead.
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0\.."

REM Check DEBUG_MODE value from Launcher
echo [ENV] Checking DEBUG_MODE from launcher...

if "%DEBUG_MODE%"=="true" (
    set "SHOW_TERMINAL=YES"
    echo [DEBUG MODE] Terminal window will remain visible
) else (
    set "SHOW_TERMINAL=NO"
    echo [NORMAL MODE] Running without terminal window
)
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

echo.

if defined MISSING_DEPS (
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
echo Launching MinimalSurfGUI...
echo ============================================================
echo.

REM Set environment variables for the Python application
set SURFMANAGER_DEBUG=%DEBUG_MODE%
set SURFMANAGER_SHOW_TERMINAL=%SHOW_TERMINAL%

REM Launch the application
if /i "%SHOW_TERMINAL%"=="YES" (
    echo [DEBUG] Terminal window will remain visible
    python app\main.py
    pause
) else (
    REM Launch with hidden console
    start /b pythonw app\main.py
)

exit /b %errorLevel%
