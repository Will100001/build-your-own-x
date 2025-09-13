@echo off
REM VNC Server Build Script for Windows

echo Building VNC Server for Windows...

REM Create build directory
if not exist "..\build\server" mkdir "..\build\server"

REM Compiler settings
set CXX=g++
set CXXFLAGS=-std=c++17 -Wall -Wextra -O2 -DWIN32
set INCLUDES=-I..\src
set LIBS=-lpthread -lgdi32 -luser32 -lws2_32

REM Source files
set COMMON_SOURCES=..\src\common\rfb_protocol.cpp ..\src\common\platform_factory.cpp
set SERVER_SOURCES=..\src\server\vnc_server.cpp
set GUI_SOURCES=..\src\gui\vnc_server_gui.cpp
set PLATFORM_SOURCES=..\platforms\windows\windows_impl.cpp
set EXAMPLE_SOURCE=..\examples\server_example.cpp

REM Compile
echo Compiling VNC Server...
%CXX% %CXXFLAGS% %INCLUDES% %COMMON_SOURCES% %SERVER_SOURCES% %GUI_SOURCES% %PLATFORM_SOURCES% %EXAMPLE_SOURCE% %LIBS% -o ..\build\server\vnc-server.exe

if %ERRORLEVEL% EQU 0 (
    echo VNC Server built successfully!
    echo Executable: ..\build\server\vnc-server.exe
) else (
    echo Build failed!
    exit /b 1
)