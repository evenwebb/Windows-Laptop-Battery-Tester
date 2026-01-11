@echo off
REM Build script for Windows Battery Tester
REM This script builds the executable using PyInstaller

echo ========================================
echo Windows Battery Tester Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/4] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist battery_tester.spec del battery_tester.spec
echo Done.
echo.

echo [2/4] Checking dependencies...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)
echo Installing/updating required packages...
pip install -r requirements.txt --quiet
echo Done.
echo.

echo [3/4] Building executable with PyInstaller...
pyinstaller build.spec
if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo Done.
echo.

echo [4/4] Copying executable to root directory...
if exist dist\battery_tester.exe (
    copy dist\battery_tester.exe battery_tester.exe >nul
    echo Executable copied to: battery_tester.exe
) else (
    echo ERROR: Executable not found in dist directory!
    pause
    exit /b 1
)
echo.

echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable location: battery_tester.exe
echo.
pause
