@echo off
REM Windows build script for VNC Server and Viewer

echo Building VNC Server and Viewer for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r ..\requirements.txt

REM Install PyInstaller for creating executables
pip install pyinstaller

REM Build VNC Server executable
echo Building VNC Server executable...
pyinstaller --onefile --windowed ^
    --name "VNC-Server" ^
    --icon=..\docs\vnc-icon.ico ^
    --add-data "..\protocol;protocol" ^
    ..\server\vnc_server.py

REM Build VNC Viewer executable
echo Building VNC Viewer executable...
pyinstaller --onefile --windowed ^
    --name "VNC-Viewer" ^
    --icon=..\docs\vnc-icon.ico ^
    --add-data "..\protocol;protocol" ^
    ..\viewer\vnc_viewer.py

REM Create distribution package
echo Creating distribution package...
if not exist "dist\windows" mkdir dist\windows
copy dist\VNC-Server.exe dist\windows\
copy dist\VNC-Viewer.exe dist\windows\
copy ..\README.md dist\windows\
copy ..\docs\windows-setup.md dist\windows\README-WINDOWS.md

REM Create installer (requires NSIS)
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo Creating Windows installer...
    "C:\Program Files (x86)\NSIS\makensis.exe" windows-installer.nsi
) else (
    echo NSIS not found, skipping installer creation
    echo You can manually create an installer using the files in dist\windows
)

echo Windows build complete!
echo Executables are in dist\windows\
pause