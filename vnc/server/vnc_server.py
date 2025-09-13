"""
VNC Server Implementation

This module implements a VNC server that can share the desktop screen
with multiple VNC clients simultaneously.
"""

import socket
import threading
import time
import struct
import logging
import argparse
from typing import List, Optional, Tuple, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol.rfb import (
    RFBProtocol, PixelFormat, SecurityType, EncodingType,
    ClientMessage, ServerMessage, Rectangle, FramebufferUpdate,
    RawEncoding, VNCAuth, KeySym, PointerMask,
    RFB_VERSION_3_8
)

# Screen capture imports - platform specific
try:
    from PIL import ImageGrab, Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not available, screen capture disabled")

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    print("Warning: pyautogui not available, input handling disabled")

class VNCClient:
    """Represents a connected VNC client"""
    
    def __init__(self, socket: socket.socket, address: Tuple[str, int]):
        self.socket = socket
        self.address = address
        self.protocol = RFBProtocol(socket)
        self.authenticated = False
        self.pixel_format = PixelFormat()
        self.encodings: List[EncodingType] = [EncodingType.RAW]
        self.last_update_time = 0
        self.incremental_update = False
        self.update_requested = False
        self.active = True
        
    def send_server_init(self, width: int, height: int, name: str) -> None:
        """Send server initialization message"""
        data = struct.pack("!HH", width, height)
        data += self.pixel_format.pack()
        name_bytes = name.encode('utf-8')
        data += struct.pack("!I", len(name_bytes))
        data += name_bytes
        self.protocol.send_data(data)
        
    def handle_set_pixel_format(self) -> None:
        """Handle SetPixelFormat client message"""
        # Skip padding bytes
        self.protocol.receive_data(3)
        # Receive pixel format (16 bytes)
        pf_data = self.protocol.receive_data(16)
        self.pixel_format = PixelFormat.unpack(pf_data)
        logging.info(f"Client {self.address} set pixel format: {self.pixel_format.bits_per_pixel}bpp")
        
    def handle_set_encodings(self) -> None:
        """Handle SetEncodings client message"""
        # Skip padding byte
        self.protocol.receive_data(1)
        # Get number of encodings
        num_encodings = self.protocol.receive_uint16()
        # Receive encodings
        self.encodings = []
        for _ in range(num_encodings):
            encoding = self.protocol.receive_uint32()
            if encoding in [e.value for e in EncodingType]:
                self.encodings.append(EncodingType(encoding))
        logging.info(f"Client {self.address} set encodings: {self.encodings}")
        
    def handle_framebuffer_update_request(self) -> None:
        """Handle FramebufferUpdateRequest client message"""
        incremental = self.protocol.receive_uint8()
        x = self.protocol.receive_uint16()
        y = self.protocol.receive_uint16()
        width = self.protocol.receive_uint16()
        height = self.protocol.receive_uint16()
        
        self.incremental_update = bool(incremental)
        self.update_requested = True
        logging.debug(f"Client {self.address} requested update: incremental={incremental}, region=({x},{y},{width},{height})")
        
    def handle_key_event(self) -> None:
        """Handle KeyEvent client message"""
        down_flag = self.protocol.receive_uint8()
        # Skip padding
        self.protocol.receive_data(2)
        key = self.protocol.receive_uint32()
        
        if HAS_PYAUTOGUI:
            try:
                # Convert keysym to pyautogui key
                key_name = self._keysym_to_key(key)
                if key_name:
                    if down_flag:
                        pyautogui.keyDown(key_name)
                    else:
                        pyautogui.keyUp(key_name)
            except Exception as e:
                logging.warning(f"Failed to handle key event: {e}")
                
    def handle_pointer_event(self) -> None:
        """Handle PointerEvent client message"""
        button_mask = self.protocol.receive_uint8()
        x = self.protocol.receive_uint16()
        y = self.protocol.receive_uint16()
        
        if HAS_PYAUTOGUI:
            try:
                # Move mouse
                pyautogui.moveTo(x, y)
                
                # Handle button clicks
                if button_mask & PointerMask.LEFT:
                    pyautogui.mouseDown(button='left')
                else:
                    pyautogui.mouseUp(button='left')
                    
                if button_mask & PointerMask.MIDDLE:
                    pyautogui.mouseDown(button='middle')
                else:
                    pyautogui.mouseUp(button='middle')
                    
                if button_mask & PointerMask.RIGHT:
                    pyautogui.mouseDown(button='right')
                else:
                    pyautogui.mouseUp(button='right')
                    
                # Handle scroll wheel
                if button_mask & PointerMask.WHEEL_UP:
                    pyautogui.scroll(1)
                elif button_mask & PointerMask.WHEEL_DOWN:
                    pyautogui.scroll(-1)
                    
            except Exception as e:
                logging.warning(f"Failed to handle pointer event: {e}")
                
    def handle_client_cut_text(self) -> None:
        """Handle ClientCutText client message"""
        # Skip padding
        self.protocol.receive_data(3)
        length = self.protocol.receive_uint32()
        text = self.protocol.receive_data(length).decode('utf-8', errors='ignore')
        logging.info(f"Client {self.address} sent clipboard text: {text[:50]}...")
        
    def _keysym_to_key(self, keysym: int) -> Optional[str]:
        """Convert X11 keysym to pyautogui key name"""
        keysym_map = {
            KeySym.BACKSPACE: 'backspace',
            KeySym.TAB: 'tab',
            KeySym.RETURN: 'enter',
            KeySym.ESCAPE: 'esc',
            KeySym.DELETE: 'delete',
            KeySym.SPACE: 'space',
        }
        
        if keysym in keysym_map:
            return keysym_map[keysym]
        elif 0x20 <= keysym <= 0x7E:  # Printable ASCII
            return chr(keysym)
        elif 0xFFBE <= keysym <= 0xFFCD:  # Function keys F1-F12
            return f'f{keysym - 0xFFBD}'
        else:
            return None

class VNCServer:
    """VNC Server implementation"""
    
    def __init__(self, host: str = "localhost", port: int = 5900, password: str = ""):
        self.host = host
        self.port = port
        self.password = password
        self.server_socket: Optional[socket.socket] = None
        self.clients: List[VNCClient] = []
        self.running = False
        self.screen_width = 1024
        self.screen_height = 768
        self.framebuffer = None
        self.last_screen_hash = None
        
        # Configure logging
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Get actual screen dimensions if available
        if HAS_PIL:
            try:
                screen = ImageGrab.grab()
                self.screen_width, self.screen_height = screen.size
            except:
                pass
                
        self.logger.info(f"VNC Server initialized for {self.screen_width}x{self.screen_height} display")
        
    def start(self) -> None:
        """Start the VNC server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            self.logger.info(f"VNC Server listening on {self.host}:{self.port}")
            if self.password:
                self.logger.info("Authentication enabled")
            else:
                self.logger.info("No authentication - server is open!")
                
            # Start framebuffer update thread
            update_thread = threading.Thread(target=self._framebuffer_update_loop)
            update_thread.daemon = True
            update_thread.start()
            
            # Accept client connections
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    self.logger.info(f"New connection from {address}")
                    
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")
                        
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
        finally:
            self.stop()
            
    def stop(self) -> None:
        """Stop the VNC server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for client in self.clients[:]:
            self._disconnect_client(client)
        self.logger.info("VNC Server stopped")
        
    def _handle_client(self, client_socket: socket.socket, address: Tuple[str, int]) -> None:
        """Handle a new client connection"""
        client = VNCClient(client_socket, address)
        
        try:
            # Protocol handshake
            if not self._do_handshake(client):
                return
                
            # Authentication
            if not self._do_authentication(client):
                return
                
            # Send ServerInit
            client.send_server_init(self.screen_width, self.screen_height, "VNC Server")
            
            # Add to client list
            self.clients.append(client)
            self.logger.info(f"Client {address} connected successfully")
            
            # Handle client messages
            while client.active and self.running:
                try:
                    message_type = client.protocol.receive_uint8()
                    
                    if message_type == ClientMessage.SET_PIXEL_FORMAT:
                        client.handle_set_pixel_format()
                    elif message_type == ClientMessage.SET_ENCODINGS:
                        client.handle_set_encodings()
                    elif message_type == ClientMessage.FRAMEBUFFER_UPDATE_REQUEST:
                        client.handle_framebuffer_update_request()
                    elif message_type == ClientMessage.KEY_EVENT:
                        client.handle_key_event()
                    elif message_type == ClientMessage.POINTER_EVENT:
                        client.handle_pointer_event()
                    elif message_type == ClientMessage.CLIENT_CUT_TEXT:
                        client.handle_client_cut_text()
                    else:
                        self.logger.warning(f"Unknown message type: {message_type}")
                        
                except Exception as e:
                    self.logger.error(f"Error handling client message: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error handling client {address}: {e}")
        finally:
            self._disconnect_client(client)
            
    def _do_handshake(self, client: VNCClient) -> bool:
        """Perform RFB protocol handshake"""
        try:
            # Send protocol version
            client.protocol.send_data(RFB_VERSION_3_8)
            
            # Receive client version
            client_version = client.protocol.receive_data(12)
            self.logger.info(f"Client version: {client_version}")
            
            return True
        except Exception as e:
            self.logger.error(f"Handshake failed: {e}")
            return False
            
    def _do_authentication(self, client: VNCClient) -> bool:
        """Perform authentication"""
        try:
            if self.password:
                # Send VNC authentication
                client.protocol.send_uint8(1)  # Number of security types
                client.protocol.send_uint8(SecurityType.VNC_AUTH)
                
                # Receive chosen security type
                chosen_type = client.protocol.receive_uint8()
                if chosen_type != SecurityType.VNC_AUTH:
                    client.protocol.send_uint32(1)  # Failed
                    return False
                    
                # Send challenge
                challenge = VNCAuth.generate_challenge()
                client.protocol.send_data(challenge)
                
                # Receive response
                response = client.protocol.receive_data(16)
                
                # Verify response (simplified)
                expected = VNCAuth.encrypt_challenge(challenge, self.password)
                if response != expected:
                    client.protocol.send_uint32(1)  # Failed
                    return False
                    
                # Send OK
                client.protocol.send_uint32(0)  # OK
            else:
                # No authentication
                client.protocol.send_uint8(1)  # Number of security types
                client.protocol.send_uint8(SecurityType.NONE)
                
                # Receive chosen security type
                chosen_type = client.protocol.receive_uint8()
                if chosen_type != SecurityType.NONE:
                    return False
                    
            client.authenticated = True
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
            
    def _disconnect_client(self, client: VNCClient) -> None:
        """Disconnect a client"""
        try:
            client.active = False
            client.socket.close()
            if client in self.clients:
                self.clients.remove(client)
            self.logger.info(f"Client {client.address} disconnected")
        except:
            pass
            
    def _capture_screen(self) -> Optional[bytes]:
        """Capture current screen"""
        if not HAS_PIL:
            return None
            
        try:
            screen = ImageGrab.grab()
            # Convert to RGB if necessary
            if screen.mode != 'RGB':
                screen = screen.convert('RGB')
            return screen.tobytes()
        except Exception as e:
            self.logger.error(f"Screen capture failed: {e}")
            return None
            
    def _framebuffer_update_loop(self) -> None:
        """Main framebuffer update loop"""
        while self.running:
            try:
                # Check if any client needs updates
                clients_needing_update = [c for c in self.clients if c.update_requested]
                
                if clients_needing_update:
                    # Capture screen
                    screen_data = self._capture_screen()
                    if screen_data:
                        # Calculate screen hash for change detection
                        import hashlib
                        screen_hash = hashlib.md5(screen_data).hexdigest()
                        
                        for client in clients_needing_update:
                            try:
                                # Only send update if screen changed or not incremental
                                if not client.incremental_update or screen_hash != self.last_screen_hash:
                                    self._send_framebuffer_update(client, screen_data)
                                    
                                client.update_requested = False
                            except Exception as e:
                                self.logger.error(f"Failed to send update to {client.address}: {e}")
                                self._disconnect_client(client)
                                
                        self.last_screen_hash = screen_hash
                        
                time.sleep(0.1)  # 10 FPS max
                
            except Exception as e:
                self.logger.error(f"Error in framebuffer update loop: {e}")
                time.sleep(1)
                
    def _send_framebuffer_update(self, client: VNCClient, screen_data: bytes) -> None:
        """Send framebuffer update to client"""
        # Use raw encoding for simplicity
        rect = Rectangle(0, 0, self.screen_width, self.screen_height, 
                        EncodingType.RAW, screen_data)
        update = FramebufferUpdate([rect])
        client.protocol.send_data(update.pack())

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='VNC Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5900, help='Port to listen on')
    parser.add_argument('--password', default='', help='VNC password')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    server = VNCServer(args.host, args.port, args.password)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()

if __name__ == "__main__":
    main()