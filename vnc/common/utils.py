"""
Common utilities for VNC Server and Viewer
"""

import logging
import threading
import time
import hashlib
from typing import Optional, Dict, Any, Callable
import os
import json

class Config:
    """Configuration management"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self.config: Dict[str, Any] = {}
        self.load()
        
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        import platform
        if platform.system() == "Windows":
            config_dir = os.path.expandvars("%APPDATA%\\VNC")
        else:
            config_dir = os.path.expanduser("~/.vnc")
        
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")
        
    def load(self) -> None:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load config: {e}")
                self.config = {}
        else:
            self.config = self._get_default_config()
            self.save()
            
    def save(self) -> None:
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
        
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "server": {
                "port": 5900,
                "host": "localhost",
                "password": "",
                "max_clients": 5,
                "update_rate": 30,
                "compression_level": 6
            },
            "viewer": {
                "default_host": "localhost",
                "default_port": 5900,
                "auto_reconnect": True,
                "scaling_mode": "fit_window",
                "color_depth": 24
            },
            "security": {
                "authentication": "vnc_auth",
                "allow_hosts": ["127.0.0.1"],
                "log_connections": True
            },
            "logging": {
                "level": "INFO",
                "file": "",
                "max_size": "10MB",
                "backup_count": 3
            }
        }

class Logger:
    """Enhanced logging utility"""
    
    def __init__(self, name: str, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(name)
        self.setup_logging()
        
    def setup_logging(self) -> None:
        """Setup logging configuration"""
        level = getattr(logging, self.config.get("logging.level", "INFO").upper())
        self.logger.setLevel(level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if configured)
        log_file = self.config.get("logging.file")
        if log_file:
            try:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=self._parse_size(self.config.get("logging.max_size", "10MB")),
                    backupCount=self.config.get("logging.backup_count", 3)
                )
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Failed to setup file logging: {e}")
                
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

class EventManager:
    """Simple event management system"""
    
    def __init__(self):
        self.listeners: Dict[str, list] = {}
        self.lock = threading.Lock()
        
    def subscribe(self, event: str, callback: Callable) -> None:
        """Subscribe to an event"""
        with self.lock:
            if event not in self.listeners:
                self.listeners[event] = []
            self.listeners[event].append(callback)
            
    def unsubscribe(self, event: str, callback: Callable) -> None:
        """Unsubscribe from an event"""
        with self.lock:
            if event in self.listeners and callback in self.listeners[event]:
                self.listeners[event].remove(callback)
                
    def emit(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all subscribers"""
        with self.lock:
            callbacks = self.listeners.get(event, []).copy()
            
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in event callback: {e}")

class PerformanceMonitor:
    """Performance monitoring utility"""
    
    def __init__(self, name: str):
        self.name = name
        self.stats: Dict[str, Any] = {
            'bytes_sent': 0,
            'bytes_received': 0,
            'frames_sent': 0,
            'frames_received': 0,
            'connections': 0,
            'errors': 0,
            'start_time': time.time()
        }
        self.lock = threading.Lock()
        
    def increment(self, counter: str, value: int = 1) -> None:
        """Increment a counter"""
        with self.lock:
            if counter in self.stats:
                self.stats[counter] += value
                
    def set(self, key: str, value: Any) -> None:
        """Set a stat value"""
        with self.lock:
            self.stats[key] = value
            
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        with self.lock:
            stats = self.stats.copy()
            
        # Calculate derived stats
        uptime = time.time() - stats['start_time']
        stats['uptime_seconds'] = uptime
        
        if uptime > 0:
            stats['bytes_per_second'] = (stats['bytes_sent'] + stats['bytes_received']) / uptime
            stats['frames_per_second'] = (stats['frames_sent'] + stats['frames_received']) / uptime
            
        return stats
        
    def log_stats(self, logger: logging.Logger) -> None:
        """Log current statistics"""
        stats = self.get_stats()
        logger.info(f"{self.name} Stats: {stats}")

class NetworkUtils:
    """Network utility functions"""
    
    @staticmethod
    def is_port_available(host: str, port: int) -> bool:
        """Check if a port is available"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return True
        except OSError:
            return False
            
    @staticmethod
    def get_local_ip() -> str:
        """Get local IP address"""
        import socket
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
            
    @staticmethod
    def resolve_hostname(hostname: str) -> Optional[str]:
        """Resolve hostname to IP address"""
        import socket
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            return None

class SecurityUtils:
    """Security-related utilities"""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate a random session ID"""
        import secrets
        return secrets.token_hex(16)
        
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple:
        """Hash a password with salt"""
        import secrets
        if salt is None:
            salt = secrets.token_hex(16)
        else:
            salt = salt.encode() if isinstance(salt, str) else salt
            
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode() if isinstance(salt, str) else salt, 
                                          100000)
        return password_hash.hex(), salt if isinstance(salt, str) else salt.decode()
        
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against hash"""
        computed_hash, _ = SecurityUtils.hash_password(password, salt)
        return computed_hash == password_hash
        
    @staticmethod
    def is_allowed_host(client_ip: str, allowed_hosts: list) -> bool:
        """Check if client IP is in allowed hosts list"""
        import ipaddress
        try:
            client_addr = ipaddress.ip_address(client_ip)
            for allowed in allowed_hosts:
                if '/' in allowed:
                    # CIDR notation
                    if client_addr in ipaddress.ip_network(allowed, strict=False):
                        return True
                else:
                    # Single IP
                    if client_addr == ipaddress.ip_address(allowed):
                        return True
            return False
        except ValueError:
            return False

class ImageUtils:
    """Image processing utilities"""
    
    @staticmethod
    def detect_changes(img1: bytes, img2: bytes, width: int, height: int, 
                      block_size: int = 32) -> list:
        """Detect changed regions between two images"""
        changes = []
        bytes_per_pixel = len(img1) // (width * height)
        
        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                # Calculate block boundaries
                block_width = min(block_size, width - x)
                block_height = min(block_size, height - y)
                
                # Extract block data
                block1 = ImageUtils._extract_block(img1, x, y, block_width, block_height, 
                                                 width, bytes_per_pixel)
                block2 = ImageUtils._extract_block(img2, x, y, block_width, block_height, 
                                                 width, bytes_per_pixel)
                
                # Compare blocks
                if block1 != block2:
                    changes.append((x, y, block_width, block_height))
                    
        return changes
        
    @staticmethod
    def _extract_block(img: bytes, x: int, y: int, width: int, height: int, 
                      img_width: int, bytes_per_pixel: int) -> bytes:
        """Extract a rectangular block from an image"""
        block = bytearray()
        for row in range(y, y + height):
            start = (row * img_width + x) * bytes_per_pixel
            end = start + width * bytes_per_pixel
            block.extend(img[start:end])
        return bytes(block)
        
    @staticmethod
    def compress_image(img_data: bytes, width: int, height: int, 
                      quality: int = 75) -> bytes:
        """Compress image data using JPEG"""
        try:
            from PIL import Image
            import io
            
            # Convert bytes to PIL Image
            image = Image.frombytes('RGB', (width, height), img_data)
            
            # Compress as JPEG
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality)
            return buffer.getvalue()
            
        except ImportError:
            # Fallback: return original data
            return img_data