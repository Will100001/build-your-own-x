# Android VNC Implementation

This directory contains Android-specific implementations for the VNC client and server.

## Overview

The Android implementation provides:
- **VNC Client App**: Native Android client application
- **VNC Server Service**: Background service for screen sharing (requires root/accessibility)
- **Java/Kotlin Integration**: JNI wrapper for C++ core
- **Touch Input Handling**: Android touch events to VNC pointer events
- **Screen Capture**: Android MediaProjection API integration

## Structure

```
android/
├── app/                    # Android client app
│   ├── src/main/
│   │   ├── java/          # Java/Kotlin source
│   │   ├── cpp/           # JNI wrapper code
│   │   └── res/           # Android resources
│   └── build.gradle       # App build configuration
├── server/                 # Android server service
│   ├── src/main/
│   │   ├── java/          # Service implementation
│   │   └── cpp/           # Native server code
│   └── build.gradle       # Service build configuration
├── shared/                 # Shared Android utilities
│   ├── jni/               # JNI helper classes
│   └── native/            # Shared native code
└── build.gradle           # Root build configuration
```

## Features

### VNC Client App
- Connect to VNC servers
- Touch-based remote control
- Zoom and pan gestures
- On-screen keyboard
- Clipboard synchronization
- Connection bookmarks

### VNC Server Service
- Screen mirroring (requires permissions)
- Touch input simulation
- Background operation
- Notification controls
- Security settings

## Building

### Prerequisites
- Android Studio 4.0+
- Android NDK 21+
- CMake 3.10+
- Target SDK 30+

### Build Steps

1. Open project in Android Studio
2. Sync Gradle files
3. Build APK or AAB

```bash
# Command line build
./gradlew assembleRelease
```

## Permissions

### Client App
- INTERNET (network access)
- WAKE_LOCK (keep screen on)

### Server Service
- SYSTEM_ALERT_WINDOW (overlay)
- CAPTURE_VIDEO_OUTPUT (screen capture)
- ACCESSIBILITY_SERVICE (input simulation)

## Integration

The Android implementation integrates with the core C++ VNC implementation through JNI:

```cpp
// JNI wrapper example
extern "C" JNIEXPORT jobject JNICALL
Java_com_vnc_client_VNCClient_connect(JNIEnv *env, jobject thiz, 
                                       jstring host, jint port) {
    const char* hostStr = env->GetStringUTFChars(host, 0);
    
    auto client = std::make_unique<vnc::VNCClient>();
    bool success = client->connect(hostStr, static_cast<uint16_t>(port));
    
    env->ReleaseStringUTFChars(host, hostStr);
    return success ? JNI_TRUE : JNI_FALSE;
}
```

## Usage Examples

### Client App Usage
1. Install VNC Client APK
2. Add server connection
3. Enter host, port, password
4. Connect and control remote desktop

### Server Service Usage
1. Install VNC Server APK
2. Grant required permissions
3. Start service from notification
4. Connect from remote VNC client

## Notes

- Server functionality requires root access or accessibility permissions
- Screen capture API availability varies by Android version
- Some features may not work on all devices due to security restrictions
- Consider battery optimization settings for background services

## Future Enhancements

- Gesture-based shortcuts
- File transfer support
- Audio streaming
- Hardware acceleration
- Multi-touch support
- Custom keyboard layouts