@echo off
REM ================================================================
REM SurfManager Main Launcher v2.1.0 by risunCode
REM ================================================================

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ===== Configuration =====
set APP_VERSION=2.1.0
set APP_NAME=SurfManager
set PYTHON_MIN_VERSION=3.8
set LAUNCHED_FROM_LAUNCHER=1
set DEBUG_MODE=false
set BUILD_TYPE=STABLE

REM ===== Color setup =====
color 0E
title %APP_NAME% v%APP_VERSION% - Main Launcher

:main_menu
cls
echo.
echo ================================================================
echo         %APP_NAME% v%APP_VERSION% - Optimized Edition
echo         Advanced Reset Tool for Windsurf, Cursor and More
echo ================================================================
echo.
echo  MAIN MENU
echo ================================================================
echo.
echo  [1] Launch Application
echo  [2] Build Executable
echo  [3] Full Cleanup
echo  [4] Exit
echo.
echo ================================================================
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto :launch_menu
if "%choice%"=="2" goto :build_menu
if "%choice%"=="3" goto :full_cleanup
if "%choice%"=="4" goto :exit_launcher

echo.
echo Invalid choice! Please try again.
timeout /t 2 >nul
goto :main_menu

:launch_menu
cls
echo.
echo ================================================================
echo  LAUNCH APPLICATION
echo ================================================================
echo.
echo  [1] Launch - Normal Mode (No console)
echo  [2] Launch - Debug Mode (With console)
echo  [3] Launch - No Splash Screen
echo  [0] Back to Main Menu
echo.
echo ================================================================
set /p launch_choice="Enter your choice: "

if "%launch_choice%"=="1" (
    set "DEBUG_MODE=false"
    set "SURFMANAGER_SHOW_TERMINAL=NO"
    goto :do_launch
)
if "%launch_choice%"=="2" (
    set "DEBUG_MODE=true"
    set "SURFMANAGER_SHOW_TERMINAL=YES"
    set "SURFMANAGER_DEBUG=1"
    goto :do_launch
)
if "%launch_choice%"=="3" (
    set "DEBUG_MODE=false"
    echo.
    echo Launching without splash screen...
    python app\main.py --no-splash
    pause
    goto :launch_menu
)
if "%launch_choice%"=="0" goto :main_menu

echo Invalid choice!
timeout /t 2 >nul
goto :launch_menu

:do_launch
echo.
echo Launching %APP_NAME%...
if "%DEBUG_MODE%"=="true" (
    echo [DEBUG MODE ACTIVE]
)
echo.
call scripts\launch_app.cmd
if %errorLevel% neq 0 (
    echo.
    echo Error launching application!
    pause
)
goto :launch_menu

:build_menu
cls
echo.
echo ================================================================
echo  BUILD EXECUTABLE
echo ================================================================
echo.
echo  [1] Build Stable (no console)
echo  [2] Build Debug (with console)
echo  [3] Build Both (Stable + Debug)
echo  [4] Clean build directories
echo  [0] Back to Main Menu
echo.
echo ================================================================
set /p build_choice="Enter your choice: "

if "%build_choice%"=="1" (
    echo.
    echo Building Stable executable...
    echo.
    python scripts\build_installer.py --type stable
    pause
    goto :build_menu
)
if "%build_choice%"=="2" (
    echo.
    echo Building Debug executable...
    echo.
    python scripts\build_installer.py --type debug
    pause
    goto :build_menu
)
if "%build_choice%"=="3" (
    echo.
    echo Building both Stable and Debug...
    echo.
    python scripts\build_installer.py --type both
    pause
    goto :build_menu
)
if "%build_choice%"=="4" (
    echo.
    echo Cleaning build directories...
    echo.
    python scripts\build_installer.py --clean-only
    pause
    goto :build_menu
)
if "%build_choice%"=="0" goto :main_menu

echo Invalid choice!
timeout /t 2 >nul
goto :build_menu

:full_cleanup
cls
echo.
echo ================================================================
echo  FULL CLEANUP
echo ================================================================
echo.
echo Performing full cleanup...
echo.
echo Cleaning __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
echo Cleaning Python cache files...
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
echo Cleaning log files...
del /s /q *.log 2>nul
echo Cleaning build directories...
if exist "build" rmdir /s /q build 2>nul
if exist "dist" rmdir /s /q dist 2>nul
if exist "output" rmdir /s /q output 2>nul
echo.
echo ✓ Full cleanup complete!
pause
goto :main_menu

:exit_launcher
cls
echo.
echo ================================================================
echo  Thank you for using %APP_NAME%!
echo ================================================================
echo.
timeout /t 2 >nul
exit /b 0
