#ifndef RFB_PROTOCOL_H
#define RFB_PROTOCOL_H

#include <cstdint>
#include <vector>
#include <string>
#include <functional>

namespace vnc {

// RFB Protocol Constants
constexpr uint16_t RFB_DEFAULT_PORT = 5900;
constexpr const char* RFB_VERSION_3_8 = "RFB 003.008\n";

// Message Types
enum ClientMessageType : uint8_t {
    SET_PIXEL_FORMAT = 0,
    SET_ENCODINGS = 2,
    FRAMEBUFFER_UPDATE_REQUEST = 3,
    KEY_EVENT = 4,
    POINTER_EVENT = 5,
    CLIENT_CUT_TEXT = 6
};

enum ServerMessageType : uint8_t {
    FRAMEBUFFER_UPDATE = 0,
    SET_COLOUR_MAP_ENTRIES = 1,
    BELL = 2,
    SERVER_CUT_TEXT = 3
};

// Security Types
enum SecurityType : uint8_t {
    INVALID = 0,
    NONE = 1,
    VNC_AUTHENTICATION = 2,
    TLS = 18
};

// Encoding Types
enum EncodingType : int32_t {
    RAW = 0,
    COPY_RECT = 1,
    RRE = 2,
    HEXTILE = 5,
    ZRLE = 16,
    CURSOR = -239,
    DESKTOP_SIZE = -223
};

// Protocol State
enum ProtocolState {
    HANDSHAKE,
    SECURITY,
    SECURITY_RESULT,
    INITIALIZATION,
    NORMAL
};

// Data Structures
struct PixelFormat {
    uint8_t bitsPerPixel;
    uint8_t depth;
    uint8_t bigEndianFlag;
    uint8_t trueColourFlag;
    uint16_t redMax;
    uint16_t greenMax;
    uint16_t blueMax;
    uint8_t redShift;
    uint8_t greenShift;
    uint8_t blueShift;
    uint8_t padding[3];
} __attribute__((packed));

struct Rectangle {
    uint16_t x;
    uint16_t y;
    uint16_t width;
    uint16_t height;
    int32_t encoding;
} __attribute__((packed));

struct FramebufferUpdateMsg {
    uint8_t messageType;
    uint8_t padding;
    uint16_t numberOfRectangles;
} __attribute__((packed));

struct KeyEventMsg {
    uint8_t messageType;
    uint8_t downFlag;
    uint16_t padding;
    uint32_t key;
} __attribute__((packed));

struct PointerEventMsg {
    uint8_t messageType;
    uint8_t buttonMask;
    uint16_t xPosition;
    uint16_t yPosition;
} __attribute__((packed));

// Main Protocol Handler
class RFBProtocol {
public:
    RFBProtocol();
    virtual ~RFBProtocol() = default;

    // Protocol State Management
    bool handleIncomingData(const uint8_t* data, size_t length);
    std::vector<uint8_t> getOutgoingData();
    ProtocolState getState() const { return state_; }

    // Callbacks
    using FramebufferUpdateCallback = std::function<void(uint16_t x, uint16_t y, uint16_t w, uint16_t h)>;
    using KeyEventCallback = std::function<void(uint32_t key, bool down)>;
    using PointerEventCallback = std::function<void(uint16_t x, uint16_t y, uint8_t buttons)>;
    
    void setFramebufferUpdateCallback(FramebufferUpdateCallback cb) { fbUpdateCallback_ = cb; }
    void setKeyEventCallback(KeyEventCallback cb) { keyEventCallback_ = cb; }
    void setPointerEventCallback(PointerEventCallback cb) { pointerEventCallback_ = cb; }

    // Screen Management
    void setFramebufferSize(uint16_t width, uint16_t height);
    void setPixelFormat(const PixelFormat& format);
    void sendFramebufferUpdate(const std::vector<Rectangle>& rectangles, const std::vector<uint8_t>& pixelData);

    // Security
    void setPassword(const std::string& password) { password_ = password; }
    void enableTLS(bool enable) { tlsEnabled_ = enable; }

protected:
    virtual bool isServer() const = 0;
    
private:
    // Protocol Handlers
    bool handleHandshake(const uint8_t* data, size_t length);
    bool handleSecurity(const uint8_t* data, size_t length);
    bool handleSecurityResult(const uint8_t* data, size_t length);
    bool handleInitialization(const uint8_t* data, size_t length);
    bool handleNormalProtocol(const uint8_t* data, size_t length);

    // Message Handlers
    bool handleSetPixelFormat(const uint8_t* data, size_t length);
    bool handleSetEncodings(const uint8_t* data, size_t length);
    bool handleFramebufferUpdateRequest(const uint8_t* data, size_t length);
    bool handleKeyEvent(const uint8_t* data, size_t length);
    bool handlePointerEvent(const uint8_t* data, size_t length);
    bool handleClientCutText(const uint8_t* data, size_t length);

    // Utility Functions
    void sendVersion();
    void sendSecurityTypes();
    void sendSecurityResult(bool success);
    void sendServerInit();
    bool verifyPassword(const std::vector<uint8_t>& challenge, const std::vector<uint8_t>& response);
    std::vector<uint8_t> generateChallenge();

    // State
    ProtocolState state_;
    std::vector<uint8_t> incomingBuffer_;
    std::vector<uint8_t> outgoingBuffer_;
    
    // Framebuffer
    uint16_t fbWidth_;
    uint16_t fbHeight_;
    PixelFormat pixelFormat_;
    std::string desktopName_;
    
    // Security
    std::string password_;
    bool tlsEnabled_;
    std::vector<uint8_t> securityChallenge_;
    
    // Supported encodings
    std::vector<int32_t> supportedEncodings_;
    
    // Callbacks
    FramebufferUpdateCallback fbUpdateCallback_;
    KeyEventCallback keyEventCallback_;
    PointerEventCallback pointerEventCallback_;
};

// Server-specific Protocol Handler
class RFBServer : public RFBProtocol {
public:
    RFBServer();
    
protected:
    bool isServer() const override { return true; }
};

// Client-specific Protocol Handler
class RFBClient : public RFBProtocol {
public:
    RFBClient();
    
    // Client-specific methods
    void requestFramebufferUpdate(uint16_t x, uint16_t y, uint16_t w, uint16_t h, bool incremental = false);
    void sendKeyEvent(uint32_t key, bool down);
    void sendPointerEvent(uint16_t x, uint16_t y, uint8_t buttons);
    
protected:
    bool isServer() const override { return false; }
};

} // namespace vnc

#endif // RFB_PROTOCOL_H