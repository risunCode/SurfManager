@echo off
echo ========================================
echo    SurfManager Windows Build Script
echo ========================================
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
call venv\Scripts\activate.bat

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
if exist "*.spec" del /q *.spec

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
    set ICON_FILE=icons\surfmanager.ico
    echo Using ICO icon: icons\surfmanager.ico
) else if exist "icons\icon.png" (
    set ICON_FILE=icons\icon.png
    echo Using PNG icon: icons\icon.png
) else (
    echo No icon found, using default
)

REM Build with optimized settings for smaller size
if defined ICON_FILE (
    pyinstaller ^
        --onefile ^
        --windowed ^
        --name "SurfManager" ^
        --icon "%ICON_FILE%" ^
        --add-data "gui;gui" ^
        --add-data "core;core" ^
        --add-data "config;config" ^
        --hidden-import "PyQt6.QtCore" ^
        --hidden-import "PyQt6.QtGui" ^
        --hidden-import "PyQt6.QtWidgets" ^
        --exclude-module "PyQt6.QtNetwork" ^
        --exclude-module "PyQt6.QtOpenGL" ^
        --exclude-module "PyQt6.QtPrintSupport" ^
        --exclude-module "PyQt6.QtSql" ^
        --exclude-module "PyQt6.QtTest" ^
        --exclude-module "PyQt6.QtWebEngineWidgets" ^
        --exclude-module "PyQt6.QtMultimedia" ^
        --exclude-module "PyQt6.QtMultimediaWidgets" ^
        --exclude-module "PyQt6.QtPositioning" ^
        --exclude-module "PyQt6.QtSensors" ^
        --exclude-module "PyQt6.QtSerialPort" ^
        --exclude-module "PyQt6.QtWebChannel" ^
        --exclude-module "PyQt6.QtWebSockets" ^
        --exclude-module "PyQt6.QtXml" ^
        --exclude-module "tkinter" ^
        --exclude-module "matplotlib" ^
        --exclude-module "numpy" ^
        --exclude-module "scipy" ^
        --exclude-module "pandas" ^
        --exclude-module "PIL.ImageTk" ^
        --exclude-module "PIL.ImageDraw2" ^
        --exclude-module "PIL.ImageCms" ^
        --exclude-module "PIL.ImageFilter" ^
        --exclude-module "PIL.ImageEnhance" ^
        --exclude-module "PIL.ImageOps" ^
        --exclude-module "PIL.ImagePath" ^
        --exclude-module "PIL.ImageSequence" ^
        --exclude-module "PIL.ImageStat" ^
        --exclude-module "PIL.ImageWin" ^
        --strip ^
        --noupx ^
        --noconsole ^
        main.py
) else (
    pyinstaller ^
        --onefile ^
        --windowed ^
        --name "SurfManager" ^
        --add-data "gui;gui" ^
        --add-data "core;core" ^
        --add-data "config;config" ^
        --hidden-import "PyQt6.QtCore" ^
        --hidden-import "PyQt6.QtGui" ^
        --hidden-import "PyQt6.QtWidgets" ^
        --exclude-module "PyQt6.QtNetwork" ^
        --exclude-module "PyQt6.QtOpenGL" ^
        --exclude-module "PyQt6.QtPrintSupport" ^
        --exclude-module "PyQt6.QtSql" ^
        --exclude-module "PyQt6.QtTest" ^
        --exclude-module "PyQt6.QtWebEngineWidgets" ^
        --exclude-module "PyQt6.QtMultimedia" ^
        --exclude-module "PyQt6.QtMultimediaWidgets" ^
        --exclude-module "PyQt6.QtPositioning" ^
        --exclude-module "PyQt6.QtSensors" ^
        --exclude-module "PyQt6.QtSerialPort" ^
        --exclude-module "PyQt6.QtWebChannel" ^
        --exclude-module "PyQt6.QtWebSockets" ^
        --exclude-module "PyQt6.QtXml" ^
        --exclude-module "tkinter" ^
        --exclude-module "matplotlib" ^
        --exclude-module "numpy" ^
        --exclude-module "scipy" ^
        --exclude-module "pandas" ^
        --exclude-module "PIL.ImageTk" ^
        --exclude-module "PIL.ImageDraw2" ^
        --exclude-module "PIL.ImageCms" ^
        --exclude-module "PIL.ImageFilter" ^
        --exclude-module "PIL.ImageEnhance" ^
        --exclude-module "PIL.ImageOps" ^
        --exclude-module "PIL.ImagePath" ^
        --exclude-module "PIL.ImageSequence" ^
        --exclude-module "PIL.ImageStat" ^
        --exclude-module "PIL.ImageWin" ^
        --strip ^
        --noupx ^
        --noconsole ^
        main.py
)

REM Check if build was successful
if exist "dist\SurfManager.exe" (
    echo.
    echo ========================================
    echo    BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable created: dist\SurfManager.exe
    echo File size: 
    for %%A in ("dist\SurfManager.exe") do echo   %%~zA bytes
    echo.
    echo You can now distribute the SurfManager.exe file
    echo.
    
    REM Ask if user wants to run the built executable
    set /p run_exe="Do you want to run the built executable? (y/n): "
    if /i "%run_exe%"=="y" (
        echo Running SurfManager.exe...
        start "" "dist\SurfManager.exe"
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
    echo.
)

REM Deactivate virtual environment
deactivate

echo.
echo Press any key to exit...
pause >nul
