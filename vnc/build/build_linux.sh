#!/bin/bash
# Linux build script for VNC Server and Viewer

echo "Building VNC Server and Viewer for Linux..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed"
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r ../requirements.txt

# Install PyInstaller for creating executables
pip install pyinstaller

# Build VNC Server executable
echo "Building VNC Server executable..."
pyinstaller --onefile \
    --name "vnc-server" \
    --add-data "../protocol:protocol" \
    ../server/vnc_server.py

# Build VNC Viewer executable
echo "Building VNC Viewer executable..."
pyinstaller --onefile \
    --name "vnc-viewer" \
    --add-data "../protocol:protocol" \
    ../viewer/vnc_viewer.py

# Create distribution package
echo "Creating distribution package..."
mkdir -p dist/linux
cp dist/vnc-server dist/linux/
cp dist/vnc-viewer dist/linux/
cp ../README.md dist/linux/
cp ../docs/linux-setup.md dist/linux/README-LINUX.md

# Create .desktop files for GUI integration
cat > dist/linux/vnc-server.desktop << EOF
[Desktop Entry]
Name=VNC Server
Comment=VNC Server for desktop sharing
Exec=$(pwd)/dist/linux/vnc-server
Icon=applications-internet
Terminal=false
Type=Application
Categories=Network;RemoteAccess;
EOF

cat > dist/linux/vnc-viewer.desktop << EOF
[Desktop Entry]
Name=VNC Viewer
Comment=VNC Viewer for remote desktop access
Exec=$(pwd)/dist/linux/vnc-viewer
Icon=applications-internet
Terminal=false
Type=Application
Categories=Network;RemoteAccess;
EOF

# Create AppImage (if appimagetool is available)
if command -v appimagetool &> /dev/null; then
    echo "Creating AppImage..."
    mkdir -p appdir/usr/bin
    mkdir -p appdir/usr/share/applications
    mkdir -p appdir/usr/share/icons/hicolor/48x48/apps
    
    cp dist/vnc-server appdir/usr/bin/
    cp dist/vnc-viewer appdir/usr/bin/
    cp dist/linux/vnc-server.desktop appdir/usr/share/applications/
    cp dist/linux/vnc-viewer.desktop appdir/usr/share/applications/
    
    # Create AppRun script
    cat > appdir/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/vnc-viewer" "$@"
EOF
    chmod +x appdir/AppRun
    
    cp dist/linux/vnc-viewer.desktop appdir/
    
    appimagetool appdir dist/linux/VNC-Viewer.AppImage
fi

# Create tarball
echo "Creating distribution tarball..."
cd dist/linux
tar -czf ../vnc-linux-x64.tar.gz *
cd ../..

echo "Linux build complete!"
echo "Distribution files are in dist/linux/"