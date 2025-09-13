# Usage Instructions

This document provides detailed instructions on how to use the VNC Server and Viewer.

## VNC Server Usage

### Starting the Server

#### Command Line
```bash
# Basic usage
python server/vnc_server.py

# With custom settings
python server/vnc_server.py --host 0.0.0.0 --port 5900 --password secret

# Verbose logging
python server/vnc_server.py --verbose
```

#### Available Options
- `--host`: IP address to bind to (default: localhost)
- `--port`: Port to listen on (default: 5900)
- `--password`: VNC password (default: no password)
- `--verbose`: Enable verbose logging

### Server Security

#### Setting a Password
Always use a password for production use:
```bash
python server/vnc_server.py --password "your_secure_password"
```

#### Host Binding
- `localhost` or `127.0.0.1`: Only local connections
- `0.0.0.0`: Accept connections from any IP (use with caution)
- Specific IP: Only accept connections from that network

### Managing Clients

The server supports multiple simultaneous clients. Each client connection is handled in a separate thread.

#### Viewing Connected Clients
Server logs show client connections:
```
2023-12-13 10:30:15 - INFO - New connection from ('192.168.1.100', 52031)
2023-12-13 10:30:16 - INFO - Client ('192.168.1.100', 52031) connected successfully
```

#### Disconnecting Clients
Clients are automatically disconnected when:
- The client application closes
- Network connection is lost
- Authentication fails
- Protocol errors occur

### Server Performance Tuning

#### Frame Rate
The server automatically adjusts frame rate based on client requests. For better performance:
- Clients should use incremental updates
- Minimize unnecessary screen changes
- Use efficient encodings

#### Memory Usage
Monitor server memory usage, especially with multiple clients:
```bash
# Linux
ps aux | grep vnc_server

# Windows
tasklist | findstr python
```

## VNC Viewer Usage

### Connecting to a Server

#### GUI Method (PyQt5)
1. Launch the viewer: `python viewer/vnc_viewer.py`
2. Click "Connect"
3. Enter server details:
   - Host: Server IP address or hostname
   - Port: Server port (default 5900)
   - Password: Server password (if required)
4. Click "OK" to connect

#### Command Line Method
```bash
# Connect with parameters
python viewer/vnc_viewer.py --host 192.168.1.100 --port 5900 --password secret
```

### Viewer Controls

#### Keyboard Input
- All keyboard input is forwarded to the server
- Special keys (Ctrl, Alt, etc.) work as expected
- Function keys (F1-F12) are supported

#### Mouse Input
- Left, right, and middle mouse buttons
- Mouse wheel scrolling
- Mouse movement tracking

#### Window Management
- Resize the viewer window to scale the remote desktop
- The remote desktop maintains aspect ratio
- Full-screen mode (implementation varies by platform)

### Connection Management

#### Reconnection
If the connection is lost:
1. The viewer will display a connection error
2. Click "Connect" to reconnect
3. Or restart the viewer application

#### Multiple Connections
You can run multiple viewer instances to connect to different servers simultaneously.

## Platform-Specific Usage

### Windows

#### Starting Server as Service
For automatic startup, you can install the server as a Windows service (advanced setup required).

#### Viewer Shortcuts
Create desktop shortcuts for frequently used connections:
```batch
"C:\path\to\vnc-viewer.exe" --host 192.168.1.100 --password secret
```

### Linux

#### X11 Display
Ensure the server has access to the X11 display:
```bash
# If running as different user
xhost +localhost
```

#### Screen Resolution
The server captures the current screen resolution. To change:
```bash
# Change resolution before starting server
xrandr --output HDMI-1 --mode 1920x1080
```

### macOS

#### Screen Recording Permission
macOS may require screen recording permissions:
1. System Preferences > Security & Privacy > Privacy
2. Select "Screen Recording"
3. Add the Python executable or VNC server

### Android

#### Network Connection
- Ensure your Android device is on the same network as the VNC server
- Use the device's IP address or hostname
- Consider using a VPN for external connections

#### Touch Controls
- Tap: Left mouse click
- Long press: Right mouse click
- Two-finger tap: Middle mouse click
- Pinch to zoom: Scale display
- Swipe: Mouse movement

## Common Use Cases

### Remote Desktop Access
```bash
# On the computer you want to control:
python server/vnc_server.py --host 0.0.0.0 --password work123

# On the device you're using to connect:
python viewer/vnc_viewer.py --host 192.168.1.50 --password work123
```

### Screen Sharing for Presentations
```bash
# Presenter's computer:
python server/vnc_server.py --password presentation

# Viewers can connect to see the screen
# Use incremental updates for smoother experience
```

### Technical Support
```bash
# Customer's computer (receiving help):
python server/vnc_server.py --password support_session_123

# Support technician:
python viewer/vnc_viewer.py --host customer_ip --password support_session_123
```

### Development and Testing
```bash
# Test server on virtual machine:
python server/vnc_server.py --port 5901

# Connect from host machine:
python viewer/vnc_viewer.py --host vm_ip --port 5901
```

## Best Practices

### Security
1. Always use passwords in production
2. Use SSH tunneling for external access
3. Limit connection time for sensitive sessions
4. Monitor server logs for unauthorized access attempts

### Performance
1. Use incremental updates when possible
2. Minimize screen changes during sessions
3. Close unnecessary applications on the server
4. Use wired connections for best performance

### Reliability
1. Ensure stable network connections
2. Monitor server resources (CPU, memory)
3. Have backup connection methods available
4. Test connections before important sessions

## Troubleshooting

### Connection Issues
- Verify server is running and listening on correct port
- Check firewall settings on both client and server
- Test with localhost connections first
- Verify network connectivity between client and server

### Performance Issues
- Check network bandwidth and latency
- Reduce screen update frequency
- Close resource-intensive applications
- Consider using more efficient encodings

### Display Issues
- Verify pixel format compatibility
- Check color depth settings
- Ensure proper screen resolution
- Test with different encoding formats

For more detailed troubleshooting, see `docs/troubleshooting.md`.