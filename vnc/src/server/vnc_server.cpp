#include "vnc_server.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <algorithm>
#include <iostream>
#include <cstring>

namespace vnc {

VNCServer::VNCServer() 
    : running_(false)
    , tlsEnabled_(false)
    , screenWidth_(1024)
    , screenHeight_(768)
    , screenChanged_(false)
    , desktopName_("VNC Desktop")
{
    // Initialize default pixel format
    pixelFormat_.bitsPerPixel = 32;
    pixelFormat_.depth = 24;
    pixelFormat_.bigEndianFlag = 0;
    pixelFormat_.trueColourFlag = 1;
    pixelFormat_.redMax = 255;
    pixelFormat_.greenMax = 255;
    pixelFormat_.blueMax = 255;
    pixelFormat_.redShift = 16;
    pixelFormat_.greenShift = 8;
    pixelFormat_.blueShift = 0;
    
    networkServer_ = std::make_unique<NetworkServer>();
    screenCapture_ = ScreenCapture::create();
    inputSimulator_ = InputSimulator::create();
}

VNCServer::~VNCServer() {
    stop();
}

bool VNCServer::start(uint16_t port) {
    if (running_) return false;
    
    // Initialize screen capture
    if (!screenCapture_->initialize()) {
        std::cerr << "Failed to initialize screen capture" << std::endl;
        return false;
    }
    
    // Initialize input simulator
    if (!inputSimulator_->initialize()) {
        std::cerr << "Failed to initialize input simulator" << std::endl;
        return false;
    }
    
    // Start network server
    if (!networkServer_->bind(port)) {
        std::cerr << "Failed to bind to port " << port << std::endl;
        return false;
    }
    
    running_ = true;
    
    // Start threads
    acceptThread_ = std::thread(&VNCServer::acceptConnections, this);
    captureThread_ = std::thread(&VNCServer::captureScreen, this);
    
    std::cout << "VNC Server started on port " << port << std::endl;
    return true;
}

void VNCServer::stop() {
    if (!running_) return;
    
    running_ = false;
    
    // Close network server
    networkServer_->close();
    
    // Wait for threads
    if (acceptThread_.joinable()) {
        acceptThread_.join();
    }
    if (captureThread_.joinable()) {
        captureThread_.join();
    }
    
    // Cleanup clients
    cleanupConnections();
    
    // Cleanup resources
    screenCapture_->cleanup();
    inputSimulator_->cleanup();
    
    std::cout << "VNC Server stopped" << std::endl;
}

void VNCServer::setPassword(const std::string& password) {
    password_ = password;
}

void VNCServer::setDesktopName(const std::string& name) {
    desktopName_ = name;
}

void VNCServer::enableTLS(bool enable) {
    tlsEnabled_ = enable;
}

void VNCServer::setScreenSize(uint16_t width, uint16_t height) {
    screenWidth_ = width;
    screenHeight_ = height;
    
    // Resize screen buffers
    std::lock_guard<std::mutex> lock(screenMutex_);
    size_t bufferSize = width * height * (pixelFormat_.bitsPerPixel / 8);
    screenBuffer_.resize(bufferSize);
    previousScreenBuffer_.resize(bufferSize);
}

void VNCServer::setPixelFormat(const PixelFormat& format) {
    pixelFormat_ = format;
    setScreenSize(screenWidth_, screenHeight_); // Resize buffers
}

std::vector<VNCServer::ClientInfo> VNCServer::getConnectedClients() const {
    std::lock_guard<std::mutex> lock(clientsMutex_);
    std::vector<ClientInfo> result;
    
    for (const auto& client : clients_) {
        if (client->isActive()) {
            result.push_back(client->getInfo());
        }
    }
    
    return result;
}

void VNCServer::disconnectClient(const std::string& address) {
    std::lock_guard<std::mutex> lock(clientsMutex_);
    
    for (auto& client : clients_) {
        if (client->getInfo().address == address) {
            client->stop();
        }
    }
}

void VNCServer::acceptConnections() {
    while (running_) {
        int clientSocket = networkServer_->acceptConnection();
        if (clientSocket < 0) {
            if (running_) {
                std::cerr << "Failed to accept connection" << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
            continue;
        }
        
        std::cout << "New client connection accepted" << std::endl;
        
        // Create new client connection
        auto client = std::make_unique<ClientConnection>(clientSocket, this);
        client->start();
        
        {
            std::lock_guard<std::mutex> lock(clientsMutex_);
            clients_.push_back(std::move(client));
        }
        
        // Cleanup inactive connections periodically
        cleanupConnections();
    }
}

void VNCServer::cleanupConnections() {
    std::lock_guard<std::mutex> lock(clientsMutex_);
    
    clients_.erase(
        std::remove_if(clients_.begin(), clients_.end(),
            [](const std::unique_ptr<ClientConnection>& client) {
                return !client->isActive();
            }),
        clients_.end()
    );
}

void VNCServer::captureScreen() {
    while (running_) {
        uint16_t width, height;
        std::vector<uint8_t> newBuffer;
        
        if (screenCapture_->captureFrame(newBuffer, width, height)) {
            std::lock_guard<std::mutex> lock(screenMutex_);
            
            // Check if screen changed
            if (newBuffer != previousScreenBuffer_) {
                screenBuffer_ = newBuffer;
                previousScreenBuffer_ = screenBuffer_;
                screenChanged_ = true;
                
                // For simplicity, mark entire screen as dirty
                // In a real implementation, you'd do region-based change detection
                std::lock_guard<std::mutex> dirtyLock(dirtyMutex_);
                dirtyRegions_.clear();
                Rectangle fullScreen;
                fullScreen.x = 0;
                fullScreen.y = 0;
                fullScreen.width = width;
                fullScreen.height = height;
                fullScreen.encoding = RAW;
                dirtyRegions_.push_back(fullScreen);
            }
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(33)); // ~30 FPS
    }
}

// ClientConnection implementation
VNCServer::ClientConnection::ClientConnection(int socket, VNCServer* server)
    : socket_(socket)
    , server_(server)
    , active_(false)
{
    protocol_ = std::make_unique<RFBServer>();
    
    // Get client address
    struct sockaddr_in clientAddr;
    socklen_t addrLen = sizeof(clientAddr);
    if (getpeername(socket, (struct sockaddr*)&clientAddr, &addrLen) == 0) {
        info_.address = inet_ntoa(clientAddr.sin_addr);
        info_.port = ntohs(clientAddr.sin_port);
    }
    info_.connectedAt = std::chrono::system_clock::now();
    info_.authenticated = false;
    
    // Set up protocol callbacks
    protocol_->setPassword(server_->password_);
    protocol_->setFramebufferSize(server_->screenWidth_, server_->screenHeight_);
    protocol_->setPixelFormat(server_->pixelFormat_);
    
    protocol_->setFramebufferUpdateCallback(
        [this](uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
            sendFramebufferUpdate();
        });
    
    protocol_->setKeyEventCallback(
        [this](uint32_t key, bool down) {
            onKeyEvent(key, down);
        });
    
    protocol_->setPointerEventCallback(
        [this](uint16_t x, uint16_t y, uint8_t buttons) {
            onPointerEvent(x, y, buttons);
        });
}

VNCServer::ClientConnection::~ClientConnection() {
    stop();
}

void VNCServer::ClientConnection::start() {
    active_ = true;
    connectionThread_ = std::thread(&ClientConnection::handleConnection, this);
}

void VNCServer::ClientConnection::stop() {
    if (active_) {
        active_ = false;
        if (socket_ >= 0) {
            close(socket_);
            socket_ = -1;
        }
        if (connectionThread_.joinable()) {
            connectionThread_.join();
        }
    }
}

void VNCServer::ClientConnection::handleConnection() {
    std::vector<uint8_t> buffer(4096);
    
    while (active_) {
        ssize_t bytesRead = recv(socket_, buffer.data(), buffer.size(), 0);
        if (bytesRead <= 0) {
            // Connection closed or error
            break;
        }
        
        // Process incoming data
        if (!protocol_->handleIncomingData(buffer.data(), bytesRead)) {
            std::cerr << "Protocol error" << std::endl;
            break;
        }
        
        // Send any outgoing data
        auto outgoingData = protocol_->getOutgoingData();
        if (!outgoingData.empty()) {
            std::lock_guard<std::mutex> lock(sendMutex_);
            ssize_t bytesSent = send(socket_, outgoingData.data(), outgoingData.size(), 0);
            if (bytesSent != static_cast<ssize_t>(outgoingData.size())) {
                std::cerr << "Failed to send data" << std::endl;
                break;
            }
        }
        
        // Mark as authenticated if we're in normal protocol state
        if (protocol_->getState() == NORMAL && !info_.authenticated) {
            info_.authenticated = true;
            std::cout << "Client " << info_.address << " authenticated" << std::endl;
        }
    }
    
    active_ = false;
    std::cout << "Client " << info_.address << " disconnected" << std::endl;
}

void VNCServer::ClientConnection::sendFramebufferUpdate() {
    if (!info_.authenticated) return;
    
    std::lock_guard<std::mutex> screenLock(server_->screenMutex_);
    std::lock_guard<std::mutex> dirtyLock(server_->dirtyMutex_);
    
    if (server_->dirtyRegions_.empty()) return;
    
    // Send framebuffer update with dirty regions
    protocol_->sendFramebufferUpdate(server_->dirtyRegions_, server_->screenBuffer_);
    
    // Send the data
    auto outgoingData = protocol_->getOutgoingData();
    if (!outgoingData.empty()) {
        std::lock_guard<std::mutex> lock(sendMutex_);
        send(socket_, outgoingData.data(), outgoingData.size(), 0);
    }
}

void VNCServer::ClientConnection::onKeyEvent(uint32_t key, bool down) {
    server_->inputSimulator_->simulateKeyPress(key, down);
}

void VNCServer::ClientConnection::onPointerEvent(uint16_t x, uint16_t y, uint8_t buttons) {
    server_->inputSimulator_->simulateMouseMove(x, y);
    if (buttons != 0) {
        server_->inputSimulator_->simulateMouseClick(x, y, buttons);
    }
}

// NetworkServer implementation
NetworkServer::NetworkServer() : serverSocket_(-1), port_(0) {}

NetworkServer::~NetworkServer() {
    close();
}

bool NetworkServer::bind(uint16_t port) {
    serverSocket_ = socket(AF_INET, SOCK_STREAM, 0);
    if (serverSocket_ < 0) {
        return false;
    }
    
    // Allow socket reuse
    int opt = 1;
    setsockopt(serverSocket_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    struct sockaddr_in serverAddr;
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(port);
    
    if (::bind(serverSocket_, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) < 0) {
        ::close(serverSocket_);
        serverSocket_ = -1;
        return false;
    }
    
    if (listen(serverSocket_, 5) < 0) {
        ::close(serverSocket_);
        serverSocket_ = -1;
        return false;
    }
    
    port_ = port;
    return true;
}

void NetworkServer::close() {
    if (serverSocket_ >= 0) {
        ::close(serverSocket_);
        serverSocket_ = -1;
    }
}

int NetworkServer::acceptConnection() {
    if (serverSocket_ < 0) return -1;
    
    struct sockaddr_in clientAddr;
    socklen_t addrLen = sizeof(clientAddr);
    return accept(serverSocket_, (struct sockaddr*)&clientAddr, &addrLen);
}

} // namespace vnc