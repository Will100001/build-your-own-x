"""
RFB (Remote Framebuffer) Protocol Implementation

This module implements the core VNC/RFB protocol for communication between
VNC server and clients.

Protocol Overview:
1. Handshaking - Version negotiation and authentication
2. Initialization - Server sends display info, client sends pixel format
3. Normal Protocol - Server sends framebuffer updates, client sends events

Reference: RFC 6143 - The Remote Framebuffer Protocol
"""

import struct
import socket
import threading
import hashlib
import logging
from typing import Optional, Tuple, List, Dict, Any
from enum import IntEnum

# Protocol constants
RFB_VERSION_3_3 = b"RFB 003.003\n"
RFB_VERSION_3_7 = b"RFB 003.007\n" 
RFB_VERSION_3_8 = b"RFB 003.008\n"

class SecurityType(IntEnum):
    INVALID = 0
    NONE = 1
    VNC_AUTH = 2

class EncodingType(IntEnum):
    RAW = 0
    COPY_RECT = 1
    RRE = 2
    HEXTILE = 5
    ZRLE = 16
    CURSOR = -239
    DESKTOP_SIZE = -223

class ClientMessage(IntEnum):
    SET_PIXEL_FORMAT = 0
    SET_ENCODINGS = 2
    FRAMEBUFFER_UPDATE_REQUEST = 3
    KEY_EVENT = 4
    POINTER_EVENT = 5
    CLIENT_CUT_TEXT = 6

class ServerMessage(IntEnum):
    FRAMEBUFFER_UPDATE = 0
    SET_COLOUR_MAP_ENTRIES = 1
    BELL = 2
    SERVER_CUT_TEXT = 3

class PixelFormat:
    """Represents pixel format information"""
    def __init__(self, bpp=32, depth=24, big_endian=False, true_colour=True,
                 red_max=255, green_max=255, blue_max=255,
                 red_shift=16, green_shift=8, blue_shift=0):
        self.bits_per_pixel = bpp
        self.depth = depth
        self.big_endian = big_endian
        self.true_colour = true_colour
        self.red_max = red_max
        self.green_max = green_max
        self.blue_max = blue_max
        self.red_shift = red_shift
        self.green_shift = green_shift
        self.blue_shift = blue_shift
        
    def pack(self) -> bytes:
        """Pack pixel format into binary data"""
        return struct.pack("!BBBBHHHBBB3x",
                          self.bits_per_pixel,
                          self.depth,
                          1 if self.big_endian else 0,
                          1 if self.true_colour else 0,
                          self.red_max,
                          self.green_max,
                          self.blue_max,
                          self.red_shift,
                          self.green_shift,
                          self.blue_shift
                          )
    
    @classmethod
    def unpack(cls, data: bytes) -> 'PixelFormat':
        """Unpack pixel format from binary data"""
        fields = struct.unpack("!BBBBHHHBBB3x", data)
        return cls(bpp=fields[0], depth=fields[1], big_endian=bool(fields[2]),
                   true_colour=bool(fields[3]), red_max=fields[4], green_max=fields[5],
                   blue_max=fields[6], red_shift=fields[7], green_shift=fields[8],
                   blue_shift=fields[9])

class RFBProtocol:
    """Base class for RFB protocol handling"""
    
    def __init__(self, socket: socket.socket):
        self.socket = socket
        self.logger = logging.getLogger(self.__class__.__name__)
        self.version = RFB_VERSION_3_8
        self.pixel_format = PixelFormat()
        
    def send_data(self, data: bytes) -> None:
        """Send data to socket"""
        try:
            self.socket.sendall(data)
        except Exception as e:
            self.logger.error(f"Failed to send data: {e}")
            raise
            
    def receive_data(self, length: int) -> bytes:
        """Receive exactly length bytes from socket"""
        data = b""
        while len(data) < length:
            chunk = self.socket.recv(length - len(data))
            if not chunk:
                raise ConnectionError("Connection closed unexpectedly")
            data += chunk
        return data
        
    def send_uint8(self, value: int) -> None:
        """Send single byte"""
        self.send_data(struct.pack("!B", value))
        
    def send_uint16(self, value: int) -> None:
        """Send 16-bit integer"""
        self.send_data(struct.pack("!H", value))
        
    def send_uint32(self, value: int) -> None:
        """Send 32-bit integer"""
        self.send_data(struct.pack("!I", value))
        
    def receive_uint8(self) -> int:
        """Receive single byte"""
        return struct.unpack("!B", self.receive_data(1))[0]
        
    def receive_uint16(self) -> int:
        """Receive 16-bit integer"""
        return struct.unpack("!H", self.receive_data(2))[0]
        
    def receive_uint32(self) -> int:
        """Receive 32-bit integer"""
        return struct.unpack("!I", self.receive_data(4))[0]

class VNCAuth:
    """VNC Authentication implementation"""
    
    @staticmethod
    def encrypt_challenge(challenge: bytes, password: str) -> bytes:
        """Encrypt challenge using simple XOR (for demo purposes)"""
        # Note: In production, this should use proper DES encryption
        # For now, using XOR as a placeholder
        password_bytes = password.encode('utf-8')[:8].ljust(8, b'\0')
        result = bytearray(16)
        for i in range(16):
            result[i] = challenge[i] ^ password_bytes[i % 8]
        return bytes(result)
    
    @staticmethod
    def generate_challenge() -> bytes:
        """Generate random 16-byte challenge"""
        import random
        return bytes([random.randint(0, 255) for _ in range(16)])

class Rectangle:
    """Represents a rectangle update"""
    def __init__(self, x: int, y: int, width: int, height: int, 
                 encoding: EncodingType, data: bytes = b""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.encoding = encoding
        self.data = data
    
    def pack_header(self) -> bytes:
        """Pack rectangle header"""
        return struct.pack("!HHHHI", self.x, self.y, self.width, 
                          self.height, self.encoding)

class FramebufferUpdate:
    """Represents a framebuffer update message"""
    def __init__(self, rectangles: List[Rectangle]):
        self.rectangles = rectangles
    
    def pack(self) -> bytes:
        """Pack framebuffer update message"""
        data = struct.pack("!BxH", ServerMessage.FRAMEBUFFER_UPDATE, 
                          len(self.rectangles))
        for rect in self.rectangles:
            data += rect.pack_header()
            data += rect.data
        return data

# Encoding implementations
class RawEncoding:
    """Raw pixel encoding - no compression"""
    
    @staticmethod
    def encode(pixel_data: bytes, width: int, height: int, 
               pixel_format: PixelFormat) -> bytes:
        """Encode raw pixel data"""
        return pixel_data
    
    @staticmethod
    def decode(data: bytes, width: int, height: int,
               pixel_format: PixelFormat) -> bytes:
        """Decode raw pixel data"""
        return data

class RREEncoding:
    """RRE (Rise-and-Run-length) encoding"""
    
    @staticmethod
    def encode(pixel_data: bytes, width: int, height: int,
               pixel_format: PixelFormat) -> bytes:
        """Encode using RRE compression"""
        # Simplified RRE encoding
        # In practice, this would analyze the image for rectangular regions
        # of the same color and encode them efficiently
        return pixel_data  # Placeholder
    
    @staticmethod
    def decode(data: bytes, width: int, height: int,
               pixel_format: PixelFormat) -> bytes:
        """Decode RRE compressed data"""
        return data  # Placeholder

# Key and button mappings
class KeySym:
    """X11 keysym definitions"""
    BACKSPACE = 0xff08
    TAB = 0xff09
    RETURN = 0xff0d
    ESCAPE = 0xff1b
    DELETE = 0xffff
    SPACE = 0x0020
    
class PointerMask:
    """Mouse button masks"""
    LEFT = 1
    MIDDLE = 2
    RIGHT = 4
    WHEEL_UP = 8
    WHEEL_DOWN = 16

# Utility functions
def rgb888_to_rgb565(r: int, g: int, b: int) -> int:
    """Convert 24-bit RGB to 16-bit RGB565"""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def rgb565_to_rgb888(rgb565: int) -> Tuple[int, int, int]:
    """Convert 16-bit RGB565 to 24-bit RGB"""
    r = (rgb565 >> 11) & 0x1F
    g = (rgb565 >> 5) & 0x3F
    b = rgb565 & 0x1F
    return (r << 3, g << 2, b << 3)