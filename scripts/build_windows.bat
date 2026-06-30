@echo off
REM Build RI Windows .exe using PyInstaller
REM
REM === IMPORTANT: Read before running ===
REM This project has heavy native dependencies (pygame, pyaudio, torch, etc.).
REM Python 3.14 often lacks prebuilt wheels for some of them, causing source builds that fail.
REM
REM RECOMMENDED: Use Python 3.12 or 3.13 on Windows.
REM
REM Quick fix if you are already in a venv and hit pygame build errors:
REM   pip install "setuptools<70"
REM   pip install pygame
REM   pip install -r requirements.txt
REM   pip install pyinstaller
REM
REM Then run this script.

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo ==^> Step 1: Create/activate a venv if you haven't already
echo     Recommended:
echo       python -m venv RI-Env
echo       RI-Env\Scripts\activate
echo.

echo ==^> Step 2: Upgrading pip/setuptools/wheel
python -m pip install --upgrade pip setuptools wheel

echo.
echo ==^> Step 3: Installing pygame (special handling for build issues on Windows)
echo     If this fails with distutils.msvccompiler, close and re-run after:
echo       pip install "setuptools<70"
echo.
python -m pip install pygame

echo.
echo ==^> Step 4: Installing all other requirements
python -m pip install -r requirements.txt

echo.
echo ==^> Step 5: Installing PyInstaller
python -m pip install --upgrade pyinstaller

echo.
echo ==^> Step 6: Cleaning previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo ==^> Step 7: Building the Windows binary (onedir layout by default)
python -m PyInstaller RI.spec --clean --noconfirm

echo.
echo ==^> Build step finished. Checking output...

set "SUCCESS=0"

if exist "dist\RI\RI.exe" (
    echo ==^> SUCCESS: onedir build
    dir "dist\RI\RI.exe" | findstr /i "RI.exe"
    set "SUCCESS=1"
)

if exist "dist\RI\_internal" (
    echo ==^> _internal folder present ^(large support files^)
)

if "%SUCCESS%"=="1" (
    echo.
    echo The packaged application is here:
    echo     dist\RI\RI.exe
    echo.
    echo To run:
    echo     cd dist\RI
    echo     RI.exe --mode text
    echo.
    echo You can copy or zip the whole "dist\RI" folder.
    echo.
    echo IMPORTANT:
    echo - Ollama must still be installed and running with the ri-instruct model.
    echo - Some tools are Linux-only ^(xdg-open, pactl, xclip, etc.^). They will fail gracefully on Windows.
    echo - Test audio and GUI features on the target machine.
) else (
    echo.
    echo PyInstaller said "Build complete" but the expected launcher was not found.
    echo Please inspect the dist folder manually:
    echo     dir dist\RI
    echo Common causes: build was interrupted or you are using an old spec.
)
echo.
echo Done.
