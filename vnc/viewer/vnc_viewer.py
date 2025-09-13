"""
VNC Viewer Implementation

This module implements a VNC viewer/client with a GUI interface
for connecting to VNC servers and viewing remote desktops.
"""

import socket
import threading
import time
import struct
import logging
import argparse
from typing import Optional, Tuple, List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol.rfb import (
    RFBProtocol, PixelFormat, SecurityType, EncodingType,
    ClientMessage, ServerMessage, Rectangle, 
    RawEncoding, VNCAuth, KeySym, PointerMask,
    RFB_VERSION_3_8
)

# GUI imports - try multiple backends
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                QHBoxLayout, QLabel, QLineEdit, QPushButton,
                                QTextEdit, QMessageBox, QDialog, QDialogButtonBox,
                                QFormLayout, QSpinBox, QCheckBox)
    from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, pyqtSlot
    from PyQt5.QtGui import QPixmap, QImage, QPainter, QKeyEvent, QMouseEvent
    GUI_BACKEND = "PyQt5"
except ImportError:
    try:
        from tkinter import *
        from tkinter import ttk, messagebox, simpledialog
        import tkinter as tk
        from PIL import Image, ImageTk
        GUI_BACKEND = "tkinter"
    except ImportError:
        GUI_BACKEND = None
        print("Warning: No GUI backend available")

class VNCConnection(QThread if GUI_BACKEND == "PyQt5" else object):
    """Handles VNC connection and protocol"""
    
    # PyQt5 signals
    if GUI_BACKEND == "PyQt5":
        frameBufferUpdated = pyqtSignal(QImage)
        connectionError = pyqtSignal(str)
        connectionEstablished = pyqtSignal()
        
    def __init__(self, host: str, port: int, password: str = ""):
        if GUI_BACKEND == "PyQt5":
            super().__init__()
        self.host = host
        self.port = port
        self.password = password
        self.socket: Optional[socket.socket] = None
        self.protocol: Optional[RFBProtocol] = None
        self.connected = False
        self.running = False
        self.screen_width = 0
        self.screen_height = 0
        self.pixel_format = PixelFormat()
        self.server_name = ""
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
    def connect_to_server(self) -> bool:
        """Connect to VNC server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.protocol = RFBProtocol(self.socket)
            
            # Handshake
            if not self._do_handshake():
                return False
                
            # Authentication
            if not self._do_authentication():
                return False
                
            # Initialization
            if not self._do_initialization():
                return False
                
            self.connected = True
            self.logger.info(f"Connected to {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            if GUI_BACKEND == "PyQt5":
                self.connectionError.emit(str(e))
            return False
            
    def disconnect(self) -> None:
        """Disconnect from server"""
        self.running = False
        self.connected = False
        if self.socket:
            self.socket.close()
        self.logger.info("Disconnected from server")
        
    def run(self) -> None:
        """Main thread loop for PyQt5"""
        if not self.connect_to_server():
            return
            
        if GUI_BACKEND == "PyQt5":
            self.connectionEstablished.emit()
            
        self.running = True
        
        # Request initial framebuffer update
        self._request_framebuffer_update(False, 0, 0, 
                                       self.screen_width, self.screen_height)
        
        # Main message loop
        while self.running and self.connected:
            try:
                message_type = self.protocol.receive_uint8()
                
                if message_type == ServerMessage.FRAMEBUFFER_UPDATE:
                    self._handle_framebuffer_update()
                elif message_type == ServerMessage.SET_COLOUR_MAP_ENTRIES:
                    self._handle_set_colour_map_entries()
                elif message_type == ServerMessage.BELL:
                    self._handle_bell()
                elif message_type == ServerMessage.SERVER_CUT_TEXT:
                    self._handle_server_cut_text()
                else:
                    self.logger.warning(f"Unknown server message: {message_type}")
                    
            except Exception as e:
                if self.running:
                    self.logger.error(f"Protocol error: {e}")
                    if GUI_BACKEND == "PyQt5":
                        self.connectionError.emit(str(e))
                break
                
    def _do_handshake(self) -> bool:
        """Perform RFB handshake"""
        try:
            # Receive server version
            server_version = self.protocol.receive_data(12)
            self.logger.info(f"Server version: {server_version}")
            
            # Send client version
            self.protocol.send_data(RFB_VERSION_3_8)
            return True
            
        except Exception as e:
            self.logger.error(f"Handshake failed: {e}")
            return False
            
    def _do_authentication(self) -> bool:
        """Perform authentication"""
        try:
            # Receive security types
            num_types = self.protocol.receive_uint8()
            if num_types == 0:
                # Connection failed
                reason_length = self.protocol.receive_uint32()
                reason = self.protocol.receive_data(reason_length).decode('utf-8')
                self.logger.error(f"Connection failed: {reason}")
                return False
                
            security_types = []
            for _ in range(num_types):
                security_types.append(self.protocol.receive_uint8())
                
            # Choose security type
            if SecurityType.NONE in security_types and not self.password:
                # No authentication
                self.protocol.send_uint8(SecurityType.NONE)
            elif SecurityType.VNC_AUTH in security_types and self.password:
                # VNC authentication
                self.protocol.send_uint8(SecurityType.VNC_AUTH)
                
                # Receive challenge
                challenge = self.protocol.receive_data(16)
                
                # Send response
                response = VNCAuth.encrypt_challenge(challenge, self.password)
                self.protocol.send_data(response)
                
                # Receive result
                result = self.protocol.receive_uint32()
                if result != 0:
                    self.logger.error("Authentication failed")
                    return False
            else:
                self.logger.error("No suitable authentication method")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
            
    def _do_initialization(self) -> bool:
        """Perform client initialization"""
        try:
            # Send ClientInit (shared flag = 1)
            self.protocol.send_uint8(1)
            
            # Receive ServerInit
            self.screen_width = self.protocol.receive_uint16()
            self.screen_height = self.protocol.receive_uint16()
            
            # Receive pixel format
            pf_data = self.protocol.receive_data(16)
            self.pixel_format = PixelFormat.unpack(pf_data)
            
            # Receive desktop name
            name_length = self.protocol.receive_uint32()
            self.server_name = self.protocol.receive_data(name_length).decode('utf-8')
            
            self.logger.info(f"Desktop: {self.server_name} ({self.screen_width}x{self.screen_height})")
            
            # Send pixel format (use server's format)
            self._send_set_pixel_format()
            
            # Send supported encodings
            self._send_set_encodings([EncodingType.RAW])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
            
    def _send_set_pixel_format(self) -> None:
        """Send SetPixelFormat message"""
        data = struct.pack("!Bxxx", ClientMessage.SET_PIXEL_FORMAT)
        data += self.pixel_format.pack()
        self.protocol.send_data(data)
        
    def _send_set_encodings(self, encodings: List[EncodingType]) -> None:
        """Send SetEncodings message"""
        data = struct.pack("!BxH", ClientMessage.SET_ENCODINGS, len(encodings))
        for encoding in encodings:
            data += struct.pack("!I", encoding.value)
        self.protocol.send_data(data)
        
    def _request_framebuffer_update(self, incremental: bool, x: int, y: int, 
                                  width: int, height: int) -> None:
        """Request framebuffer update"""
        data = struct.pack("!BBHHHH", ClientMessage.FRAMEBUFFER_UPDATE_REQUEST,
                          incremental, x, y, width, height)
        self.protocol.send_data(data)
        
    def _handle_framebuffer_update(self) -> None:
        """Handle FramebufferUpdate message"""
        # Skip padding
        self.protocol.receive_data(1)
        num_rectangles = self.protocol.receive_uint16()
        
        for _ in range(num_rectangles):
            x = self.protocol.receive_uint16()
            y = self.protocol.receive_uint16()
            width = self.protocol.receive_uint16()
            height = self.protocol.receive_uint16()
            encoding = self.protocol.receive_uint32()
            
            if encoding == EncodingType.RAW:
                # Calculate expected data size
                bytes_per_pixel = self.pixel_format.bits_per_pixel // 8
                data_size = width * height * bytes_per_pixel
                pixel_data = self.protocol.receive_data(data_size)
                
                # Convert to QImage and emit signal
                if GUI_BACKEND == "PyQt5":
                    image = self._create_qimage(pixel_data, width, height, x, y)
                    if image:
                        self.frameBufferUpdated.emit(image)
                        
        # Request next update
        self._request_framebuffer_update(True, 0, 0, 
                                       self.screen_width, self.screen_height)
        
    def _create_qimage(self, pixel_data: bytes, width: int, height: int, 
                      x: int, y: int) -> Optional[QImage]:
        """Create QImage from pixel data"""
        if GUI_BACKEND != "PyQt5":
            return None
            
        try:
            # Create QImage (assuming RGB888 format)
            if self.pixel_format.bits_per_pixel == 32:
                format = QImage.Format_RGB32
            elif self.pixel_format.bits_per_pixel == 24:
                format = QImage.Format_RGB888
            else:
                format = QImage.Format_RGB888
                
            image = QImage(pixel_data, width, height, format)
            return image
            
        except Exception as e:
            self.logger.error(f"Failed to create QImage: {e}")
            return None
            
    def _handle_set_colour_map_entries(self) -> None:
        """Handle SetColourMapEntries message"""
        # Skip for now
        pass
        
    def _handle_bell(self) -> None:
        """Handle Bell message"""
        self.logger.info("Server bell")
        
    def _handle_server_cut_text(self) -> None:
        """Handle ServerCutText message"""
        # Skip padding
        self.protocol.receive_data(3)
        length = self.protocol.receive_uint32()
        text = self.protocol.receive_data(length).decode('utf-8', errors='ignore')
        self.logger.info(f"Server clipboard: {text[:50]}...")
        
    def send_key_event(self, key: int, down: bool) -> None:
        """Send key event to server"""
        if not self.connected:
            return
            
        data = struct.pack("!BBxxI", ClientMessage.KEY_EVENT, down, key)
        self.protocol.send_data(data)
        
    def send_pointer_event(self, x: int, y: int, button_mask: int) -> None:
        """Send pointer event to server"""
        if not self.connected:
            return
            
        data = struct.pack("!BBHH", ClientMessage.POINTER_EVENT, 
                          button_mask, x, y)
        self.protocol.send_data(data)

class VNCWidget(QWidget if GUI_BACKEND == "PyQt5" else object):
    """Widget for displaying VNC framebuffer"""
    
    def __init__(self, connection: VNCConnection):
        if GUI_BACKEND == "PyQt5":
            super().__init__()
        self.connection = connection
        self.framebuffer_image: Optional[QImage] = None
        self.scale_factor = 1.0
        
        if GUI_BACKEND == "PyQt5":
            self.setMinimumSize(800, 600)
            self.setFocusPolicy(Qt.StrongFocus)
            
    @pyqtSlot(QImage) if GUI_BACKEND == "PyQt5" else lambda x: None
    def update_framebuffer(self, image: QImage) -> None:
        """Update framebuffer display"""
        self.framebuffer_image = image
        if GUI_BACKEND == "PyQt5":
            self.update()
            
    def paintEvent(self, event) -> None:
        """Paint event handler"""
        if GUI_BACKEND != "PyQt5" or not self.framebuffer_image:
            return
            
        painter = QPainter(self)
        
        # Scale image to fit widget
        widget_size = self.size()
        image_size = self.framebuffer_image.size()
        
        scaled_image = self.framebuffer_image.scaled(
            widget_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
        # Center the image
        x = (widget_size.width() - scaled_image.width()) // 2
        y = (widget_size.height() - scaled_image.height()) // 2
        
        painter.drawImage(x, y, scaled_image)
        
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events"""
        if GUI_BACKEND != "PyQt5":
            return
            
        key = self._qt_key_to_keysym(event.key())
        if key:
            self.connection.send_key_event(key, True)
            
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Handle key release events"""
        if GUI_BACKEND != "PyQt5":
            return
            
        key = self._qt_key_to_keysym(event.key())
        if key:
            self.connection.send_key_event(key, False)
            
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events"""
        if GUI_BACKEND != "PyQt5":
            return
            
        button_mask = self._qt_buttons_to_mask(event.buttons())
        self.connection.send_pointer_event(event.x(), event.y(), button_mask)
        
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release events"""
        if GUI_BACKEND != "PyQt5":
            return
            
        button_mask = self._qt_buttons_to_mask(event.buttons())
        self.connection.send_pointer_event(event.x(), event.y(), button_mask)
        
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move events"""
        if GUI_BACKEND != "PyQt5":
            return
            
        button_mask = self._qt_buttons_to_mask(event.buttons())
        self.connection.send_pointer_event(event.x(), event.y(), button_mask)
        
    def _qt_key_to_keysym(self, qt_key: int) -> Optional[int]:
        """Convert Qt key to X11 keysym"""
        if GUI_BACKEND != "PyQt5":
            return None
            
        key_map = {
            Qt.Key_Backspace: KeySym.BACKSPACE,
            Qt.Key_Tab: KeySym.TAB,
            Qt.Key_Return: KeySym.RETURN,
            Qt.Key_Escape: KeySym.ESCAPE,
            Qt.Key_Delete: KeySym.DELETE,
            Qt.Key_Space: KeySym.SPACE,
        }
        
        if qt_key in key_map:
            return key_map[qt_key]
        elif Qt.Key_A <= qt_key <= Qt.Key_Z:
            return ord('a') + (qt_key - Qt.Key_A)
        elif Qt.Key_0 <= qt_key <= Qt.Key_9:
            return ord('0') + (qt_key - Qt.Key_0)
        else:
            return None
            
    def _qt_buttons_to_mask(self, qt_buttons) -> int:
        """Convert Qt mouse buttons to VNC button mask"""
        if GUI_BACKEND != "PyQt5":
            return 0
            
        mask = 0
        if qt_buttons & Qt.LeftButton:
            mask |= PointerMask.LEFT
        if qt_buttons & Qt.MiddleButton:
            mask |= PointerMask.MIDDLE
        if qt_buttons & Qt.RightButton:
            mask |= PointerMask.RIGHT
        return mask

class ConnectionDialog(QDialog if GUI_BACKEND == "PyQt5" else object):
    """Dialog for connection settings"""
    
    def __init__(self, parent=None):
        if GUI_BACKEND == "PyQt5":
            super().__init__(parent)
            self.setWindowTitle("Connect to VNC Server")
            self.setup_ui()
            
    def setup_ui(self) -> None:
        """Setup dialog UI"""
        if GUI_BACKEND != "PyQt5":
            return
            
        layout = QFormLayout(self)
        
        self.host_edit = QLineEdit("localhost")
        layout.addRow("Host:", self.host_edit)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(5900)
        layout.addRow("Port:", self.port_spin)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.password_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def get_connection_info(self) -> Tuple[str, int, str]:
        """Get connection information"""
        if GUI_BACKEND != "PyQt5":
            return "localhost", 5900, ""
            
        return (self.host_edit.text(), 
                self.port_spin.value(),
                self.password_edit.text())

class VNCViewer(QMainWindow if GUI_BACKEND == "PyQt5" else object):
    """Main VNC Viewer application"""
    
    def __init__(self):
        if GUI_BACKEND == "PyQt5":
            super().__init__()
            self.setWindowTitle("VNC Viewer")
            self.setGeometry(100, 100, 1024, 768)
            
        self.connection: Optional[VNCConnection] = None
        self.vnc_widget: Optional[VNCWidget] = None
        
        if GUI_BACKEND == "PyQt5":
            self.setup_ui()
            
    def setup_ui(self) -> None:
        """Setup main window UI"""
        if GUI_BACKEND != "PyQt5":
            return
            
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Connection controls
        conn_layout = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.show_connection_dialog)
        conn_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect)
        self.disconnect_button.setEnabled(False)
        conn_layout.addWidget(self.disconnect_button)
        
        conn_layout.addStretch()
        self.status_label = QLabel("Not connected")
        conn_layout.addWidget(self.status_label)
        
        layout.addLayout(conn_layout)
        
        # VNC display area
        self.vnc_widget = VNCWidget(None)
        layout.addWidget(self.vnc_widget)
        
    def show_connection_dialog(self) -> None:
        """Show connection dialog"""
        if GUI_BACKEND != "PyQt5":
            return
            
        dialog = ConnectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            host, port, password = dialog.get_connection_info()
            self.connect_to_server(host, port, password)
            
    def connect_to_server(self, host: str, port: int, password: str) -> None:
        """Connect to VNC server"""
        if self.connection:
            self.disconnect()
            
        self.connection = VNCConnection(host, port, password)
        self.vnc_widget.connection = self.connection
        
        if GUI_BACKEND == "PyQt5":
            self.connection.frameBufferUpdated.connect(self.vnc_widget.update_framebuffer)
            self.connection.connectionError.connect(self.on_connection_error)
            self.connection.connectionEstablished.connect(self.on_connection_established)
            
        self.connection.start()
        self.status_label.setText(f"Connecting to {host}:{port}...")
        
    def disconnect(self) -> None:
        """Disconnect from server"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
            
        if GUI_BACKEND == "PyQt5":
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.status_label.setText("Not connected")
            
    @pyqtSlot(str) if GUI_BACKEND == "PyQt5" else lambda x: None
    def on_connection_error(self, error: str) -> None:
        """Handle connection error"""
        if GUI_BACKEND == "PyQt5":
            QMessageBox.critical(self, "Connection Error", error)
            self.disconnect()
            
    @pyqtSlot() if GUI_BACKEND == "PyQt5" else lambda: None
    def on_connection_established(self) -> None:
        """Handle successful connection"""
        if GUI_BACKEND == "PyQt5":
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.status_label.setText(f"Connected to {self.connection.server_name}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='VNC Viewer')
    parser.add_argument('--host', default='', help='VNC server host')
    parser.add_argument('--port', type=int, default=5900, help='VNC server port')
    parser.add_argument('--password', default='', help='VNC password')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        
    if GUI_BACKEND == "PyQt5":
        app = QApplication(sys.argv)
        viewer = VNCViewer()
        viewer.show()
        
        # Auto-connect if host specified
        if args.host:
            viewer.connect_to_server(args.host, args.port, args.password)
            
        sys.exit(app.exec_())
    else:
        print("No GUI backend available. Please install PyQt5.")
        sys.exit(1)

if __name__ == "__main__":
    main()