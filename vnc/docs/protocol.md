# RFB Protocol Implementation Guide

## Overview

The Remote Framebuffer (RFB) protocol is the foundation of VNC. This document explains how to implement the protocol from scratch.

## Protocol Flow

1. **Handshake**: Version negotiation
2. **Security**: Authentication method selection
3. **Initialization**: Screen format and name exchange
4. **Normal Protocol**: Message exchange for screen updates and input

## Message Types

### Client to Server Messages
- **SetPixelFormat**: Change pixel format
- **SetEncodings**: Specify supported encodings
- **FramebufferUpdateRequest**: Request screen update
- **KeyEvent**: Keyboard input
- **PointerEvent**: Mouse input
- **ClientCutText**: Clipboard data

### Server to Client Messages
- **FramebufferUpdate**: Screen data
- **SetColourMapEntries**: Color map changes
- **Bell**: Audio bell notification
- **ServerCutText**: Clipboard data

## Implementation Steps

### 1. Basic Protocol Handler

```cpp
class RFBProtocol {
public:
    enum State {
        HANDSHAKE,
        SECURITY,
        INITIALIZATION,
        NORMAL
    };
    
    bool handleMessage(const uint8_t* data, size_t length);
    void sendFramebufferUpdate();
    void processInput(const InputEvent& event);
};
```

### 2. Message Encoding

```cpp
// FramebufferUpdate message structure
struct FramebufferUpdate {
    uint8_t type = 0;           // Message type
    uint8_t padding = 0;        // Padding
    uint16_t numRects;          // Number of rectangles
    // Followed by rectangle data
};

struct Rectangle {
    uint16_t x, y;              // Position
    uint16_t width, height;     // Dimensions
    int32_t encoding;           // Encoding type
    // Followed by pixel data
};
```

### 3. Encoding Formats

- **Raw Encoding (0)**: Uncompressed pixel data
- **RRE Encoding (2)**: Rise-and-Run-length Encoding
- **Hextile Encoding (5)**: 16x16 tile-based encoding
- **ZRLE Encoding (16)**: Zlib compressed RLE

## Security Implementation

### Authentication Types
- **None (1)**: No authentication
- **VNC Authentication (2)**: Challenge-response with DES
- **TLS (18)**: Transport Layer Security

### Example VNC Authentication

```cpp
void handleVNCAuth(const std::vector<uint8_t>& challenge) {
    // Encrypt challenge with password using DES
    std::vector<uint8_t> response = desEncrypt(challenge, password);
    sendResponse(response);
}
```

## Performance Considerations

1. **Efficient Encoding**: Choose appropriate encoding based on content
2. **Differential Updates**: Only send changed regions
3. **Compression**: Use ZRLE for better compression
4. **Adaptive Quality**: Adjust quality based on bandwidth

## Next Steps

1. Implement basic handshake and security
2. Add framebuffer capture and encoding
3. Implement input handling
4. Add GUI components
5. Platform-specific optimizations