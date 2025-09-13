# VNC Server and Viewer

A cross-platform VNC (Virtual Network Computing) implementation with user-friendly GUI interfaces for both Windows and Android platforms.

## Features

### VNC Viewer
- **Cross-platform**: Windows (Electron) and Android (WebView) support
- **User-friendly GUI**: Intuitive interface with connection management
- **Remote control**: Full mouse and keyboard support
- **Screen sharing**: Real-time framebuffer updates
- **Security**: Password protection and secure connections
- **Zoom & Fullscreen**: Flexible viewing options
- **Connection history**: Save and manage connections

### VNC Server
- **Desktop sharing**: Share your screen with remote clients
- **Connection monitoring**: Real-time client connection tracking
- **System tray integration**: Run in background on Windows
- **Access control**: Password protection and view-only modes
- **Logging**: Comprehensive activity logging
- **Firewall configuration**: Automatic Windows Firewall setup assistance

## Supported Platforms

- **Windows**: Native Electron applications with system integration
- **Android**: WebView-based applications for mobile access
- **Web Browser**: HTML5-based demos for testing and development

## Quick Start

### Building the Applications

1. **Prerequisites**:
   - Node.js 18+ and npm
   - For Android: Android Studio and SDK

2. **Build all applications**:
   ```bash
   cd vnc
   chmod +x build.sh
   ./build.sh all
   ```

3. **Build specific components**:
   ```bash
   # Build only viewer
   ./build.sh viewer
   
   # Build only server
   ./build.sh server
   
   # Build only Windows versions
   ./build.sh all windows-only
   
   # Build only Android versions
   ./build.sh all android-only
   ```

### Running the Applications

#### Windows
- **VNC Viewer**: Run `viewer/dist/VNC Viewer Setup.exe`
- **VNC Server**: Run `server/dist/VNC Server Setup.exe`

#### Android
- Import projects from `android/viewer/` and `android/server/` in Android Studio
- Build and install APK files

#### Web Demo
```bash
cd vnc
python3 -m http.server 8080
```
Then open:
- Viewer: http://localhost:8080/demo-viewer.html
- Server: http://localhost:8080/demo-server.html

## Architecture

### Core Components

1. **VNC Protocol** (`shared/vnc-protocol.js`):
   - Simplified VNC protocol implementation
   - Event-driven architecture
   - Cross-platform compatibility

2. **GUI Components** (`shared/vnc-gui.js`):
   - Reusable UI components
   - VNCViewer and VNCServer classes
   - Canvas-based framebuffer rendering

3. **Styling** (`shared/vnc-styles.css`):
   - Professional, responsive design
   - Dark/light theme support
   - Mobile-optimized interface

### Platform-Specific Implementations

#### Windows (Electron)
- **Main Process**: Window management, system integration, menus
- **Renderer Process**: Web-based GUI using shared components
- **Features**: System tray, native menus, file system access

#### Android (WebView)
- **MainActivity**: Native Android activity with WebView
- **Web Assets**: HTML/CSS/JS files loaded in WebView
- **Features**: Touch-optimized interface, mobile-specific controls

## Development

### Project Structure
```
vnc/
├── shared/              # Cross-platform components
│   ├── vnc-protocol.js  # VNC protocol implementation
│   ├── vnc-gui.js       # GUI components
│   └── vnc-styles.css   # Styling
├── viewer/              # VNC Viewer (Windows)
│   ├── main.js          # Electron main process
│   ├── viewer.html      # Renderer HTML
│   ├── viewer.js        # Renderer logic
│   └── package.json     # Dependencies and build config
├── server/              # VNC Server (Windows)
│   ├── main.js          # Electron main process
│   ├── server.html      # Renderer HTML
│   ├── server.js        # Renderer logic
│   └── package.json     # Dependencies and build config
├── android/             # Android apps
│   ├── build-android.js # Android project generator
│   ├── viewer/          # Generated Android viewer project
│   └── server/          # Generated Android server project
├── build.sh             # Unix build script
├── build.bat            # Windows build script
└── README.md            # This file
```

### Key Design Decisions

1. **Cross-platform GUI**: Using web technologies (HTML/CSS/JS) allows sharing UI code between Windows (Electron) and Android (WebView)

2. **Modular Architecture**: Shared components in `vnc/shared/` can be reused across all platforms

3. **Event-driven Protocol**: VNC protocol implementation uses events for loose coupling between components

4. **Responsive Design**: CSS media queries and flexible layouts work on both desktop and mobile

### Adding New Features

1. **Protocol Extensions**: Add new message types to `vnc-protocol.js`
2. **GUI Features**: Extend `VNCViewer` or `VNCServer` classes in `vnc-gui.js`
3. **Platform Integration**: Modify platform-specific files (main.js, MainActivity.java)

## Security Considerations

- **Password Protection**: Configurable password authentication
- **Network Security**: Connections should use VNC over SSH or VPN in production
- **Access Control**: Server-side connection filtering and view-only modes
- **Input Validation**: All user inputs are validated and sanitized

## Performance Optimization

- **Framebuffer Compression**: Real implementations should use RFB compression algorithms
- **Update Regions**: Only transmit changed screen regions
- **Connection Pooling**: Efficient handling of multiple client connections
- **Mobile Optimization**: Touch-friendly controls and reduced bandwidth usage

## Troubleshooting

### Common Issues

1. **Connection Failed**:
   - Check firewall settings (port 5900)
   - Verify network connectivity
   - Ensure server is running

2. **Performance Issues**:
   - Reduce screen resolution
   - Use local network connections
   - Check system resources

3. **Android Build Issues**:
   - Ensure Android SDK is properly configured
   - Check WebView compatibility
   - Verify permissions in AndroidManifest.xml

### Debug Mode

Enable debug mode for detailed logging:
```bash
# Windows (Electron)
npm run dev

# Web demo with console
Open browser developer tools (F12)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on both Windows and Android
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Credits

Built as part of the "Build Your Own X" tutorial series, demonstrating cross-platform GUI development with web technologies.