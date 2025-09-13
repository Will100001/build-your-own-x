#include "../src/gui/vnc_server_gui.h"
#include <iostream>

int main(int argc, char* argv[]) {
    std::cout << "VNC Server Example Application" << std::endl;
    std::cout << "==============================" << std::endl;
    
    try {
        vnc::VNCServerConsoleGUI serverGUI;
        serverGUI.run();
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}