#!/usr/bin/env python3
"""
Example Usage of Enhanced VNC Server
====================================

This script demonstrates how to use the VNC server components
in your own applications.
"""

import time
import threading
from core_vnc_server import VNCServer, ScreenRecorder, NetworkMonitor


def example_basic_server():
    """Example 1: Basic VNC server usage."""
    print("Example 1: Basic VNC Server")
    print("-" * 30)
    
    # Create and start server
    server = VNCServer(host='0.0.0.0', port=5903)
    
    if server.start_server():
        print("✓ VNC server started successfully")
        print(f"  Listening on port {server.port}")
        print(f"  Connect with: telnet localhost {server.port}")
        
        # Run for 10 seconds
        print("  Server will run for 10 seconds...")
        time.sleep(10)
        
        # Stop server
        server.stop_server()
        print("✓ VNC server stopped")
    else:
        print("✗ Failed to start VNC server")


def example_screen_recording():
    """Example 2: Screen recording usage."""
    print("\nExample 2: Screen Recording")
    print("-" * 30)
    
    # Create recorder
    recorder = ScreenRecorder()
    
    # Start recording
    output_file = "example_recording.log"
    if recorder.start_recording(output_file):
        print(f"✓ Recording started: {output_file}")
        
        # Record for 5 seconds
        print("  Recording for 5 seconds...")
        for i in range(5, 0, -1):
            print(f"  {i}...", end=" ", flush=True)
            time.sleep(1)
        print()
        
        # Stop recording
        recorder.stop_recording()
        print("✓ Recording stopped")
        
        # Show file info
        import os
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"  File size: {size} bytes")
            
            # Show first few lines
            print("  First few lines:")
            with open(output_file, 'r') as f:
                for i, line in enumerate(f):
                    if i < 3:
                        print(f"    {line.strip()}")
                    else:
                        break
    else:
        print("✗ Failed to start recording")


def example_network_monitoring():
    """Example 3: Network monitoring usage."""
    print("\nExample 3: Network Monitoring")
    print("-" * 30)
    
    # Create monitor
    monitor = NetworkMonitor()
    
    # Get local IP
    local_ip = monitor.get_local_ip()
    print(f"Local IP: {local_ip}")
    
    # Scan network
    print("Scanning network for active devices...")
    devices = monitor.scan_network()
    
    if devices:
        print(f"Found {len(devices)} active devices:")
        for device in devices:
            print(f"  • {device['ip']} - {device['status']}")
    else:
        print("No active devices found")
    
    # Start monitoring
    print("\nStarting continuous monitoring for 5 seconds...")
    monitor.start_monitoring()
    time.sleep(5)
    monitor.stop_monitoring()
    print("✓ Monitoring stopped")


def example_combined_usage():
    """Example 4: Using all components together."""
    print("\nExample 4: Combined Usage")
    print("-" * 30)
    
    # Initialize all components
    server = VNCServer(port=5904)
    recorder = ScreenRecorder()
    monitor = NetworkMonitor()
    
    print("Starting all components...")
    
    # Start everything
    server_ok = server.start_server()
    recorder_ok = recorder.start_recording("combined_example.log")
    monitor_ok = monitor.start_monitoring()
    
    active_components = sum([server_ok, recorder_ok, monitor_ok])
    print(f"✓ {active_components}/3 components started successfully")
    
    if active_components > 0:
        print("Running combined demo for 8 seconds...")
        
        # Simulate some activity
        for i in range(8):
            time.sleep(1)
            client_count = len(server.clients) if server_ok else 0
            recording_status = "active" if recorder.is_recording else "stopped"
            device_count = len(monitor.devices) if monitor_ok else 0
            
            print(f"  Status: Clients={client_count}, Recording={recording_status}, Devices={device_count}")
        
        print("\nStopping all components...")
        
        # Clean shutdown
        if server_ok:
            server.stop_server()
            print("✓ VNC server stopped")
        
        if recorder_ok:
            recorder.stop_recording()
            print("✓ Recording stopped")
        
        if monitor_ok:
            monitor.stop_monitoring()
            print("✓ Monitoring stopped")
    
    print("✓ Combined example completed")


def example_custom_server():
    """Example 5: Custom server implementation."""
    print("\nExample 5: Custom Server Implementation")
    print("-" * 30)
    
    class LoggingVNCServer(VNCServer):
        """Custom VNC server with enhanced logging."""
        
        def _handle_client(self, client_socket, addr):
            print(f"[CUSTOM] Client {addr} connected")
            
            try:
                # Send custom welcome message
                welcome = f"Welcome to Custom VNC Server! Time: {time.ctime()}\n"
                client_socket.send(welcome.encode())
                
                # Call parent implementation
                super()._handle_client(client_socket, addr)
                
            except Exception as e:
                print(f"[CUSTOM] Error with client {addr}: {e}")
            finally:
                print(f"[CUSTOM] Client {addr} disconnected")
    
    # Use custom server
    custom_server = LoggingVNCServer(port=5905)
    
    if custom_server.start_server():
        print("✓ Custom VNC server started")
        print("  Try: telnet localhost 5905")
        
        time.sleep(8)
        
        custom_server.stop_server()
        print("✓ Custom server stopped")
    else:
        print("✗ Failed to start custom server")


def main():
    """Run all examples."""
    print("Enhanced VNC Server - Usage Examples")
    print("=" * 40)
    
    try:
        # Run examples
        example_basic_server()
        example_screen_recording()
        example_network_monitoring()
        example_combined_usage()
        example_custom_server()
        
        print("\n" + "=" * 40)
        print("✓ All examples completed successfully!")
        print("\nNext steps:")
        print("• Run 'python core_vnc_server.py --demo' for interactive demo")
        print("• Run 'python core_vnc_server.py --test' for comprehensive tests")
        print("• Check USAGE.md for detailed documentation")
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\nError running examples: {e}")


if __name__ == "__main__":
    main()