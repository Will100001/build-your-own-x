#ifndef WINDOWS_SCREEN_CAPTURE_H
#define WINDOWS_SCREEN_CAPTURE_H

#include "../../src/server/vnc_server.h"

#ifdef _WIN32
#include <windows.h>

namespace vnc {

class WindowsScreenCapture : public ScreenCapture {
public:
    WindowsScreenCapture();
    virtual ~WindowsScreenCapture();

    bool initialize() override;
    bool captureFrame(std::vector<uint8_t>& buffer, uint16_t& width, uint16_t& height) override;
    void cleanup() override;

private:
    HDC screenDC_;
    HDC memoryDC_;
    HBITMAP bitmap_;
    BITMAPINFO bitmapInfo_;
    int screenWidth_;
    int screenHeight_;
    std::vector<uint8_t> tempBuffer_;
};

class WindowsInputSimulator : public InputSimulator {
public:
    WindowsInputSimulator();
    virtual ~WindowsInputSimulator();

    bool initialize() override;
    void simulateKeyPress(uint32_t key, bool down) override;
    void simulateMouseMove(uint16_t x, uint16_t y) override;
    void simulateMouseClick(uint16_t x, uint16_t y, uint8_t buttons) override;
    void cleanup() override;

private:
    uint32_t convertVNCKeyToWindows(uint32_t vncKey);
    void sendKeyInput(uint32_t windowsKey, bool down);
    void sendMouseInput(uint16_t x, uint16_t y, uint32_t flags, uint32_t data = 0);
};

} // namespace vnc

#endif // _WIN32
#endif // WINDOWS_SCREEN_CAPTURE_H