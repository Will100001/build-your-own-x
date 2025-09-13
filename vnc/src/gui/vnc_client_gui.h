#ifndef VNC_CLIENT_GUI_H
#define VNC_CLIENT_GUI_H

#include "../client/vnc_client.h"
#include <memory>
#include <string>
#include <functional>

namespace vnc {

class VNCClientGUI {
public:
    VNCClientGUI();
    ~VNCClientGUI();

    // GUI lifecycle
    bool initialize();
    void run();
    void shutdown();

    // Connection management
    void connectToServer(const std::string& host, uint16_t port, const std::string& password = "");
    void disconnect();
    bool isConnected() const;

    // Display and interaction
    void renderFramebuffer();
    void handleKeyInput(uint32_t key, bool down);
    void handleMouseInput(uint16_t x, uint16_t y, uint8_t buttons);

    // Configuration
    struct DisplaySettings {
        bool fullscreen;
        bool fitToWindow;
        double scaleFactor;
        bool showCursor;
        bool captureMouse;
        bool captureKeyboard;
    };

    void setDisplaySettings(const DisplaySettings& settings);
    const DisplaySettings& getDisplaySettings() const { return displaySettings_; }

    // Connection settings
    struct ConnectionSettings {
        std::string lastHost;
        uint16_t lastPort;
        bool savePassword;
        std::vector<int32_t> preferredEncodings;
        bool enableClipboard;
        bool enableAudio;
    };

    void setConnectionSettings(const ConnectionSettings& settings);
    const ConnectionSettings& getConnectionSettings() const { return connectionSettings_; }

    // Callbacks
    using StatusUpdateCallback = std::function<void(bool connected, const std::string& message)>;
    using FramebufferUpdateCallback = std::function<void()>;

    void setStatusUpdateCallback(StatusUpdateCallback cb) { statusUpdateCallback_ = cb; }
    void setFramebufferUpdateCallback(FramebufferUpdateCallback cb) { fbUpdateCallback_ = cb; }

private:
    // GUI implementation
    void createMainWindow();
    void createConnectionDialog();
    void createDisplayArea();
    void createMenuBar();
    void createStatusBar();

    // Event handlers
    void onConnect();
    void onDisconnect();
    void onFramebufferUpdate(uint16_t x, uint16_t y, uint16_t w, uint16_t h);
    void onConnectionStatus(bool connected, const std::string& message);
    void onClipboardUpdate(const std::string& text);

    // Display management
    void updateDisplay();
    void scaleFramebuffer();
    void handleWindowResize();

    std::unique_ptr<VNCClient> client_;
    
    // Settings
    DisplaySettings displaySettings_;
    ConnectionSettings connectionSettings_;
    
    // State
    bool guiInitialized_;
    bool connectionDialogOpen_;
    std::string currentStatus_;
    
    // Callbacks
    StatusUpdateCallback statusUpdateCallback_;
    FramebufferUpdateCallback fbUpdateCallback_;
    
    // Display data
    std::vector<uint8_t> scaledFramebuffer_;
    uint16_t displayWidth_;
    uint16_t displayHeight_;
};

// Simple console-based client for demonstration
class VNCClientConsoleGUI {
public:
    VNCClientConsoleGUI();
    ~VNCClientConsoleGUI();
    
    void run();
    
private:
    void showMenu();
    void handleUserInput();
    void connectToServer();
    void showStatus();
    void showConnectionInfo();
    void simulateInput();
    void showSettings();
    
    std::unique_ptr<VNCClient> client_;
    bool running_;
    std::string lastHost_;
    uint16_t lastPort_;
    std::string lastPassword_;
};

} // namespace vnc

#endif // VNC_CLIENT_GUI_H