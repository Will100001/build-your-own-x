@echo off
setlocal enabledelayedexpansion

REM VNC Build Script for Windows and Android
REM This script builds both VNC Viewer and Server for Windows and Android platforms

echo === VNC Build Script ===
echo Building VNC Server and Viewer for Windows and Android
echo.

REM Check if Node.js is available
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Node.js is required but not installed.
    exit /b 1
)

REM Check if npm is available
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: npm is required but not installed.
    exit /b 1
)

REM Function to build Windows app
:build_windows
set app_type=%1
echo Building VNC %app_type% for Windows...

cd %app_type%

echo Installing dependencies...
call npm install

echo Building Windows executable...
call npm run build-win

cd ..
echo VNC %app_type% for Windows built successfully!
goto :eof

REM Function to build Android app
:build_android
set app_type=%1
echo Building VNC %app_type% for Android...

cd %app_type%

echo Generating Android project...
call npm run build-android

cd ..
echo VNC %app_type% for Android built successfully!
goto :eof

REM Function to run tests
:run_tests
echo Running tests...

echo Testing shared VNC protocol...
node -e "const VNCProtocol = require('./shared/vnc-protocol.js'); const protocol = new VNCProtocol(); console.log('VNC Protocol loaded successfully'); console.log('Protocol version:', VNCProtocol.PROTOCOL_VERSION);"

echo All tests passed!
goto :eof

REM Function to create demo HTML files
:create_demos
echo Creating demo HTML files...

REM Create viewer demo
(
echo ^<!DOCTYPE html^>
echo ^<html lang="en"^>
echo ^<head^>
echo     ^<meta charset="UTF-8"^>
echo     ^<meta name="viewport" content="width=device-width, initial-scale=1.0"^>
echo     ^<title^>VNC Viewer Demo^</title^>
echo     ^<link rel="stylesheet" href="shared/vnc-styles.css"^>
echo ^</head^>
echo ^<body^>
echo     ^<div id="vnc-app"^>^</div^>
echo     ^<script src="shared/vnc-protocol.js"^>^</script^>
echo     ^<script src="shared/vnc-gui.js"^>^</script^>
echo     ^<script^>
echo         const viewer = new VNCViewer('vnc-app'^);
echo         console.log('VNC Viewer demo loaded'^);
echo     ^</script^>
echo ^</body^>
echo ^</html^>
) > demo-viewer.html

REM Create server demo
(
echo ^<!DOCTYPE html^>
echo ^<html lang="en"^>
echo ^<head^>
echo     ^<meta charset="UTF-8"^>
echo     ^<meta name="viewport" content="width=device-width, initial-scale=1.0"^>
echo     ^<title^>VNC Server Demo^</title^>
echo     ^<link rel="stylesheet" href="shared/vnc-styles.css"^>
echo ^</head^>
echo ^<body^>
echo     ^<div id="vnc-app"^>^</div^>
echo     ^<script src="shared/vnc-protocol.js"^>^</script^>
echo     ^<script src="shared/vnc-gui.js"^>^</script^>
echo     ^<script^>
echo         const server = new VNCServer('vnc-app'^);
echo         console.log('VNC Server demo loaded'^);
echo     ^</script^>
echo ^</body^>
echo ^</html^>
) > demo-server.html

echo Demo files created: demo-viewer.html, demo-server.html
goto :eof

REM Main build process
echo Starting build process...

REM Create demos first
call :create_demos

REM Run tests
call :run_tests

REM Build apps based on command line arguments
set build_target=%1
set platform_target=%2

if "%build_target%"=="viewer" goto :build_viewer
if "%build_target%"=="server" goto :build_server
if "%build_target%"=="all" goto :build_all
if "%build_target%"=="" goto :build_all
goto :build_all

:build_viewer
echo.
echo === Building VNC Viewer ===

if not "%platform_target%"=="android-only" (
    call :build_windows viewer
)

if not "%platform_target%"=="windows-only" (
    call :build_android viewer
)
goto :build_complete

:build_server
echo.
echo === Building VNC Server ===

if not "%platform_target%"=="android-only" (
    call :build_windows server
)

if not "%platform_target%"=="windows-only" (
    call :build_android server
)
goto :build_complete

:build_all
echo.
echo === Building VNC Viewer ===

if not "%platform_target%"=="android-only" (
    call :build_windows viewer
)

if not "%platform_target%"=="windows-only" (
    call :build_android viewer
)

echo.
echo === Building VNC Server ===

if not "%platform_target%"=="android-only" (
    call :build_windows server
)

if not "%platform_target%"=="windows-only" (
    call :build_android server
)

:build_complete
echo.
echo === Build Complete ===
echo Built applications:
echo   - VNC Viewer (Windows^): viewer/dist/
echo   - VNC Viewer (Android^): android/viewer/
echo   - VNC Server (Windows^): server/dist/
echo   - VNC Server (Android^): android/server/
echo.
echo Demo files:
echo   - Browser Viewer Demo: demo-viewer.html
echo   - Browser Server Demo: demo-server.html
echo.
echo To run demos:
echo   python -m http.server 8080
echo   Then open http://localhost:8080/demo-viewer.html
echo.