"""
Test suite for VNC Server and Viewer

This module contains comprehensive tests for the VNC implementation,
including protocol tests, server tests, and integration tests.
"""

import unittest
import socket
import threading
import time
import struct
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol.rfb import (
    RFBProtocol, PixelFormat, SecurityType, EncodingType,
    ClientMessage, ServerMessage, Rectangle, FramebufferUpdate,
    RawEncoding, VNCAuth, KeySym, PointerMask,
    RFB_VERSION_3_8, rgb888_to_rgb565, rgb565_to_rgb888
)

from server.vnc_server import VNCServer, VNCClient
# Note: viewer import may fail without GUI dependencies, that's OK for testing

class TestPixelFormat(unittest.TestCase):
    """Test PixelFormat class"""
    
    def test_default_pixel_format(self):
        """Test default pixel format creation"""
        pf = PixelFormat()
        self.assertEqual(pf.bits_per_pixel, 32)
        self.assertEqual(pf.depth, 24)
        self.assertFalse(pf.big_endian)
        self.assertTrue(pf.true_colour)
        
    def test_pixel_format_pack_unpack(self):
        """Test pixel format serialization"""
        pf1 = PixelFormat(bpp=16, depth=16, red_max=31, green_max=63, blue_max=31)
        packed = pf1.pack()
        pf2 = PixelFormat.unpack(packed)
        
        self.assertEqual(pf1.bits_per_pixel, pf2.bits_per_pixel)
        self.assertEqual(pf1.depth, pf2.depth)
        self.assertEqual(pf1.red_max, pf2.red_max)
        self.assertEqual(pf1.green_max, pf2.green_max)
        self.assertEqual(pf1.blue_max, pf2.blue_max)

class TestRFBProtocol(unittest.TestCase):
    """Test RFB protocol implementation"""
    
    def setUp(self):
        """Set up test socket and protocol"""
        self.mock_socket = Mock()
        self.protocol = RFBProtocol(self.mock_socket)
        
    def test_send_data(self):
        """Test data sending"""
        test_data = b"hello world"
        self.protocol.send_data(test_data)
        self.mock_socket.sendall.assert_called_once_with(test_data)
        
    def test_send_integers(self):
        """Test integer sending methods"""
        # Test uint8
        self.protocol.send_uint8(255)
        self.mock_socket.sendall.assert_called_with(struct.pack("!B", 255))
        
        # Test uint16
        self.mock_socket.reset_mock()
        self.protocol.send_uint16(65535)
        self.mock_socket.sendall.assert_called_with(struct.pack("!H", 65535))
        
        # Test uint32
        self.mock_socket.reset_mock()
        self.protocol.send_uint32(4294967295)
        self.mock_socket.sendall.assert_called_with(struct.pack("!I", 4294967295))
        
    def test_receive_data(self):
        """Test data receiving"""
        test_data = b"hello world"
        self.mock_socket.recv.return_value = test_data
        
        result = self.protocol.receive_data(len(test_data))
        self.assertEqual(result, test_data)
        
    def test_receive_partial_data(self):
        """Test receiving data in chunks"""
        test_data = b"hello world"
        # Simulate partial receives
        self.mock_socket.recv.side_effect = [b"hello", b" world"]
        
        result = self.protocol.receive_data(len(test_data))
        self.assertEqual(result, test_data)

class TestVNCAuth(unittest.TestCase):
    """Test VNC authentication"""
    
    def test_generate_challenge(self):
        """Test challenge generation"""
        challenge = VNCAuth.generate_challenge()
        self.assertEqual(len(challenge), 16)
        self.assertIsInstance(challenge, bytes)
        
    def test_encrypt_challenge(self):
        """Test challenge encryption"""
        challenge = b"1234567890123456"
        password = "test"
        encrypted = VNCAuth.encrypt_challenge(challenge, password)
        
        self.assertEqual(len(encrypted), 16)
        self.assertIsInstance(encrypted, bytes)
        self.assertNotEqual(encrypted, challenge)

class TestRectangle(unittest.TestCase):
    """Test Rectangle class"""
    
    def test_rectangle_creation(self):
        """Test rectangle creation"""
        rect = Rectangle(10, 20, 100, 200, EncodingType.RAW, b"test_data")
        
        self.assertEqual(rect.x, 10)
        self.assertEqual(rect.y, 20)
        self.assertEqual(rect.width, 100)
        self.assertEqual(rect.height, 200)
        self.assertEqual(rect.encoding, EncodingType.RAW)
        self.assertEqual(rect.data, b"test_data")
        
    def test_rectangle_pack_header(self):
        """Test rectangle header packing"""
        rect = Rectangle(10, 20, 100, 200, EncodingType.RAW)
        header = rect.pack_header()
        
        expected = struct.pack("!HHHHI", 10, 20, 100, 200, EncodingType.RAW)
        self.assertEqual(header, expected)

class TestFramebufferUpdate(unittest.TestCase):
    """Test FramebufferUpdate class"""
    
    def test_framebuffer_update_pack(self):
        """Test framebuffer update packing"""
        rect1 = Rectangle(0, 0, 100, 100, EncodingType.RAW, b"data1")
        rect2 = Rectangle(100, 100, 200, 200, EncodingType.RAW, b"data2")
        
        update = FramebufferUpdate([rect1, rect2])
        packed = update.pack()
        
        # Should start with message type and rectangle count
        expected_start = struct.pack("!BxH", ServerMessage.FRAMEBUFFER_UPDATE, 2)
        self.assertTrue(packed.startswith(expected_start))

class TestColorConversion(unittest.TestCase):
    """Test color conversion functions"""
    
    def test_rgb888_to_rgb565(self):
        """Test 24-bit to 16-bit color conversion"""
        # Test pure colors
        self.assertEqual(rgb888_to_rgb565(255, 0, 0), 0xF800)  # Red
        self.assertEqual(rgb888_to_rgb565(0, 255, 0), 0x07E0)  # Green
        self.assertEqual(rgb888_to_rgb565(0, 0, 255), 0x001F)  # Blue
        self.assertEqual(rgb888_to_rgb565(255, 255, 255), 0xFFFF)  # White
        
    def test_rgb565_to_rgb888(self):
        """Test 16-bit to 24-bit color conversion"""
        # Test pure colors (note: some precision loss expected)
        r, g, b = rgb565_to_rgb888(0xF800)  # Red
        self.assertGreater(r, 240)
        self.assertEqual(g, 0)
        self.assertEqual(b, 0)

class TestEncodings(unittest.TestCase):
    """Test encoding implementations"""
    
    def test_raw_encoding(self):
        """Test raw encoding"""
        test_data = b"test pixel data"
        width, height = 10, 10
        pf = PixelFormat()
        
        encoded = RawEncoding.encode(test_data, width, height, pf)
        decoded = RawEncoding.decode(encoded, width, height, pf)
        
        self.assertEqual(test_data, encoded)
        self.assertEqual(test_data, decoded)

class MockSocket:
    """Mock socket for testing"""
    
    def __init__(self):
        self.sent_data = b""
        self.receive_data = b""
        self.receive_pos = 0
        self.closed = False
        
    def sendall(self, data):
        if self.closed:
            raise ConnectionError("Socket is closed")
        self.sent_data += data
        
    def recv(self, size):
        if self.closed:
            raise ConnectionError("Socket is closed")
        if self.receive_pos >= len(self.receive_data):
            return b""
        
        end_pos = min(self.receive_pos + size, len(self.receive_data))
        data = self.receive_data[self.receive_pos:end_pos]
        self.receive_pos = end_pos
        return data
        
    def close(self):
        self.closed = True
        
    def set_receive_data(self, data):
        self.receive_data = data
        self.receive_pos = 0

class TestVNCClient(unittest.TestCase):
    """Test VNC client handling"""
    
    def setUp(self):
        """Set up test client"""
        self.mock_socket = MockSocket()
        self.client = VNCClient(self.mock_socket, ("127.0.0.1", 12345))
        
    def test_client_creation(self):
        """Test client creation"""
        self.assertEqual(self.client.address, ("127.0.0.1", 12345))
        self.assertFalse(self.client.authenticated)
        self.assertTrue(self.client.active)
        
    def test_send_server_init(self):
        """Test server initialization message"""
        self.client.send_server_init(1024, 768, "Test Server")
        
        sent = self.mock_socket.sent_data
        # Should contain width, height, pixel format, and name
        self.assertGreater(len(sent), 20)  # At least basic data
        
        # Check width and height
        width, height = struct.unpack("!HH", sent[:4])
        self.assertEqual(width, 1024)
        self.assertEqual(height, 768)

class TestVNCServer(unittest.TestCase):
    """Test VNC server functionality"""
    
    def setUp(self):
        """Set up test server"""
        self.server = VNCServer("localhost", 0)  # Port 0 for random port
        
    def tearDown(self):
        """Clean up server"""
        if self.server.running:
            self.server.stop()
            
    def test_server_creation(self):
        """Test server creation"""
        server = VNCServer("localhost", 5900, "test_password")
        self.assertEqual(server.host, "localhost")
        self.assertEqual(server.port, 5900)
        self.assertEqual(server.password, "test_password")
        
    def test_server_start_stop(self):
        """Test server start and stop"""
        # Start server in thread
        server_thread = threading.Thread(target=self.server.start)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for server to start
        time.sleep(0.1)
        self.assertTrue(self.server.running)
        
        # Stop server
        self.server.stop()
        time.sleep(0.1)
        self.assertFalse(self.server.running)

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.server_port = 15900  # Use non-standard port for testing
        
    def test_basic_connection(self):
        """Test basic client-server connection"""
        # Start server
        server = VNCServer("localhost", self.server_port)
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for server to start
        time.sleep(0.2)
        
        try:
            # Test basic connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("localhost", self.server_port))
            
            # Receive protocol version
            version = client_socket.recv(12)
            self.assertEqual(version, RFB_VERSION_3_8)
            
            # Send client version
            client_socket.send(RFB_VERSION_3_8)
            
            # Basic handshake successful
            client_socket.close()
            
        finally:
            server.stop()

class TestProtocolMessages(unittest.TestCase):
    """Test protocol message handling"""
    
    def test_client_messages(self):
        """Test client message constants"""
        self.assertEqual(ClientMessage.SET_PIXEL_FORMAT, 0)
        self.assertEqual(ClientMessage.SET_ENCODINGS, 2)
        self.assertEqual(ClientMessage.FRAMEBUFFER_UPDATE_REQUEST, 3)
        self.assertEqual(ClientMessage.KEY_EVENT, 4)
        self.assertEqual(ClientMessage.POINTER_EVENT, 5)
        self.assertEqual(ClientMessage.CLIENT_CUT_TEXT, 6)
        
    def test_server_messages(self):
        """Test server message constants"""
        self.assertEqual(ServerMessage.FRAMEBUFFER_UPDATE, 0)
        self.assertEqual(ServerMessage.SET_COLOUR_MAP_ENTRIES, 1)
        self.assertEqual(ServerMessage.BELL, 2)
        self.assertEqual(ServerMessage.SERVER_CUT_TEXT, 3)
        
    def test_encoding_types(self):
        """Test encoding type constants"""
        self.assertEqual(EncodingType.RAW, 0)
        self.assertEqual(EncodingType.COPY_RECT, 1)
        self.assertEqual(EncodingType.RRE, 2)
        self.assertEqual(EncodingType.HEXTILE, 5)

class TestSecurityTypes(unittest.TestCase):
    """Test security implementations"""
    
    def test_security_constants(self):
        """Test security type constants"""
        self.assertEqual(SecurityType.INVALID, 0)
        self.assertEqual(SecurityType.NONE, 1)
        self.assertEqual(SecurityType.VNC_AUTH, 2)

if __name__ == "__main__":
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)