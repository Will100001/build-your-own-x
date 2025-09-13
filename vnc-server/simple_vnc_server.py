#!/usr/bin/env python3
"""
Basic VNC Server Implementation (Standard Library Only)
======================================================

A simplified VNC server implementation using only Python standard library.
This version demonstrates the core networking and architecture concepts
without requiring external dependencies.

Features:
- Basic VNC server socket handling
- Simple screen capture (text-based simulation)
- Network device discovery using built-in tools
- Basic GUI using tkinter (included in Python)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import time
import os
import json
import subprocess
import platform
import sys
from datetime import datetime


class SimpleVNCServer:
    """Basic VNC server implementation using standard library only."""
    
    def __init__(self, host='0.0.0.0', port=5900):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.is_running = False
        self.server_thread = None
        
    def start_server(self):
        """Start the VNC server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.is_running = True
            self.server_thread = threading.Thread(target=self._accept_connections)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            print(f"VNC Server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"Error starting VNC server: {e}")
            return False
    
    def stop_server(self):
        """Stop the VNC server."""
        self.is_running = False
        
        # Close all client connections
        for client in self.clients[:]:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("VNC Server stopped")
        return True
    
    def _accept_connections(self):
        """Accept incoming client connections."""
        while self.is_running:
            try:
                if self.server_socket:
                    client_socket, addr = self.server_socket.accept()
                    print(f"Client connected from {addr}")
                    
                    self.clients.append(client_socket)
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
            except Exception as e:
                if self.is_running:
                    print(f"Error accepting connection: {e}")
                break
    
    def _handle_client(self, client_socket, addr):
        """Handle individual client connection."""
        try:
            # Send basic VNC handshake
            client_socket.send(b"RFB 003.008\n")
            
            # Simple message loop
            while self.is_running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Echo back for basic functionality
                    response = f"VNC Server Response: {datetime.now()}\n".encode()
                    client_socket.send(response)
                    
                except socket.timeout:
                    continue
                except Exception:
                    break
                    
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            try:
                client_socket.close()
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
                print(f"Client {addr} disconnected")
            except:
                pass


class SimpleScreenRecorder:
    """Simple screen recording simulation using standard library."""
    
    def __init__(self):
        self.is_recording = False
        self.recording_thread = None
        self.output_file = None
        self.start_time = None
        
    def start_recording(self, output_file=None):
        """Start screen recording simulation."""
        if self.is_recording:
            return False
        
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"screen_recording_{timestamp}.log"
            
            self.output_file = output_file
            self.start_time = datetime.now()
            self.is_recording = True
            
            self.recording_thread = threading.Thread(target=self._record_loop)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            print(f"Screen recording started: {output_file}")
            return True
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            return False
    
    def stop_recording(self):
        """Stop screen recording."""
        if not self.is_recording:
            return False
        
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join(timeout=5)
        
        print(f"Screen recording stopped: {self.output_file}")
        return True
    
    def _record_loop(self):
        """Simulate screen recording by logging system information."""
        try:
            with open(self.output_file, 'w') as f:
                f.write(f"Screen Recording Started: {self.start_time}\n")
                f.write("="*50 + "\n")
                
                frame_count = 0
                while self.is_recording:
                    frame_count += 1
                    timestamp = datetime.now()
                    
                    # Simulate screen capture by recording system state
                    f.write(f"Frame {frame_count}: {timestamp}\n")
                    f.write(f"  System time: {time.time()}\n")
                    f.write(f"  Active threads: {threading.active_count()}\n")
                    f.flush()
                    
                    time.sleep(1)  # 1 FPS for demo
                
                f.write("="*50 + "\n")
                f.write(f"Recording ended: {datetime.now()}\n")
                f.write(f"Total frames: {frame_count}\n")
                
        except Exception as e:
            print(f"Error in recording loop: {e}")
            self.is_recording = False


class SimpleNetworkMonitor:
    """Simple network monitoring using standard library tools."""
    
    def __init__(self):
        self.devices = {}
        self.monitoring = False
        self.monitor_thread = None
        
    def get_local_ip(self):
        """Get the local IP address."""
        try:
            # Connect to Google DNS to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    def start_monitoring(self):
        """Start network monitoring."""
        if self.monitoring:
            return True
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        print("Network monitoring started")
        return True
    
    def stop_monitoring(self):
        """Stop network monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Network monitoring stopped")
    
    def scan_network(self):
        """Scan the local network for active devices."""
        local_ip = self.get_local_ip()
        network = ".".join(local_ip.split(".")[:-1]) + "."
        
        active_devices = []
        
        # Test a few key IPs for demonstration
        test_ips = [
            f"{network}1",    # Typical gateway
            f"{network}254",  # Alternative gateway
            local_ip,         # Self
            "8.8.8.8",       # Google DNS (external test)
        ]
        
        for ip in test_ips:
            if self._ping_host(ip):
                active_devices.append({
                    'ip': ip,
                    'status': 'online',
                    'last_seen': datetime.now().isoformat(),
                    'type': 'host'
                })
        
        # Update internal device list
        for device in active_devices:
            self.devices[device['ip']] = device
        
        return active_devices
    
    def _ping_host(self, ip):
        """Ping a host to check if it's active."""
        try:
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
            
            return result.returncode == 0
        except:
            return False
    
    def _monitor_loop(self):
        """Continuous monitoring loop."""
        while self.monitoring:
            try:
                # Periodic network scan
                self.scan_network()
                time.sleep(30)  # Scan every 30 seconds
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(10)


class SimpleVNCGUI:
    """Simplified GUI for the VNC server using only tkinter."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simple VNC Server")
        self.root.geometry("700x500")
        
        # Initialize components
        self.vnc_server = SimpleVNCServer()
        self.screen_recorder = SimpleScreenRecorder()
        self.network_monitor = SimpleNetworkMonitor()
        
        self.create_widgets()
        self.setup_status_updates()
        
    def create_widgets(self):
        """Create and arrange GUI widgets."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # VNC Server tab
        self.create_vnc_tab(notebook)
        
        # Screen Recording tab
        self.create_recording_tab(notebook)
        
        # Network Monitoring tab
        self.create_network_tab(notebook)
        
        # Status bar
        self.status_bar = tk.Label(
            self.root, 
            text="Ready - Using standard library implementation", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_vnc_tab(self, notebook):
        """Create VNC server control tab."""
        vnc_frame = ttk.Frame(notebook)
        notebook.add(vnc_frame, text="VNC Server")
        
        # Server controls
        control_frame = ttk.LabelFrame(vnc_frame, text="Server Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(pady=5)
        
        ttk.Button(
            btn_frame,
            text="Start Server",
            command=self.start_vnc_server
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Stop Server",
            command=self.stop_vnc_server
        ).pack(side=tk.LEFT, padx=5)
        
        # Server status
        status_frame = ttk.LabelFrame(vnc_frame, text="Server Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.server_status_label = ttk.Label(status_frame, text="Server: Stopped")
        self.server_status_label.pack(pady=5)
        
        self.client_count_label = ttk.Label(status_frame, text="Connected clients: 0")
        self.client_count_label.pack(pady=5)
        
        # Connection info
        info_frame = ttk.LabelFrame(vnc_frame, text="Connection Information")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        local_ip = self.network_monitor.get_local_ip()
        ttk.Label(info_frame, text=f"Server IP: {local_ip}").pack(pady=2)
        ttk.Label(info_frame, text=f"Server Port: {self.vnc_server.port}").pack(pady=2)
        ttk.Label(info_frame, text=f"Connect with: {local_ip}:{self.vnc_server.port}").pack(pady=2)
        
        # Instructions
        inst_frame = ttk.LabelFrame(vnc_frame, text="Instructions")
        inst_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        instructions = tk.Text(inst_frame, wrap=tk.WORD, height=8)
        instructions.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        instructions.insert(tk.END, 
            "This is a basic VNC server implementation for demonstration.\n\n"
            "To test the server:\n"
            "1. Start the server using the button above\n"
            "2. Use telnet or netcat to connect:\n"
            f"   telnet {local_ip} {self.vnc_server.port}\n"
            "3. The server will respond with basic VNC handshake\n\n"
            "Note: This is a simplified implementation for educational purposes."
        )
        instructions.config(state=tk.DISABLED)
    
    def create_recording_tab(self, notebook):
        """Create screen recording control tab."""
        recording_frame = ttk.Frame(notebook)
        notebook.add(recording_frame, text="Screen Recording")
        
        # Recording controls
        control_frame = ttk.LabelFrame(recording_frame, text="Recording Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(pady=5)
        
        ttk.Button(
            btn_frame,
            text="Start Recording",
            command=self.start_recording
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Stop Recording",
            command=self.stop_recording
        ).pack(side=tk.LEFT, padx=5)
        
        # Recording status
        status_frame = ttk.LabelFrame(recording_frame, text="Recording Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.recording_status_label = ttk.Label(status_frame, text="Recording: Stopped")
        self.recording_status_label.pack(pady=5)
        
        self.output_file_label = ttk.Label(status_frame, text="Output file: Not set")
        self.output_file_label.pack(pady=5)
        
        # Recording info
        info_frame = ttk.LabelFrame(recording_frame, text="Recording Information")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = tk.Text(info_frame, wrap=tk.WORD, height=10)
        info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        info_text.insert(tk.END,
            "Screen Recording Simulation\n"
            "==========================\n\n"
            "This implementation simulates screen recording by creating a log file\n"
            "that records system information over time.\n\n"
            "In a full implementation, this would:\n"
            "• Capture actual screen content using libraries like PIL or OpenCV\n"
            "• Encode video using codecs like H.264\n"
            "• Save in formats like MP4 or AVI\n\n"
            "The simulation creates a text log showing:\n"
            "• Timestamp for each 'frame'\n"
            "• System information\n"
            "• Thread activity\n\n"
            "This demonstrates the recording architecture without requiring\n"
            "external dependencies."
        )
        info_text.config(state=tk.DISABLED)
    
    def create_network_tab(self, notebook):
        """Create network monitoring tab."""
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="Network Monitoring")
        
        # Monitoring controls
        control_frame = ttk.LabelFrame(network_frame, text="Monitoring Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(pady=5)
        
        ttk.Button(
            btn_frame,
            text="Start Monitoring",
            command=self.start_network_monitoring
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Stop Monitoring",
            command=self.stop_network_monitoring
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Scan Network",
            command=self.scan_network
        ).pack(side=tk.LEFT, padx=5)
        
        # Device list
        devices_frame = ttk.LabelFrame(network_frame, text="Discovered Devices")
        devices_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create listbox for devices
        self.device_listbox = tk.Listbox(devices_frame)
        self.device_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Network info
        local_ip = self.network_monitor.get_local_ip()
        network = ".".join(local_ip.split(".")[:-1]) + ".0/24"
        
        info_label = ttk.Label(
            devices_frame, 
            text=f"Local IP: {local_ip} | Network: {network}"
        )
        info_label.pack(pady=5)
    
    def setup_status_updates(self):
        """Setup periodic status updates."""
        self.update_status()
        self.root.after(1000, self.setup_status_updates)
    
    def update_status(self):
        """Update status displays."""
        # Update VNC server status
        if self.vnc_server.is_running:
            self.server_status_label.config(text="Server: Running")
            client_count = len(self.vnc_server.clients)
            self.client_count_label.config(text=f"Connected clients: {client_count}")
        else:
            self.server_status_label.config(text="Server: Stopped")
            self.client_count_label.config(text="Connected clients: 0")
        
        # Update recording status
        if self.screen_recorder.is_recording:
            self.recording_status_label.config(text="Recording: Active")
            if self.screen_recorder.output_file:
                self.output_file_label.config(text=f"Output file: {self.screen_recorder.output_file}")
        else:
            self.recording_status_label.config(text="Recording: Stopped")
    
    def start_vnc_server(self):
        """Start the VNC server."""
        if self.vnc_server.start_server():
            self.status_bar.config(text="VNC Server started successfully")
            messagebox.showinfo("Success", "VNC Server started successfully!")
        else:
            messagebox.showerror("Error", "Failed to start VNC Server")
    
    def stop_vnc_server(self):
        """Stop the VNC server."""
        if self.vnc_server.stop_server():
            self.status_bar.config(text="VNC Server stopped")
            messagebox.showinfo("Success", "VNC Server stopped successfully!")
        else:
            messagebox.showerror("Error", "Failed to stop VNC Server")
    
    def start_recording(self):
        """Start screen recording."""
        if self.screen_recorder.start_recording():
            self.status_bar.config(text="Screen recording started")
            messagebox.showinfo("Success", "Screen recording started!")
        else:
            messagebox.showerror("Error", "Failed to start screen recording")
    
    def stop_recording(self):
        """Stop screen recording."""
        if self.screen_recorder.stop_recording():
            self.status_bar.config(text="Screen recording stopped")
            messagebox.showinfo("Success", f"Recording saved to {self.screen_recorder.output_file}")
        else:
            messagebox.showerror("Error", "Failed to stop screen recording")
    
    def start_network_monitoring(self):
        """Start network monitoring."""
        if self.network_monitor.start_monitoring():
            self.status_bar.config(text="Network monitoring started")
            messagebox.showinfo("Success", "Network monitoring started!")
        else:
            messagebox.showerror("Error", "Failed to start network monitoring")
    
    def stop_network_monitoring(self):
        """Stop network monitoring."""
        self.network_monitor.stop_monitoring()
        self.status_bar.config(text="Network monitoring stopped")
        messagebox.showinfo("Success", "Network monitoring stopped!")
    
    def scan_network(self):
        """Scan the network for devices."""
        self.status_bar.config(text="Scanning network...")
        
        def scan_thread():
            devices = self.network_monitor.scan_network()
            
            # Update device list on main thread
            self.root.after(0, lambda: self.update_device_list(devices))
            self.root.after(0, lambda: self.status_bar.config(text=f"Found {len(devices)} devices"))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def update_device_list(self, devices):
        """Update the device list display."""
        self.device_listbox.delete(0, tk.END)
        
        for device in devices:
            ip = device.get('ip', 'Unknown')
            status = device.get('status', 'Unknown')
            device_type = device.get('type', 'Unknown')
            
            display_text = f"{ip} - {status} ({device_type})"
            self.device_listbox.insert(tk.END, display_text)
    
    def run(self):
        """Start the GUI application."""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        finally:
            self.cleanup()
    
    def on_closing(self):
        """Handle window closing event."""
        self.cleanup()
        self.root.destroy()
    
    def cleanup(self):
        """Cleanup all resources."""
        self.vnc_server.stop_server()
        self.screen_recorder.stop_recording()
        self.network_monitor.stop_monitoring()


def main():
    """Main application entry point."""
    print("Simple VNC Server v1.0 (Standard Library)")
    print("=========================================")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--no-gui":
        # Command line mode
        print("Running in command line mode...")
        
        server = SimpleVNCServer()
        monitor = SimpleNetworkMonitor()
        
        try:
            print("Starting VNC server...")
            server.start_server()
            
            print("Starting network monitoring...")
            monitor.start_monitoring()
            
            print("Server running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            server.stop_server()
            monitor.stop_monitoring()
    else:
        # GUI mode
        print("Starting GUI application...")
        try:
            app = SimpleVNCGUI()
            app.run()
        except Exception as e:
            print(f"GUI Error: {e}")


if __name__ == "__main__":
    main()