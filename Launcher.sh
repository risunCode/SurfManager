#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 not found!${NC}"
    exit 1
fi

# Get version from app/__init__.py
VERSION=$(grep "__version__" app/__init__.py | cut -d"'" -f2)

# Detect OS and architecture
OS=$(uname -s)
ARCH=$(uname -m)

case "$OS" in
    Linux*)
        OS_NAME="Linux"
        ;;
    Darwin*)
        OS_NAME="macOS"
        ;;
    *)
        OS_NAME="Unknown"
        ;;
esac

# Normalize architecture names
case "$ARCH" in
    x86_64)
        ARCH_NAME="x64"
        ;;
    arm64|aarch64)
        ARCH_NAME="arm64"
        ;;
    *)
        ARCH_NAME="$ARCH"
        ;;
esac

# Setup virtual environment
setup_venv() {
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt -q
}

# Menu
show_menu() {
    clear
    echo "============================================"
    echo "     SurfManager Launcher"
    echo "============================================"
    echo "OS: $OS_NAME | Arch: $ARCH_NAME | Version: $VERSION"
    echo ""
    echo "  [1] Run Normal Mode"
    echo "  [2] Run Debug Mode"
    echo ""
    echo "  [3] Build $OS_NAME Stable"
    echo "  [4] Build $OS_NAME Debug"
    echo ""
    echo "  [5] Clean Build Artifacts"
    echo "  [6] Exit"
    echo ""
    echo "============================================"
    read -p "Select option: " choice
}

# Run normal mode
run_normal() {
    setup_venv
    echo ""
    echo -e "${GREEN}Starting SurfManager...${NC}"
    python3 app/main.py
}

# Run debug mode
run_debug() {
    setup_venv
    echo ""
    echo -e "${GREEN}Starting SurfManager (Debug)...${NC}"
    export SURFMANAGER_DEBUG=TRUE
    python3 app/main.py
}

# Build stable
build_stable() {
    setup_venv
    echo ""
    echo -e "${YELLOW}Building SurfManager Stable (Release)...${NC}"
    echo "OS: $OS_NAME | Arch: $ARCH_NAME | Version: $VERSION"
    echo ""
    pip install pyinstaller -q
    
    FILENAME="SurfManager-${OS_NAME}-${ARCH_NAME}-${VERSION}"
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    
    # Platform-specific options
    PLATFORM_OPTS=""
    ICON_DATA=""
    
    # Include icons folder for runtime
    if [ -d "app/icons" ]; then
        ICON_DATA="--add-data app/icons:app/icons"
    fi
    
    if [ "$OS" = "Darwin" ]; then
        # macOS: use .icns if available, set bundle identifier
        if [ -f "app/icons/app.icns" ]; then
            PLATFORM_OPTS="--icon=app/icons/app.icns"
        elif [ -f "app/icons/app.ico" ]; then
            PLATFORM_OPTS="--icon=app/icons/app.ico"
        fi
        PLATFORM_OPTS="$PLATFORM_OPTS --osx-bundle-identifier=com.risuncode.surfmanager"
    else
        # Linux: use .png or .ico
        if [ -f "app/icons/app.png" ]; then
            PLATFORM_OPTS="--icon=app/icons/app.png"
        elif [ -f "app/icons/app.ico" ]; then
            PLATFORM_OPTS="--icon=app/icons/app.ico"
        fi
    fi
    
    echo "Generating executable (this may take 2-3 minutes)..."
    pyinstaller --onefile --windowed --clean --name="$FILENAME" \
        --distpath="dist/stable" --workpath="build/stable" --specpath="build/stable" \
        $PLATFORM_OPTS $ICON_DATA \
        --hidden-import PyQt6.QtCore \
        --hidden-import PyQt6.QtWidgets \
        --hidden-import PyQt6.QtGui \
        --hidden-import PyQt6.QtNetwork \
        --hidden-import qtawesome \
        --hidden-import psutil \
        --exclude-module tkinter \
        --exclude-module matplotlib \
        --exclude-module numpy \
        --exclude-module pandas \
        --exclude-module PyQt6.QtWebEngine \
        --exclude-module PyQt6.QtWebEngineWidgets \
        --exclude-module PyQt6.QtQml \
        --exclude-module PyQt6.QtQuick \
        --exclude-module PyQt6.QtMultimedia \
        --exclude-module PyQt6.QtBluetooth \
        --exclude-module PyQt6.QtPositioning \
        --exclude-module PyQt6.QtPrintSupport \
        --exclude-module PyQt6.QtTest \
        --exclude-module PyQt6.QtSql \
        --exclude-module PyQt6.QtOpenGL \
        --exclude-module PIL \
        --exclude-module IPython \
        --exclude-module pytest \
        --exclude-module unittest \
        --exclude-module test \
        --strip \
        --noupx \
        app/main.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}Build successful!${NC}"
        echo "Executable: dist/stable/$FILENAME"
        echo ""
    else
        echo ""
        echo -e "${RED}Build failed!${NC}"
        echo ""
    fi
    read -p "Press Enter to continue..."
}

# Build debug
build_debug() {
    setup_venv
    echo ""
    echo -e "${YELLOW}Building SurfManager Debug...${NC}"
    echo "OS: $OS_NAME | Arch: $ARCH_NAME | Version: $VERSION"
    echo ""
    pip install pyinstaller -q
    
    FILENAME="SurfManager-${OS_NAME}-${ARCH_NAME}-${VERSION}-debug"
    
    # Platform-specific options
    PLATFORM_OPTS=""
    ICON_DATA=""
    
    # Include icons folder for runtime
    if [ -d "app/icons" ]; then
        ICON_DATA="--add-data app/icons:app/icons"
    fi
    
    if [ "$OS" = "Darwin" ]; then
        # macOS: use .icns if available, set bundle identifier
        if [ -f "app/icons/app.icns" ]; then
            PLATFORM_OPTS="--icon=app/icons/app.icns"
        elif [ -f "app/icons/app.ico" ]; then
            PLATFORM_OPTS="--icon=app/icons/app.ico"
        fi
        PLATFORM_OPTS="$PLATFORM_OPTS --osx-bundle-identifier=com.risuncode.surfmanager"
    else
        # Linux: use .png or .ico
        if [ -f "app/icons/app.png" ]; then
            PLATFORM_OPTS="--icon=app/icons/app.png"
        elif [ -f "app/icons/app.ico" ]; then
            PLATFORM_OPTS="--icon=app/icons/app.ico"
        fi
    fi
    
    echo "Generating executable with debug info..."
    pyinstaller --onefile --console --clean --name="$FILENAME" \
        --distpath="dist/debug" --workpath="build/debug" --specpath="build/debug" \
        $PLATFORM_OPTS $ICON_DATA \
        --hidden-import PyQt6.QtCore \
        --hidden-import PyQt6.QtWidgets \
        --hidden-import PyQt6.QtGui \
        --hidden-import PyQt6.QtNetwork \
        --hidden-import qtawesome \
        --hidden-import psutil \
        --exclude-module tkinter \
        --exclude-module matplotlib \
        --exclude-module numpy \
        --exclude-module pandas \
        --exclude-module PyQt6.QtWebEngine \
        --exclude-module PyQt6.QtWebEngineWidgets \
        --exclude-module PyQt6.QtQml \
        --exclude-module PyQt6.QtQuick \
        --exclude-module PyQt6.QtMultimedia \
        --exclude-module PyQt6.QtBluetooth \
        --exclude-module PyQt6.QtPositioning \
        --exclude-module PyQt6.QtPrintSupport \
        --exclude-module PyQt6.QtTest \
        --exclude-module PyQt6.QtSql \
        --exclude-module PyQt6.QtOpenGL \
        --exclude-module PIL \
        --exclude-module IPython \
        --exclude-module pytest \
        --exclude-module unittest \
        --exclude-module test \
        --debug all \
        --noupx \
        app/main.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}Build successful!${NC}"
        echo "Executable: dist/debug/$FILENAME"
        echo ""
    else
        echo ""
        echo -e "${RED}Build failed!${NC}"
        echo ""
    fi
    read -p "Press Enter to continue..."
}

# Clean artifacts
clean_artifacts() {
    echo ""
    echo -e "${YELLOW}Cleaning build artifacts...${NC}"
    rm -rf build dist __pycache__ app/__pycache__ app/core/__pycache__ app/gui/__pycache__ *.spec
    echo -e "${GREEN}Done!${NC}"
    echo ""
    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    show_menu
    case $choice in
        1) run_normal ;;
        2) run_debug ;;
        3) build_stable ;;
        4) build_debug ;;
        5) clean_artifacts ;;
        6) echo "Exiting..."; exit 0 ;;
        *) echo -e "${RED}Invalid option!${NC}"; read -p "Press Enter to continue..." ;;
    esac
done
