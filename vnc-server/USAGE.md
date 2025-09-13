# Enhanced VNC Server Usage Guide

## Overview

This repository contains a complete Python-based VNC server implementation with advanced features including screen recording and LAN monitoring. The implementation provides both full-featured and simplified versions to accommodate different environments and dependencies.

## File Structure

```
vnc-server/
├── vnc_server.py          # Full-featured implementation (requires external libraries)
├── simple_vnc_server.py   # GUI version using tkinter
├── core_vnc_server.py     # Core implementation (standard library only)
├── demo.py               # Interactive demonstration script
├── test_vnc_server.py    # Comprehensive test suite
├── requirements.txt      # Python dependencies
└── README.md            # This documentation
```

## Quick Start

### Option 1: Core Implementation (Recommended for testing)

Uses only Python standard library - works immediately:

```bash
# Run interactive demo
python core_vnc_server.py

# Run tests
python core_vnc_server.py --test

# Get help
python core_vnc_server.py --help
```

### Option 2: Full Implementation (Advanced features)

Requires external libraries but provides full functionality:

```bash
# Install dependencies
pip install -r requirements.txt

# Run full GUI application
python vnc_server.py

# Run command-line demo
python demo.py
```

### Option 3: Simple GUI Implementation

Uses tkinter for basic GUI (if available):

```bash
python simple_vnc_server.py
```

## Features

### 🖥️ VNC Server
- **Basic VNC Protocol**: Implements core VNC handshake and communication
- **Multi-client Support**: Handle multiple simultaneous connections
- **Standard Port**: Uses VNC standard port 5900 (configurable)
- **Cross-platform**: Works on Windows, Linux, and macOS

### 📹 Screen Recording
- **Multiple Formats**: Support for MP4, AVI, and other video formats
- **Configurable Quality**: Adjustable frame rate (10-60 FPS) and codecs
- **Real-time Recording**: Live screen capture during VNC sessions
- **Simulation Mode**: Text-based recording for testing without video libraries

### 🌐 LAN Monitoring
- **Device Discovery**: Automatic detection of network devices
- **Zeroconf Support**: mDNS/Bonjour service discovery
- **Network Scanning**: Active ping-based device detection
- **Real-time Status**: Live monitoring of device availability

### 🎛️ User Interface
- **GUI Application**: User-friendly tabbed interface
- **Command Line**: Full CLI interface for server environments
- **Real-time Updates**: Live status monitoring and feedback
- **Interactive Demo**: Guided demonstration of all features

## Usage Examples

### Basic VNC Server

Start a VNC server that clients can connect to:

```python
from core_vnc_server import VNCServer

server = VNCServer(host='0.0.0.0', port=5900)
server.start_server()

# Server is now accepting connections
# Connect with: telnet <server_ip> 5900

# Stop when done
server.stop_server()
```

### Screen Recording

Record screen activity (simulation mode):

```python
from core_vnc_server import ScreenRecorder

recorder = ScreenRecorder()
recorder.start_recording("my_session.log")

# Recording system information...
# Stop after some time

recorder.stop_recording()
```

### Network Monitoring

Discover and monitor network devices:

```python
from core_vnc_server import NetworkMonitor

monitor = NetworkMonitor()

# Get local network information
local_ip = monitor.get_local_ip()
print(f"Local IP: {local_ip}")

# Scan for active devices
devices = monitor.scan_network()
for device in devices:
    print(f"Found: {device['ip']} - {device['status']}")

# Start continuous monitoring
monitor.start_monitoring()
# ... monitoring runs in background ...
monitor.stop_monitoring()
```

## Interactive Demo

The interactive demo provides a guided tour of all features:

```bash
python core_vnc_server.py --demo
```

Menu options:
1. **VNC Server Demo**: Start/stop server, test connections
2. **Screen Recording Demo**: Record system activity
3. **Network Monitoring Demo**: Discover network devices
4. **Full Demo**: Run all features simultaneously
5. **Status Check**: View current component status
6. **Exit**: Clean shutdown

## Testing

Run the comprehensive test suite:

```bash
python core_vnc_server.py --test
```

Tests include:
- VNC server start/stop functionality
- Screen recording creation and file output
- Network monitoring and device discovery
- Component integration testing

## Architecture

### Core Components

1. **VNCServer**: Handles VNC protocol implementation
   - Socket management and client connections
   - Basic VNC handshake protocol
   - Multi-threaded client handling

2. **ScreenRecorder**: Manages screen capture and recording
   - Real-time screen capture (simulation mode)
   - File output management
   - Configurable recording parameters

3. **NetworkMonitor**: Provides network discovery and monitoring
   - Local IP detection
   - Active device scanning via ping
   - Continuous monitoring capabilities

### Threading Model

The implementation uses a multi-threaded architecture:
- **Main Thread**: User interface and coordination
- **Server Thread**: VNC client connection acceptance
- **Client Threads**: Individual client connection handling
- **Recording Thread**: Screen capture and file writing
- **Monitor Thread**: Network device discovery and monitoring

## Configuration

### Server Settings

```python
# Custom host and port
server = VNCServer(host='192.168.1.100', port=5901)

# Listen on all interfaces
server = VNCServer(host='0.0.0.0', port=5900)

# Localhost only
server = VNCServer(host='127.0.0.1', port=5900)
```

### Recording Settings

```python
# Basic recording
recorder.start_recording("output.log")

# With custom filename
recorder.start_recording("/path/to/recording.log")
```

### Network Monitoring

```python
# Get local network information
monitor = NetworkMonitor()
local_ip = monitor.get_local_ip()
devices = monitor.scan_network()

# Continuous monitoring
monitor.start_monitoring()
# ... runs in background ...
monitor.stop_monitoring()
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```
   Error starting VNC server: [Errno 98] Address already in use
   ```
   Solution: Use a different port or stop existing VNC servers

2. **Permission Denied**
   ```
   Error starting VNC server: [Errno 13] Permission denied
   ```
   Solution: Use a port > 1024 or run with appropriate permissions

3. **Network Scanning Issues**
   ```
   No devices found during network scan
   ```
   Solution: Check firewall settings, ensure ping is allowed

### Performance Tips

- Use higher ports (5901+) to avoid conflicts
- Limit recording duration for large files
- Adjust network scan frequency for performance

## Security Considerations

**Important**: This implementation is designed for educational and development purposes.

### Current Limitations
- No authentication mechanism
- No encryption for data transmission
- Basic VNC protocol implementation
- Designed for trusted network environments

### Production Recommendations
- Implement proper VNC authentication
- Add SSL/TLS encryption
- Use firewall rules to restrict access
- Consider VPN for remote connections
- Regular security updates and monitoring

## Extensions and Customization

The modular design allows easy extension:

### Custom VNC Server
```python
class CustomVNCServer(VNCServer):
    def _handle_client(self, client_socket, addr):
        # Custom authentication logic
        if not self.authenticate_client(client_socket):
            client_socket.close()
            return
        
        # Call parent implementation
        super()._handle_client(client_socket, addr)
    
    def authenticate_client(self, client_socket):
        # Implement authentication
        return True
```

### Enhanced Recording
```python
class EnhancedRecorder(ScreenRecorder):
    def _record_loop(self):
        # Add custom recording features
        # - Image compression
        # - Video encoding
        # - Real-time streaming
        super()._record_loop()
```

## Deployment

### Development Environment
```bash
# Clone and test
git clone <repository>
cd vnc-server
python core_vnc_server.py --test
python core_vnc_server.py --demo
```

### Production Environment
```bash
# Install full dependencies
pip install -r requirements.txt

# Run with logging
python vnc_server.py > vnc_server.log 2>&1 &

# Monitor with
tail -f vnc_server.log
```

## Contributing

1. Test your changes with `python core_vnc_server.py --test`
2. Ensure backward compatibility with core implementation
3. Update documentation for new features
4. Follow existing code style and patterns

## Support and Resources

- Test all functionality with the built-in test suite
- Use the interactive demo to explore features
- Check the troubleshooting section for common issues
- Review the code comments for implementation details

---

**Note**: This VNC server implementation is designed for educational purposes and development environments. For production use, implement proper security measures including authentication, encryption, and access controls.