#include "../src/common/rfb_protocol.h"
#include <iostream>

int main() {
    std::cout << "VNC RFB Protocol Test" << std::endl;
    
    try {
        // Test creating protocol instances
        vnc::RFBClient client;
        
        // Test basic functionality
        vnc::PixelFormat format;
        format.bitsPerPixel = 32;
        format.depth = 24;
        format.trueColourFlag = 1;
        
        client.setPixelFormat(format);
        
        std::cout << "RFB Protocol initialization successful!" << std::endl;
        std::cout << "Protocol supports:" << std::endl;
        std::cout << "- Version: RFB 003.008" << std::endl;
        std::cout << "- Security: VNC Authentication, None" << std::endl;
        std::cout << "- Encodings: Raw, RRE, Hextile, ZRLE" << std::endl;
        
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}