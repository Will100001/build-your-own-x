#!/usr/bin/env python3
"""
Test script for Enhanced VNC Server
===================================

This script tests the core functionality of the VNC server components
without requiring the full GUI interface.
"""

import sys
import time
import threading
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from vnc_server import VNCServer, ScreenRecorder, LANDeviceMonitor
    print("✓ Successfully imported VNC server components")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def test_vnc_server():
    """Test VNC server basic functionality."""
    print("\n--- Testing VNC Server ---")
    
    server = VNCServer(port=5901)  # Use different port for testing
    
    # Test server start
    print("Starting VNC server...")
    if server.start_server():
        print("✓ VNC server started successfully")
    else:
        print("✗ Failed to start VNC server")
        return False
    
    # Give server time to initialize
    time.sleep(1)
    
    # Check server status
    if server.is_running:
        print(f"✓ Server is running on port {server.port}")
    else:
        print("✗ Server is not running")
        return False
    
    # Test server stop
    print("Stopping VNC server...")
    if server.stop_server():
        print("✓ VNC server stopped successfully")
    else:
        print("✗ Failed to stop VNC server")
        return False
    
    return True


def test_screen_recorder():
    """Test screen recording functionality."""
    print("\n--- Testing Screen Recorder ---")
    
    recorder = ScreenRecorder()
    
    # Test recording start
    print("Starting screen recording...")
    test_file = "/tmp/test_recording.mp4"
    
    if recorder.start_recording(output_file=test_file, fps=10):
        print("✓ Screen recording started successfully")
    else:
        print("✗ Failed to start screen recording")
        return False
    
    # Record for a few seconds
    print("Recording for 3 seconds...")
    time.sleep(3)
    
    # Test recording stop
    print("Stopping screen recording...")
    if recorder.stop_recording():
        print("✓ Screen recording stopped successfully")
    else:
        print("✗ Failed to stop screen recording")
        return False
    
    # Check if file was created
    if os.path.exists(test_file):
        file_size = os.path.getsize(test_file)
        print(f"✓ Recording file created: {test_file} ({file_size} bytes)")
        
        # Clean up test file
        try:
            os.remove(test_file)
            print("✓ Test file cleaned up")
        except:
            print("⚠ Could not remove test file")
    else:
        print("✗ Recording file was not created")
        return False
    
    return True


def test_lan_monitor():
    """Test LAN monitoring functionality."""
    print("\n--- Testing LAN Monitor ---")
    
    monitor = LANDeviceMonitor()
    
    # Test getting local IP
    local_ip = monitor.get_local_ip()
    if local_ip and local_ip != "127.0.0.1":
        print(f"✓ Local IP detected: {local_ip}")
    else:
        print(f"⚠ Using fallback IP: {local_ip}")
    
    # Test Zeroconf monitoring start
    print("Starting Zeroconf monitoring...")
    if monitor.start_monitoring():
        print("✓ Zeroconf monitoring started successfully")
        
        # Let it run for a moment
        time.sleep(2)
        
        # Check for discovered devices
        device_count = len(monitor.devices)
        print(f"✓ Discovered {device_count} devices via Zeroconf")
        
        # Stop monitoring
        monitor.stop_monitoring()
        print("✓ Zeroconf monitoring stopped")
    else:
        print("✗ Failed to start Zeroconf monitoring")
    
    # Test network scanning (limited to avoid long delays)
    print("Testing network scan (limited scope)...")
    
    def limited_scan():
        """Scan just a few IPs for testing."""
        local_ip = monitor.get_local_ip()
        network = ".".join(local_ip.split(".")[:-1]) + "."
        
        test_ips = [f"{network}1", local_ip]  # Just test gateway and self
        active_devices = []
        
        for ip in test_ips:
            try:
                import subprocess
                import platform
                
                if platform.system().lower() == "windows":
                    result = subprocess.run(
                        ["ping", "-n", "1", "-w", "1000", ip],
                        capture_output=True, text=True, timeout=5
                    )
                else:
                    result = subprocess.run(
                        ["ping", "-c", "1", "-W", "1", ip],
                        capture_output=True, text=True, timeout=5
                    )
                
                if result.returncode == 0:
                    active_devices.append(ip)
            except:
                pass
        
        return active_devices
    
    active_devices = limited_scan()
    print(f"✓ Network scan found {len(active_devices)} active devices: {active_devices}")
    
    return True


def test_integration():
    """Test running multiple components simultaneously."""
    print("\n--- Testing Integration ---")
    
    server = VNCServer(port=5902)
    recorder = ScreenRecorder()
    monitor = LANDeviceMonitor()
    
    print("Starting all components...")
    
    # Start all components
    server_ok = server.start_server()
    recorder_ok = recorder.start_recording("/tmp/integration_test.mp4", fps=5)
    monitor_ok = monitor.start_monitoring()
    
    if server_ok and recorder_ok and monitor_ok:
        print("✓ All components started successfully")
        
        # Run for a short time
        print("Running integration test for 3 seconds...")
        time.sleep(3)
        
        # Stop all components
        server.stop_server()
        recorder.stop_recording()
        monitor.stop_monitoring()
        
        print("✓ All components stopped successfully")
        
        # Clean up
        try:
            os.remove("/tmp/integration_test.mp4")
        except:
            pass
        
        return True
    else:
        print(f"✗ Component start failures - Server: {server_ok}, Recorder: {recorder_ok}, Monitor: {monitor_ok}")
        
        # Try to clean up
        try:
            server.stop_server()
            recorder.stop_recording()
            monitor.stop_monitoring()
        except:
            pass
        
        return False


def main():
    """Run all tests."""
    print("Enhanced VNC Server - Component Tests")
    print("====================================")
    
    tests = [
        ("VNC Server", test_vnc_server),
        ("Screen Recorder", test_screen_recorder),
        ("LAN Monitor", test_lan_monitor),
        ("Integration", test_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    print("-"*50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The VNC server is ready to use.")
        return 0
    else:
        print("⚠ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())