"""
VNC Viewer Package
"""

try:
    from .vnc_viewer import VNCViewer, VNCConnection, VNCWidget
    __all__ = ['VNCViewer', 'VNCConnection', 'VNCWidget']
except ImportError:
    # GUI dependencies not available
    __all__ = []

__version__ = "1.0.0"