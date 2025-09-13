# VNC Build and Deployment Guide

## Prerequisites

### Development Environment

**Minimum Requirements:**
- C++17 compatible compiler (GCC 7+, Clang 5+, MSVC 2017+)
- CMake 3.10+
- Git

**Platform-Specific Requirements:**

#### Windows
- Visual Studio 2017+ or MinGW-w64
- Windows SDK 10+
- Git for Windows

#### Linux
- GCC 7+ or Clang 5+
- X11 development libraries
- XTest extension libraries

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential cmake git
sudo apt install libx11-dev libxtst-dev

# CentOS/RHEL/Fedora
sudo dnf install gcc-c++ cmake git
sudo dnf install libX11-devel libXtst-devel
```

#### macOS
- Xcode Command Line Tools
- Homebrew (recommended)

```bash
xcode-select --install
brew install cmake git
```

#### Android
- Android Studio 4.0+
- Android NDK 21+
- CMake 3.10+
- Target SDK 30+

### Optional Dependencies

**TLS/SSL Support:**
```bash
# Ubuntu/Debian
sudo apt install libssl-dev

# CentOS/RHEL/Fedora
sudo dnf install openssl-devel

# macOS
brew install openssl

# Windows
# Download OpenSSL from https://slproweb.com/products/Win32OpenSSL.html
```

## Building from Source

### Method 1: CMake (Recommended)

```bash
# Clone repository
git clone https://github.com/Will100001/build-your-own-x.git
cd build-your-own-x/vnc

# Create build directory
mkdir build && cd build

# Configure build
cmake .. -DCMAKE_BUILD_TYPE=Release

# Optional: Enable TLS support
cmake .. -DCMAKE_BUILD_TYPE=Release -DENABLE_TLS=ON

# Build
cmake --build . --config Release

# Install (optional)
sudo cmake --install .
```

### Method 2: Platform Scripts

#### Linux/macOS
```bash
cd vnc/build
chmod +x *.sh

# Build server
./build-server.sh

# Build client
./build-client.sh
```

#### Windows
```batch
cd vnc\build

REM Build server
build-server.bat

REM Build client
build-client.bat
```

### Method 3: Manual Compilation

#### Server
```bash
g++ -std=c++17 -O2 -I./src \
    src/common/rfb_protocol.cpp \
    src/common/platform_factory.cpp \
    src/server/vnc_server.cpp \
    src/gui/vnc_server_gui.cpp \
    examples/server_example.cpp \
    -lpthread -lX11 -lXtst \
    -o vnc-server
```

#### Client
```bash
g++ -std=c++17 -O2 -I./src \
    src/common/rfb_protocol.cpp \
    src/client/vnc_client.cpp \
    src/gui/vnc_client_gui.cpp \
    examples/client_example.cpp \
    -lpthread \
    -o vnc-client
```

## Build Configuration

### CMake Options

| Option | Default | Description |
|--------|---------|-------------|
| BUILD_SERVER | ON | Build VNC server |
| BUILD_CLIENT | ON | Build VNC client |
| BUILD_EXAMPLES | ON | Build example applications |
| BUILD_TESTS | OFF | Build test suite |
| ENABLE_TLS | OFF | Enable TLS/SSL support |

Example:
```bash
cmake .. -DBUILD_SERVER=ON -DBUILD_CLIENT=OFF -DENABLE_TLS=ON
```

### Compiler Flags

**Debug Build:**
```bash
cmake .. -DCMAKE_BUILD_TYPE=Debug
```

**Release Build:**
```bash
cmake .. -DCMAKE_BUILD_TYPE=Release
```

**Custom Flags:**
```bash
cmake .. -DCMAKE_CXX_FLAGS="-Wall -Wextra -march=native"
```

## Cross-Platform Building

### Windows Cross-Compilation (Linux → Windows)

```bash
# Install MinGW cross-compiler
sudo apt install gcc-mingw-w64

# Configure for Windows
cmake .. -DCMAKE_TOOLCHAIN_FILE=../cmake/mingw-w64.cmake

# Build
cmake --build .
```

### Android Build

```bash
# Configure for Android
cmake .. -DANDROID_ABI=arm64-v8a \
         -DANDROID_PLATFORM=android-21 \
         -DCMAKE_TOOLCHAIN_FILE=$ANDROID_NDK/build/cmake/android.toolchain.cmake

# Build
cmake --build .
```

## Installation

### System Installation

```bash
# Install to system directories
sudo cmake --install . --prefix /usr/local

# Custom installation directory
cmake --install . --prefix /opt/vnc
```

### Package Creation

```bash
# Create distribution packages
cmake --build . --target package

# Available packages:
# - vnc-1.0.0-Linux.tar.gz
# - vnc-1.0.0-Linux.deb (Ubuntu/Debian)
# - vnc-1.0.0-Linux.rpm (CentOS/RHEL/Fedora)
```

## Deployment

### Server Deployment

#### Linux Service

Create systemd service file `/etc/systemd/system/vnc-server.service`:

```ini
[Unit]
Description=VNC Server
After=network.target

[Service]
Type=simple
User=vnc
ExecStart=/usr/local/bin/vnc-server
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable vnc-server
sudo systemctl start vnc-server
```

#### Windows Service

```batch
REM Install as Windows service (requires admin privileges)
sc create VNCServer binPath="C:\Program Files\VNC\vnc-server.exe" start=auto
sc start VNCServer
```

#### Docker Container

Create `Dockerfile`:
```dockerfile
FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y libx11-6 libxtst6 && \
    rm -rf /var/lib/apt/lists/*

COPY vnc-server /usr/local/bin/
COPY config/server.conf /etc/vnc/

EXPOSE 5900

CMD ["vnc-server"]
```

Build and run:
```bash
docker build -t vnc-server .
docker run -p 5900:5900 vnc-server
```

### Client Deployment

#### Desktop Application

**Linux:**
```bash
# Install to user directory
mkdir -p ~/.local/bin
cp vnc-client ~/.local/bin/

# Create desktop entry
cat > ~/.local/share/applications/vnc-client.desktop << EOF
[Desktop Entry]
Name=VNC Client
Exec=/home/$USER/.local/bin/vnc-client
Icon=vnc-client
Type=Application
Categories=Network;RemoteAccess;
EOF
```

**Windows:**
```batch
REM Create installer using NSIS or similar
REM Copy executable to Program Files
copy vnc-client.exe "C:\Program Files\VNC\"

REM Create Start Menu shortcut
```

**macOS:**
```bash
# Create application bundle
mkdir -p VNCClient.app/Contents/MacOS
cp vnc-client VNCClient.app/Contents/MacOS/

# Create Info.plist
cat > VNCClient.app/Contents/Info.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>vnc-client</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.vncclient</string>
    <key>CFBundleName</key>
    <string>VNC Client</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
</dict>
</plist>
EOF
```

#### Android APK

```bash
cd platforms/android
./gradlew assembleRelease

# APK location: app/build/outputs/apk/release/app-release.apk
```

## Configuration

### Server Configuration

Create `/etc/vnc/server.conf`:
```ini
[server]
port = 5900
password = yourpassword
desktop_name = VNC Desktop
max_clients = 5

[security]
enable_tls = false
tls_cert = /etc/vnc/server.crt
tls_key = /etc/vnc/server.key

[display]
width = 1920
height = 1080
depth = 24
```

### Client Configuration

Create `~/.vnc/client.conf`:
```ini
[connections]
default_port = 5900
save_passwords = false

[display]
fullscreen = false
scaling = fit_window
color_depth = 24

[input]
capture_keyboard = true
capture_mouse = false
```

## Testing

### Unit Tests

```bash
# Build with tests enabled
cmake .. -DBUILD_TESTS=ON
cmake --build .

# Run tests
ctest -V
```

### Integration Tests

```bash
# Start test server
./vnc-server --test-mode --port 5901 &

# Run client tests
./test-client --host localhost --port 5901

# Cleanup
killall vnc-server
```

### Performance Testing

```bash
# Benchmark encoding performance
./vnc-server --benchmark --encoding raw
./vnc-server --benchmark --encoding rre
./vnc-server --benchmark --encoding hextile

# Network latency testing
./vnc-client --host remote-host --latency-test
```

## Troubleshooting

### Common Build Issues

**Missing X11 libraries (Linux):**
```bash
sudo apt install libx11-dev libxtst-dev
```

**CMake version too old:**
```bash
# Install newer CMake from official website
wget https://cmake.org/files/v3.20/cmake-3.20.0-linux-x86_64.sh
chmod +x cmake-3.20.0-linux-x86_64.sh
sudo ./cmake-3.20.0-linux-x86_64.sh --prefix=/usr/local --skip-license
```

**OpenSSL not found (Windows):**
```batch
REM Set OpenSSL paths
set OPENSSL_ROOT_DIR=C:\OpenSSL-Win64
cmake .. -DENABLE_TLS=ON
```

### Runtime Issues

**Permission denied (screen capture):**
```bash
# Linux: Add user to appropriate groups
sudo usermod -a -G video $USER

# Logout and login again
```

**Port already in use:**
```bash
# Find process using port
sudo netstat -tulpn | grep :5900
sudo lsof -i :5900

# Kill process or use different port
sudo kill -9 <PID>
./vnc-server --port 5901
```

**Connection refused:**
```bash
# Check firewall settings
sudo ufw allow 5900
sudo firewall-cmd --add-port=5900/tcp --permanent

# Verify server is listening
netstat -ln | grep :5900
```

## Performance Tuning

### Server Optimization

```bash
# Adjust frame rate
./vnc-server --fps 30

# Enable hardware acceleration
./vnc-server --hw-accel

# Optimize for LAN/WAN
./vnc-server --profile lan    # Low compression, high quality
./vnc-server --profile wan    # High compression, lower quality
```

### Client Optimization

```bash
# Preferred encodings (ordered by preference)
./vnc-client --encodings "hextile,rre,raw"

# Display optimization
./vnc-client --color-depth 16  # Reduce color depth for speed
./vnc-client --compress-level 9 # Maximum compression
```

## Security Hardening

### Server Security

```bash
# Enable TLS
./vnc-server --tls --cert server.crt --key server.key

# Restrict access
./vnc-server --allow-hosts "192.168.1.0/24,10.0.0.0/8"

# Set strong password
./vnc-server --password-file /etc/vnc/passwd
```

### Network Security

```bash
# Use SSH tunnel
ssh -L 5900:localhost:5900 user@remote-host
./vnc-client --host localhost --port 5900

# VPN access only
# Configure firewall to only allow VPN subnet
```

This guide provides comprehensive instructions for building, deploying, and maintaining VNC installations across all supported platforms.