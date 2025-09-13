#!/bin/bash

# VNC Client Build Script
echo "Building VNC Client..."

# Create build directory
mkdir -p ../build/client

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
    LIBS="$LIBS -lws2_32"
fi

# Source files
COMMON_SOURCES="../src/common/rfb_protocol.cpp"
CLIENT_SOURCES="../src/client/vnc_client.cpp"
GUI_SOURCES="../src/gui/vnc_client_gui.cpp"

EXAMPLE_SOURCE="../examples/client_example.cpp"

# Compile
echo "Compiling VNC Client..."
$CXX $CXXFLAGS $INCLUDES \
    $COMMON_SOURCES $CLIENT_SOURCES $GUI_SOURCES $EXAMPLE_SOURCE \
    $LIBS -o ../build/client/vnc-client

if [ $? -eq 0 ]; then
    echo "VNC Client built successfully!"
    echo "Executable: ../build/client/vnc-client"
else
    echo "Build failed!"
    exit 1
fi