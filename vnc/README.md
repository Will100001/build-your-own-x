# Build Your Own VNC Server and Viewer

This project implements a VNC (Virtual Network Computing) Server and Viewer from scratch, demonstrating the Remote Framebuffer (RFB) protocol and cross-platform desktop sharing capabilities.

## Features

### VNC Server
- Screen capture and sharing
- Multi-client support
- Keyboard and mouse input handling
- Multiple encoding formats (Raw, RRE, ZRLE)
- Authentication support
- Cross-platform compatibility (Windows, Linux, macOS)

### VNC Viewer
- Remote desktop viewing
- Keyboard and mouse forwarding
- Multiple connection support
- Full-screen mode
- Connection management
- Cross-platform GUI (Windows, Linux, macOS, Android)

## Architecture

```
vnc/
├── server/           # VNC Server implementation
├── viewer/           # VNC Viewer implementation
├── protocol/         # RFB protocol implementation
├── common/           # Shared utilities
├── build/            # Build scripts and configurations
├── docs/             # Documentation
└── tests/            # Test suite
```

## Quick Start

### Server
```bash
cd vnc/server
python vnc_server.py --port 5900 --password secret
```

### Viewer
```bash
cd vnc/viewer
python vnc_viewer.py --host localhost --port 5900
```

## Building

### Prerequisites
- Python 3.8+
- PyQt5/PySide2 for GUI
- Pillow for image processing
- Platform-specific dependencies (see docs/)

### Windows
```bash
cd vnc/build
./build_windows.bat
```

### Android
```bash
cd vnc/build
./build_android.sh
```

## Documentation

- [Setup Guide](docs/setup.md)
- [Usage Instructions](docs/usage.md)
- [Protocol Documentation](docs/protocol.md)
- [Build Instructions](docs/build.md)
- [Troubleshooting](docs/troubleshooting.md)

## License

This project is part of the build-your-own-x educational repository.