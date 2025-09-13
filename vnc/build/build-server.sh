#!/bin/bash

# VNC Server Build Script
echo "Building VNC Server..."

# Create build directory
mkdir -p ../build/server

# Compiler settings
CXX="g++"
CXXFLAGS="-std=c++17 -Wall -Wextra -O2"
INCLUDES="-I../src"
LIBS="-lpthread"

# Add platform-specific settings
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Building for Linux..."
    LIBS="$LIBS -lX11 -lXtst"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Building for macOS..."
    # Add macOS-specific libraries here
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "Building for Windows..."
    LIBS="$LIBS -lgdi32 -luser32"
fi

# Source files
COMMON_SOURCES="../src/common/rfb_protocol.cpp ../src/common/platform_factory.cpp"
SERVER_SOURCES="../src/server/vnc_server.cpp"
GUI_SOURCES="../src/gui/vnc_server_gui.cpp"
PLATFORM_SOURCES=""

# Add platform-specific sources
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    PLATFORM_SOURCES="../platforms/windows/windows_impl.cpp"
fi

EXAMPLE_SOURCE="../examples/server_example.cpp"

# Compile
echo "Compiling VNC Server..."
$CXX $CXXFLAGS $INCLUDES \
    $COMMON_SOURCES $SERVER_SOURCES $GUI_SOURCES $PLATFORM_SOURCES $EXAMPLE_SOURCE \
    $LIBS -o ../build/server/vnc-server

if [ $? -eq 0 ]; then
    echo "VNC Server built successfully!"
    echo "Executable: ../build/server/vnc-server"
else
    echo "Build failed!"
    exit 1
fi