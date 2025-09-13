#!/usr/bin/env python3
"""
RFB (Remote Framebuffer) Protocol Implementation for VNC Server
Implements the core VNC protocol for remote desktop access.
"""

import struct
import socket
import threading
import hashlib
import time
from typing import Optional, Tuple, Dict, Any


class RFBProtocol:
    """Implements the RFB protocol for VNC communication."""
    
    # RFB Protocol constants
    RFB_VERSION = b"RFB 003.008\n"
    
    # Security types
    SECURITY_INVALID = 0
    SECURITY_NONE = 1
    SECURITY_VNC_AUTH = 2
    
    # Client to server message types
    SET_PIXEL_FORMAT = 0
    SET_ENCODINGS = 2
    FRAMEBUFFER_UPDATE_REQUEST = 3
    KEY_EVENT = 4
    POINTER_EVENT = 5
    CLIENT_CUT_TEXT = 6
    
    # Server to client message types
    FRAMEBUFFER_UPDATE = 0
    SET_COLOR_MAP_ENTRIES = 1
    BELL = 2
    SERVER_CUT_TEXT = 3
    
    # Encoding types
    RAW_ENCODING = 0
    COPY_RECT_ENCODING = 1
    RRE_ENCODING = 2
    HEXTILE_ENCODING = 5
    
    def __init__(self, width: int = 1024, height: int = 768, name: str = "Python VNC Server"):
        self.width = width
        self.height = height
        self.name = name.encode('utf-8')
        self.pixel_format = {
            'bits_per_pixel': 32,
            'depth': 24,
            'big_endian': 0,
            'true_color': 1,
            'red_max': 255,
            'green_max': 255,
            'blue_max': 255,
            'red_shift': 16,
            'green_shift': 8,
            'blue_shift': 0
        }
        
    def pack_pixel_format(self) -> bytes:
        """Pack pixel format into bytes according to RFB specification."""
        return struct.pack('!BBBBHHHBBB3x',
                          self.pixel_format['bits_per_pixel'],
                          self.pixel_format['depth'],
                          self.pixel_format['big_endian'],
                          self.pixel_format['true_color'],
                          self.pixel_format['red_max'],
                          self.pixel_format['green_max'],
                          self.pixel_format['blue_max'],
                          self.pixel_format['red_shift'],
                          self.pixel_format['green_shift'],
                          self.pixel_format['blue_shift'])
    
    def create_server_init(self) -> bytes:
        """Create server initialization message."""
        pixel_format = self.pack_pixel_format()
        name_length = len(self.name)
        return struct.pack('!HH', self.width, self.height) + pixel_format + \
               struct.pack('!I', name_length) + self.name
    
    def venc_encrypt(self, password: str, challenge: bytes) -> bytes:
        """VNC DES encryption for authentication."""
        # Simplified DES encryption for VNC authentication
        # Note: This is a basic implementation for demonstration
        key = (password + '\x00' * 8)[:8].encode('utf-8')
        
        # Basic XOR encryption (simplified for demo purposes)
        # In a real implementation, this would use proper DES encryption
        encrypted = bytearray()
        for i in range(16):
            encrypted.append(challenge[i] ^ key[i % 8])
        
        return bytes(encrypted)


class VNCConnection:
    """Handles a single VNC client connection."""
    
    def __init__(self, socket: socket.socket, address: Tuple[str, int], 
                 auth_callback=None, screen_capture_callback=None):
        self.socket = socket
        self.address = address
        self.auth_callback = auth_callback
        self.screen_capture_callback = screen_capture_callback
        self.rfb = RFBProtocol()
        self.authenticated = False
        self.running = False
        
    def send_data(self, data: bytes) -> bool:
        """Send data to client with error handling."""
        try:
            self.socket.sendall(data)
            return True
        except socket.error:
            return False
    
    def receive_data(self, length: int) -> Optional[bytes]:
        """Receive exact amount of data from client."""
        try:
            data = b''
            while len(data) < length:
                chunk = self.socket.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            return data
        except socket.error:
            return None
    
    def handle_authentication(self) -> bool:
        """Handle VNC authentication process."""
        # Send security types
        if self.auth_callback:
            # VNC authentication
            security_types = struct.pack('!BB', 1, self.rfb.SECURITY_VNC_AUTH)
        else:
            # No authentication
            security_types = struct.pack('!BB', 1, self.rfb.SECURITY_NONE)
        
        if not self.send_data(security_types):
            return False
        
        # Receive client's choice
        choice_data = self.receive_data(1)
        if not choice_data:
            return False
        
        choice = struct.unpack('!B', choice_data)[0]
        
        if choice == self.rfb.SECURITY_NONE:
            # Send security result (success)
            result = struct.pack('!I', 0)
            return self.send_data(result)
        
        elif choice == self.rfb.SECURITY_VNC_AUTH and self.auth_callback:
            # Generate challenge
            challenge = hashlib.md5(str(time.time()).encode()).digest()
            if not self.send_data(challenge):
                return False
            
            # Receive response
            response = self.receive_data(16)
            if not response:
                return False
            
            # Verify authentication
            if self.auth_callback(challenge, response):
                result = struct.pack('!I', 0)  # Success
                self.authenticated = True
            else:
                result = struct.pack('!I', 1)  # Failed
            
            return self.send_data(result)
        
        return False
    
    def handle_initialization(self) -> bool:
        """Handle client initialization."""
        # Receive client init
        client_init = self.receive_data(1)
        if not client_init:
            return False
        
        # Send server init
        server_init = self.rfb.create_server_init()
        return self.send_data(server_init)
    
    def create_framebuffer_update(self, x: int, y: int, width: int, height: int, 
                                 pixels: bytes) -> bytes:
        """Create a framebuffer update message."""
        header = struct.pack('!BXHHHHHHI', 
                            self.rfb.FRAMEBUFFER_UPDATE,
                            1,  # number of rectangles
                            x, y, width, height,
                            self.rfb.RAW_ENCODING)
        return header + pixels
    
    def handle_client_messages(self):
        """Handle incoming client messages."""
        while self.running:
            try:
                message_type_data = self.receive_data(1)
                if not message_type_data:
                    break
                
                message_type = struct.unpack('!B', message_type_data)[0]
                
                if message_type == self.rfb.FRAMEBUFFER_UPDATE_REQUEST:
                    # Handle framebuffer update request
                    request_data = self.receive_data(9)
                    if not request_data:
                        break
                    
                    incremental, x, y, width, height = struct.unpack('!BHHHH', request_data)
                    
                    # Generate or capture screen data
                    if self.screen_capture_callback:
                        pixels = self.screen_capture_callback(x, y, width, height)
                    else:
                        # Generate a simple pattern for demo
                        pixels = self.generate_demo_pixels(width, height)
                    
                    # Send framebuffer update
                    update = self.create_framebuffer_update(x, y, width, height, pixels)
                    if not self.send_data(update):
                        break
                
                elif message_type == self.rfb.KEY_EVENT:
                    # Handle key event
                    key_data = self.receive_data(7)
                    if key_data:
                        down_flag, key = struct.unpack('!BXXl', key_data)
                        print(f"Key event: {'down' if down_flag else 'up'}, key: {key}")
                
                elif message_type == self.rfb.POINTER_EVENT:
                    # Handle pointer event
                    pointer_data = self.receive_data(5)
                    if pointer_data:
                        button_mask, x, y = struct.unpack('!BHH', pointer_data)
                        print(f"Pointer event: buttons: {button_mask}, pos: ({x}, {y})")
                
                elif message_type == self.rfb.SET_PIXEL_FORMAT:
                    # Handle pixel format change
                    format_data = self.receive_data(19)
                    if not format_data:
                        break
                
                elif message_type == self.rfb.SET_ENCODINGS:
                    # Handle encoding preferences
                    header = self.receive_data(3)
                    if not header:
                        break
                    count = struct.unpack('!BH', header)[1]
                    encodings = self.receive_data(count * 4)
                    if not encodings:
                        break
            
            except Exception as e:
                print(f"Error handling client message: {e}")
                break
    
    def generate_demo_pixels(self, width: int, height: int) -> bytes:
        """Generate demo pixel data for testing."""
        pixels = bytearray()
        for y in range(height):
            for x in range(width):
                # Create a simple gradient pattern
                r = (x * 255) // width
                g = (y * 255) // height
                b = ((x + y) * 255) // (width + height)
                # 32-bit RGBA format
                pixels.extend(struct.pack('!I', (r << 16) | (g << 8) | b))
        return bytes(pixels)
    
    def start(self):
        """Start handling the VNC connection."""
        self.running = True
        try:
            # RFB version handshake
            if not self.send_data(self.rfb.RFB_VERSION):
                return
            
            client_version = self.receive_data(12)
            if not client_version or not client_version.startswith(b'RFB '):
                return
            
            # Authentication
            if not self.handle_authentication():
                return
            
            # Initialization
            if not self.handle_initialization():
                return
            
            print(f"VNC client {self.address} connected and initialized")
            
            # Handle client messages
            self.handle_client_messages()
            
        except Exception as e:
            print(f"Error in VNC connection {self.address}: {e}")
        finally:
            self.running = False
            self.socket.close()
            print(f"VNC client {self.address} disconnected")


if __name__ == "__main__":
    # Test the RFB protocol
    rfb = RFBProtocol()
    print("RFB Protocol initialized")
    print(f"Server framebuffer: {rfb.width}x{rfb.height}")
    print(f"Pixel format: {rfb.pixel_format}")