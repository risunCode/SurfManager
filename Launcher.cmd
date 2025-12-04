@echo off
:: Run as Admin check
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title SurfManager Launcher
cd /d "%~dp0"

:menu
cls
echo ============================================
echo           SurfManager Launcher
echo ============================================
echo.
echo  [1] Run Normal Mode
echo  [2] Run Debug Mode (show terminal)
echo  [3] Clean Build Artifacts
echo  [4] Exit
echo.
echo ============================================
set /p choice="Select option: "

if "%choice%"=="1" goto normal
if "%choice%"=="2" goto debug
if "%choice%"=="3" goto clean
if "%choice%"=="4" exit /b 0
goto menu

:setup
:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found! Please install Python 3.8+
    pause
    goto menu
)

:: Create venv if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate and install deps
call venv\Scripts\activate.bat
echo Checking dependencies...
pip install -r requirements.txt -q
goto :eof

:normal
call :setup
echo.
echo Starting SurfManager...
set SURFMANAGER_SHOW_TERMINAL=NO
start "" pythonw app/main.py
goto menu

:debug
call :setup
echo.
echo Starting SurfManager (Debug)...
set SURFMANAGER_SHOW_TERMINAL=YES
set SURFMANAGER_DEBUG=TRUE
python app/main.py
pause
goto menu

:clean
echo.
echo Cleaning build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q __pycache__ 2>nul
rmdir /s /q app\__pycache__ 2>nul
rmdir /s /q app\core\__pycache__ 2>nul
rmdir /s /q app\gui\__pycache__ 2>nul
del /q *.spec 2>nul
echo Done!
echo.
pause
goto menu
