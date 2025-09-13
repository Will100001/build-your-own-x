#ifndef VNC_SERVER_H
#define VNC_SERVER_H

#include "../common/rfb_protocol.h"
#include <thread>
#include <atomic>
#include <memory>
#include <vector>
#include <mutex>

namespace vnc {

// Forward declarations
class ScreenCapture;
class InputSimulator;
class NetworkServer;

class VNCServer {
public:
    VNCServer();
    ~VNCServer();

    // Server control
    bool start(uint16_t port = RFB_DEFAULT_PORT);
    void stop();
    bool isRunning() const { return running_; }

    // Configuration
    void setPassword(const std::string& password);
    void setDesktopName(const std::string& name);
    void enableTLS(bool enable);
    
    // Screen settings
    void setScreenSize(uint16_t width, uint16_t height);
    void setPixelFormat(const PixelFormat& format);
    
    // Client management
    struct ClientInfo {
        std::string address;
        uint16_t port;
        std::chrono::system_clock::time_point connectedAt;
        bool authenticated;
    };
    
    std::vector<ClientInfo> getConnectedClients() const;
    void disconnectClient(const std::string& address);

private:
    // Client connection handling
    class ClientConnection {
    public:
        ClientConnection(int socket, VNCServer* server);
        ~ClientConnection();
        
        void start();
        void stop();
        bool isActive() const { return active_; }
        const ClientInfo& getInfo() const { return info_; }
        
    private:
        void handleConnection();
        void sendFramebufferUpdate();
        void onKeyEvent(uint32_t key, bool down);
        void onPointerEvent(uint16_t x, uint16_t y, uint8_t buttons);
        
        int socket_;
        VNCServer* server_;
        std::unique_ptr<RFBServer> protocol_;
        std::thread connectionThread_;
        std::atomic<bool> active_;
        ClientInfo info_;
        std::mutex sendMutex_;
    };

    // Network handling
    void acceptConnections();
    void cleanupConnections();
    
    // Screen capture and input
    void captureScreen();
    void simulateInput();
    
    // Member variables
    std::atomic<bool> running_;
    std::unique_ptr<NetworkServer> networkServer_;
    std::unique_ptr<ScreenCapture> screenCapture_;
    std::unique_ptr<InputSimulator> inputSimulator_;
    
    std::thread acceptThread_;
    std::thread captureThread_;
    
    std::vector<std::unique_ptr<ClientConnection>> clients_;
    mutable std::mutex clientsMutex_;
    
    // Configuration
    std::string password_;
    std::string desktopName_;
    bool tlsEnabled_;
    uint16_t screenWidth_;
    uint16_t screenHeight_;
    PixelFormat pixelFormat_;
    
    // Screen data
    std::vector<uint8_t> screenBuffer_;
    std::vector<uint8_t> previousScreenBuffer_;
    mutable std::mutex screenMutex_;
    
    // Update tracking
    std::atomic<bool> screenChanged_;
    std::vector<Rectangle> dirtyRegions_;
    mutable std::mutex dirtyMutex_;
};

// Network server abstraction
class NetworkServer {
public:
    NetworkServer();
    ~NetworkServer();
    
    bool bind(uint16_t port);
    void close();
    int acceptConnection();
    
private:
    int serverSocket_;
    uint16_t port_;
};

// Screen capture abstraction
class ScreenCapture {
public:
    virtual ~ScreenCapture() = default;
    
    virtual bool initialize() = 0;
    virtual bool captureFrame(std::vector<uint8_t>& buffer, uint16_t& width, uint16_t& height) = 0;
    virtual void cleanup() = 0;
    
    static std::unique_ptr<ScreenCapture> create();
};

// Input simulation abstraction
class InputSimulator {
public:
    virtual ~InputSimulator() = default;
    
    virtual bool initialize() = 0;
    virtual void simulateKeyPress(uint32_t key, bool down) = 0;
    virtual void simulateMouseMove(uint16_t x, uint16_t y) = 0;
    virtual void simulateMouseClick(uint16_t x, uint16_t y, uint8_t buttons) = 0;
    virtual void cleanup() = 0;
    
    static std::unique_ptr<InputSimulator> create();
};

} // namespace vnc

#endif // VNC_SERVER_H