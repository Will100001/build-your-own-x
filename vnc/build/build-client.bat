@echo off
REM VNC Client Build Script for Windows

echo Building VNC Client for Windows...

REM Create build directory
if not exist "..\build\client" mkdir "..\build\client"

REM Compiler settings
set CXX=g++
set CXXFLAGS=-std=c++17 -Wall -Wextra -O2 -DWIN32
set INCLUDES=-I..\src
set LIBS=-lpthread -lws2_32

REM Source files
set COMMON_SOURCES=..\src\common\rfb_protocol.cpp
set CLIENT_SOURCES=..\src\client\vnc_client.cpp
set GUI_SOURCES=..\src\gui\vnc_client_gui.cpp
set EXAMPLE_SOURCE=..\examples\client_example.cpp

REM Compile
echo Compiling VNC Client...
%CXX% %CXXFLAGS% %INCLUDES% %COMMON_SOURCES% %CLIENT_SOURCES% %GUI_SOURCES% %EXAMPLE_SOURCE% %LIBS% -o ..\build\client\vnc-client.exe

if %ERRORLEVEL% EQU 0 (
    echo VNC Client built successfully!
    echo Executable: ..\build\client\vnc-client.exe
) else (
    echo Build failed!
    exit /b 1
)