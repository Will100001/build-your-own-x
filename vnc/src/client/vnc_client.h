#ifndef VNC_CLIENT_H
#define VNC_CLIENT_H

#include "../common/rfb_protocol.h"
#include <thread>
#include <atomic>
#include <memory>
#include <functional>
#include <chrono>

namespace vnc {

class VNCClient {
public:
    VNCClient();
    ~VNCClient();

    // Connection management
    bool connect(const std::string& host, uint16_t port = RFB_DEFAULT_PORT);
    void disconnect();
    bool isConnected() const { return connected_; }
    
    // Authentication
    void setPassword(const std::string& password);
    bool authenticate();
    
    // Screen interaction
    void requestFramebufferUpdate(uint16_t x = 0, uint16_t y = 0, uint16_t w = 0, uint16_t h = 0, bool incremental = false);
    void sendKeyEvent(uint32_t key, bool down);
    void sendPointerEvent(uint16_t x, uint16_t y, uint8_t buttons);
    void sendClipboardText(const std::string& text);
    
    // Framebuffer access
    const std::vector<uint8_t>& getFramebuffer() const { return framebuffer_; }
    uint16_t getFramebufferWidth() const { return fbWidth_; }
    uint16_t getFramebufferHeight() const { return fbHeight_; }
    const PixelFormat& getPixelFormat() const { return pixelFormat_; }
    
    // Callbacks
    using FramebufferUpdateCallback = std::function<void(uint16_t x, uint16_t y, uint16_t w, uint16_t h)>;
    using ConnectionStatusCallback = std::function<void(bool connected, const std::string& message)>;
    using ClipboardCallback = std::function<void(const std::string& text)>;
    
    void setFramebufferUpdateCallback(FramebufferUpdateCallback cb) { fbUpdateCallback_ = cb; }
    void setConnectionStatusCallback(ConnectionStatusCallback cb) { connectionStatusCallback_ = cb; }
    void setClipboardCallback(ClipboardCallback cb) { clipboardCallback_ = cb; }
    
    // Settings
    void setSupportedEncodings(const std::vector<int32_t>& encodings);
    void setPixelFormat(const PixelFormat& format);
    
    // Connection info
    struct ConnectionInfo {
        std::string host;
        uint16_t port;
        std::string desktopName;
        std::chrono::system_clock::time_point connectedAt;
        bool authenticated;
        size_t bytesReceived;
        size_t bytesSent;
    };
    
    const ConnectionInfo& getConnectionInfo() const { return connectionInfo_; }

private:
    // Network handling
    bool connectSocket(const std::string& host, uint16_t port);
    void closeSocket();
    void receiveData();
    void sendData();
    
    // Protocol handling
    void onFramebufferUpdate(const std::vector<Rectangle>& rectangles, const std::vector<uint8_t>& pixelData);
    void onServerCutText(const std::string& text);
    void onBell();
    
    // Framebuffer management
    void updateFramebuffer(uint16_t x, uint16_t y, uint16_t w, uint16_t h, const uint8_t* pixelData, int32_t encoding);
    void decodeRawEncoding(uint16_t x, uint16_t y, uint16_t w, uint16_t h, const uint8_t* data);
    void decodeRREEncoding(uint16_t x, uint16_t y, uint16_t w, uint16_t h, const uint8_t* data);
    
    // Member variables
    std::atomic<bool> connected_;
    std::atomic<bool> running_;
    
    int socket_;
    std::unique_ptr<RFBClient> protocol_;
    
    std::thread receiveThread_;
    std::thread sendThread_;
    
    // Framebuffer
    std::vector<uint8_t> framebuffer_;
    uint16_t fbWidth_;
    uint16_t fbHeight_;
    PixelFormat pixelFormat_;
    
    // Connection info
    ConnectionInfo connectionInfo_;
    
    // Settings
    std::string password_;
    std::vector<int32_t> supportedEncodings_;
    
    // Callbacks
    FramebufferUpdateCallback fbUpdateCallback_;
    ConnectionStatusCallback connectionStatusCallback_;
    ClipboardCallback clipboardCallback_;
    
    // Synchronization
    std::mutex framebufferMutex_;
    std::mutex sendMutex_;
};

} // namespace vnc

#endif // VNC_CLIENT_H