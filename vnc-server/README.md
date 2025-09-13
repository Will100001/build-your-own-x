# Python VNC Server

A complete Python implementation of a VNC (Virtual Network Computing) server with a web-based graphical user interface. This project demonstrates the RFB (Remote Framebuffer) protocol implementation and provides remote desktop access functionality.

## Features

### Core VNC Functionality
- **RFB Protocol Implementation**: Complete implementation of the Remote Framebuffer protocol
- **Screen Capture**: Cross-platform screen capture with automatic platform detection
- **Network Communication**: Efficient socket-based client-server communication
- **Authentication**: Username/password authentication with secure storage
- **Multiple Client Support**: Handles multiple concurrent VNC client connections

### Web-based GUI
- **Server Control**: Start, stop, and restart the VNC server
- **Configuration Management**: Adjust screen resolution, frame rate, and other settings
- **User Management**: Add, remove, and manage user accounts
- **Connection Monitoring**: View active connections and connection logs
- **Real-time Status**: Live updates of server status and metrics

### Cross-Platform Compatibility
- **Linux**: Native X11 screen capture support
- **Windows/macOS**: Simulated screen capture for demonstration
- **Fallback Mode**: Generates animated demo content when screen capture is unavailable

## Installation

### Prerequisites
- Python 3.7 or higher
- Optional: PIL/Pillow for enhanced image processing (will fallback if not available)
- Optional: pyautogui for advanced screen capture (will fallback if not available)

### Quick Start
1. Clone or download the VNC server files
2. Navigate to the vnc-server directory
3. Run the server:
   ```bash
   python3 main.py --start-vnc
   ```

### Optional Dependencies
If you want enhanced screen capture capabilities, install the optional dependencies:
```bash
pip3 install -r requirements.txt
```

## Usage

### Command Line Options

#### Basic Usage
```bash
# Start with web GUI only (default)
python3 main.py

# Start VNC server and web GUI
python3 main.py --start-vnc

# Start VNC server without web GUI
python3 main.py --start-vnc --no-gui

# Custom ports
python3 main.py --port 5901 --gui-port 8081
```

#### Authentication Options
```bash
# Disable authentication (not recommended)
python3 main.py --no-auth

# Set custom admin password
python3 main.py --admin-password mypassword123
```

#### Screen Configuration
```bash
# Custom screen resolution
python3 main.py --width 1920 --height 1080

# Adjust frame rate
python3 main.py --fps 30

# Multiple options
python3 main.py --start-vnc --width 1600 --height 900 --fps 15
```

### Web Interface

After starting the server, open your web browser and navigate to:
- Default: http://127.0.0.1:8080
- Custom: http://[gui-host]:[gui-port]

The web interface provides:

1. **Server Status**: View current server state and configuration
2. **Server Control**: Start, stop, and restart the VNC server
3. **Configuration**: Modify server settings
4. **User Management**: Add/remove user accounts
5. **Active Connections**: Monitor connected clients
6. **Connection Logs**: View connection history and events

### VNC Client Connection

Connect to the VNC server using any standard VNC client:

1. **Server Address**: [host]:[port] (default: localhost:5900)
2. **Authentication**: 
   - Default username: `admin`
   - Default password: `password`
3. **Recommended VNC Clients**:
   - TigerVNC
   - RealVNC
   - TightVNC
   - UltraVNC

## Architecture

### Core Components

#### 1. RFB Protocol (`rfb_protocol.py`)
- Implements the Remote Framebuffer protocol specification
- Handles client handshake, authentication, and message processing
- Supports standard VNC message types and encodings
- Manages pixel format negotiation

#### 2. Screen Capture (`screen_capture.py`)
- Cross-platform screen capture abstraction
- Linux X11 integration for real screen capture
- Simulated screen generation for testing and demonstration
- Continuous capture with configurable frame rates

#### 3. Authentication (`authentication.py`)
- Secure password hashing with PBKDF2
- User account management with JSON persistence
- Login attempt tracking and lockout protection
- VNC challenge-response authentication

#### 4. VNC Server (`vnc_server.py`)
- Main server coordination and connection management
- Thread-safe client connection handling
- Configuration management and status reporting
- Connection logging and monitoring

#### 5. Web GUI (`web_gui.py`)
- HTTP server with REST API endpoints
- Real-time server monitoring and control
- Responsive web interface with auto-refresh
- AJAX-based client-server communication

#### 6. Main Application (`main.py`)
- Command-line interface and argument parsing
- Application lifecycle management
- Signal handling for graceful shutdown
- Service coordination

### Protocol Support

#### Supported RFB Features
- RFB Protocol Version 3.8
- Security Types: None, VNC Authentication
- Pixel Formats: 32-bit BGRA
- Encodings: Raw (with planned support for RRE, Hextile)
- Client Messages: Framebuffer Update Request, Key Event, Pointer Event
- Server Messages: Framebuffer Update, Bell, Server Cut Text

#### Message Flow
1. **Handshake**: Version negotiation
2. **Security**: Authentication method selection
3. **Authentication**: Challenge-response (if enabled)
4. **Initialization**: Client/server capability exchange
5. **Normal Protocol**: Ongoing message exchange

## Configuration

### Server Configuration
- **Host/Port**: Network binding configuration
- **Authentication**: Enable/disable and user management
- **Screen Settings**: Resolution and frame rate
- **Connection Limits**: Maximum concurrent clients

### Authentication Configuration
- **User Accounts**: Username/password management
- **Security**: Password hashing and storage
- **Access Control**: Login attempt limiting

### Performance Configuration
- **Frame Rate**: Adjustable FPS for different use cases
- **Screen Resolution**: Configurable virtual screen size
- **Connection Limits**: Resource management

## Testing

### Manual Testing
1. Start the server:
   ```bash
   python3 main.py --start-vnc
   ```

2. Connect with a VNC client to `localhost:5900`

3. Use the web interface at `http://localhost:8080`

### Unit Testing
Run individual component tests:
```bash
# Test RFB protocol
python3 rfb_protocol.py

# Test screen capture
python3 screen_capture.py

# Test authentication
python3 authentication.py

# Test VNC server
python3 vnc_server.py

# Test web GUI
python3 web_gui.py
```

### Integration Testing
1. **Multi-client**: Connect multiple VNC clients simultaneously
2. **Authentication**: Test with various user accounts
3. **Configuration**: Modify settings through web interface
4. **Stability**: Long-running tests with continuous connections

## Troubleshooting

### Common Issues

#### 1. "Address already in use"
- Another VNC server is running on the same port
- Solution: Use a different port with `--port 5901`

#### 2. "Permission denied"
- Insufficient privileges for low-numbered ports
- Solution: Use ports above 1024 or run with sudo

#### 3. "Screen capture not working"
- X11 tools not available or display not accessible
- Solution: Server falls back to simulated screen capture

#### 4. "Web GUI not accessible"
- Firewall blocking the port
- Solution: Configure firewall or use `--gui-host 0.0.0.0`

### Debug Mode
Enable verbose logging by modifying the logging level in the source code:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Performance Issues
- Reduce frame rate: `--fps 5`
- Lower resolution: `--width 800 --height 600`
- Limit connections: `--max-connections 2`

## Security Considerations

### Authentication
- Always use authentication in production: `--auth`
- Use strong passwords for user accounts
- Regularly rotate passwords

### Network Security
- Consider running behind a reverse proxy
- Use VPN or SSH tunneling for remote access
- Bind to localhost only for local use: `--host 127.0.0.1`

### Data Protection
- User credentials are hashed with PBKDF2
- No plaintext password storage
- Connection logs include timestamps and IP addresses

## Limitations

### Current Limitations
1. **Encoding Support**: Currently only Raw encoding (uncompressed)
2. **Platform Support**: Limited real screen capture on non-Linux platforms
3. **Performance**: Not optimized for high-resolution or high-FPS scenarios
4. **Audio**: No audio redirection support
5. **File Transfer**: No file transfer capabilities

### Future Enhancements
- Additional RFB encodings (RRE, Hextile, ZRLE)
- Clipboard synchronization
- Enhanced cross-platform screen capture
- SSL/TLS encryption support
- Audio streaming
- File transfer protocol

## Contributing

This is an educational implementation demonstrating VNC/RFB protocol concepts. Contributions welcome for:
- Additional RFB encoding support
- Enhanced cross-platform compatibility
- Performance optimizations
- Security improvements
- Documentation updates

## License

This project is provided for educational purposes. See individual component files for specific licensing information.

## References

- [RFB Protocol Specification](https://tools.ietf.org/html/rfc6143)
- [VNC Protocol Documentation](https://github.com/rfbproto/rfbproto/blob/master/rfbproto.rst)
- [X11 Screen Capture Documentation](https://www.x.org/releases/X11R7.6/doc/man/man1/xwd.1.xhtml)