@echo off
REM Build RI Windows .exe using PyInstaller
REM Run this from a Windows machine with Python + the project checked out.
REM
REM Prerequisites:
REM   python -m venv venv
REM   venv\Scripts\activate
REM   pip install -r requirements.txt
REM   pip install pyinstaller
REM
REM Then:
REM   scripts\build_windows.bat

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo ==^> Cleaning
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo ==^> Installing/ensuring PyInstaller
python -m pip install --upgrade pyinstaller

echo ==^> Building Windows binary (onefile)
python -m PyInstaller RI.spec --clean --noconfirm

if exist dist\RI.exe (
    echo.
    echo ==^> SUCCESS: dist\RI.exe created
    dir dist\RI.exe
    echo.
    echo Run with: dist\RI.exe --mode text
    echo.
    echo IMPORTANT:
    echo - You still need Ollama installed and `ollama serve` + ri-instruct model.
    echo - Audio stack (PyAudio) and some GUI tools may need extra DLLs / system setup on target machine.
) else (
    echo Build failed. See above logs.
    exit /b 1
)
