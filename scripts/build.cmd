@echo off
echo Building SurfManager...
pyinstaller --onefile --windowed --icon=app/icons/app.ico --name=SurfManager app/main.py
echo Build complete!
pause
