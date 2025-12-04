@echo off
echo Cleaning build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q __pycache__ 2>nul
del /q *.spec 2>nul
echo Done!
pause
