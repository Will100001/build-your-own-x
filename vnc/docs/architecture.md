# VNC System Architecture

## Overview

This VNC implementation follows a modular, layered architecture that separates protocol handling, platform abstraction, and user interface components.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐              │
│  │   Server GUI    │    │   Client GUI    │              │
│  │  - Console UI   │    │  - Console UI   │              │
│  │  - Config UI    │    │  - Display UI   │              │
│  │  - Monitor UI   │    │  - Control UI   │              │
│  └─────────────────┘    └─────────────────┘              │
├─────────────────────────────────────────────────────────────┤
│                   Application Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐              │
│  │   VNC Server    │    │   VNC Client    │              │
│  │  - Connection   │    │  - Connection   │              │
│  │  - Management   │    │  - Management   │              │
│  │  - Client List  │    │  - Display      │              │
│  └─────────────────┘    └─────────────────┘              │
├─────────────────────────────────────────────────────────────┤
│                    Protocol Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐│
│  │                RFB Protocol Handler                    ││
│  │  - Handshake    - Security      - Initialization      ││
│  │  - Message Processing           - Encoding/Decoding   ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                  Platform Abstraction                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Screen Capture  │  │ Input Simulator │  │  Network    │ │
│  │ - Windows       │  │ - Windows       │  │ - Sockets   │ │
│  │ - Linux/X11     │  │ - Linux/X11     │  │ - TLS       │ │
│  │ - Android       │  │ - Android       │  │ - Auth      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     System Layer                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐│
│  │                Operating System                        ││
│  │  Windows GDI/Win32    Linux X11/Wayland    Android    ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. RFB Protocol Handler

The heart of the VNC implementation, handling the Remote Framebuffer protocol:

**Responsibilities:**
- Protocol negotiation and handshake
- Security and authentication
- Message encoding/decoding
- Connection state management

**Key Classes:**
- `RFBProtocol` - Base protocol implementation
- `RFBServer` - Server-side protocol handler
- `RFBClient` - Client-side protocol handler

### 2. VNC Server

Manages server-side operations:

**Responsibilities:**
- Accept and manage client connections
- Screen capture and change detection
- Input event simulation
- Multi-client support

**Key Classes:**
- `VNCServer` - Main server class
- `ClientConnection` - Individual client handler
- `NetworkServer` - TCP server abstraction

### 3. VNC Client

Handles client-side functionality:

**Responsibilities:**
- Connect to VNC servers
- Display remote framebuffer
- Send input events
- Handle server messages

**Key Classes:**
- `VNCClient` - Main client class
- Connection management
- Framebuffer rendering

### 4. Platform Abstraction

Provides cross-platform functionality:

**Screen Capture:**
- Windows: GDI/DirectX
- Linux: X11/XShm
- Android: MediaProjection

**Input Simulation:**
- Windows: SendInput API
- Linux: XTest extension
- Android: Accessibility Service

## Data Flow

### Server Data Flow

```
Screen → Capture → Encode → Network → Client
  ↑                                      ↓
Input ← Simulate ← Decode ← Network ← Client
```

1. **Screen Capture**: Continuously capture screen changes
2. **Change Detection**: Identify modified regions
3. **Encoding**: Compress pixel data (Raw, RLE, etc.)
4. **Network**: Send updates to connected clients
5. **Input Processing**: Receive and simulate input events

### Client Data Flow

```
Display ← Decode ← Network ← Server
   ↓                          ↑
Input → Encode → Network → Server
```

1. **Network**: Receive framebuffer updates
2. **Decoding**: Decompress pixel data
3. **Display**: Render to screen
4. **Input Capture**: Capture local input events
5. **Network**: Send input to server

## Threading Model

### Server Threading

```
Main Thread
├── Accept Thread (Network connections)
├── Capture Thread (Screen capture)
└── Client Threads (One per client)
    ├── Receive Thread (Client messages)
    └── Send Thread (Framebuffer updates)
```

### Client Threading

```
Main Thread (GUI)
├── Receive Thread (Server messages)
├── Send Thread (Input events)
└── Display Thread (Framebuffer rendering)
```

## Security Architecture

### Authentication Flow

1. **Version Negotiation**: Exchange supported protocol versions
2. **Security Type Selection**: Choose authentication method
3. **Authentication**: Perform chosen authentication
4. **Security Result**: Confirm authentication success

### Supported Security Types

- **None**: No authentication (development only)
- **VNC Authentication**: Challenge-response with DES
- **TLS**: Transport Layer Security (optional)

### Security Considerations

- Password-based authentication
- Encrypted connections (TLS)
- Access control lists
- Session timeouts
- Audit logging

## Performance Optimizations

### Encoding Strategies

- **Raw**: Uncompressed for low latency
- **RRE**: Run-length encoding for simple graphics
- **Hextile**: Tile-based encoding for mixed content
- **ZRLE**: Compressed RLE for bandwidth efficiency

### Change Detection

- **Full Screen**: Simple but inefficient
- **Region-based**: Track dirty rectangles
- **Pixel-level**: Compare individual pixels
- **Hardware-assisted**: Use GPU for comparison

### Network Optimizations

- **Adaptive encoding**: Choose encoding based on content
- **Compression**: Reduce bandwidth usage
- **Batching**: Combine small updates
- **Priority**: Send visible areas first

## Error Handling

### Connection Errors

- Network timeouts
- Protocol violations
- Authentication failures
- Resource exhaustion

### Recovery Strategies

- Automatic reconnection
- Graceful degradation
- Error reporting
- Fallback protocols

## Extensibility

### Plugin Architecture

The system supports extensions through:

- Custom encodings
- Authentication methods
- Input filters
- Display filters

### Platform Extensions

New platforms can be added by implementing:

- `ScreenCapture` interface
- `InputSimulator` interface
- Platform-specific initialization

## Configuration

### Server Configuration

- Network settings (port, interfaces)
- Security settings (passwords, TLS)
- Performance settings (encodings, quality)
- Access control (allowed clients)

### Client Configuration

- Connection profiles
- Display settings (scaling, color depth)
- Input settings (keyboard mapping)
- Performance preferences

## Monitoring and Diagnostics

### Metrics

- Connection count and duration
- Data transfer rates
- Frame rates and latency
- Error rates and types

### Logging

- Connection events
- Authentication attempts
- Performance statistics
- Error conditions

This architecture provides a solid foundation for a production-quality VNC implementation with good separation of concerns, platform independence, and extensibility.