#include "vnc_client.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netdb.h>
#include <iostream>
#include <cstring>

namespace vnc {

VNCClient::VNCClient()
    : connected_(false)
    , running_(false)
    , socket_(-1)
    , fbWidth_(0)
    , fbHeight_(0)
{
    protocol_ = std::make_unique<RFBClient>();
    
    // Set default supported encodings
    supportedEncodings_ = {RAW, RRE, HEXTILE, ZRLE, CURSOR, DESKTOP_SIZE};
    
    connectionInfo_.host = "";
    connectionInfo_.port = 0;
    connectionInfo_.authenticated = false;
    connectionInfo_.bytesReceived = 0;
    connectionInfo_.bytesSent = 0;
}

VNCClient::~VNCClient() {
    disconnect();
}

bool VNCClient::connect(const std::string& host, uint16_t port) {
    if (connected_) {
        return false;
    }
    
    if (!connectSocket(host, port)) {
        return false;
    }
    
    connectionInfo_.host = host;
    connectionInfo_.port = port;
    connectionInfo_.connectedAt = std::chrono::system_clock::now();
    connectionInfo_.authenticated = false;
    connectionInfo_.bytesReceived = 0;
    connectionInfo_.bytesSent = 0;
    
    protocol_->setPassword(password_);
    
    connected_ = true;
    running_ = true;
    
    // Start communication threads
    receiveThread_ = std::thread(&VNCClient::receiveData, this);
    sendThread_ = std::thread(&VNCClient::sendData, this);
    
    std::cout << "Connected to VNC server at " << host << ":" << port << std::endl;
    
    if (connectionStatusCallback_) {
        connectionStatusCallback_(true, "Connected successfully");
    }
    
    return true;
}

void VNCClient::disconnect() {
    if (!connected_) return;
    
    running_ = false;
    
    // Close socket to unblock threads
    closeSocket();
    
    // Wait for threads to finish
    if (receiveThread_.joinable()) {
        receiveThread_.join();
    }
    if (sendThread_.joinable()) {
        sendThread_.join();
    }
    
    connected_ = false;
    
    std::cout << "Disconnected from VNC server" << std::endl;
    
    if (connectionStatusCallback_) {
        connectionStatusCallback_(false, "Disconnected");
    }
}

void VNCClient::setPassword(const std::string& password) {
    password_ = password;
    if (protocol_) {
        protocol_->setPassword(password);
    }
}

bool VNCClient::authenticate() {
    // Authentication is handled automatically by the protocol
    // This method can be used to check authentication status
    return connectionInfo_.authenticated;
}

void VNCClient::requestFramebufferUpdate(uint16_t x, uint16_t y, uint16_t w, uint16_t h, bool incremental) {
    if (!connected_ || !protocol_) return;
    
    if (w == 0) w = fbWidth_;
    if (h == 0) h = fbHeight_;
    
    protocol_->requestFramebufferUpdate(x, y, w, h, incremental);
}

void VNCClient::sendKeyEvent(uint32_t key, bool down) {
    if (!connected_ || !protocol_) return;
    
    protocol_->sendKeyEvent(key, down);
}

void VNCClient::sendPointerEvent(uint16_t x, uint16_t y, uint8_t buttons) {
    if (!connected_ || !protocol_) return;
    
    protocol_->sendPointerEvent(x, y, buttons);
}

void VNCClient::sendClipboardText(const std::string& text) {
    if (!connected_ || !protocol_) return;
    
    // Build ClientCutText message
    std::vector<uint8_t> message;
    message.push_back(CLIENT_CUT_TEXT);
    message.push_back(0); // padding
    message.push_back(0); // padding
    message.push_back(0); // padding
    
    uint32_t textLength = htonl(static_cast<uint32_t>(text.length()));
    const uint8_t* lengthBytes = reinterpret_cast<const uint8_t*>(&textLength);
    message.insert(message.end(), lengthBytes, lengthBytes + 4);
    message.insert(message.end(), text.begin(), text.end());
    
    // Send via protocol (would need to extend protocol class for this)
    // For now, just log it
    std::cout << "Clipboard text sent: " << text << std::endl;
}

void VNCClient::setSupportedEncodings(const std::vector<int32_t>& encodings) {
    supportedEncodings_ = encodings;
    
    if (connected_ && protocol_) {
        // Build SetEncodings message
        std::vector<uint8_t> message;
        message.push_back(SET_ENCODINGS);
        message.push_back(0); // padding
        
        uint16_t numEncodings = htons(static_cast<uint16_t>(encodings.size()));
        const uint8_t* numBytes = reinterpret_cast<const uint8_t*>(&numEncodings);
        message.insert(message.end(), numBytes, numBytes + 2);
        
        for (int32_t encoding : encodings) {
            uint32_t netEncoding = htonl(static_cast<uint32_t>(encoding));
            const uint8_t* encBytes = reinterpret_cast<const uint8_t*>(&netEncoding);
            message.insert(message.end(), encBytes, encBytes + 4);
        }
        
        // Send message (would need protocol support)
        std::cout << "Supported encodings set: " << encodings.size() << " encodings" << std::endl;
    }
}

void VNCClient::setPixelFormat(const PixelFormat& format) {
    pixelFormat_ = format;
    
    if (connected_ && protocol_) {
        protocol_->setPixelFormat(format);
    }
}

bool VNCClient::connectSocket(const std::string& host, uint16_t port) {
    socket_ = socket(AF_INET, SOCK_STREAM, 0);
    if (socket_ < 0) {
        std::cerr << "Failed to create socket" << std::endl;
        return false;
    }
    
    // Resolve hostname
    struct hostent* hostEntry = gethostbyname(host.c_str());
    if (!hostEntry) {
        std::cerr << "Failed to resolve hostname: " << host << std::endl;
        closeSocket();
        return false;
    }
    
    // Connect to server
    struct sockaddr_in serverAddr;
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(port);
    memcpy(&serverAddr.sin_addr, hostEntry->h_addr_list[0], hostEntry->h_length);
    
    if (::connect(socket_, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) < 0) {
        std::cerr << "Failed to connect to server" << std::endl;
        closeSocket();
        return false;
    }
    
    return true;
}

void VNCClient::closeSocket() {
    if (socket_ >= 0) {
        ::close(socket_);
        socket_ = -1;
    }
}

void VNCClient::receiveData() {
    std::vector<uint8_t> buffer(4096);
    
    while (running_ && connected_) {
        ssize_t bytesRead = recv(socket_, buffer.data(), buffer.size(), 0);
        if (bytesRead <= 0) {
            // Connection closed or error
            std::cerr << "Connection lost" << std::endl;
            break;
        }
        
        connectionInfo_.bytesReceived += bytesRead;
        
        // Process incoming data through protocol
        if (!protocol_->handleIncomingData(buffer.data(), bytesRead)) {
            std::cerr << "Protocol error" << std::endl;
            break;
        }
        
        // Check if we became authenticated
        if (protocol_->getState() == NORMAL && !connectionInfo_.authenticated) {
            connectionInfo_.authenticated = true;
            std::cout << "Authentication successful" << std::endl;
            
            // Send initial messages
            setSupportedEncodings(supportedEncodings_);
            requestFramebufferUpdate(); // Request full screen update
        }
        
        // Handle any server messages here
        // For a complete implementation, you'd parse server messages
        // and call appropriate callbacks
    }
    
    running_ = false;
    connected_ = false;
}

void VNCClient::sendData() {
    while (running_ && connected_) {
        // Get outgoing data from protocol
        auto outgoingData = protocol_->getOutgoingData();
        
        if (!outgoingData.empty()) {
            std::lock_guard<std::mutex> lock(sendMutex_);
            ssize_t bytesSent = send(socket_, outgoingData.data(), outgoingData.size(), 0);
            
            if (bytesSent != static_cast<ssize_t>(outgoingData.size())) {
                std::cerr << "Failed to send data" << std::endl;
                break;
            }
            
            connectionInfo_.bytesSent += bytesSent;
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void VNCClient::onFramebufferUpdate(const std::vector<Rectangle>& rectangles, const std::vector<uint8_t>& pixelData) {
    std::lock_guard<std::mutex> lock(framebufferMutex_);
    
    size_t dataOffset = 0;
    for (const auto& rect : rectangles) {
        updateFramebuffer(rect.x, rect.y, rect.width, rect.height, 
                         pixelData.data() + dataOffset, rect.encoding);
        
        // Calculate data size for this rectangle (simplified for Raw encoding)
        size_t rectDataSize = rect.width * rect.height * (pixelFormat_.bitsPerPixel / 8);
        dataOffset += rectDataSize;
        
        if (fbUpdateCallback_) {
            fbUpdateCallback_(rect.x, rect.y, rect.width, rect.height);
        }
    }
}

void VNCClient::onServerCutText(const std::string& text) {
    if (clipboardCallback_) {
        clipboardCallback_(text);
    }
}

void VNCClient::onBell() {
    std::cout << "Bell!" << std::endl;
}

void VNCClient::updateFramebuffer(uint16_t x, uint16_t y, uint16_t w, uint16_t h, 
                                  const uint8_t* pixelData, int32_t encoding) {
    switch (encoding) {
        case RAW:
            decodeRawEncoding(x, y, w, h, pixelData);
            break;
        case RRE:
            decodeRREEncoding(x, y, w, h, pixelData);
            break;
        default:
            std::cerr << "Unsupported encoding: " << encoding << std::endl;
            break;
    }
}

void VNCClient::decodeRawEncoding(uint16_t x, uint16_t y, uint16_t w, uint16_t h, const uint8_t* data) {
    if (framebuffer_.empty()) {
        // Initialize framebuffer
        size_t bufferSize = fbWidth_ * fbHeight_ * (pixelFormat_.bitsPerPixel / 8);
        framebuffer_.resize(bufferSize);
    }
    
    size_t bytesPerPixel = pixelFormat_.bitsPerPixel / 8;
    
    for (uint16_t row = 0; row < h; row++) {
        for (uint16_t col = 0; col < w; col++) {
            size_t srcOffset = (row * w + col) * bytesPerPixel;
            size_t dstOffset = ((y + row) * fbWidth_ + (x + col)) * bytesPerPixel;
            
            if (dstOffset + bytesPerPixel <= framebuffer_.size()) {
                memcpy(&framebuffer_[dstOffset], &data[srcOffset], bytesPerPixel);
            }
        }
    }
}

void VNCClient::decodeRREEncoding(uint16_t x, uint16_t y, uint16_t w, uint16_t h, const uint8_t* data) {
    // Simplified RRE decoding
    // A complete implementation would properly decode RRE format
    decodeRawEncoding(x, y, w, h, data);
}

} // namespace vnc