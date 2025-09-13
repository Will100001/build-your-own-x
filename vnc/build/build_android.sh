#!/bin/bash
# Android build script for VNC Viewer using Kivy

echo "Building VNC Viewer for Android..."

# Check if buildozer is installed
if ! command -v buildozer &> /dev/null; then
    echo "Installing buildozer..."
    pip install buildozer
fi

# Check if cython is installed
if ! pip show cython &> /dev/null; then
    echo "Installing cython..."
    pip install cython
fi

# Create buildozer.spec if it doesn't exist
if [ ! -f "buildozer.spec" ]; then
    echo "Creating buildozer.spec..."
    buildozer init
    
    # Modify buildozer.spec for VNC Viewer
    cat > buildozer.spec << 'EOF'
[app]
title = VNC Viewer
package.name = vncviewer
package.domain = org.buildyourownx

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0
requirements = python3,kivy,pillow,pyjnius

[buildozer]
log_level = 2

[android]
api = 31
minapi = 21
ndk = 25b
sdk = 31

archs = arm64-v8a, armeabi-v7a

[ios]
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.7.0

[osx]
osx.python_version = 3
osx.kivy_version = 1.9.1
EOF
fi

# Create Kivy-based VNC Viewer for Android
cat > vnc_viewer_android.py << 'EOF'
"""
Android VNC Viewer using Kivy
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import threading
import socket
import struct
import sys
import os

# Add protocol directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'protocol'))

try:
    from rfb import (RFBProtocol, PixelFormat, SecurityType, EncodingType,
                     ClientMessage, ServerMessage, RFB_VERSION_3_8)
except ImportError:
    print("Warning: Could not import RFB protocol")

class VNCViewerApp(App):
    def __init__(self):
        super().__init__()
        self.connection = None
        self.connected = False
        
    def build(self):
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Connection controls
        conn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        
        self.host_input = TextInput(text='192.168.1.100', hint_text='Host', multiline=False)
        self.port_input = TextInput(text='5900', hint_text='Port', multiline=False)
        self.password_input = TextInput(hint_text='Password', password=True, multiline=False)
        
        conn_layout.add_widget(Label(text='Host:', size_hint_x=None, width=50))
        conn_layout.add_widget(self.host_input)
        conn_layout.add_widget(Label(text='Port:', size_hint_x=None, width=50))
        conn_layout.add_widget(self.port_input)
        conn_layout.add_widget(Label(text='Pass:', size_hint_x=None, width=50))
        conn_layout.add_widget(self.password_input)
        
        main_layout.add_widget(conn_layout)
        
        # Connect button
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        self.connect_button = Button(text='Connect')
        self.connect_button.bind(on_press=self.connect)
        self.disconnect_button = Button(text='Disconnect', disabled=True)
        self.disconnect_button.bind(on_press=self.disconnect)
        
        button_layout.add_widget(self.connect_button)
        button_layout.add_widget(self.disconnect_button)
        main_layout.add_widget(button_layout)
        
        # Status label
        self.status_label = Label(text='Not connected', size_hint_y=None, height=30)
        main_layout.add_widget(self.status_label)
        
        # VNC display
        self.vnc_image = Image()
        main_layout.add_widget(self.vnc_image)
        
        return main_layout
    
    def connect(self, instance):
        """Connect to VNC server"""
        host = self.host_input.text or '192.168.1.100'
        port = int(self.port_input.text or '5900')
        password = self.password_input.text
        
        self.status_label.text = f'Connecting to {host}:{port}...'
        
        # Start connection in separate thread
        thread = threading.Thread(target=self._connect_thread, args=(host, port, password))
        thread.daemon = True
        thread.start()
    
    def disconnect(self, instance):
        """Disconnect from VNC server"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
        
        self.connected = False
        self.connect_button.disabled = False
        self.disconnect_button.disabled = True
        self.status_label.text = 'Disconnected'
    
    def _connect_thread(self, host, port, password):
        """Connection thread"""
        try:
            # Simple connection test for demo
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            sock.close()
            
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._connection_success(host, port), 0)
            
        except Exception as e:
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._connection_error(str(e)), 0)
    
    def _connection_success(self, host, port):
        """Handle successful connection"""
        self.connected = True
        self.connect_button.disabled = True
        self.disconnect_button.disabled = False
        self.status_label.text = f'Connected to {host}:{port}'
        
        # Create a dummy framebuffer for demo
        self._create_dummy_framebuffer()
    
    def _connection_error(self, error):
        """Handle connection error"""
        self.status_label.text = f'Connection failed: {error}'
        
        # Show error popup
        popup = Popup(title='Connection Error',
                     content=Label(text=str(error)),
                     size_hint=(None, None), size=(400, 200))
        popup.open()
    
    def _create_dummy_framebuffer(self):
        """Create a dummy framebuffer for demonstration"""
        # Create a simple gradient texture
        width, height = 320, 240
        buf = []
        
        for y in range(height):
            for x in range(width):
                r = int((x / width) * 255)
                g = int((y / height) * 255)
                b = 128
                buf.extend([r, g, b])
        
        # Create texture
        texture = Texture.create(size=(width, height))
        texture.blit_buffer(bytes(buf), colorfmt='rgb', bufferfmt='ubyte')
        
        # Apply texture to image
        self.vnc_image.texture = texture

if __name__ == '__main__':
    VNCViewerApp().run()
EOF

# Create main.py for buildozer
cp vnc_viewer_android.py main.py

# Build for Android
echo "Building Android APK..."
buildozer android debug

# Check if build was successful
if [ -f "bin/*.apk" ]; then
    echo "Android build complete!"
    echo "APK file: $(ls bin/*.apk)"
    
    # Create distribution directory
    mkdir -p dist/android
    cp bin/*.apk dist/android/
    cp ../README.md dist/android/
    cp ../docs/android-setup.md dist/android/README-ANDROID.md
    
    echo "Android distribution files are in dist/android/"
else
    echo "Android build failed!"
    echo "Check the buildozer output above for errors"
    exit 1
fi