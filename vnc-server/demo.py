#!/usr/bin/env python3
"""
Demo script for Enhanced VNC Server
===================================

This script demonstrates the key features of the VNC server
in a simple command-line interface.
"""

import sys
import time
import threading
import os
import signal

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from vnc_server import VNCServer, ScreenRecorder, LANDeviceMonitor
    print("Enhanced VNC Server Demo v1.0")
    print("=============================")
except ImportError as e:
    print(f"Error importing VNC server components: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)


class VNCDemo:
    """Command-line demo of VNC server features."""
    
    def __init__(self):
        self.vnc_server = VNCServer()
        self.screen_recorder = ScreenRecorder()
        self.lan_monitor = LANDeviceMonitor()
        self.running = True
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\nShutting down VNC server demo...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Clean up all resources."""
        print("Cleaning up...")
        self.vnc_server.stop_server()
        self.screen_recorder.stop_recording()
        self.lan_monitor.stop_monitoring()
    
    def show_menu(self):
        """Display the main menu."""
        print("\n" + "="*50)
        print("VNC SERVER DEMO - MAIN MENU")
        print("="*50)
        print("1. VNC Server Demo")
        print("2. Screen Recording Demo")
        print("3. LAN Monitoring Demo")
        print("4. Full Demo (All Features)")
        print("5. Status Check")
        print("6. Exit")
        print("-"*50)
    
    def vnc_server_demo(self):
        """Demonstrate VNC server functionality."""
        print("\n--- VNC SERVER DEMO ---")
        
        local_ip = self.lan_monitor.get_local_ip()
        print(f"Local IP: {local_ip}")
        print(f"VNC Port: {self.vnc_server.port}")
        
        if not self.vnc_server.is_running:
            print("Starting VNC server...")
            if self.vnc_server.start_server():
                print("✓ VNC server started successfully!")
                print(f"Connect with VNC client to: {local_ip}:{self.vnc_server.port}")
                print("Note: This is a basic implementation for demonstration.")
            else:
                print("✗ Failed to start VNC server")
                return
        else:
            print("VNC server is already running")
        
        print("\nVNC server is now accepting connections...")
        print("Press Enter to stop the server...")
        input()
        
        if self.vnc_server.stop_server():
            print("✓ VNC server stopped")
        else:
            print("✗ Error stopping VNC server")
    
    def screen_recording_demo(self):
        """Demonstrate screen recording functionality."""
        print("\n--- SCREEN RECORDING DEMO ---")
        
        if self.screen_recorder.is_recording:
            print("Recording is already active")
            print("Press Enter to stop current recording...")
            input()
            if self.screen_recorder.stop_recording():
                print("✓ Recording stopped")
            return
        
        # Setup recording
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"demo_recording_{timestamp}.mp4"
        
        print(f"Starting screen recording: {output_file}")
        print("Recording will capture your screen for 10 seconds...")
        
        if self.screen_recorder.start_recording(output_file, fps=15):
            print("✓ Recording started!")
            
            # Countdown
            for i in range(10, 0, -1):
                print(f"\rRecording... {i} seconds remaining", end="", flush=True)
                time.sleep(1)
            
            print("\nStopping recording...")
            if self.screen_recorder.stop_recording():
                print(f"✓ Recording saved to: {output_file}")
                
                # Check file size
                if os.path.exists(output_file):
                    size = os.path.getsize(output_file)
                    print(f"File size: {size:,} bytes")
                else:
                    print("⚠ Warning: Recording file not found")
            else:
                print("✗ Error stopping recording")
        else:
            print("✗ Failed to start recording")
    
    def lan_monitoring_demo(self):
        """Demonstrate LAN monitoring functionality."""
        print("\n--- LAN MONITORING DEMO ---")
        
        # Show local network info
        local_ip = self.lan_monitor.get_local_ip()
        network = ".".join(local_ip.split(".")[:-1]) + ".0/24"
        print(f"Local IP: {local_ip}")
        print(f"Network: {network}")
        
        print("\n1. Starting Zeroconf monitoring...")
        if self.lan_monitor.start_monitoring():
            print("✓ Zeroconf monitoring active")
            
            # Let it discover for a moment
            print("Scanning for services for 5 seconds...")
            time.sleep(5)
            
            if self.lan_monitor.devices:
                print(f"\nDiscovered {len(self.lan_monitor.devices)} services:")
                for name, info in self.lan_monitor.devices.items():
                    print(f"  - {name}")
                    print(f"    IP: {info.get('ip', 'Unknown')}")
                    print(f"    Type: {info.get('type', 'Unknown')}")
                    print(f"    Status: {info.get('status', 'Unknown')}")
            else:
                print("No Zeroconf services discovered")
        else:
            print("✗ Failed to start Zeroconf monitoring")
        
        print("\n2. Performing network scan...")
        print("Scanning for active devices (this may take a moment)...")
        
        def scan_progress():
            for i in range(10):
                print(".", end="", flush=True)
                time.sleep(0.5)
        
        # Start progress indicator
        progress_thread = threading.Thread(target=scan_progress)
        progress_thread.daemon = True
        progress_thread.start()
        
        # Perform scan
        active_devices = self.lan_monitor.scan_network()
        
        # Wait for progress to finish
        progress_thread.join()
        print()
        
        if active_devices:
            print(f"\nFound {len(active_devices)} active devices:")
            for device in active_devices:
                print(f"  - {device['ip']} (Status: {device['status']})")
        else:
            print("No active devices found")
        
        print("\nStopping monitoring...")
        self.lan_monitor.stop_monitoring()
        print("✓ Monitoring stopped")
    
    def full_demo(self):
        """Demonstrate all features together."""
        print("\n--- FULL FEATURE DEMO ---")
        print("This demo will start all components simultaneously")
        
        print("\n1. Starting VNC server...")
        vnc_ok = self.vnc_server.start_server()
        if vnc_ok:
            local_ip = self.lan_monitor.get_local_ip()
            print(f"✓ VNC server running on {local_ip}:{self.vnc_server.port}")
        else:
            print("✗ VNC server failed to start")
        
        print("\n2. Starting screen recording...")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        record_file = f"full_demo_{timestamp}.mp4"
        record_ok = self.screen_recorder.start_recording(record_file, fps=10)
        if record_ok:
            print(f"✓ Recording to: {record_file}")
        else:
            print("✗ Screen recording failed to start")
        
        print("\n3. Starting LAN monitoring...")
        monitor_ok = self.lan_monitor.start_monitoring()
        if monitor_ok:
            print("✓ LAN monitoring active")
        else:
            print("✗ LAN monitoring failed to start")
        
        if vnc_ok or record_ok or monitor_ok:
            print(f"\n🎉 Demo running with {sum([vnc_ok, record_ok, monitor_ok])} active components!")
            print("The server is now:")
            if vnc_ok:
                print("  • Accepting VNC connections")
            if record_ok:
                print("  • Recording screen activity")
            if monitor_ok:
                print("  • Monitoring network devices")
            
            print("\nPress Enter to stop all components...")
            input()
        
        # Cleanup
        print("\nStopping all components...")
        if vnc_ok:
            self.vnc_server.stop_server()
            print("✓ VNC server stopped")
        if record_ok:
            self.screen_recorder.stop_recording()
            print(f"✓ Recording saved to: {record_file}")
        if monitor_ok:
            self.lan_monitor.stop_monitoring()
            print("✓ LAN monitoring stopped")
    
    def status_check(self):
        """Show current status of all components."""
        print("\n--- STATUS CHECK ---")
        
        print("VNC Server:")
        if self.vnc_server.is_running:
            client_count = len(self.vnc_server.clients)
            print(f"  Status: Running (Port {self.vnc_server.port})")
            print(f"  Clients: {client_count} connected")
        else:
            print("  Status: Stopped")
        
        print("\nScreen Recorder:")
        if self.screen_recorder.is_recording:
            print("  Status: Recording active")
            if self.screen_recorder.output_file:
                print(f"  File: {self.screen_recorder.output_file}")
        else:
            print("  Status: Not recording")
        
        print("\nLAN Monitor:")
        device_count = len(self.lan_monitor.devices)
        print(f"  Discovered devices: {device_count}")
        if device_count > 0:
            for name, info in list(self.lan_monitor.devices.items())[:3]:  # Show first 3
                print(f"    - {name} ({info.get('ip', 'Unknown')})")
            if device_count > 3:
                print(f"    ... and {device_count - 3} more")
        
        local_ip = self.lan_monitor.get_local_ip()
        print(f"\nLocal IP: {local_ip}")
    
    def run(self):
        """Run the demo application."""
        print("Welcome to the Enhanced VNC Server demo!")
        print("This demo showcases the key features of the VNC server.")
        
        while self.running:
            try:
                self.show_menu()
                choice = input("Enter your choice (1-6): ").strip()
                
                if choice == "1":
                    self.vnc_server_demo()
                elif choice == "2":
                    self.screen_recording_demo()
                elif choice == "3":
                    self.lan_monitoring_demo()
                elif choice == "4":
                    self.full_demo()
                elif choice == "5":
                    self.status_check()
                elif choice == "6":
                    print("Exiting demo...")
                    break
                else:
                    print("Invalid choice. Please enter 1-6.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        self.cleanup()


def main():
    """Main entry point."""
    demo = VNCDemo()
    try:
        demo.run()
    except Exception as e:
        print(f"Demo error: {e}")
        demo.cleanup()
    finally:
        print("Demo ended. Thank you!")


if __name__ == "__main__":
    main()