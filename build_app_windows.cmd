@echo off
echo ========================================
echo    SurfManager Windows Build Script
echo ========================================
echo.

REM ============================================================
REM BUILD CONFIGURATION
REM ============================================================
REM Set DEBUG_BUILD=YES to build with console and debug symbols
REM Set DEBUG_BUILD=NO for production build (no console, optimized)
set DEBUG_BUILD=NO
REM ============================================================

if /i "%DEBUG_BUILD%"=="YES" (
    echo [CONFIG] Building in DEBUG mode
    echo  - Console window enabled
    echo  - Debug symbols included
    echo  - Verbose logging enabled
) else (
    echo [CONFIG] Building in PRODUCTION mode
    echo  - Console window hidden
    echo  - Optimized for size
    echo  - No debug symbols
)
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment activation script not found
    echo Please ensure venv was created successfully
    pause
    exit /b 1
)

REM Install/upgrade required packages
echo Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller installation failed
    pause
    exit /b 1
)

REM Create build directory
if not exist "build\" mkdir build
if not exist "dist\" mkdir dist

REM Clean previous builds
echo Cleaning previous builds...
if exist "build\*" rmdir /s /q build
if exist "dist\*" rmdir /s /q dist
REM Note: .spec files are kept for reference, PyInstaller will regenerate if needed

REM Check for application icon
echo Preparing application icon...
if exist "icons\surfmanager.ico" (
    echo ✅ ICO icon found: icons\surfmanager.ico
) else if exist "icons\icon.png" (
    echo ✅ PNG icon found: icons\icon.png
) else (
    echo ⚠️ No icon found in icons folder, will use default icon
)

REM Build the application
echo Building SurfManager executable...

REM Determine which icon to use
set ICON_FILE=
if exist "icons\surfmanager.ico" (
    set ICON_FILE=--icon "icons\surfmanager.ico"
    echo Using ICO icon: icons\surfmanager.ico
) else if exist "icons\icon.png" (
    set ICON_FILE=--icon "icons\icon.png"
    echo Using PNG icon: icons\icon.png
) else (
    echo No icon found, using default
)

REM Build with PyInstaller based on DEBUG_BUILD setting
if /i "%DEBUG_BUILD%"=="YES" (
    echo Building DEBUG version...
    pyinstaller --onefile --name "SurfManager_Debug" %ICON_FILE% --add-data "gui;gui" --add-data "core;core" --add-data "config;config" --hidden-import "PyQt6.QtCore" --hidden-import "PyQt6.QtGui" --hidden-import "PyQt6.QtWidgets" --console --debug all --clean --noconfirm main.py
) else (
    echo Building PRODUCTION version with size optimizations...
    pyinstaller --onefile --windowed --name "SurfManager" %ICON_FILE% --add-data "gui;gui" --add-data "core;core" --add-data "config;config" --hidden-import "PyQt6.QtCore" --hidden-import "PyQt6.QtGui" --hidden-import "PyQt6.QtWidgets" --exclude-module "PyQt6.QtWebEngine" --exclude-module "PyQt6.QtWebEngineCore" --exclude-module "PyQt6.QtWebEngineWidgets" --exclude-module "PyQt6.QtNetwork" --exclude-module "PyQt6.QtMultimedia" --exclude-module "PyQt6.QtMultimediaWidgets" --exclude-module "PyQt6.QtOpenGL" --exclude-module "PyQt6.QtOpenGLWidgets" --exclude-module "PyQt6.QtPositioning" --exclude-module "PyQt6.QtPrintSupport" --exclude-module "PyQt6.QtQml" --exclude-module "PyQt6.QtQuick" --exclude-module "PyQt6.QtQuickWidgets" --exclude-module "PyQt6.QtSql" --exclude-module "PyQt6.QtSvg" --exclude-module "PyQt6.QtSvgWidgets" --exclude-module "PyQt6.QtTest" --exclude-module "PyQt6.QtXml" --exclude-module "matplotlib" --exclude-module "numpy" --exclude-module "pandas" --exclude-module "scipy" --exclude-module "PIL" --exclude-module "tkinter" --exclude-module "unittest" --exclude-module "email" --exclude-module "http" --exclude-module "urllib3" --exclude-module "xml" --exclude-module "pydoc" --noconsole --strip --clean --noconfirm main.py
)

REM Check if build was successful
if /i "%DEBUG_BUILD%"=="YES" (
    set "EXE_NAME=SurfManager_Debug.exe"
) else (
    set "EXE_NAME=SurfManager.exe"
)

if exist "dist\%EXE_NAME%" (
    echo.
    echo ========================================
    echo    BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable created: dist\%EXE_NAME%
    echo File size: 
    for %%A in ("dist\%EXE_NAME%") do echo   %%~zA bytes
    echo.
    
    if /i "%DEBUG_BUILD%"=="YES" (
        echo DEBUG BUILD - Console window will be visible
        echo.
    ) else (
        echo PRODUCTION BUILD - Ready for distribution
        echo.
    )
    
    REM Ask if user wants to run the built executable
    set /p run_exe="Do you want to run the built executable? (y/n): "
    if /i "%run_exe%"=="y" (
        echo Running %EXE_NAME%...
        start "" "dist\%EXE_NAME%"
    )
) else (
    echo.
    echo ========================================
    echo    BUILD FAILED!
    echo ========================================
    echo.
    echo Check the output above for errors.
    echo Common issues:
    echo - Missing dependencies in requirements.txt
    echo - Missing icon file: icons\surfmanager.ico
    echo - Python path issues
    echo - Virtual environment not activated properly
    echo.
)

REM Deactivate virtual environment
deactivate

echo.
echo Press any key to exit...
pause >nul
