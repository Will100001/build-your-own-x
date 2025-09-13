cmake_minimum_required(VERSION 3.10)
project(VNC VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Build options
option(BUILD_SERVER "Build VNC Server" ON)
option(BUILD_CLIENT "Build VNC Client" ON)
option(BUILD_EXAMPLES "Build example applications" ON)
option(BUILD_TESTS "Build test suite" OFF)
option(ENABLE_TLS "Enable TLS/SSL support" OFF)

# Find required packages
find_package(Threads REQUIRED)

# Platform-specific libraries
if(WIN32)
    set(PLATFORM_LIBS gdi32 user32 ws2_32)
    set(PLATFORM_SOURCES platforms/windows/windows_impl.cpp)
elseif(UNIX AND NOT APPLE)
    find_package(X11 REQUIRED)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(XTST REQUIRED xtst)
    set(PLATFORM_LIBS ${X11_LIBRARIES} ${XTST_LIBRARIES})
    set(PLATFORM_INCLUDES ${X11_INCLUDE_DIR} ${XTST_INCLUDE_DIRS})
endif()

# Optional TLS support
if(ENABLE_TLS)
    find_package(OpenSSL REQUIRED)
    set(TLS_LIBS OpenSSL::SSL OpenSSL::Crypto)
    add_definitions(-DENABLE_TLS)
endif()

# Include directories
include_directories(src ${PLATFORM_INCLUDES})

# Common library
set(COMMON_SOURCES
    src/common/rfb_protocol.cpp
    src/common/platform_factory.cpp
    ${PLATFORM_SOURCES}
)

add_library(vnc_common STATIC ${COMMON_SOURCES})
target_link_libraries(vnc_common ${PLATFORM_LIBS} ${TLS_LIBS} Threads::Threads)

# VNC Server
if(BUILD_SERVER)
    set(SERVER_SOURCES
        src/server/vnc_server.cpp
        src/gui/vnc_server_gui.cpp
    )
    
    add_library(vnc_server STATIC ${SERVER_SOURCES})
    target_link_libraries(vnc_server vnc_common)
    
    if(BUILD_EXAMPLES)
        add_executable(vnc-server examples/server_example.cpp)
        target_link_libraries(vnc-server vnc_server vnc_common)
    endif()
endif()

# VNC Client
if(BUILD_CLIENT)
    set(CLIENT_SOURCES
        src/client/vnc_client.cpp
        src/gui/vnc_client_gui.cpp
    )
    
    add_library(vnc_client STATIC ${CLIENT_SOURCES})
    target_link_libraries(vnc_client vnc_common)
    
    if(BUILD_EXAMPLES)
        add_executable(vnc-client examples/client_example.cpp)
        target_link_libraries(vnc-client vnc_client vnc_common)
    endif()
endif()

# Tests
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Installation
if(BUILD_SERVER AND BUILD_EXAMPLES)
    install(TARGETS vnc-server DESTINATION bin)
endif()

if(BUILD_CLIENT AND BUILD_EXAMPLES)
    install(TARGETS vnc-client DESTINATION bin)
endif()

install(FILES README.md DESTINATION share/doc/vnc)
install(DIRECTORY docs/ DESTINATION share/doc/vnc/docs)

# Package configuration
set(CPACK_PACKAGE_NAME "VNC")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Complete VNC implementation")
set(CPACK_PACKAGE_VENDOR "Build Your Own X")

include(CPack)