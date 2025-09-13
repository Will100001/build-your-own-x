# Enhanced VNC Server

A Python-based VNC server implementation with advanced features including screen recording and LAN monitoring capabilities.

## Features

### 🖥️ Core VNC Server
- Basic VNC server functionality for remote desktop access
- Support for multiple client connections
- Real-time status monitoring
- Cross-platform compatibility (Windows, Linux, macOS)

### 📹 Screen Recording
- Record screen activity in MP4 or AVI format
- Configurable frame rate (10-60 FPS)
- Multiple codec support (MP4V, XVID, MJPG)
- Start/stop recording via GUI controls
- Automatic timestamp-based file naming

### 🌐 LAN Monitoring
- Automatic device discovery using Zeroconf
- Network scanning for active devices
- Real-time device status monitoring
- Support for both online and offline operation
- Device list with IP addresses and last seen timestamps

### 🎛️ User Interface
- Intuitive tabbed GUI interface
- Real-time status updates
- Easy-to-use controls for all features
- Visual feedback for all operations

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Install Dependencies

```bash
cd vnc-server
pip install -r requirements.txt
```

### Required Libraries

- `opencv-python`: For screen recording functionality
- `Pillow`: For image processing
- `pyautogui`: For screen capture
- `zeroconf`: For LAN device discovery
- `psutil`: For system monitoring
- `numpy`: For numerical operations

## Usage

### Starting the Application

```bash
python vnc_server.py
```

This will open the main GUI window with three tabs:

### 1. VNC Server Tab

**Starting the Server:**
1. Click "Start Server" to begin accepting connections
2. The server will listen on all interfaces (0.0.0.0) port 5900
3. Connection information is displayed for clients to connect

**Connecting Clients:**
- Use any VNC client to connect to: `<server_ip>:5900`
- The server supports basic VNC protocol handshake
- Multiple clients can connect simultaneously

**Server Status:**
- View current server status (Running/Stopped)
- Monitor number of connected clients
- See local IP address and port information

### 2. Screen Recording Tab

**Starting Recording:**
1. (Optional) Click "Choose Output File" to specify recording location
2. Configure recording settings (FPS, codec)
3. Click "Start Recording" to begin
4. Recording starts immediately and saves to specified file

**Recording Settings:**
- **FPS**: Frame rate from 10-60 (default: 30)
- **Codec**: Video codec (MP4V, XVID, MJPG)
- **Output Format**: MP4 or AVI files supported

**Stopping Recording:**
1. Click "Stop Recording" to finish
2. Video file is automatically saved and available for playback

### 3. LAN Monitoring Tab

**Device Discovery:**
1. Click "Start Monitoring" for automatic Zeroconf discovery
2. Click "Scan Network" for active device scanning
3. Click "Refresh" to update the device list

**Device Information:**
- Device name/identifier
- IP address
- Current status (online/offline)
- Last seen timestamp

**Monitoring Modes:**
- **Zeroconf**: Discovers services broadcasting on the network
- **Network Scan**: Pings all IPs in the local subnet
- **Real-time**: Continuous monitoring of device status

## Configuration

### Server Settings

The VNC server can be configured by modifying the `VNCServer` class initialization:

```python
vnc_server = VNCServer(host='0.0.0.0', port=5900)
```

- `host`: Interface to bind to (0.0.0.0 for all interfaces)
- `port`: Port number (default VNC port is 5900)

### Recording Settings

Default recording settings can be modified in the GUI or programmatically:

```python
screen_recorder.start_recording(
    output_file="my_recording.mp4",
    fps=30,
    codec='mp4v'
)
```

### Network Monitoring

LAN monitoring can be customized for different service types:

```python
# Monitor additional service types
services = ["_http._tcp.local.", "_ssh._tcp.local.", "_vnc._tcp.local.", "_ftp._tcp.local."]
```

## Architecture

### Core Components

1. **VNCServer**: Handles VNC protocol and client connections
2. **ScreenRecorder**: Manages screen capture and video encoding
3. **LANDeviceMonitor**: Discovers and monitors network devices
4. **VNCServerGUI**: Main GUI interface and coordination

### Threading Model

The application uses multiple threads to ensure responsive operation:
- **Main Thread**: GUI event loop
- **Server Thread**: VNC client connection handling
- **Recording Thread**: Screen capture and encoding
- **Monitoring Thread**: Network device discovery
- **Scan Thread**: Active device scanning

### Network Protocols

- **VNC Protocol**: Basic implementation for remote desktop
- **Zeroconf/mDNS**: Service discovery on local network
- **ICMP/Ping**: Device availability checking
- **TCP Sockets**: Client-server communication

## Troubleshooting

### Common Issues

**1. Import Errors**
```
ImportError: No module named 'cv2'
```
Solution: Install requirements with `pip install -r requirements.txt`

**2. Recording Fails to Start**
```
Error starting recording: Failed to open video writer
```
Solutions:
- Check file permissions in output directory
- Try different codec (XVID or MJPG)
- Ensure sufficient disk space

**3. VNC Server Won't Start**
```
Error starting VNC server: [Errno 98] Address already in use
```
Solutions:
- Check if another VNC server is running on port 5900
- Change port number in server configuration
- Kill existing VNC processes

**4. No Devices Found in LAN Scan**
```
Found 0 devices
```
Solutions:
- Check network connectivity
- Ensure firewall allows ICMP/ping
- Try Zeroconf monitoring for service discovery
- Verify correct network interface is being used

### Performance Optimization

**Screen Recording:**
- Lower FPS for smaller file sizes
- Use MJPG codec for better compatibility
- Record to fast storage (SSD) for high frame rates

**Network Monitoring:**
- Limit scan range for faster scanning
- Increase timeout for slower networks
- Use Zeroconf for passive discovery

## Security Considerations

### Current Implementation
- **No Authentication**: Basic implementation without password protection
- **No Encryption**: Data transmitted in plain text
- **Local Network**: Designed for trusted LAN environments

### Production Recommendations
- Implement VNC authentication mechanisms
- Add SSL/TLS encryption for remote connections
- Use firewall rules to restrict access
- Consider VPN for remote access

## Advanced Usage

### Programmatic Control

The server can be controlled programmatically:

```python
from vnc_server import VNCServer, ScreenRecorder, LANDeviceMonitor

# Start VNC server
server = VNCServer()
server.start_server()

# Start recording
recorder = ScreenRecorder()
recorder.start_recording("session.mp4")

# Monitor network
monitor = LANDeviceMonitor()
monitor.start_monitoring()

# ... do work ...

# Cleanup
server.stop_server()
recorder.stop_recording()
monitor.stop_monitoring()
```

### Custom Extensions

The modular design allows easy extension:

```python
class CustomVNCServer(VNCServer):
    def _handle_client(self, client_socket, addr):
        # Custom client handling logic
        super()._handle_client(client_socket, addr)

class CustomRecorder(ScreenRecorder):
    def _record_loop(self):
        # Custom recording logic with filters/effects
        super()._record_loop()
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is released under CC0 (Public Domain). Feel free to use, modify, and distribute as needed.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the GitHub issues
3. Create a new issue with detailed information

---

**Note**: This implementation provides basic VNC functionality suitable for development and testing. For production use, consider implementing proper authentication, encryption, and security measures.