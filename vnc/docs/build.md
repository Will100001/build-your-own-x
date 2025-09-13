# Build Instructions

This document provides detailed instructions for building the VNC Server and Viewer on different platforms.

## Prerequisites

### All Platforms
- Python 3.8 or higher
- Git (for cloning the repository)
- Internet connection (for downloading dependencies)

### Platform-Specific Prerequisites

#### Windows
- Visual Studio 2019 or newer (for PyQt5 compilation)
- Windows 10 SDK
- NSIS (optional, for creating installers)

#### Linux
- Build tools: `sudo apt-get install build-essential python3-dev python3-tk`
- X11 development libraries: `sudo apt-get install libx11-dev`
- Virtual display tools (for headless building): `sudo apt-get install xvfb`

#### Android
- Java Development Kit (JDK) 8 or 11
- Android SDK (API level 31)
- Android NDK (version 25b)
- Buildozer: `pip install buildozer`

## Building from Source

### 1. Clone the Repository
```bash
git clone https://github.com/codecrafters-io/build-your-own-x.git
cd build-your-own-x/vnc
```

### 2. Set Up Development Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Tests (Optional but Recommended)
```bash
python tests/test_vnc.py
```

## Platform-Specific Builds

### Windows Build

#### Using the Build Script
```batch
cd build
build_windows.bat
```

#### Manual Build
```batch
# Install PyInstaller
pip install pyinstaller

# Build server
pyinstaller --onefile --windowed ^
    --name "VNC-Server" ^
    --add-data "..\protocol;protocol" ^
    ..\server\vnc_server.py

# Build viewer
pyinstaller --onefile --windowed ^
    --name "VNC-Viewer" ^
    --add-data "..\protocol;protocol" ^
    ..\viewer\vnc_viewer.py
```

#### Output Files
- `dist/VNC-Server.exe` - Standalone VNC Server
- `dist/VNC-Viewer.exe` - Standalone VNC Viewer

### Linux Build

#### Using the Build Script
```bash
cd build
chmod +x build_linux.sh
./build_linux.sh
```

#### Manual Build
```bash
# Install PyInstaller
pip install pyinstaller

# Build server
pyinstaller --onefile \
    --name "vnc-server" \
    --add-data "../protocol:protocol" \
    ../server/vnc_server.py

# Build viewer
pyinstaller --onefile \
    --name "vnc-viewer" \
    --add-data "../protocol:protocol" \
    ../viewer/vnc_viewer.py
```

#### Output Files
- `dist/vnc-server` - VNC Server executable
- `dist/vnc-viewer` - VNC Viewer executable
- `dist/linux/vnc-linux-x64.tar.gz` - Distribution package

### Android Build

#### Using the Build Script
```bash
cd build
chmod +x build_android.sh
./build_android.sh
```

#### Manual Build
```bash
# Install buildozer
pip install buildozer cython kivy

# Initialize buildozer
buildozer init

# Build APK
buildozer android debug
```

#### Output Files
- `bin/vncviewer-*.apk` - Android VNC Viewer app

## Build Configuration

### PyInstaller Options

#### Common Options
- `--onefile` - Create a single executable file
- `--windowed` - Hide console window (Windows/macOS)
- `--add-data` - Include additional data files
- `--icon` - Set application icon

#### Advanced Options
```bash
# Optimize for size
pyinstaller --onefile --strip --exclude-module matplotlib

# Include specific modules
pyinstaller --onefile --hidden-import=PyQt5.QtCore

# Custom paths
pyinstaller --onefile --paths=/path/to/custom/modules
```

### Buildozer Configuration (Android)

Edit `buildozer.spec` for custom Android builds:

```ini
[app]
title = VNC Viewer
package.name = vncviewer
package.domain = org.buildyourownx

requirements = python3,kivy,pillow,pyjnius

[android]
api = 31
minapi = 21
archs = arm64-v8a, armeabi-v7a
```

## Troubleshooting Build Issues

### Common Windows Issues

#### "MSVCR140.dll not found"
Install Visual C++ Redistributable 2019 or newer.

#### "PyQt5 compilation failed"
```batch
pip install --only-binary=PyQt5 PyQt5
```

### Common Linux Issues

#### "Python.h not found"
```bash
sudo apt-get install python3-dev
```

#### "Tk module not available"
```bash
sudo apt-get install python3-tk
```

### Common Android Issues

#### "SDK not found"
Set Android SDK path:
```bash
export ANDROID_HOME=/path/to/android-sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

#### "NDK not found"
Download and set NDK path:
```bash
export ANDROID_NDK_HOME=/path/to/android-ndk
```

## Optimization

### Size Optimization
```bash
# Use UPX compression (Windows/Linux)
upx --best dist/vnc-server.exe

# Exclude unnecessary modules
pyinstaller --exclude-module matplotlib --exclude-module scipy
```

### Performance Optimization
```bash
# Use Nuitka for better performance
pip install nuitka
nuitka --onefile --enable-plugin=pyqt5 server/vnc_server.py
```

## Distribution

### Creating Installers

#### Windows (NSIS)
```nsis
; vnc-installer.nsi
!include "MUI2.nsh"

Name "VNC Server and Viewer"
OutFile "VNC-Setup.exe"
InstallDir "$PROGRAMFILES\VNC"

Section "Main"
    SetOutPath "$INSTDIR"
    File "dist\VNC-Server.exe"
    File "dist\VNC-Viewer.exe"
    CreateDirectory "$SMPROGRAMS\VNC"
    CreateShortCut "$SMPROGRAMS\VNC\VNC Server.lnk" "$INSTDIR\VNC-Server.exe"
    CreateShortCut "$SMPROGRAMS\VNC\VNC Viewer.lnk" "$INSTDIR\VNC-Viewer.exe"
SectionEnd
```

#### Linux (AppImage)
```bash
# Create AppDir structure
mkdir -p AppDir/usr/bin
cp dist/vnc-viewer AppDir/usr/bin/
cp vnc-viewer.desktop AppDir/
cp vnc-icon.png AppDir/

# Create AppImage
appimagetool AppDir VNC-Viewer.AppImage
```

### Package Verification
```bash
# Check dependencies
ldd dist/vnc-viewer  # Linux
otool -L dist/vnc-viewer  # macOS

# Test executable
./dist/vnc-viewer --version
```

## Continuous Integration

The GitHub Actions workflow automatically builds for all platforms:

```yaml
# Triggered on push to main branches
- Build Linux executables
- Build Windows executables  
- Build Android APK
- Run comprehensive tests
- Create release artifacts
```

## Development Builds

For development and testing:

```bash
# Quick development server
python server/vnc_server.py --verbose

# Development viewer with debug
python viewer/vnc_viewer.py --verbose
```

## Build Verification

After building, verify the executables:

```bash
# Test server startup
./dist/vnc-server --help

# Test viewer startup
./dist/vnc-viewer --help

# Test basic connection
./dist/vnc-server --port 5901 &
./dist/vnc-viewer --host localhost --port 5901
```