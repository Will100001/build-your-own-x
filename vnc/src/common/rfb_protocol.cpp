#include "rfb_protocol.h"
#include <cstring>
#include <arpa/inet.h>
#include <algorithm>
#include <openssl/des.h>
#include <random>

namespace vnc {

RFBProtocol::RFBProtocol() 
    : state_(HANDSHAKE)
    , fbWidth_(1024)
    , fbHeight_(768)
    , tlsEnabled_(false)
    , desktopName_("VNC Desktop")
{
    // Initialize default pixel format (32-bit RGBA)
    pixelFormat_.bitsPerPixel = 32;
    pixelFormat_.depth = 24;
    pixelFormat_.bigEndianFlag = 0;
    pixelFormat_.trueColourFlag = 1;
    pixelFormat_.redMax = htons(255);
    pixelFormat_.greenMax = htons(255);
    pixelFormat_.blueMax = htons(255);
    pixelFormat_.redShift = 16;
    pixelFormat_.greenShift = 8;
    pixelFormat_.blueShift = 0;
    memset(pixelFormat_.padding, 0, sizeof(pixelFormat_.padding));
}

bool RFBProtocol::handleIncomingData(const uint8_t* data, size_t length) {
    // Add data to incoming buffer
    incomingBuffer_.insert(incomingBuffer_.end(), data, data + length);
    
    bool processed = false;
    do {
        processed = false;
        switch (state_) {
            case HANDSHAKE:
                processed = handleHandshake(incomingBuffer_.data(), incomingBuffer_.size());
                break;
            case SECURITY:
                processed = handleSecurity(incomingBuffer_.data(), incomingBuffer_.size());
                break;
            case SECURITY_RESULT:
                processed = handleSecurityResult(incomingBuffer_.data(), incomingBuffer_.size());
                break;
            case INITIALIZATION:
                processed = handleInitialization(incomingBuffer_.data(), incomingBuffer_.size());
                break;
            case NORMAL:
                processed = handleNormalProtocol(incomingBuffer_.data(), incomingBuffer_.size());
                break;
        }
    } while (processed);
    
    return true;
}

std::vector<uint8_t> RFBProtocol::getOutgoingData() {
    std::vector<uint8_t> data = std::move(outgoingBuffer_);
    outgoingBuffer_.clear();
    return data;
}

void RFBProtocol::setFramebufferSize(uint16_t width, uint16_t height) {
    fbWidth_ = width;
    fbHeight_ = height;
}

void RFBProtocol::setPixelFormat(const PixelFormat& format) {
    pixelFormat_ = format;
}

bool RFBProtocol::handleHandshake(const uint8_t* data, size_t length) {
    const size_t versionLength = 12;
    
    if (isServer()) {
        // Server sends version first
        if (state_ == HANDSHAKE) {
            sendVersion();
            return false; // Wait for client response
        }
        
        if (length < versionLength) return false;
        
        // Check client version
        std::string clientVersion(reinterpret_cast<const char*>(data), versionLength);
        if (clientVersion.substr(0, 11) == "RFB 003.008") {
            state_ = SECURITY;
            incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + versionLength);
            sendSecurityTypes();
            return true;
        }
    } else {
        // Client waits for server version
        if (length < versionLength) return false;
        
        std::string serverVersion(reinterpret_cast<const char*>(data), versionLength);
        if (serverVersion.substr(0, 11) == "RFB 003.008") {
            // Send our version
            outgoingBuffer_.insert(outgoingBuffer_.end(), RFB_VERSION_3_8, RFB_VERSION_3_8 + versionLength);
            state_ = SECURITY;
            incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + versionLength);
            return true;
        }
    }
    
    return false;
}

bool RFBProtocol::handleSecurity(const uint8_t* data, size_t length) {
    if (isServer()) {
        // Server waits for client security choice
        if (length < 1) return false;
        
        uint8_t securityType = data[0];
        incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 1);
        
        if (securityType == NONE) {
            sendSecurityResult(true);
            state_ = INITIALIZATION;
        } else if (securityType == VNC_AUTHENTICATION) {
            securityChallenge_ = generateChallenge();
            outgoingBuffer_.insert(outgoingBuffer_.end(), securityChallenge_.begin(), securityChallenge_.end());
            state_ = SECURITY_RESULT;
        }
        return true;
    } else {
        // Client receives security types
        if (length < 1) return false;
        
        uint8_t numTypes = data[0];
        if (length < 1 + numTypes) return false;
        
        // Choose security type (prefer NONE for simplicity)
        bool foundNone = false;
        bool foundVNC = false;
        
        for (int i = 0; i < numTypes; i++) {
            if (data[1 + i] == NONE) foundNone = true;
            if (data[1 + i] == VNC_AUTHENTICATION) foundVNC = true;
        }
        
        uint8_t chosenType = NONE;
        if (foundNone) {
            chosenType = NONE;
            state_ = INITIALIZATION;
        } else if (foundVNC && !password_.empty()) {
            chosenType = VNC_AUTHENTICATION;
            state_ = SECURITY_RESULT;
        }
        
        outgoingBuffer_.push_back(chosenType);
        incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 1 + numTypes);
        return true;
    }
}

bool RFBProtocol::handleSecurityResult(const uint8_t* data, size_t length) {
    if (isServer()) {
        // Server waits for VNC auth response
        if (length < 16) return false;
        
        std::vector<uint8_t> response(data, data + 16);
        bool success = verifyPassword(securityChallenge_, response);
        sendSecurityResult(success);
        
        if (success) {
            state_ = INITIALIZATION;
        }
        
        incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 16);
        return true;
    } else {
        // Client waits for security result
        if (length < 4) return false;
        
        uint32_t result = ntohl(*reinterpret_cast<const uint32_t*>(data));
        if (result == 0) {
            state_ = INITIALIZATION;
        }
        
        incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 4);
        return true;
    }
}

bool RFBProtocol::handleInitialization(const uint8_t* data, size_t length) {
    if (isServer()) {
        // Server waits for ClientInit
        if (length < 1) return false;
        
        uint8_t sharedFlag = data[0];
        sendServerInit();
        state_ = NORMAL;
        
        incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 1);
        return true;
    } else {
        // Client waits for ServerInit
        if (length < 24) return false;
        
        uint16_t fbWidth = ntohs(*reinterpret_cast<const uint16_t*>(data));
        uint16_t fbHeight = ntohs(*reinterpret_cast<const uint16_t*>(data + 2));
        PixelFormat serverPixelFormat;
        memcpy(&serverPixelFormat, data + 4, sizeof(PixelFormat));
        uint32_t nameLength = ntohl(*reinterpret_cast<const uint32_t*>(data + 20));
        
        if (length < 24 + nameLength) return false;
        
        fbWidth_ = fbWidth;
        fbHeight_ = fbHeight;
        pixelFormat_ = serverPixelFormat;
        
        state_ = NORMAL;
        incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 24 + nameLength);
        return true;
    }
}

bool RFBProtocol::handleNormalProtocol(const uint8_t* data, size_t length) {
    if (length < 1) return false;
    
    uint8_t messageType = data[0];
    
    switch (messageType) {
        case SET_PIXEL_FORMAT:
            return handleSetPixelFormat(data, length);
        case SET_ENCODINGS:
            return handleSetEncodings(data, length);
        case FRAMEBUFFER_UPDATE_REQUEST:
            return handleFramebufferUpdateRequest(data, length);
        case KEY_EVENT:
            return handleKeyEvent(data, length);
        case POINTER_EVENT:
            return handlePointerEvent(data, length);
        case CLIENT_CUT_TEXT:
            return handleClientCutText(data, length);
        default:
            // Unknown message type, skip it
            incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 1);
            return true;
    }
}

bool RFBProtocol::handleKeyEvent(const uint8_t* data, size_t length) {
    if (length < sizeof(KeyEventMsg)) return false;
    
    const KeyEventMsg* msg = reinterpret_cast<const KeyEventMsg*>(data);
    if (keyEventCallback_) {
        keyEventCallback_(ntohl(msg->key), msg->downFlag != 0);
    }
    
    incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + sizeof(KeyEventMsg));
    return true;
}

bool RFBProtocol::handlePointerEvent(const uint8_t* data, size_t length) {
    if (length < sizeof(PointerEventMsg)) return false;
    
    const PointerEventMsg* msg = reinterpret_cast<const PointerEventMsg*>(data);
    if (pointerEventCallback_) {
        pointerEventCallback_(ntohs(msg->xPosition), ntohs(msg->yPosition), msg->buttonMask);
    }
    
    incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + sizeof(PointerEventMsg));
    return true;
}

bool RFBProtocol::handleFramebufferUpdateRequest(const uint8_t* data, size_t length) {
    if (length < 10) return false;
    
    uint8_t incremental = data[1];
    uint16_t x = ntohs(*reinterpret_cast<const uint16_t*>(data + 2));
    uint16_t y = ntohs(*reinterpret_cast<const uint16_t*>(data + 4));
    uint16_t w = ntohs(*reinterpret_cast<const uint16_t*>(data + 6));
    uint16_t h = ntohs(*reinterpret_cast<const uint16_t*>(data + 8));
    
    if (fbUpdateCallback_) {
        fbUpdateCallback_(x, y, w, h);
    }
    
    incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 10);
    return true;
}

void RFBProtocol::sendVersion() {
    const char* version = RFB_VERSION_3_8;
    outgoingBuffer_.insert(outgoingBuffer_.end(), version, version + strlen(version));
}

void RFBProtocol::sendSecurityTypes() {
    std::vector<uint8_t> types;
    types.push_back(NONE);
    if (!password_.empty()) {
        types.push_back(VNC_AUTHENTICATION);
    }
    
    outgoingBuffer_.push_back(static_cast<uint8_t>(types.size()));
    outgoingBuffer_.insert(outgoingBuffer_.end(), types.begin(), types.end());
}

void RFBProtocol::sendSecurityResult(bool success) {
    uint32_t result = success ? 0 : 1;
    result = htonl(result);
    const uint8_t* resultBytes = reinterpret_cast<const uint8_t*>(&result);
    outgoingBuffer_.insert(outgoingBuffer_.end(), resultBytes, resultBytes + 4);
}

void RFBProtocol::sendServerInit() {
    // Framebuffer width and height
    uint16_t width = htons(fbWidth_);
    uint16_t height = htons(fbHeight_);
    outgoingBuffer_.insert(outgoingBuffer_.end(), reinterpret_cast<const uint8_t*>(&width), reinterpret_cast<const uint8_t*>(&width) + 2);
    outgoingBuffer_.insert(outgoingBuffer_.end(), reinterpret_cast<const uint8_t*>(&height), reinterpret_cast<const uint8_t*>(&height) + 2);
    
    // Pixel format
    outgoingBuffer_.insert(outgoingBuffer_.end(), reinterpret_cast<const uint8_t*>(&pixelFormat_), reinterpret_cast<const uint8_t*>(&pixelFormat_) + sizeof(PixelFormat));
    
    // Desktop name
    uint32_t nameLength = htonl(static_cast<uint32_t>(desktopName_.length()));
    outgoingBuffer_.insert(outgoingBuffer_.end(), reinterpret_cast<const uint8_t*>(&nameLength), reinterpret_cast<const uint8_t*>(&nameLength) + 4);
    outgoingBuffer_.insert(outgoingBuffer_.end(), desktopName_.begin(), desktopName_.end());
}

std::vector<uint8_t> RFBProtocol::generateChallenge() {
    std::vector<uint8_t> challenge(16);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 255);
    
    for (auto& byte : challenge) {
        byte = static_cast<uint8_t>(dis(gen));
    }
    
    return challenge;
}

// Server implementation
RFBServer::RFBServer() : RFBProtocol() {
}

// Client implementation
RFBClient::RFBClient() : RFBProtocol() {
}

void RFBClient::requestFramebufferUpdate(uint16_t x, uint16_t y, uint16_t w, uint16_t h, bool incremental) {
    std::vector<uint8_t> msg;
    msg.push_back(FRAMEBUFFER_UPDATE_REQUEST);
    msg.push_back(incremental ? 1 : 0);
    
    uint16_t netX = htons(x);
    uint16_t netY = htons(y);
    uint16_t netW = htons(w);
    uint16_t netH = htons(h);
    
    msg.insert(msg.end(), reinterpret_cast<const uint8_t*>(&netX), reinterpret_cast<const uint8_t*>(&netX) + 2);
    msg.insert(msg.end(), reinterpret_cast<const uint8_t*>(&netY), reinterpret_cast<const uint8_t*>(&netY) + 2);
    msg.insert(msg.end(), reinterpret_cast<const uint8_t*>(&netW), reinterpret_cast<const uint8_t*>(&netW) + 2);
    msg.insert(msg.end(), reinterpret_cast<const uint8_t*>(&netH), reinterpret_cast<const uint8_t*>(&netH) + 2);
    
    outgoingBuffer_.insert(outgoingBuffer_.end(), msg.begin(), msg.end());
}

void RFBClient::sendKeyEvent(uint32_t key, bool down) {
    KeyEventMsg msg;
    msg.messageType = KEY_EVENT;
    msg.downFlag = down ? 1 : 0;
    msg.padding = 0;
    msg.key = htonl(key);
    
    const uint8_t* msgBytes = reinterpret_cast<const uint8_t*>(&msg);
    outgoingBuffer_.insert(outgoingBuffer_.end(), msgBytes, msgBytes + sizeof(KeyEventMsg));
}

void RFBClient::sendPointerEvent(uint16_t x, uint16_t y, uint8_t buttons) {
    PointerEventMsg msg;
    msg.messageType = POINTER_EVENT;
    msg.buttonMask = buttons;
    msg.xPosition = htons(x);
    msg.yPosition = htons(y);
    
    const uint8_t* msgBytes = reinterpret_cast<const uint8_t*>(&msg);
    outgoingBuffer_.insert(outgoingBuffer_.end(), msgBytes, msgBytes + sizeof(PointerEventMsg));
}

// Placeholder implementations for remaining methods
bool RFBProtocol::handleSetPixelFormat(const uint8_t* data, size_t length) {
    if (length < 20) return false;
    memcpy(&pixelFormat_, data + 4, sizeof(PixelFormat));
    incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 20);
    return true;
}

bool RFBProtocol::handleSetEncodings(const uint8_t* data, size_t length) {
    if (length < 4) return false;
    uint16_t numEncodings = ntohs(*reinterpret_cast<const uint16_t*>(data + 2));
    if (length < 4 + numEncodings * 4) return false;
    
    supportedEncodings_.clear();
    for (int i = 0; i < numEncodings; i++) {
        int32_t encoding = ntohl(*reinterpret_cast<const int32_t*>(data + 4 + i * 4));
        supportedEncodings_.push_back(encoding);
    }
    
    incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 4 + numEncodings * 4);
    return true;
}

bool RFBProtocol::handleClientCutText(const uint8_t* data, size_t length) {
    if (length < 8) return false;
    uint32_t textLength = ntohl(*reinterpret_cast<const uint32_t*>(data + 4));
    if (length < 8 + textLength) return false;
    
    // Handle clipboard text here
    incomingBuffer_.erase(incomingBuffer_.begin(), incomingBuffer_.begin() + 8 + textLength);
    return true;
}

bool RFBProtocol::verifyPassword(const std::vector<uint8_t>& challenge, const std::vector<uint8_t>& response) {
    // Simplified password verification - in real implementation use proper DES encryption
    return !password_.empty();
}

void RFBProtocol::sendFramebufferUpdate(const std::vector<Rectangle>& rectangles, const std::vector<uint8_t>& pixelData) {
    FramebufferUpdateMsg msg;
    msg.messageType = FRAMEBUFFER_UPDATE;
    msg.padding = 0;
    msg.numberOfRectangles = htons(static_cast<uint16_t>(rectangles.size()));
    
    const uint8_t* msgBytes = reinterpret_cast<const uint8_t*>(&msg);
    outgoingBuffer_.insert(outgoingBuffer_.end(), msgBytes, msgBytes + sizeof(FramebufferUpdateMsg));
    
    // Add rectangles and pixel data
    for (const auto& rect : rectangles) {
        Rectangle netRect = rect;
        netRect.x = htons(rect.x);
        netRect.y = htons(rect.y);
        netRect.width = htons(rect.width);
        netRect.height = htons(rect.height);
        netRect.encoding = htonl(rect.encoding);
        
        const uint8_t* rectBytes = reinterpret_cast<const uint8_t*>(&netRect);
        outgoingBuffer_.insert(outgoingBuffer_.end(), rectBytes, rectBytes + sizeof(Rectangle));
    }
    
    outgoingBuffer_.insert(outgoingBuffer_.end(), pixelData.begin(), pixelData.end());
}

} // namespace vnc