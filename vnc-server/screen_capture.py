#!/usr/bin/env python3
"""
Screen Capture Module for VNC Server
Provides cross-platform screen capture functionality.
"""

import struct
import subprocess
import tempfile
import os
import time
import threading
from typing import Optional, Tuple, Callable
from abc import ABC, abstractmethod


class ScreenCapture(ABC):
    """Abstract base class for screen capture implementations."""
    
    @abstractmethod
    def capture_screen(self, x: int = 0, y: int = 0, 
                      width: Optional[int] = None, 
                      height: Optional[int] = None) -> Optional[bytes]:
        """Capture a portion of the screen and return raw pixel data."""
        pass
    
    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        """Get the screen dimensions."""
        pass


class SimulatedScreenCapture(ScreenCapture):
    """Simulated screen capture for demonstration purposes."""
    
    def __init__(self, width: int = 1024, height: int = 768):
        self.screen_width = width
        self.screen_height = height
        self.frame_counter = 0
        
    def capture_screen(self, x: int = 0, y: int = 0, 
                      width: Optional[int] = None, 
                      height: Optional[int] = None) -> Optional[bytes]:
        """Generate simulated screen data."""
        if width is None:
            width = self.screen_width - x
        if height is None:
            height = self.screen_height - y
        
        # Ensure coordinates are within bounds
        x = max(0, min(x, self.screen_width))
        y = max(0, min(y, self.screen_height))
        width = min(width, self.screen_width - x)
        height = min(height, self.screen_height - y)
        
        pixels = bytearray()
        self.frame_counter += 1
        
        for row in range(height):
            for col in range(width):
                # Create animated patterns
                actual_x = x + col
                actual_y = y + row
                
                # Create a moving wave pattern
                wave = int(128 + 127 * (
                    (actual_x + self.frame_counter) / 100.0 * 3.14159
                ))
                
                # RGB values based on position and time
                r = (actual_x + self.frame_counter) % 256
                g = (actual_y + self.frame_counter // 2) % 256
                b = wave % 256
                
                # 32-bit BGRA format (common for VNC)
                pixel = struct.pack('<I', (b << 24) | (g << 16) | (r << 8) | 0xFF)
                pixels.extend(pixel)
        
        return bytes(pixels)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Return simulated screen size."""
        return (self.screen_width, self.screen_height)


class LinuxScreenCapture(ScreenCapture):
    """Linux-specific screen capture using X11 tools."""
    
    def __init__(self):
        self.screen_width, self.screen_height = self._get_screen_dimensions()
        
    def _get_screen_dimensions(self) -> Tuple[int, int]:
        """Get screen dimensions using xdpyinfo or fallback."""
        try:
            # Try using xdpyinfo
            result = subprocess.run(['xdpyinfo'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'dimensions:' in line:
                        dims = line.split('dimensions:')[1].split('pixels')[0].strip()
                        width, height = map(int, dims.split('x'))
                        return (width, height)
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        
        # Fallback to default resolution
        return (1024, 768)
    
    def capture_screen(self, x: int = 0, y: int = 0, 
                      width: Optional[int] = None, 
                      height: Optional[int] = None) -> Optional[bytes]:
        """Capture screen using X11 tools."""
        if width is None:
            width = self.screen_width - x
        if height is None:
            height = self.screen_height - y
        
        try:
            # Try using xwd (X Window Dump)
            with tempfile.NamedTemporaryFile(suffix='.xwd', delete=False) as tmp_file:
                cmd = ['xwd', '-root', '-out', tmp_file.name]
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                
                if result.returncode == 0:
                    # Read the XWD file and convert to raw pixels
                    with open(tmp_file.name, 'rb') as f:
                        xwd_data = f.read()
                    
                    # Remove temporary file
                    os.unlink(tmp_file.name)
                    
                    # Parse XWD header and extract pixel data
                    return self._parse_xwd_data(xwd_data, x, y, width, height)
                
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        # Fallback to simulated capture
        fallback = SimulatedScreenCapture(self.screen_width, self.screen_height)
        return fallback.capture_screen(x, y, width, height)
    
    def _parse_xwd_data(self, xwd_data: bytes, x: int, y: int, 
                       width: int, height: int) -> Optional[bytes]:
        """Parse XWD file format and extract pixel data."""
        try:
            # XWD header is 100 bytes
            if len(xwd_data) < 100:
                return None
            
            # Parse header (simplified)
            header = struct.unpack('>25I', xwd_data[:100])
            
            # Extract relevant information
            pixmap_width = header[6]
            pixmap_height = header[7]
            bits_per_pixel = header[13]
            
            # Skip header and color map
            pixel_data_offset = 100
            if header[10] > 0:  # colormap entries
                pixel_data_offset += header[10] * 12
            
            pixel_data = xwd_data[pixel_data_offset:]
            
            # Convert to 32-bit BGRA format for VNC
            return self._convert_pixels(pixel_data, pixmap_width, pixmap_height,
                                      bits_per_pixel, x, y, width, height)
            
        except (struct.error, IndexError):
            return None
    
    def _convert_pixels(self, pixel_data: bytes, src_width: int, src_height: int,
                       bits_per_pixel: int, x: int, y: int, 
                       width: int, height: int) -> bytes:
        """Convert pixel data to VNC format."""
        # Simplified conversion - in practice, this would handle different formats
        output = bytearray()
        bytes_per_pixel = bits_per_pixel // 8
        
        for row in range(height):
            for col in range(width):
                src_x = x + col
                src_y = y + row
                
                if src_x < src_width and src_y < src_height:
                    offset = (src_y * src_width + src_x) * bytes_per_pixel
                    if offset + bytes_per_pixel <= len(pixel_data):
                        # Extract pixel and convert to BGRA
                        if bytes_per_pixel >= 3:
                            pixel = pixel_data[offset:offset + bytes_per_pixel]
                            if len(pixel) >= 3:
                                b, g, r = pixel[0], pixel[1], pixel[2]
                                output.extend(struct.pack('<I', (b << 24) | (g << 16) | (r << 8) | 0xFF))
                                continue
                
                # Fallback to black pixel
                output.extend(struct.pack('<I', 0xFF000000))
        
        return bytes(output)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Return actual screen size."""
        return (self.screen_width, self.screen_height)


class ScreenCaptureManager:
    """Manages screen capture with automatic platform detection."""
    
    def __init__(self):
        self.capture_impl = self._create_capture_implementation()
        self.capture_thread = None
        self.is_capturing = False
        self.last_capture = None
        self.capture_lock = threading.Lock()
        
    def _create_capture_implementation(self) -> ScreenCapture:
        """Create appropriate screen capture implementation for the platform."""
        import platform
        system = platform.system().lower()
        
        if system == 'linux':
            return LinuxScreenCapture()
        else:
            # Fallback to simulated capture for unsupported platforms
            return SimulatedScreenCapture()
    
    def start_continuous_capture(self, fps: int = 10):
        """Start continuous screen capture in a background thread."""
        if self.is_capturing:
            return
        
        self.is_capturing = True
        self.capture_thread = threading.Thread(
            target=self._capture_loop, 
            args=(fps,), 
            daemon=True
        )
        self.capture_thread.start()
    
    def stop_continuous_capture(self):
        """Stop continuous screen capture."""
        self.is_capturing = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
    
    def _capture_loop(self, fps: int):
        """Continuous capture loop."""
        interval = 1.0 / fps
        
        while self.is_capturing:
            start_time = time.time()
            
            try:
                # Capture full screen
                width, height = self.capture_impl.get_screen_size()
                pixels = self.capture_impl.capture_screen(0, 0, width, height)
                
                if pixels:
                    with self.capture_lock:
                        self.last_capture = {
                            'pixels': pixels,
                            'width': width,
                            'height': height,
                            'timestamp': time.time()
                        }
            except Exception as e:
                print(f"Error in capture loop: {e}")
            
            # Maintain frame rate
            elapsed = time.time() - start_time
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def get_screen_region(self, x: int, y: int, width: int, height: int) -> Optional[bytes]:
        """Get a specific region of the screen."""
        with self.capture_lock:
            if self.last_capture:
                # Extract region from last full capture
                return self._extract_region(
                    self.last_capture['pixels'],
                    self.last_capture['width'],
                    self.last_capture['height'],
                    x, y, width, height
                )
        
        # If no cached capture available, capture directly
        return self.capture_impl.capture_screen(x, y, width, height)
    
    def _extract_region(self, full_pixels: bytes, full_width: int, full_height: int,
                       x: int, y: int, width: int, height: int) -> bytes:
        """Extract a region from full screen capture."""
        output = bytearray()
        bytes_per_pixel = 4  # 32-bit BGRA
        
        for row in range(height):
            for col in range(width):
                src_x = x + col
                src_y = y + row
                
                if src_x < full_width and src_y < full_height:
                    offset = (src_y * full_width + src_x) * bytes_per_pixel
                    if offset + bytes_per_pixel <= len(full_pixels):
                        output.extend(full_pixels[offset:offset + bytes_per_pixel])
                        continue
                
                # Fallback to black pixel
                output.extend(struct.pack('<I', 0xFF000000))
        
        return bytes(output)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions."""
        return self.capture_impl.get_screen_size()


if __name__ == "__main__":
    # Test screen capture
    manager = ScreenCaptureManager()
    
    print(f"Screen size: {manager.get_screen_size()}")
    
    # Test capture
    pixels = manager.get_screen_region(0, 0, 100, 100)
    if pixels:
        print(f"Captured {len(pixels)} bytes of pixel data")
        print(f"Expected: {100 * 100 * 4} bytes")
    
    # Test continuous capture
    print("Starting continuous capture for 3 seconds...")
    manager.start_continuous_capture(fps=5)
    time.sleep(3)
    manager.stop_continuous_capture()
    print("Continuous capture stopped")