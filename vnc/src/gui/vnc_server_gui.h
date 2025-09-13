#ifndef VNC_SERVER_GUI_H
#define VNC_SERVER_GUI_H

#include "../server/vnc_server.h"
#include <memory>
#include <string>
#include <functional>

namespace vnc {

class VNCServerGUI {
public:
    VNCServerGUI();
    ~VNCServerGUI();

    // GUI lifecycle
    bool initialize();
    void run();
    void shutdown();

    // Server control
    void startServer();
    void stopServer();
    bool isServerRunning() const;

    // Configuration
    void setServerPort(uint16_t port);
    void setServerPassword(const std::string& password);
    void setDesktopName(const std::string& name);
    void enableTLS(bool enable);

    // Status and monitoring
    struct ServerStatus {
        bool running;
        uint16_t port;
        std::string desktopName;
        size_t connectedClients;
        std::chrono::system_clock::time_point startTime;
        size_t totalConnections;
        size_t bytesTransferred;
    };

    ServerStatus getServerStatus() const;

    // Callbacks
    using StatusUpdateCallback = std::function<void(const ServerStatus& status)>;
    using ClientConnectedCallback = std::function<void(const VNCServer::ClientInfo& client)>;
    using ClientDisconnectedCallback = std::function<void(const std::string& address)>;

    void setStatusUpdateCallback(StatusUpdateCallback cb) { statusUpdateCallback_ = cb; }
    void setClientConnectedCallback(ClientConnectedCallback cb) { clientConnectedCallback_ = cb; }
    void setClientDisconnectedCallback(ClientDisconnectedCallback cb) { clientDisconnectedCallback_ = cb; }

private:
    // GUI implementation
    void createMainWindow();
    void createServerConfigPanel();
    void createClientMonitorPanel();
    void createLogPanel();
    void updateStatus();

    // Event handlers
    void onStartStopClicked();
    void onConfigChanged();
    void onClientDisconnect(const std::string& address);

    std::unique_ptr<VNCServer> server_;
    
    // Configuration
    uint16_t serverPort_;
    std::string serverPassword_;
    std::string desktopName_;
    bool tlsEnabled_;
    
    // Status
    ServerStatus status_;
    
    // Callbacks
    StatusUpdateCallback statusUpdateCallback_;
    ClientConnectedCallback clientConnectedCallback_;
    ClientDisconnectedCallback clientDisconnectedCallback_;
    
    // GUI state
    bool guiInitialized_;
};

// Simple console-based GUI for demonstration
class VNCServerConsoleGUI {
public:
    VNCServerConsoleGUI();
    ~VNCServerConsoleGUI();
    
    void run();
    
private:
    void showMenu();
    void handleUserInput();
    void configureServer();
    void showStatus();
    void showConnectedClients();
    void showLogs();
    
    std::unique_ptr<VNCServer> server_;
    bool running_;
};

} // namespace vnc

#endif // VNC_SERVER_GUI_H