@echo off
setlocal enabledelayedexpansion
:: Run as Admin check
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title SurfManager Launcher
cd /d "%~dp0"

:: Get version from app/__init__.py
for /f "tokens=2 delims='" %%i in ('findstr "__version__" app\__init__.py') do set VERSION=%%i

:: Detect architecture
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set ARCH=x64
) else if "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set ARCH=arm64
) else (
    set ARCH=x86
)

:menu
cls
echo ============================================
echo        SurfManager Launcher
echo ============================================
echo.
echo  [1] Run Normal Mode
echo  [2] Run Debug Mode (show terminal)
echo.
echo  [3] Build Windows Stable (Release)
echo  [4] Build Windows Debug
echo.
echo  [5] Clean Build Artifacts
echo  [6] Exit
echo.
echo ============================================
set /p choice="Select option: "

if "%choice%"=="1" goto normal
if "%choice%"=="2" goto debug
if "%choice%"=="3" goto build_stable
if "%choice%"=="4" goto build_debug
if "%choice%"=="5" goto clean
if "%choice%"=="6" exit /b 0
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

:build_stable
call :setup
echo.
echo Building SurfManager Stable (Release)...
echo Architecture: !ARCH!
echo Version: !VERSION!
echo.
pip install pyinstaller -q

set FILENAME=SurfManager-windows-!ARCH!-!VERSION!

echo Generating executable (this may take 2-3 minutes)...
echo Filename: %FILENAME%

pyinstaller --onefile --windowed --clean --icon="%~dp0app/icons/app.ico" --name="%FILENAME%" --distpath="dist/stable" --workpath="build/stable" --specpath="build/stable" ^
    --add-data "%~dp0app/icons/app.ico;app/icons" ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtNetwork ^
    --hidden-import qtawesome ^
    --hidden-import psutil ^
    --exclude-module tkinter ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module PyQt6.QtWebEngine ^
    --exclude-module PyQt6.QtWebEngineWidgets ^
    --exclude-module PyQt6.QtQml ^
    --exclude-module PyQt6.QtQuick ^
    --exclude-module PyQt6.QtMultimedia ^
    --exclude-module PyQt6.QtBluetooth ^
    --exclude-module PyQt6.QtPositioning ^
    --exclude-module PyQt6.QtPrintSupport ^
    --exclude-module PyQt6.QtTest ^
    --exclude-module PyQt6.QtSql ^
    --exclude-module PyQt6.QtOpenGL ^
    --exclude-module PIL ^
    --exclude-module IPython ^
    --exclude-module pytest ^
    --exclude-module unittest ^
    --exclude-module test ^
    --strip ^
    --noupx ^
    app/main.py

if %errorlevel% equ 0 (
    echo.
    echo ✓ Build successful!
    echo Executable: dist\stable\%FILENAME%.exe
    echo.
) else (
    echo.
    echo ✗ Build failed!
    echo.
)
pause
goto menu

:build_debug
call :setup
echo.
echo Building SurfManager Debug...
echo Architecture: !ARCH!
echo Version: !VERSION!
echo.
pip install pyinstaller -q

set FILENAME=SurfManager-windows-!ARCH!-!VERSION!-debug

echo Generating executable with debug info...
echo Filename: %FILENAME%

pyinstaller --onefile --console --clean --icon="%~dp0app/icons/app.ico" --name="%FILENAME%" --distpath="dist/debug" --workpath="build/debug" --specpath="build/debug" ^
    --add-data "%~dp0app/icons/app.ico;app/icons" ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtNetwork ^
    --hidden-import qtawesome ^
    --hidden-import psutil ^
    --exclude-module tkinter ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module PyQt6.QtWebEngine ^
    --exclude-module PyQt6.QtWebEngineWidgets ^
    --exclude-module PyQt6.QtQml ^
    --exclude-module PyQt6.QtQuick ^
    --exclude-module PyQt6.QtMultimedia ^
    --exclude-module PyQt6.QtBluetooth ^
    --exclude-module PyQt6.QtPositioning ^
    --exclude-module PyQt6.QtPrintSupport ^
    --exclude-module PyQt6.QtTest ^
    --exclude-module PyQt6.QtSql ^
    --exclude-module PyQt6.QtOpenGL ^
    --exclude-module PIL ^
    --exclude-module IPython ^
    --exclude-module pytest ^
    --exclude-module unittest ^
    --exclude-module test ^
    --debug all ^
    --noupx ^
    app/main.py

if %errorlevel% equ 0 (
    echo.
    echo ✓ Build successful!
    echo Executable: dist\debug\%FILENAME%.exe
    echo.
) else (
    echo.
    echo ✗ Build failed!
    echo.
)
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
