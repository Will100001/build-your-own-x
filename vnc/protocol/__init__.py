"""
VNC Server and Viewer Protocol Package

This package implements the RFB (Remote Framebuffer) protocol
for VNC communication.
"""

from .rfb import (
    RFBProtocol,
    PixelFormat,
    SecurityType,
    EncodingType,
    ClientMessage,
    ServerMessage,
    Rectangle,
    FramebufferUpdate,
    RawEncoding,
    RREEncoding,
    VNCAuth,
    KeySym,
    PointerMask,
    RFB_VERSION_3_8,
    rgb888_to_rgb565,
    rgb565_to_rgb888
)

__version__ = "1.0.0"
__author__ = "Build Your Own X"

__all__ = [
    'RFBProtocol',
    'PixelFormat',
    'SecurityType',
    'EncodingType',
    'ClientMessage',
    'ServerMessage',
    'Rectangle',
    'FramebufferUpdate',
    'RawEncoding',
    'RREEncoding',
    'VNCAuth',
    'KeySym',
    'PointerMask',
    'RFB_VERSION_3_8',
    'rgb888_to_rgb565',
    'rgb565_to_rgb888'
]