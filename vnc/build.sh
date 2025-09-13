#!/bin/bash

# VNC Build Script for Windows and Android
# This script builds both VNC Viewer and Server for Windows and Android platforms

set -e

echo "=== VNC Build Script ==="
echo "Building VNC Server and Viewer for Windows and Android"
echo ""

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not installed."
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "Error: npm is required but not installed."
    exit 1
fi

# Function to build Windows app
build_windows() {
    local app_type=$1
    echo "Building VNC $app_type for Windows..."
    
    cd "$app_type"
    
    # Install dependencies
    echo "Installing dependencies..."
    npm install
    
    # Build for Windows
    echo "Building Windows executable..."
    npm run build-win
    
    cd ..
    echo "VNC $app_type for Windows built successfully!"
}

# Function to build Android app
build_android() {
    local app_type=$1
    echo "Building VNC $app_type for Android..."
    
    cd "$app_type"
    
    # Build Android WebView app
    echo "Generating Android project..."
    npm run build-android
    
    cd ..
    echo "VNC $app_type for Android built successfully!"
}

# Function to run tests
run_tests() {
    echo "Running tests..."
    
    # Test shared components
    echo "Testing shared VNC protocol..."
    node -e "
        const VNCProtocol = require('./shared/vnc-protocol.js');
        const protocol = new VNCProtocol();
        console.log('VNC Protocol loaded successfully');
        console.log('Protocol version:', VNCProtocol.PROTOCOL_VERSION);
    "
    
    echo "All tests passed!"
}

# Function to create demo HTML files
create_demos() {
    echo "Creating demo HTML files..."
    
    # Create viewer demo
    cat > demo-viewer.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VNC Viewer Demo</title>
    <link rel="stylesheet" href="shared/vnc-styles.css">
</head>
<body>
    <div id="vnc-app"></div>
    <script src="shared/vnc-protocol.js"></script>
    <script src="shared/vnc-gui.js"></script>
    <script>
        const viewer = new VNCViewer('vnc-app');
        console.log('VNC Viewer demo loaded');
    </script>
</body>
</html>
EOF

    # Create server demo
    cat > demo-server.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VNC Server Demo</title>
    <link rel="stylesheet" href="shared/vnc-styles.css">
</head>
<body>
    <div id="vnc-app"></div>
    <script src="shared/vnc-protocol.js"></script>
    <script src="shared/vnc-gui.js"></script>
    <script>
        const server = new VNCServer('vnc-app');
        console.log('VNC Server demo loaded');
    </script>
</body>
</html>
EOF

    echo "Demo files created: demo-viewer.html, demo-server.html"
}

# Main build process
echo "Starting build process..."

# Create demos first
create_demos

# Run tests
run_tests

# Build apps based on command line arguments
if [ "$1" = "viewer" ] || [ "$1" = "all" ] || [ -z "$1" ]; then
    echo ""
    echo "=== Building VNC Viewer ==="
    
    # Build Windows version
    if [ "$2" != "android-only" ]; then
        build_windows "viewer"
    fi
    
    # Build Android version
    if [ "$2" != "windows-only" ]; then
        build_android "viewer"
    fi
fi

if [ "$1" = "server" ] || [ "$1" = "all" ] || [ -z "$1" ]; then
    echo ""
    echo "=== Building VNC Server ==="
    
    # Build Windows version
    if [ "$2" != "android-only" ]; then
        build_windows "server"
    fi
    
    # Build Android version
    if [ "$2" != "windows-only" ]; then
        build_android "server"
    fi
fi

echo ""
echo "=== Build Complete ==="
echo "Built applications:"
echo "  - VNC Viewer (Windows): viewer/dist/"
echo "  - VNC Viewer (Android): android/viewer/"
echo "  - VNC Server (Windows): server/dist/"
echo "  - VNC Server (Android): android/server/"
echo ""
echo "Demo files:"
echo "  - Browser Viewer Demo: demo-viewer.html"
echo "  - Browser Server Demo: demo-server.html"
echo ""
echo "To run demos:"
echo "  python3 -m http.server 8080"
echo "  Then open http://localhost:8080/demo-viewer.html"
echo ""