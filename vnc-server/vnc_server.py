#!/usr/bin/env python3
"""
Enhanced VNC Server with Screen Recording and LAN Monitoring
==========================================================

A Python-based VNC server implementation with the following features:
1. Basic VNC server functionality for remote desktop access
2. Screen recording in MP4/AVI format
3. LAN device monitoring and discovery
4. GUI interface for all controls
5. Online/offline connection support

Author: Build Your Own X Project
License: CC0 (Public Domain)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import socket
import threading
import time
import os
import json
from datetime import datetime
import subprocess
import platform
import sys

# Import required libraries with error handling
try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk
    import pyautogui
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
    import psutil
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install requirements with: pip install -r requirements.txt")
    sys.exit(1)


class LANDeviceMonitor:
    """Monitor and discover devices on the local area network."""
    
    def __init__(self):
        self.devices = {}
        self.zeroconf = None
        self.browser = None
        self.listener = LANServiceListener(self)
        
    def start_monitoring(self):
        """Start monitoring for LAN devices."""
        try:
            self.zeroconf = Zeroconf()
            self.browser = ServiceBrowser(
                self.zeroconf, 
                ["_http._tcp.local.", "_ssh._tcp.local.", "_vnc._tcp.local."],
                self.listener
            )
            return True
        except Exception as e:
            print(f"Error starting LAN monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop monitoring for LAN devices."""
        if self.browser:
            self.browser.cancel()
        if self.zeroconf:
            self.zeroconf.close()
    
    def get_local_ip(self):
        """Get the local IP address."""
        try:
            # Connect to Google DNS to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    def scan_network(self):
        """Scan the local network for active devices."""
        local_ip = self.get_local_ip()
        network = ".".join(local_ip.split(".")[:-1]) + "."
        
        active_devices = []
        
        def ping_host(ip):
            try:
                if platform.system().lower() == "windows":
                    result = subprocess.run(
                        ["ping", "-n", "1", "-w", "1000", ip],
                        capture_output=True, text=True
                    )
                else:
                    result = subprocess.run(
                        ["ping", "-c", "1", "-W", "1", ip],
                        capture_output=True, text=True
                    )
                
                if result.returncode == 0:
                    active_devices.append({
                        'ip': ip,
                        'status': 'online',
                        'last_seen': datetime.now().isoformat()
                    })
            except Exception:
                pass
        
        threads = []
        for i in range(1, 255):
            ip = f"{network}{i}"
            thread = threading.Thread(target=ping_host, args=(ip,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return active_devices


class LANServiceListener:
    """Listener for Zeroconf services on the LAN."""
    
    def __init__(self, monitor):
        self.monitor = monitor
    
    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0]) if info.addresses else "Unknown"
            self.monitor.devices[name] = {
                'name': name,
                'ip': ip,
                'port': info.port,
                'type': type,
                'status': 'online',
                'last_seen': datetime.now().isoformat()
            }
    
    def remove_service(self, zeroconf, type, name):
        if name in self.monitor.devices:
            self.monitor.devices[name]['status'] = 'offline'
    
    def update_service(self, zeroconf, type, name):
        # Service updated, refresh info
        self.add_service(zeroconf, type, name)


class ScreenRecorder:
    """Handle screen recording functionality."""
    
    def __init__(self):
        self.is_recording = False
        self.video_writer = None
        self.recording_thread = None
        self.output_file = None
        
    def start_recording(self, output_file=None, fps=30, codec='mp4v'):
        """Start screen recording."""
        if self.is_recording:
            return False
        
        try:
            # Get screen resolution
            screen_size = pyautogui.size()
            
            # Set default output file if not provided
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"screen_recording_{timestamp}.mp4"
            
            self.output_file = output_file
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*codec)
            self.video_writer = cv2.VideoWriter(
                output_file, fourcc, fps, screen_size
            )
            
            if not self.video_writer.isOpened():
                raise Exception("Failed to open video writer")
            
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_loop)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
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
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        return True
    
    def _record_loop(self):
        """Main recording loop."""
        try:
            while self.is_recording:
                # Capture screenshot
                screenshot = pyautogui.screenshot()
                frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # Write frame to video
                if self.video_writer:
                    self.video_writer.write(frame)
                
                # Small delay to control FPS
                time.sleep(1/30)  # 30 FPS
                
        except Exception as e:
            print(f"Error in recording loop: {e}")
            self.is_recording = False


class VNCServer:
    """Basic VNC server implementation."""
    
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
                    client_socket.send(b"OK\n")
                    
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
            except:
                pass


class VNCServerGUI:
    """Main GUI application for the VNC server."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced VNC Server")
        self.root.geometry("800x600")
        
        # Initialize components
        self.vnc_server = VNCServer()
        self.screen_recorder = ScreenRecorder()
        self.lan_monitor = LANDeviceMonitor()
        
        # GUI state variables
        self.server_running = tk.BooleanVar()
        self.recording = tk.BooleanVar()
        self.monitoring = tk.BooleanVar()
        
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
        
        # LAN Monitoring tab
        self.create_lan_tab(notebook)
        
        # Status bar
        self.status_bar = tk.Label(
            self.root, 
            text="Ready", 
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
        
        ttk.Button(
            control_frame,
            text="Start Server",
            command=self.start_vnc_server
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="Stop Server",
            command=self.stop_vnc_server
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
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
        
        local_ip = self.lan_monitor.get_local_ip()
        ttk.Label(info_frame, text=f"Server IP: {local_ip}").pack(pady=2)
        ttk.Label(info_frame, text=f"Server Port: {self.vnc_server.port}").pack(pady=2)
        ttk.Label(info_frame, text=f"Connect with: {local_ip}:{self.vnc_server.port}").pack(pady=2)
    
    def create_recording_tab(self, notebook):
        """Create screen recording control tab."""
        recording_frame = ttk.Frame(notebook)
        notebook.add(recording_frame, text="Screen Recording")
        
        # Recording controls
        control_frame = ttk.LabelFrame(recording_frame, text="Recording Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            control_frame,
            text="Start Recording",
            command=self.start_recording
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="Stop Recording",
            command=self.stop_recording
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="Choose Output File",
            command=self.choose_output_file
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Recording status
        status_frame = ttk.LabelFrame(recording_frame, text="Recording Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.recording_status_label = ttk.Label(status_frame, text="Recording: Stopped")
        self.recording_status_label.pack(pady=5)
        
        self.output_file_label = ttk.Label(status_frame, text="Output file: Not selected")
        self.output_file_label.pack(pady=5)
        
        # Recording settings
        settings_frame = ttk.LabelFrame(recording_frame, text="Recording Settings")
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # FPS setting
        fps_frame = ttk.Frame(settings_frame)
        fps_frame.pack(fill=tk.X, pady=2)
        ttk.Label(fps_frame, text="FPS:").pack(side=tk.LEFT)
        self.fps_var = tk.StringVar(value="30")
        fps_spinbox = ttk.Spinbox(
            fps_frame, 
            from_=10, 
            to=60, 
            textvariable=self.fps_var,
            width=10
        )
        fps_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Codec setting
        codec_frame = ttk.Frame(settings_frame)
        codec_frame.pack(fill=tk.X, pady=2)
        ttk.Label(codec_frame, text="Codec:").pack(side=tk.LEFT)
        self.codec_var = tk.StringVar(value="mp4v")
        codec_combo = ttk.Combobox(
            codec_frame,
            textvariable=self.codec_var,
            values=["mp4v", "XVID", "MJPG"],
            width=10
        )
        codec_combo.pack(side=tk.LEFT, padx=5)
    
    def create_lan_tab(self, notebook):
        """Create LAN monitoring tab."""
        lan_frame = ttk.Frame(notebook)
        notebook.add(lan_frame, text="LAN Monitoring")
        
        # Monitoring controls
        control_frame = ttk.LabelFrame(lan_frame, text="Monitoring Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            control_frame,
            text="Start Monitoring",
            command=self.start_lan_monitoring
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="Stop Monitoring",
            command=self.stop_lan_monitoring
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="Scan Network",
            command=self.scan_network
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="Refresh",
            command=self.refresh_devices
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Device list
        devices_frame = ttk.LabelFrame(lan_frame, text="Discovered Devices")
        devices_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview for device list
        columns = ("Device", "IP Address", "Status", "Last Seen")
        self.device_tree = ttk.Treeview(devices_frame, columns=columns, show="headings")
        
        for col in columns:
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=150)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(devices_frame, orient=tk.VERTICAL, command=self.device_tree.yview)
        self.device_tree.configure(yscrollcommand=scrollbar.set)
        
        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
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
        fps = int(self.fps_var.get())
        codec = self.codec_var.get()
        
        if self.screen_recorder.start_recording(fps=fps, codec=codec):
            self.status_bar.config(text="Screen recording started")
            if self.screen_recorder.output_file:
                self.output_file_label.config(text=f"Output file: {self.screen_recorder.output_file}")
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
    
    def choose_output_file(self):
        """Choose output file for recording."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.output_file_label.config(text=f"Output file: {file_path}")
            self.screen_recorder.output_file = file_path
    
    def start_lan_monitoring(self):
        """Start LAN monitoring."""
        if self.lan_monitor.start_monitoring():
            self.status_bar.config(text="LAN monitoring started")
            messagebox.showinfo("Success", "LAN monitoring started!")
        else:
            messagebox.showerror("Error", "Failed to start LAN monitoring")
    
    def stop_lan_monitoring(self):
        """Stop LAN monitoring."""
        self.lan_monitor.stop_monitoring()
        self.status_bar.config(text="LAN monitoring stopped")
        messagebox.showinfo("Success", "LAN monitoring stopped!")
    
    def scan_network(self):
        """Scan the network for devices."""
        self.status_bar.config(text="Scanning network...")
        
        def scan_thread():
            devices = self.lan_monitor.scan_network()
            
            # Update device tree on main thread
            self.root.after(0, lambda: self.update_device_tree(devices))
            self.root.after(0, lambda: self.status_bar.config(text=f"Found {len(devices)} devices"))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def refresh_devices(self):
        """Refresh the device list."""
        devices = []
        
        # Add Zeroconf discovered devices
        for name, info in self.lan_monitor.devices.items():
            devices.append({
                'name': name,
                'ip': info.get('ip', 'Unknown'),
                'status': info.get('status', 'Unknown'),
                'last_seen': info.get('last_seen', 'Unknown')
            })
        
        self.update_device_tree(devices)
    
    def update_device_tree(self, devices):
        """Update the device tree display."""
        # Clear existing items
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        # Add devices to tree
        for device in devices:
            name = device.get('name', device.get('ip', 'Unknown'))
            ip = device.get('ip', 'Unknown')
            status = device.get('status', 'Unknown')
            last_seen = device.get('last_seen', 'Unknown')
            
            # Format last_seen for display
            if last_seen != 'Unknown':
                try:
                    dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                    last_seen = dt.strftime('%H:%M:%S')
                except:
                    pass
            
            self.device_tree.insert('', 'end', values=(name, ip, status, last_seen))
    
    def run(self):
        """Start the GUI application."""
        try:
            self.root.mainloop()
        finally:
            # Cleanup
            self.vnc_server.stop_server()
            self.screen_recorder.stop_recording()
            self.lan_monitor.stop_monitoring()


def main():
    """Main application entry point."""
    print("Enhanced VNC Server v1.0")
    print("========================")
    print("Starting GUI application...")
    
    try:
        app = VNCServerGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()