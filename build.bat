@echo off
setlocal
cd /d "%~dp0"
set APP=FloridaPlateChecker
set VERSION=1.0.0

echo ==== Building %APP% %VERSION% ====

rem Find a REAL Python. The Microsoft Store shortcut named "python" fails --version, so it is skipped.
set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY python --version >nul 2>nul && set "PY=python"
if not defined PY (
    echo.
    echo Python is not installed, or only the Microsoft Store shortcut was found.
    echo.
    echo 1. Download Python from https://www.python.org/downloads/windows/
    echo 2. Run the installer and TICK "Add python.exe to PATH" on the first screen.
    echo 3. Close this window, then run build.bat again.
    echo.
    pause
    exit /b 1
)
echo Using: %PY%

if not exist .venv\Scripts\python.exe %PY% -m venv .venv
if not exist .venv\Scripts\python.exe (
    echo Could not create the virtual environment.
    pause
    exit /b 1
)
set VPY=.venv\Scripts\python.exe

"%VPY%" -m pip install --upgrade pip >nul
"%VPY%" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo Package install failed. Check your internet connection.
    pause
    exit /b 1
)

rmdir /s /q build dist 2>nul

"%VPY%" -m PyInstaller --noconfirm --clean --onedir --windowed --name %APP% ^
    --icon app.ico --version-file version_info.txt ^
    --add-data "app.ico;." --add-data "logo.png;." ^
    plate_checker_gui.py
if errorlevel 1 (
    echo PyInstaller failed. See the messages above.
    pause
    exit /b 1
)

copy /y plate_dictionary.txt dist\%APP%\ >nul
copy /y README.md dist\%APP%\ >nul

echo Creating zip...
powershell -NoProfile -Command "Compress-Archive -Path 'dist\%APP%' -DestinationPath 'dist\%APP%-v%VERSION%.zip' -Force"

where iscc >nul 2>nul
if not errorlevel 1 (
    echo Building installer with Inno Setup...
    iscc installer.iss
) else (
    echo Inno Setup not found, skipping installer. Get it free at jrsoftware.org
)

echo.
echo Done. Output:
echo   dist\%APP%\                 run %APP%.exe from here
echo   dist\%APP%-v%VERSION%.zip   share this
echo   installer_output\           Setup.exe, if Inno Setup is installed
pause
