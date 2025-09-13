#include "vnc_server_gui.h"
#include <iostream>
#include <iomanip>
#include <sstream>
#include <thread>
#include <chrono>

namespace vnc {

VNCServerGUI::VNCServerGUI()
    : serverPort_(5900)
    , tlsEnabled_(false)
    , guiInitialized_(false)
    , desktopName_("VNC Desktop")
{
    server_ = std::make_unique<VNCServer>();
    
    status_.running = false;
    status_.port = serverPort_;
    status_.desktopName = desktopName_;
    status_.connectedClients = 0;
    status_.totalConnections = 0;
    status_.bytesTransferred = 0;
}

VNCServerGUI::~VNCServerGUI() {
    shutdown();
}

bool VNCServerGUI::initialize() {
    std::cout << "Initializing VNC Server GUI..." << std::endl;
    guiInitialized_ = true;
    return true;
}

void VNCServerGUI::run() {
    if (!guiInitialized_) {
        if (!initialize()) {
            std::cerr << "Failed to initialize GUI" << std::endl;
            return;
        }
    }
    
    std::cout << "VNC Server GUI running" << std::endl;
    
    // Simple main loop for demonstration
    while (true) {
        updateStatus();
        std::this_thread::sleep_for(std::chrono::seconds(1));
        
        // In a real GUI, this would be the message loop
        // For now, just update status periodically
    }
}

void VNCServerGUI::shutdown() {
    if (server_ && server_->isRunning()) {
        server_->stop();
    }
    guiInitialized_ = false;
}

void VNCServerGUI::startServer() {
    if (server_ && !server_->isRunning()) {
        server_->setPassword(serverPassword_);
        server_->setDesktopName(desktopName_);
        server_->enableTLS(tlsEnabled_);
        
        if (server_->start(serverPort_)) {
            status_.running = true;
            status_.startTime = std::chrono::system_clock::now();
            std::cout << "VNC Server started on port " << serverPort_ << std::endl;
        } else {
            std::cerr << "Failed to start VNC Server" << std::endl;
        }
    }
}

void VNCServerGUI::stopServer() {
    if (server_ && server_->isRunning()) {
        server_->stop();
        status_.running = false;
        std::cout << "VNC Server stopped" << std::endl;
    }
}

bool VNCServerGUI::isServerRunning() const {
    return server_ && server_->isRunning();
}

void VNCServerGUI::setServerPort(uint16_t port) {
    serverPort_ = port;
    status_.port = port;
}

void VNCServerGUI::setServerPassword(const std::string& password) {
    serverPassword_ = password;
}

void VNCServerGUI::setDesktopName(const std::string& name) {
    desktopName_ = name;
    status_.desktopName = name;
}

void VNCServerGUI::enableTLS(bool enable) {
    tlsEnabled_ = enable;
}

VNCServerGUI::ServerStatus VNCServerGUI::getServerStatus() const {
    return status_;
}

void VNCServerGUI::updateStatus() {
    if (server_) {
        status_.running = server_->isRunning();
        
        if (status_.running) {
            auto clients = server_->getConnectedClients();
            status_.connectedClients = clients.size();
            
            // In a real implementation, you'd track these stats
            // status_.totalConnections += newConnections;
            // status_.bytesTransferred += newBytes;
        }
    }
    
    if (statusUpdateCallback_) {
        statusUpdateCallback_(status_);
    }
}

// Console GUI Implementation
VNCServerConsoleGUI::VNCServerConsoleGUI() 
    : running_(true)
{
    server_ = std::make_unique<VNCServer>();
}

VNCServerConsoleGUI::~VNCServerConsoleGUI() {
    if (server_ && server_->isRunning()) {
        server_->stop();
    }
}

void VNCServerConsoleGUI::run() {
    std::cout << "\n=== VNC Server Console Interface ===" << std::endl;
    std::cout << "Welcome to the VNC Server management console!" << std::endl;
    
    while (running_) {
        showMenu();
        handleUserInput();
    }
}

void VNCServerConsoleGUI::showMenu() {
    std::cout << "\n=== VNC Server Control ===" << std::endl;
    std::cout << "1. Start Server" << std::endl;
    std::cout << "2. Stop Server" << std::endl;
    std::cout << "3. Configure Server" << std::endl;
    std::cout << "4. Show Status" << std::endl;
    std::cout << "5. Show Connected Clients" << std::endl;
    std::cout << "6. Show Logs" << std::endl;
    std::cout << "7. Exit" << std::endl;
    std::cout << "\nServer Status: " << (server_->isRunning() ? "RUNNING" : "STOPPED") << std::endl;
    std::cout << "Enter your choice (1-7): ";
}

void VNCServerConsoleGUI::handleUserInput() {
    int choice;
    std::cin >> choice;
    
    switch (choice) {
        case 1: {
            if (!server_->isRunning()) {
                std::cout << "Starting VNC Server..." << std::endl;
                if (server_->start()) {
                    std::cout << "VNC Server started successfully!" << std::endl;
                } else {
                    std::cout << "Failed to start VNC Server!" << std::endl;
                }
            } else {
                std::cout << "Server is already running!" << std::endl;
            }
            break;
        }
        
        case 2: {
            if (server_->isRunning()) {
                std::cout << "Stopping VNC Server..." << std::endl;
                server_->stop();
                std::cout << "VNC Server stopped." << std::endl;
            } else {
                std::cout << "Server is not running!" << std::endl;
            }
            break;
        }
        
        case 3:
            configureServer();
            break;
            
        case 4:
            showStatus();
            break;
            
        case 5:
            showConnectedClients();
            break;
            
        case 6:
            showLogs();
            break;
            
        case 7:
            std::cout << "Exiting..." << std::endl;
            if (server_->isRunning()) {
                server_->stop();
            }
            running_ = false;
            break;
            
        default:
            std::cout << "Invalid choice! Please enter 1-7." << std::endl;
            break;
    }
}

void VNCServerConsoleGUI::configureServer() {
    std::cout << "\n=== Server Configuration ===" << std::endl;
    
    if (server_->isRunning()) {
        std::cout << "Please stop the server before changing configuration." << std::endl;
        return;
    }
    
    std::cout << "1. Set Port (current: 5900)" << std::endl;
    std::cout << "2. Set Password" << std::endl;
    std::cout << "3. Set Desktop Name" << std::endl;
    std::cout << "4. Enable/Disable TLS" << std::endl;
    std::cout << "5. Return to main menu" << std::endl;
    std::cout << "Enter your choice (1-5): ";
    
    int choice;
    std::cin >> choice;
    
    switch (choice) {
        case 1: {
            uint16_t port;
            std::cout << "Enter new port: ";
            std::cin >> port;
            std::cout << "Port set to: " << port << std::endl;
            break;
        }
        
        case 2: {
            std::string password;
            std::cout << "Enter password (empty for no password): ";
            std::cin.ignore();
            std::getline(std::cin, password);
            server_->setPassword(password);
            std::cout << "Password " << (password.empty() ? "cleared" : "set") << std::endl;
            break;
        }
        
        case 3: {
            std::string name;
            std::cout << "Enter desktop name: ";
            std::cin.ignore();
            std::getline(std::cin, name);
            server_->setDesktopName(name);
            std::cout << "Desktop name set to: " << name << std::endl;
            break;
        }
        
        case 4: {
            char enable;
            std::cout << "Enable TLS? (y/n): ";
            std::cin >> enable;
            bool tlsEnabled = (enable == 'y' || enable == 'Y');
            server_->enableTLS(tlsEnabled);
            std::cout << "TLS " << (tlsEnabled ? "enabled" : "disabled") << std::endl;
            break;
        }
        
        case 5:
            break;
            
        default:
            std::cout << "Invalid choice!" << std::endl;
            break;
    }
}

void VNCServerConsoleGUI::showStatus() {
    std::cout << "\n=== Server Status ===" << std::endl;
    std::cout << "Running: " << (server_->isRunning() ? "YES" : "NO") << std::endl;
    
    if (server_->isRunning()) {
        auto clients = server_->getConnectedClients();
        std::cout << "Connected Clients: " << clients.size() << std::endl;
        std::cout << "Port: 5900" << std::endl;
        std::cout << "Desktop Name: VNC Desktop" << std::endl;
    }
}

void VNCServerConsoleGUI::showConnectedClients() {
    std::cout << "\n=== Connected Clients ===" << std::endl;
    
    if (!server_->isRunning()) {
        std::cout << "Server is not running." << std::endl;
        return;
    }
    
    auto clients = server_->getConnectedClients();
    
    if (clients.empty()) {
        std::cout << "No clients connected." << std::endl;
        return;
    }
    
    std::cout << std::left << std::setw(20) << "Address" 
              << std::setw(8) << "Port" 
              << std::setw(12) << "Auth" 
              << "Connected At" << std::endl;
    std::cout << std::string(60, '-') << std::endl;
    
    for (const auto& client : clients) {
        auto timeT = std::chrono::system_clock::to_time_t(client.connectedAt);
        std::stringstream timeStr;
        timeStr << std::put_time(std::localtime(&timeT), "%Y-%m-%d %H:%M:%S");
        
        std::cout << std::left << std::setw(20) << client.address
                  << std::setw(8) << client.port
                  << std::setw(12) << (client.authenticated ? "YES" : "NO")
                  << timeStr.str() << std::endl;
    }
}

void VNCServerConsoleGUI::showLogs() {
    std::cout << "\n=== Server Logs ===" << std::endl;
    std::cout << "Log functionality not implemented in this demo." << std::endl;
    std::cout << "In a full implementation, this would show:" << std::endl;
    std::cout << "- Connection events" << std::endl;
    std::cout << "- Authentication attempts" << std::endl;
    std::cout << "- Error messages" << std::endl;
    std::cout << "- Performance statistics" << std::endl;
}

} // namespace vnc