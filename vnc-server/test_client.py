#!/usr/bin/env python3
"""
Simple VNC Client for Testing
A basic VNC client to test the VNC server implementation.
"""

import socket
import struct
import time
from typing import Optional


class SimpleVNCClient:
    """Simple VNC client for testing the server."""
    
    def __init__(self, host: str = 'localhost', port: int = 5900):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to VNC server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to VNC server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from VNC server."""
        if self.socket:
            self.socket.close()
            self.connected = False
            print("Disconnected from VNC server")
    
    def send_data(self, data: bytes) -> bool:
        """Send data to server."""
        try:
            self.socket.sendall(data)
            return True
        except Exception as e:
            print(f"Send error: {e}")
            return False
    
    def receive_data(self, length: int) -> Optional[bytes]:
        """Receive data from server."""
        try:
            data = b''
            while len(data) < length:
                chunk = self.socket.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            return data
        except Exception as e:
            print(f"Receive error: {e}")
            return None
    
    def handshake(self) -> bool:
        """Perform VNC handshake."""
        # Receive server version
        server_version = self.receive_data(12)
        if not server_version:
            print("Failed to receive server version")
            return False
        
        print(f"Server version: {server_version.decode().strip()}")
        
        # Send client version
        client_version = b"RFB 003.008\n"
        if not self.send_data(client_version):
            print("Failed to send client version")
            return False
        
        print(f"Sent client version: {client_version.decode().strip()}")
        return True
    
    def handle_security(self) -> bool:
        """Handle security negotiation."""
        # Receive security types
        security_data = self.receive_data(2)
        if not security_data:
            print("Failed to receive security types")
            return False
        
        num_types, first_type = struct.unpack('!BB', security_data)
        print(f"Security types: {num_types}, first type: {first_type}")
        
        # Choose security type (1 = None, 2 = VNC Auth)
        choice = struct.pack('!B', first_type)
        if not self.send_data(choice):
            print("Failed to send security choice")
            return False
        
        print(f"Selected security type: {first_type}")
        
        if first_type == 1:  # No authentication
            # Receive security result
            result_data = self.receive_data(4)
            if not result_data:
                print("Failed to receive security result")
                return False
            
            result = struct.unpack('!I', result_data)[0]
            if result == 0:
                print("Security handshake successful")
                return True
            else:
                print(f"Security handshake failed: {result}")
                return False
        
        elif first_type == 2:  # VNC Authentication
            # Receive challenge
            challenge = self.receive_data(16)
            if not challenge:
                print("Failed to receive challenge")
                return False
            
            print("Received VNC authentication challenge")
            
            # Create response (simplified)
            password = b'password'
            response = bytearray()
            for i in range(16):
                response.append(challenge[i] ^ password[i % len(password)])
            
            if not self.send_data(bytes(response)):
                print("Failed to send authentication response")
                return False
            
            # Receive result
            result_data = self.receive_data(4)
            if not result_data:
                print("Failed to receive authentication result")
                return False
            
            result = struct.unpack('!I', result_data)[0]
            if result == 0:
                print("Authentication successful")
                return True
            else:
                print(f"Authentication failed: {result}")
                return False
        
        return False
    
    def client_init(self) -> bool:
        """Send client initialization."""
        # Send ClientInit (shared flag = 1)
        client_init = struct.pack('!B', 1)
        if not self.send_data(client_init):
            print("Failed to send client init")
            return False
        
        # Receive ServerInit
        server_init_header = self.receive_data(20)  # 2+2+16 bytes
        if not server_init_header:
            print("Failed to receive server init header")
            return False
        
        width, height = struct.unpack('!HH', server_init_header[:4])
        print(f"Server framebuffer: {width}x{height}")
        
        # Receive name length and name
        name_length_data = self.receive_data(4)
        if not name_length_data:
            print("Failed to receive name length")
            return False
        
        name_length = struct.unpack('!I', name_length_data)[0]
        if name_length > 0:
            name_data = self.receive_data(name_length)
            if name_data:
                name = name_data.decode('utf-8', errors='ignore')
                print(f"Server name: {name}")
        
        print("Client initialization successful")
        return True
    
    def request_framebuffer_update(self) -> bool:
        """Request a framebuffer update."""
        # FramebufferUpdateRequest: type(1) + incremental(1) + x(2) + y(2) + width(2) + height(2)
        message = struct.pack('!BBHHHH', 3, 0, 0, 0, 100, 100)  # Request 100x100 area
        if not self.send_data(message):
            print("Failed to send framebuffer update request")
            return False
        
        print("Requested framebuffer update")
        return True
    
    def receive_framebuffer_update(self) -> bool:
        """Receive and process framebuffer update."""
        # Receive message header
        header = self.receive_data(4)
        if not header:
            print("Failed to receive framebuffer update header")
            return False
        
        msg_type, padding, num_rects = struct.unpack('!BxH', header)
        if msg_type != 0:
            print(f"Unexpected message type: {msg_type}")
            return False
        
        print(f"Received framebuffer update with {num_rects} rectangles")
        
        # Process rectangles
        for i in range(num_rects):
            rect_header = self.receive_data(12)
            if not rect_header:
                print(f"Failed to receive rectangle {i} header")
                return False
            
            x, y, width, height, encoding = struct.unpack('!HHHHI', rect_header)
            print(f"Rectangle {i}: {x},{y} {width}x{height} encoding={encoding}")
            
            # Calculate pixel data size (assuming 32-bit pixels)
            pixel_count = width * height
            pixel_data_size = pixel_count * 4
            
            # Receive pixel data
            pixel_data = self.receive_data(pixel_data_size)
            if not pixel_data:
                print(f"Failed to receive pixel data for rectangle {i}")
                return False
            
            print(f"Received {len(pixel_data)} bytes of pixel data")
        
        return True
    
    def test_connection(self) -> bool:
        """Test the complete VNC connection process."""
        print("Starting VNC client test...")
        
        if not self.connect():
            return False
        
        try:
            if not self.handshake():
                print("Handshake failed")
                return False
            
            if not self.handle_security():
                print("Security negotiation failed")
                return False
            
            if not self.client_init():
                print("Client initialization failed")
                return False
            
            # Request and receive a framebuffer update
            if not self.request_framebuffer_update():
                print("Framebuffer update request failed")
                return False
            
            # Give server time to respond
            time.sleep(0.5)
            
            if not self.receive_framebuffer_update():
                print("Framebuffer update receive failed")
                return False
            
            print("✅ VNC client test completed successfully!")
            return True
            
        except Exception as e:
            print(f"Test failed with exception: {e}")
            return False
        finally:
            self.disconnect()


def main():
    """Test the VNC client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple VNC Client for Testing")
    parser.add_argument('--host', default='localhost', help='VNC server host')
    parser.add_argument('--port', type=int, default=5900, help='VNC server port')
    
    args = parser.parse_args()
    
    client = SimpleVNCClient(args.host, args.port)
    success = client.test_connection()
    
    if success:
        print("VNC server test passed!")
        return 0
    else:
        print("VNC server test failed!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())