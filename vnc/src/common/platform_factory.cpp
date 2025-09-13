#include "../server/vnc_server.h"

#ifdef _WIN32
#include "../platforms/windows/windows_impl.h"
#elif defined(__linux__)
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/XTest.h>
#include <iostream>

namespace vnc {

class LinuxScreenCapture : public ScreenCapture {
public:
    LinuxScreenCapture() : display_(nullptr), screen_(0), screenWidth_(0), screenHeight_(0) {}
    
    virtual ~LinuxScreenCapture() {
        cleanup();
    }
    
    bool initialize() override {
        display_ = XOpenDisplay(nullptr);
        if (!display_) {
            std::cerr << "Failed to open X display" << std::endl;
            return false;
        }
        
        screen_ = DefaultScreen(display_);
        screenWidth_ = DisplayWidth(display_, screen_);
        screenHeight_ = DisplayHeight(display_, screen_);
        
        std::cout << "Linux screen capture initialized: " << screenWidth_ << "x" << screenHeight_ << std::endl;
        return true;
    }
    
    bool captureFrame(std::vector<uint8_t>& buffer, uint16_t& width, uint16_t& height) override {
        if (!display_) return false;
        
        Window root = RootWindow(display_, screen_);
        XImage* image = XGetImage(display_, root, 0, 0, screenWidth_, screenHeight_, AllPlanes, ZPixmap);
        
        if (!image) {
            std::cerr << "Failed to capture screen" << std::endl;
            return false;
        }
        
        // Convert image to RGBA format
        size_t bufferSize = screenWidth_ * screenHeight_ * 4;
        buffer.resize(bufferSize);
        
        for (int y = 0; y < screenHeight_; y++) {
            for (int x = 0; x < screenWidth_; x++) {
                unsigned long pixel = XGetPixel(image, x, y);
                size_t offset = (y * screenWidth_ + x) * 4;
                
                buffer[offset] = (pixel >> 16) & 0xFF;     // R
                buffer[offset + 1] = (pixel >> 8) & 0xFF;  // G
                buffer[offset + 2] = pixel & 0xFF;         // B
                buffer[offset + 3] = 0xFF;                 // A
            }
        }
        
        XDestroyImage(image);
        
        width = static_cast<uint16_t>(screenWidth_);
        height = static_cast<uint16_t>(screenHeight_);
        
        return true;
    }
    
    void cleanup() override {
        if (display_) {
            XCloseDisplay(display_);
            display_ = nullptr;
        }
    }
    
private:
    Display* display_;
    int screen_;
    int screenWidth_;
    int screenHeight_;
};

class LinuxInputSimulator : public InputSimulator {
public:
    LinuxInputSimulator() : display_(nullptr) {}
    
    virtual ~LinuxInputSimulator() {
        cleanup();
    }
    
    bool initialize() override {
        display_ = XOpenDisplay(nullptr);
        if (!display_) {
            std::cerr << "Failed to open X display for input" << std::endl;
            return false;
        }
        
        // Check if XTest extension is available
        int event_base, error_base, major_version, minor_version;
        if (!XTestQueryExtension(display_, &event_base, &error_base, &major_version, &minor_version)) {
            std::cerr << "XTest extension not available" << std::endl;
            return false;
        }
        
        std::cout << "Linux input simulator initialized" << std::endl;
        return true;
    }
    
    void simulateKeyPress(uint32_t key, bool down) override {
        if (!display_) return;
        
        KeyCode keycode = XKeysymToKeycode(display_, key);
        if (keycode != 0) {
            XTestFakeKeyEvent(display_, keycode, down, CurrentTime);
            XFlush(display_);
        }
    }
    
    void simulateMouseMove(uint16_t x, uint16_t y) override {
        if (!display_) return;
        
        XTestFakeMotionEvent(display_, DefaultScreen(display_), x, y, CurrentTime);
        XFlush(display_);
    }
    
    void simulateMouseClick(uint16_t x, uint16_t y, uint8_t buttons) override {
        if (!display_) return;
        
        // Move mouse first
        simulateMouseMove(x, y);
        
        // Simulate button clicks
        if (buttons & 0x01) { // Left button
            XTestFakeButtonEvent(display_, 1, True, CurrentTime);
            XTestFakeButtonEvent(display_, 1, False, CurrentTime);
        }
        
        if (buttons & 0x02) { // Middle button
            XTestFakeButtonEvent(display_, 2, True, CurrentTime);
            XTestFakeButtonEvent(display_, 2, False, CurrentTime);
        }
        
        if (buttons & 0x04) { // Right button
            XTestFakeButtonEvent(display_, 3, True, CurrentTime);
            XTestFakeButtonEvent(display_, 3, False, CurrentTime);
        }
        
        if (buttons & 0x08) { // Scroll up
            XTestFakeButtonEvent(display_, 4, True, CurrentTime);
            XTestFakeButtonEvent(display_, 4, False, CurrentTime);
        }
        
        if (buttons & 0x10) { // Scroll down
            XTestFakeButtonEvent(display_, 5, True, CurrentTime);
            XTestFakeButtonEvent(display_, 5, False, CurrentTime);
        }
        
        XFlush(display_);
    }
    
    void cleanup() override {
        if (display_) {
            XCloseDisplay(display_);
            display_ = nullptr;
        }
    }
    
private:
    Display* display_;
};

} // namespace vnc

#endif

// Platform factory implementations
namespace vnc {

std::unique_ptr<ScreenCapture> ScreenCapture::create() {
#ifdef _WIN32
    return std::make_unique<WindowsScreenCapture>();
#elif defined(__linux__)
    return std::make_unique<LinuxScreenCapture>();
#else
    return nullptr;
#endif
}

std::unique_ptr<InputSimulator> InputSimulator::create() {
#ifdef _WIN32
    return std::make_unique<WindowsInputSimulator>();
#elif defined(__linux__)
    return std::make_unique<LinuxInputSimulator>();
#else
    return nullptr;
#endif
}

}