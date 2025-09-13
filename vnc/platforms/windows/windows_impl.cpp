#include "windows_impl.h"

#ifdef _WIN32

#include <iostream>
#include <algorithm>

namespace vnc {

// WindowsScreenCapture implementation
WindowsScreenCapture::WindowsScreenCapture() 
    : screenDC_(nullptr)
    , memoryDC_(nullptr)
    , bitmap_(nullptr)
    , screenWidth_(0)
    , screenHeight_(0)
{
}

WindowsScreenCapture::~WindowsScreenCapture() {
    cleanup();
}

bool WindowsScreenCapture::initialize() {
    // Get screen dimensions
    screenWidth_ = GetSystemMetrics(SM_CXSCREEN);
    screenHeight_ = GetSystemMetrics(SM_CYSCREEN);
    
    // Get screen device context
    screenDC_ = GetDC(nullptr);
    if (!screenDC_) {
        std::cerr << "Failed to get screen DC" << std::endl;
        return false;
    }
    
    // Create compatible memory DC
    memoryDC_ = CreateCompatibleDC(screenDC_);
    if (!memoryDC_) {
        std::cerr << "Failed to create memory DC" << std::endl;
        return false;
    }
    
    // Set up bitmap info
    memset(&bitmapInfo_, 0, sizeof(bitmapInfo_));
    bitmapInfo_.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bitmapInfo_.bmiHeader.biWidth = screenWidth_;
    bitmapInfo_.bmiHeader.biHeight = -screenHeight_; // Top-down DIB
    bitmapInfo_.bmiHeader.biPlanes = 1;
    bitmapInfo_.bmiHeader.biBitCount = 32;
    bitmapInfo_.bmiHeader.biCompression = BI_RGB;
    
    // Create DIB section
    void* bitmapData = nullptr;
    bitmap_ = CreateDIBSection(memoryDC_, &bitmapInfo_, DIB_RGB_COLORS, &bitmapData, nullptr, 0);
    if (!bitmap_) {
        std::cerr << "Failed to create DIB section" << std::endl;
        return false;
    }
    
    // Select bitmap into memory DC
    SelectObject(memoryDC_, bitmap_);
    
    // Allocate buffer
    size_t bufferSize = screenWidth_ * screenHeight_ * 4; // 32 bits per pixel
    tempBuffer_.resize(bufferSize);
    
    std::cout << "Windows screen capture initialized: " << screenWidth_ << "x" << screenHeight_ << std::endl;
    return true;
}

bool WindowsScreenCapture::captureFrame(std::vector<uint8_t>& buffer, uint16_t& width, uint16_t& height) {
    if (!screenDC_ || !memoryDC_ || !bitmap_) {
        return false;
    }
    
    // Copy screen to memory DC
    if (!BitBlt(memoryDC_, 0, 0, screenWidth_, screenHeight_, screenDC_, 0, 0, SRCCOPY)) {
        std::cerr << "BitBlt failed" << std::endl;
        return false;
    }
    
    // Get bitmap bits
    if (GetDIBits(screenDC_, bitmap_, 0, screenHeight_, tempBuffer_.data(), &bitmapInfo_, DIB_RGB_COLORS) == 0) {
        std::cerr << "GetDIBits failed" << std::endl;
        return false;
    }
    
    // Convert BGRA to RGBA (Windows uses BGRA format)
    buffer.resize(tempBuffer_.size());
    for (size_t i = 0; i < tempBuffer_.size(); i += 4) {
        buffer[i] = tempBuffer_[i + 2];     // R
        buffer[i + 1] = tempBuffer_[i + 1]; // G
        buffer[i + 2] = tempBuffer_[i];     // B
        buffer[i + 3] = tempBuffer_[i + 3]; // A
    }
    
    width = static_cast<uint16_t>(screenWidth_);
    height = static_cast<uint16_t>(screenHeight_);
    
    return true;
}

void WindowsScreenCapture::cleanup() {
    if (bitmap_) {
        DeleteObject(bitmap_);
        bitmap_ = nullptr;
    }
    
    if (memoryDC_) {
        DeleteDC(memoryDC_);
        memoryDC_ = nullptr;
    }
    
    if (screenDC_) {
        ReleaseDC(nullptr, screenDC_);
        screenDC_ = nullptr;
    }
}

// WindowsInputSimulator implementation
WindowsInputSimulator::WindowsInputSimulator() {
}

WindowsInputSimulator::~WindowsInputSimulator() {
    cleanup();
}

bool WindowsInputSimulator::initialize() {
    // No special initialization needed for Windows input simulation
    std::cout << "Windows input simulator initialized" << std::endl;
    return true;
}

void WindowsInputSimulator::simulateKeyPress(uint32_t key, bool down) {
    uint32_t windowsKey = convertVNCKeyToWindows(key);
    if (windowsKey != 0) {
        sendKeyInput(windowsKey, down);
    }
}

void WindowsInputSimulator::simulateMouseMove(uint16_t x, uint16_t y) {
    // Convert to screen coordinates (0-65535 range)
    int screenX = (x * 65535) / GetSystemMetrics(SM_CXSCREEN);
    int screenY = (y * 65535) / GetSystemMetrics(SM_CYSCREEN);
    
    sendMouseInput(screenX, screenY, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE);
}

void WindowsInputSimulator::simulateMouseClick(uint16_t x, uint16_t y, uint8_t buttons) {
    // Move mouse first
    simulateMouseMove(x, y);
    
    // Simulate button presses
    if (buttons & 0x01) { // Left button
        sendMouseInput(x, y, MOUSEEVENTF_LEFTDOWN);
        sendMouseInput(x, y, MOUSEEVENTF_LEFTUP);
    }
    
    if (buttons & 0x02) { // Middle button
        sendMouseInput(x, y, MOUSEEVENTF_MIDDLEDOWN);
        sendMouseInput(x, y, MOUSEEVENTF_MIDDLEUP);
    }
    
    if (buttons & 0x04) { // Right button
        sendMouseInput(x, y, MOUSEEVENTF_RIGHTDOWN);
        sendMouseInput(x, y, MOUSEEVENTF_RIGHTUP);
    }
    
    if (buttons & 0x08) { // Scroll up
        sendMouseInput(x, y, MOUSEEVENTF_WHEEL, WHEEL_DELTA);
    }
    
    if (buttons & 0x10) { // Scroll down
        sendMouseInput(x, y, MOUSEEVENTF_WHEEL, -WHEEL_DELTA);
    }
}

void WindowsInputSimulator::cleanup() {
    // No cleanup needed
}

uint32_t WindowsInputSimulator::convertVNCKeyToWindows(uint32_t vncKey) {
    // VNC keysyms to Windows virtual key codes mapping
    // This is a simplified mapping - a complete implementation would have more keys
    
    switch (vncKey) {
        // Letter keys
        case 0x0061: case 0x0041: return 'A'; // a/A
        case 0x0062: case 0x0042: return 'B'; // b/B
        case 0x0063: case 0x0043: return 'C'; // c/C
        case 0x0064: case 0x0044: return 'D'; // d/D
        case 0x0065: case 0x0045: return 'E'; // e/E
        case 0x0066: case 0x0046: return 'F'; // f/F
        case 0x0067: case 0x0047: return 'G'; // g/G
        case 0x0068: case 0x0048: return 'H'; // h/H
        case 0x0069: case 0x0049: return 'I'; // i/I
        case 0x006a: case 0x004a: return 'J'; // j/J
        case 0x006b: case 0x004b: return 'K'; // k/K
        case 0x006c: case 0x004c: return 'L'; // l/L
        case 0x006d: case 0x004d: return 'M'; // m/M
        case 0x006e: case 0x004e: return 'N'; // n/N
        case 0x006f: case 0x004f: return 'O'; // o/O
        case 0x0070: case 0x0050: return 'P'; // p/P
        case 0x0071: case 0x0051: return 'Q'; // q/Q
        case 0x0072: case 0x0052: return 'R'; // r/R
        case 0x0073: case 0x0053: return 'S'; // s/S
        case 0x0074: case 0x0054: return 'T'; // t/T
        case 0x0075: case 0x0055: return 'U'; // u/U
        case 0x0076: case 0x0056: return 'V'; // v/V
        case 0x0077: case 0x0057: return 'W'; // w/W
        case 0x0078: case 0x0058: return 'X'; // x/X
        case 0x0079: case 0x0059: return 'Y'; // y/Y
        case 0x007a: case 0x005a: return 'Z'; // z/Z
        
        // Number keys
        case 0x0030: return '0';
        case 0x0031: return '1';
        case 0x0032: return '2';
        case 0x0033: return '3';
        case 0x0034: return '4';
        case 0x0035: return '5';
        case 0x0036: return '6';
        case 0x0037: return '7';
        case 0x0038: return '8';
        case 0x0039: return '9';
        
        // Special keys
        case 0x0020: return VK_SPACE;
        case 0xff0d: return VK_RETURN;
        case 0xff08: return VK_BACK;
        case 0xff09: return VK_TAB;
        case 0xff1b: return VK_ESCAPE;
        case 0xffe1: return VK_LSHIFT;
        case 0xffe2: return VK_RSHIFT;
        case 0xffe3: return VK_LCONTROL;
        case 0xffe4: return VK_RCONTROL;
        case 0xffe9: return VK_LMENU; // Alt
        case 0xffea: return VK_RMENU; // Alt
        
        // Arrow keys
        case 0xff51: return VK_LEFT;
        case 0xff52: return VK_UP;
        case 0xff53: return VK_RIGHT;
        case 0xff54: return VK_DOWN;
        
        // Function keys
        case 0xffbe: return VK_F1;
        case 0xffbf: return VK_F2;
        case 0xffc0: return VK_F3;
        case 0xffc1: return VK_F4;
        case 0xffc2: return VK_F5;
        case 0xffc3: return VK_F6;
        case 0xffc4: return VK_F7;
        case 0xffc5: return VK_F8;
        case 0xffc6: return VK_F9;
        case 0xffc7: return VK_F10;
        case 0xffc8: return VK_F11;
        case 0xffc9: return VK_F12;
        
        default:
            return 0; // Unknown key
    }
}

void WindowsInputSimulator::sendKeyInput(uint32_t windowsKey, bool down) {
    INPUT input;
    memset(&input, 0, sizeof(input));
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = static_cast<WORD>(windowsKey);
    input.ki.dwFlags = down ? 0 : KEYEVENTF_KEYUP;
    
    SendInput(1, &input, sizeof(INPUT));
}

void WindowsInputSimulator::sendMouseInput(uint16_t x, uint16_t y, uint32_t flags, uint32_t data) {
    INPUT input;
    memset(&input, 0, sizeof(input));
    input.type = INPUT_MOUSE;
    input.mi.dx = x;
    input.mi.dy = y;
    input.mi.dwFlags = flags;
    input.mi.mouseData = data;
    
    SendInput(1, &input, sizeof(INPUT));
}

} // namespace vnc

#endif // _WIN32