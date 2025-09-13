#include "../src/gui/vnc_client_gui.h"
#include <iostream>

int main(int argc, char* argv[]) {
    std::cout << "VNC Client Example Application" << std::endl;
    std::cout << "==============================" << std::endl;
    
    try {
        vnc::VNCClientConsoleGUI clientGUI;
        clientGUI.run();
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}