#!/usr/bin/env python3
"""
VNC Server Core Implementation
Main VNC server class that coordinates all components.
"""

import socket
import threading
import time
import logging
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime

from rfb_protocol import VNCConnection, RFBProtocol
from screen_capture import ScreenCaptureManager
from authentication import VNCAuth, SimpleAuth


class VNCServer:
    """Main VNC Server class."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5900, 
                 use_auth: bool = True, max_connections: int = 5):
        self.host = host
        self.port = port
        self.use_auth = use_auth
        self.max_connections = max_connections
        
        # Server state
        self.running = False
        self.server_socket = None
        self.connections: List[VNCConnection] = []
        self.connection_lock = threading.Lock()
        
        # Components
        self.screen_capture = ScreenCaptureManager()
        if use_auth:
            self.auth = VNCAuth()
        else:
            self.auth = SimpleAuth()
        
        # Logging
        self.connection_log: List[Dict[str, Any]] = []
        self.log_lock = threading.Lock()
        
        # Configuration
        self.config = {
            'screen_width': 1024,
            'screen_height': 768,
            'frame_rate': 10,
            'compression': False,
            'encryption': False
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('VNCServer')
    
    def configure(self, **kwargs):
        """Update server configuration."""
        self.config.update(kwargs)
        
        # Update screen capture if dimensions changed
        if 'screen_width' in kwargs or 'screen_height' in kwargs:
            # This would typically trigger a screen resolution change
            self.logger.info(f"Configuration updated: {kwargs}")
    
    def start(self) -> bool:
        """Start the VNC server."""
        if self.running:
            self.logger.warning("Server is already running")
            return False
        
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_connections)
            
            self.running = True
            
            # Start screen capture
            self.screen_capture.start_continuous_capture(fps=self.config['frame_rate'])
            
            # Start accepting connections
            self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.accept_thread.start()
            
            self.logger.info(f"VNC Server started on {self.host}:{self.port}")
            self._log_connection_event("SERVER_START", None, {"port": self.port})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop the VNC server."""
        if not self.running:
            return
        
        self.logger.info("Stopping VNC Server...")
        self.running = False
        
        # Close all connections
        with self.connection_lock:
            for connection in self.connections[:]:
                connection.running = False
                connection.socket.close()
            self.connections.clear()
        
        # Stop screen capture
        self.screen_capture.stop_continuous_capture()
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        
        self._log_connection_event("SERVER_STOP", None, {})
        self.logger.info("VNC Server stopped")
    
    def _accept_connections(self):
        """Accept incoming connections."""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                
                with self.connection_lock:
                    if len(self.connections) >= self.max_connections:
                        self.logger.warning(f"Max connections reached, rejecting {address}")
                        client_socket.close()
                        continue
                
                self.logger.info(f"New connection from {address}")
                self._log_connection_event("CLIENT_CONNECT", address, {})
                
                # Create VNC connection
                auth_callback = self.auth.create_auth_callback() if self.use_auth else None
                connection = VNCConnection(
                    client_socket, 
                    address,
                    auth_callback=auth_callback,
                    screen_capture_callback=self._screen_capture_callback
                )
                
                with self.connection_lock:
                    self.connections.append(connection)
                
                # Start connection handler in new thread
                connection_thread = threading.Thread(
                    target=self._handle_connection,
                    args=(connection,),
                    daemon=True
                )
                connection_thread.start()
                
            except socket.error:
                if self.running:
                    self.logger.error("Error accepting connection")
                break
    
    def _handle_connection(self, connection: VNCConnection):
        """Handle a VNC connection."""
        try:
            connection.start()
        except Exception as e:
            self.logger.error(f"Error handling connection {connection.address}: {e}")
        finally:
            # Remove connection from list
            with self.connection_lock:
                if connection in self.connections:
                    self.connections.remove(connection)
            
            self._log_connection_event("CLIENT_DISCONNECT", connection.address, {})
            self.logger.info(f"Connection {connection.address} closed")
    
    def _screen_capture_callback(self, x: int, y: int, width: int, height: int) -> bytes:
        """Callback for screen capture requests."""
        try:
            return self.screen_capture.get_screen_region(x, y, width, height)
        except Exception as e:
            self.logger.error(f"Screen capture error: {e}")
            # Return black screen as fallback
            return b'\x00' * (width * height * 4)
    
    def _log_connection_event(self, event_type: str, address: Optional[tuple], details: Dict[str, Any]):
        """Log connection events."""
        with self.log_lock:
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'address': f"{address[0]}:{address[1]}" if address else None,
                'details': details
            }
            self.connection_log.append(event)
            
            # Keep only last 1000 events
            if len(self.connection_log) > 1000:
                self.connection_log = self.connection_log[-1000:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status information."""
        with self.connection_lock:
            active_connections = len(self.connections)
            connection_details = [
                {
                    'address': f"{conn.address[0]}:{conn.address[1]}",
                    'authenticated': conn.authenticated,
                    'running': conn.running
                }
                for conn in self.connections
            ]
        
        screen_width, screen_height = self.screen_capture.get_screen_size()
        
        return {
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'active_connections': active_connections,
            'max_connections': self.max_connections,
            'use_auth': self.use_auth,
            'screen_size': (screen_width, screen_height),
            'config': self.config.copy(),
            'connections': connection_details
        }
    
    def get_connection_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent connection log entries."""
        with self.log_lock:
            return self.connection_log[-limit:] if limit > 0 else self.connection_log[:]
    
    def add_user(self, username: str, password: str) -> bool:
        """Add a user account."""
        if hasattr(self.auth, 'add_user'):
            return self.auth.add_user(username, password)
        return False
    
    def remove_user(self, username: str) -> bool:
        """Remove a user account."""
        if hasattr(self.auth, 'remove_user'):
            return self.auth.remove_user(username)
        return False
    
    def list_users(self):
        """List users."""
        if hasattr(self.auth, 'list_users'):
            return self.auth.list_users()
        return {}
    
    def disconnect_client(self, address: str) -> bool:
        """Disconnect a specific client."""
        with self.connection_lock:
            for connection in self.connections[:]:
                if f"{connection.address[0]}:{connection.address[1]}" == address:
                    connection.running = False
                    connection.socket.close()
                    self.connections.remove(connection)
                    self._log_connection_event("CLIENT_FORCED_DISCONNECT", connection.address, {})
                    return True
        return False
    
    def broadcast_message(self, message: str):
        """Send a message to all connected clients (if protocol supports it)."""
        # This would require extending the RFB protocol to support custom messages
        self.logger.info(f"Broadcasting message: {message}")
        with self.connection_lock:
            for connection in self.connections:
                # In a real implementation, this would send a custom message
                pass


def create_test_server() -> VNCServer:
    """Create a test VNC server with default settings."""
    server = VNCServer(
        host='127.0.0.1',
        port=5900,
        use_auth=True,
        max_connections=3
    )
    
    # Add some test users
    server.add_user('admin', 'admin123')
    server.add_user('guest', 'guest')
    
    return server


if __name__ == "__main__":
    # Test the VNC server
    print("Creating VNC Server...")
    
    server = create_test_server()
    
    try:
        print("Starting server...")
        if server.start():
            print(f"VNC Server is running on {server.host}:{server.port}")
            print("Server status:")
            status = server.get_status()
            for key, value in status.items():
                print(f"  {key}: {value}")
            
            print("\nPress Ctrl+C to stop the server")
            
            # Keep server running
            while server.running:
                time.sleep(1)
                
        else:
            print("Failed to start server")
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()
        print("Server stopped")
    except Exception as e:
        print(f"Server error: {e}")
        server.stop()