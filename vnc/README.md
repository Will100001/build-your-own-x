# Build Your Own VNC (Virtual Network Computing)

A complete implementation of VNC server and client supporting both Windows and Android platforms.

## Overview

This project demonstrates how to build a fully functional VNC solution from scratch, including:

- **VNC Server**: Remote desktop server allowing others to control your screen
- **VNC Viewer**: Client application to connect to remote desktops
- **Cross-Platform Support**: Works on Windows and Android
- **GUI Interfaces**: User-friendly graphical interfaces for both server and client
- **Security Features**: SSL/TLS encryption and authentication
- **Modern Protocol**: Implementation of RFB (Remote Framebuffer) protocol

## Project Structure

```
vnc/
├── README.md              # This file
├── docs/                  # Documentation
│   ├── protocol.md        # RFB protocol documentation
│   ├── architecture.md    # System architecture
│   └── build-guide.md     # Build and deployment guide
├── src/                   # Source code
│   ├── common/            # Shared utilities and protocol implementation
│   ├── server/            # VNC Server implementation
│   ├── client/            # VNC Viewer implementation
│   └── gui/               # GUI components
├── platforms/             # Platform-specific implementations
│   ├── windows/           # Windows-specific code
│   └── android/           # Android-specific code
├── tests/                 # Test suite
├── examples/              # Usage examples
└── build/                 # Build scripts and configuration
```

## Features

### Core VNC Features
- Screen capture and transmission
- Remote keyboard and mouse input
- Multiple encoding formats (Raw, RRE, Hextile, ZRLE)
- Connection management and authentication
- Multi-client support

### Security Features
- SSL/TLS encryption for secure connections
- VNC password authentication
- Connection access control
- Secure key exchange

### GUI Features
- Server configuration interface
- Client connection manager
- Real-time connection monitoring
- Settings and preferences management

### Cross-Platform Support
- Native Windows implementation using Win32 API
- Android implementation with Java/Kotlin
- Shared C/C++ core for protocol handling
- Platform-specific optimizations

## Quick Start

### Building the VNC Server

```bash
cd vnc/build
./build-server.sh          # Linux/macOS
build-server.bat           # Windows
```

### Building the VNC Viewer

```bash
cd vnc/build
./build-client.sh          # Linux/macOS
build-client.bat           # Windows
```

### Running Examples

```bash
# Start VNC server
./vnc-server --port 5900 --password mypassword

# Connect with VNC viewer
./vnc-viewer --host localhost --port 5900
```

## Learning Path

1. **Start with Protocol Basics** - Understand the RFB protocol
2. **Build Core Components** - Implement screen capture and network communication
3. **Add Security** - Implement authentication and encryption
4. **Create GUI** - Build user-friendly interfaces
5. **Platform Integration** - Add Windows and Android support
6. **Optimization** - Performance tuning and advanced features

## Documentation

- [RFB Protocol Guide](docs/protocol.md) - Understanding the VNC protocol
- [Architecture Overview](docs/architecture.md) - System design and components
- [Build Guide](docs/build-guide.md) - Compilation and deployment
- [Platform Notes](platforms/) - Platform-specific implementation details

## Implementation Highlights

This implementation showcases several advanced concepts:

- **Network Programming**: TCP socket handling and protocol implementation
- **Graphics Programming**: Screen capture, pixel format conversion, encoding
- **Cross-Platform Development**: Abstraction layers and platform-specific code
- **Security**: Encryption, authentication, and secure communication
- **GUI Development**: Modern interface design for different platforms
- **Performance Optimization**: Efficient encoding and compression algorithms

## Educational Value

Building this VNC implementation teaches:

- Network protocol design and implementation
- Real-time graphics and screen capture
- Cross-platform software development
- Security best practices in remote access software
- GUI application development
- Performance optimization techniques

## Contributing

Feel free to extend this implementation with:
- Additional encoding formats
- New platform support
- Enhanced security features
- Performance improvements
- GUI enhancements

## License

This implementation is provided for educational purposes. See LICENSE file for details.