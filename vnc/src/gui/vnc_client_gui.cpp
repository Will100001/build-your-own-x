#include "vnc_client_gui.h"
#include <iostream>
#include <iomanip>
#include <thread>
#include <chrono>

namespace vnc {

VNCClientGUI::VNCClientGUI()
    : guiInitialized_(false)
    , connectionDialogOpen_(false)
    , displayWidth_(800)
    , displayHeight_(600)
    , lastHost_("localhost")
    , lastPort_(5900)
{
    client_ = std::make_unique<VNCClient>();
    
    // Initialize default display settings
    displaySettings_.fullscreen = false;
    displaySettings_.fitToWindow = true;
    displaySettings_.scaleFactor = 1.0;
    displaySettings_.showCursor = true;
    displaySettings_.captureMouse = false;
    displaySettings_.captureKeyboard = false;
    
    // Initialize default connection settings
    connectionSettings_.lastHost = "localhost";
    connectionSettings_.lastPort = 5900;
    connectionSettings_.savePassword = false;
    connectionSettings_.preferredEncodings = {RAW, RRE, HEXTILE, ZRLE};
    connectionSettings_.enableClipboard = true;
    connectionSettings_.enableAudio = false;
    
    // Set up client callbacks
    client_->setFramebufferUpdateCallback(
        [this](uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
            onFramebufferUpdate(x, y, w, h);
        });
    
    client_->setConnectionStatusCallback(
        [this](bool connected, const std::string& message) {
            onConnectionStatus(connected, message);
        });
    
    client_->setClipboardCallback(
        [this](const std::string& text) {
            onClipboardUpdate(text);
        });
}

VNCClientGUI::~VNCClientGUI() {
    shutdown();
}

bool VNCClientGUI::initialize() {
    std::cout << "Initializing VNC Client GUI..." << std::endl;
    guiInitialized_ = true;
    return true;
}

void VNCClientGUI::run() {
    if (!guiInitialized_) {
        if (!initialize()) {
            std::cerr << "Failed to initialize GUI" << std::endl;
            return;
        }
    }
    
    std::cout << "VNC Client GUI running" << std::endl;
    
    // Simple main loop for demonstration
    while (true) {
        updateDisplay();
        std::this_thread::sleep_for(std::chrono::milliseconds(16)); // ~60 FPS
        
        // In a real GUI, this would be the message loop
    }
}

void VNCClientGUI::shutdown() {
    if (client_ && client_->isConnected()) {
        client_->disconnect();
    }
    guiInitialized_ = false;
}

void VNCClientGUI::connectToServer(const std::string& host, uint16_t port, const std::string& password) {
    if (client_->isConnected()) {
        client_->disconnect();
    }
    
    if (!password.empty()) {
        client_->setPassword(password);
    }
    
    client_->setSupportedEncodings(connectionSettings_.preferredEncodings);
    
    if (client_->connect(host, port)) {
        connectionSettings_.lastHost = host;
        connectionSettings_.lastPort = port;
        std::cout << "Connecting to " << host << ":" << port << std::endl;
    } else {
        std::cerr << "Failed to connect to " << host << ":" << port << std::endl;
    }
}

void VNCClientGUI::disconnect() {
    if (client_) {
        client_->disconnect();
    }
}

bool VNCClientGUI::isConnected() const {
    return client_ && client_->isConnected();
}

void VNCClientGUI::renderFramebuffer() {
    if (!client_ || !client_->isConnected()) return;
    
    const auto& framebuffer = client_->getFramebuffer();
    if (framebuffer.empty()) return;
    
    // In a real implementation, this would render to the screen
    // For now, just log the framebuffer info
    std::cout << "Rendering framebuffer: " << client_->getFramebufferWidth() 
              << "x" << client_->getFramebufferHeight() 
              << " (" << framebuffer.size() << " bytes)" << std::endl;
}

void VNCClientGUI::handleKeyInput(uint32_t key, bool down) {
    if (client_ && client_->isConnected()) {
        client_->sendKeyEvent(key, down);
    }
}

void VNCClientGUI::handleMouseInput(uint16_t x, uint16_t y, uint8_t buttons) {
    if (client_ && client_->isConnected()) {
        client_->sendPointerEvent(x, y, buttons);
    }
}

void VNCClientGUI::setDisplaySettings(const DisplaySettings& settings) {
    displaySettings_ = settings;
    updateDisplay();
}

void VNCClientGUI::setConnectionSettings(const ConnectionSettings& settings) {
    connectionSettings_ = settings;
}

void VNCClientGUI::onFramebufferUpdate(uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
    if (fbUpdateCallback_) {
        fbUpdateCallback_();
    }
}

void VNCClientGUI::onConnectionStatus(bool connected, const std::string& message) {
    currentStatus_ = message;
    
    if (statusUpdateCallback_) {
        statusUpdateCallback_(connected, message);
    }
    
    std::cout << "Connection status: " << (connected ? "Connected" : "Disconnected") 
              << " - " << message << std::endl;
}

void VNCClientGUI::onClipboardUpdate(const std::string& text) {
    std::cout << "Clipboard updated: " << text << std::endl;
}

void VNCClientGUI::updateDisplay() {
    if (client_ && client_->isConnected()) {
        renderFramebuffer();
    }
}

// Console GUI Implementation
VNCClientConsoleGUI::VNCClientConsoleGUI() 
    : running_(true)
    , lastHost_("localhost")
    , lastPort_(5900)
{
    client_ = std::make_unique<VNCClient>();
    
    // Set up callbacks
    client_->setConnectionStatusCallback(
        [](bool connected, const std::string& message) {
            std::cout << "\nConnection status: " << (connected ? "Connected" : "Disconnected") 
                      << " - " << message << std::endl;
        });
    
    client_->setFramebufferUpdateCallback(
        [](uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
            std::cout << "Screen updated: " << x << "," << y << " " << w << "x" << h << std::endl;
        });
}

VNCClientConsoleGUI::~VNCClientConsoleGUI() {
    if (client_ && client_->isConnected()) {
        client_->disconnect();
    }
}

void VNCClientConsoleGUI::run() {
    std::cout << "\n=== VNC Client Console Interface ===" << std::endl;
    std::cout << "Welcome to the VNC Client!" << std::endl;
    
    while (running_) {
        showMenu();
        handleUserInput();
    }
}

void VNCClientConsoleGUI::showMenu() {
    std::cout << "\n=== VNC Client Control ===" << std::endl;
    std::cout << "1. Connect to Server" << std::endl;
    std::cout << "2. Disconnect" << std::endl;
    std::cout << "3. Show Status" << std::endl;
    std::cout << "4. Show Connection Info" << std::endl;
    std::cout << "5. Simulate Input" << std::endl;
    std::cout << "6. Settings" << std::endl;
    std::cout << "7. Exit" << std::endl;
    std::cout << "\nConnection Status: " << (client_->isConnected() ? "CONNECTED" : "DISCONNECTED") << std::endl;
    std::cout << "Enter your choice (1-7): ";
}

void VNCClientConsoleGUI::handleUserInput() {
    int choice;
    std::cin >> choice;
    
    switch (choice) {
        case 1:
            connectToServer();
            break;
            
        case 2: {
            if (client_->isConnected()) {
                std::cout << "Disconnecting..." << std::endl;
                client_->disconnect();
                std::cout << "Disconnected." << std::endl;
            } else {
                std::cout << "Not connected!" << std::endl;
            }
            break;
        }
        
        case 3:
            showStatus();
            break;
            
        case 4:
            showConnectionInfo();
            break;
            
        case 5:
            simulateInput();
            break;
            
        case 6:
            showSettings();
            break;
            
        case 7:
            std::cout << "Exiting..." << std::endl;
            if (client_->isConnected()) {
                client_->disconnect();
            }
            running_ = false;
            break;
            
        default:
            std::cout << "Invalid choice! Please enter 1-7." << std::endl;
            break;
    }
}

void VNCClientConsoleGUI::connectToServer() {
    std::cout << "\n=== Connect to VNC Server ===" << std::endl;
    
    if (client_->isConnected()) {
        std::cout << "Already connected! Disconnect first." << std::endl;
        return;
    }
    
    std::string host;
    uint16_t port;
    std::string password;
    
    std::cout << "Enter hostname/IP [" << lastHost_ << "]: ";
    std::cin.ignore();
    std::getline(std::cin, host);
    if (host.empty()) host = lastHost_;
    
    std::cout << "Enter port [" << lastPort_ << "]: ";
    std::string portStr;
    std::getline(std::cin, portStr);
    if (portStr.empty()) {
        port = lastPort_;
    } else {
        port = static_cast<uint16_t>(std::stoi(portStr));
    }
    
    std::cout << "Enter password (empty for none): ";
    std::getline(std::cin, password);
    
    lastHost_ = host;
    lastPort_ = port;
    lastPassword_ = password;
    
    std::cout << "Connecting to " << host << ":" << port << "..." << std::endl;
    
    if (!password.empty()) {
        client_->setPassword(password);
    }
    
    if (client_->connect(host, port)) {
        std::cout << "Connection initiated. Check status for updates." << std::endl;
        
        // Request initial screen update
        std::this_thread::sleep_for(std::chrono::seconds(2));
        if (client_->isConnected()) {
            client_->requestFramebufferUpdate();
        }
    } else {
        std::cout << "Failed to connect!" << std::endl;
    }
}

void VNCClientConsoleGUI::showStatus() {
    std::cout << "\n=== Client Status ===" << std::endl;
    std::cout << "Connected: " << (client_->isConnected() ? "YES" : "NO") << std::endl;
    
    if (client_->isConnected()) {
        const auto& info = client_->getConnectionInfo();
        std::cout << "Host: " << info.host << ":" << info.port << std::endl;
        std::cout << "Desktop: " << info.desktopName << std::endl;
        std::cout << "Authenticated: " << (info.authenticated ? "YES" : "NO") << std::endl;
        std::cout << "Bytes Received: " << info.bytesReceived << std::endl;
        std::cout << "Bytes Sent: " << info.bytesSent << std::endl;
        
        std::cout << "Framebuffer: " << client_->getFramebufferWidth() 
                  << "x" << client_->getFramebufferHeight() << std::endl;
    }
}

void VNCClientConsoleGUI::showConnectionInfo() {
    std::cout << "\n=== Connection Information ===" << std::endl;
    
    if (!client_->isConnected()) {
        std::cout << "Not connected." << std::endl;
        return;
    }
    
    const auto& info = client_->getConnectionInfo();
    const auto& pixelFormat = client_->getPixelFormat();
    
    std::cout << "Remote Host: " << info.host << ":" << info.port << std::endl;
    std::cout << "Desktop Name: " << info.desktopName << std::endl;
    std::cout << "Screen Size: " << client_->getFramebufferWidth() 
              << "x" << client_->getFramebufferHeight() << std::endl;
    std::cout << "Pixel Format: " << static_cast<int>(pixelFormat.bitsPerPixel) 
              << " bits/pixel, depth " << static_cast<int>(pixelFormat.depth) << std::endl;
    std::cout << "Data Transfer: " << info.bytesReceived << " received, " 
              << info.bytesSent << " sent" << std::endl;
    
    auto timeT = std::chrono::system_clock::to_time_t(info.connectedAt);
    std::cout << "Connected At: " << std::put_time(std::localtime(&timeT), "%Y-%m-%d %H:%M:%S") << std::endl;
}

void VNCClientConsoleGUI::simulateInput() {
    std::cout << "\n=== Simulate Input ===" << std::endl;
    
    if (!client_->isConnected()) {
        std::cout << "Not connected!" << std::endl;
        return;
    }
    
    std::cout << "1. Send Key Event" << std::endl;
    std::cout << "2. Send Mouse Click" << std::endl;
    std::cout << "3. Send Mouse Move" << std::endl;
    std::cout << "4. Send Text" << std::endl;
    std::cout << "Enter choice (1-4): ";
    
    int choice;
    std::cin >> choice;
    
    switch (choice) {
        case 1: {
            uint32_t key;
            std::cout << "Enter key code (e.g., 65 for 'A'): ";
            std::cin >> key;
            
            client_->sendKeyEvent(key, true);  // Key down
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
            client_->sendKeyEvent(key, false); // Key up
            
            std::cout << "Key event sent: " << key << std::endl;
            break;
        }
        
        case 2: {
            uint16_t x, y;
            std::cout << "Enter X coordinate: ";
            std::cin >> x;
            std::cout << "Enter Y coordinate: ";
            std::cin >> y;
            
            client_->sendPointerEvent(x, y, 0x01); // Left click
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
            client_->sendPointerEvent(x, y, 0x00); // Release
            
            std::cout << "Mouse click sent at (" << x << "," << y << ")" << std::endl;
            break;
        }
        
        case 3: {
            uint16_t x, y;
            std::cout << "Enter X coordinate: ";
            std::cin >> x;
            std::cout << "Enter Y coordinate: ";
            std::cin >> y;
            
            client_->sendPointerEvent(x, y, 0x00);
            
            std::cout << "Mouse moved to (" << x << "," << y << ")" << std::endl;
            break;
        }
        
        case 4: {
            std::string text;
            std::cout << "Enter text to send: ";
            std::cin.ignore();
            std::getline(std::cin, text);
            
            // Send each character as key events
            for (char c : text) {
                uint32_t key = static_cast<uint32_t>(c);
                client_->sendKeyEvent(key, true);
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
                client_->sendKeyEvent(key, false);
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
            
            std::cout << "Text sent: " << text << std::endl;
            break;
        }
        
        default:
            std::cout << "Invalid choice!" << std::endl;
            break;
    }
}

void VNCClientConsoleGUI::showSettings() {
    std::cout << "\n=== Client Settings ===" << std::endl;
    std::cout << "Last Host: " << lastHost_ << ":" << lastPort_ << std::endl;
    std::cout << "Supported Encodings: RAW, RRE, HEXTILE, ZRLE" << std::endl;
    std::cout << "Settings modification not implemented in this demo." << std::endl;
}

} // namespace vnc