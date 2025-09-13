#!/usr/bin/env python3
"""
Python VNC Server - Main Application
Complete VNC server implementation with web-based GUI.
"""

import argparse
import sys
import time
import signal
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from vnc_server import VNCServer
from web_gui import VNCWebServer


class VNCServerApp:
    """Main VNC Server application."""
    
    def __init__(self):
        self.vnc_server = None
        self.web_server = None
        self.running = False
        
    def create_vnc_server(self, args) -> VNCServer:
        """Create VNC server with command line arguments."""
        server = VNCServer(
            host=args.host,
            port=args.port,
            use_auth=args.auth,
            max_connections=args.max_connections
        )
        
        # Configure screen settings
        server.configure(
            screen_width=args.width,
            screen_height=args.height,
            frame_rate=args.fps
        )
        
        return server
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run(self, args):
        """Run the VNC server application."""
        print("🖥️  Python VNC Server")
        print("=" * 50)
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Create VNC server
        print("Creating VNC server...")
        self.vnc_server = self.create_vnc_server(args)
        
        # Add initial users if authentication is enabled
        if args.auth:
            if args.admin_password:
                self.vnc_server.add_user('admin', args.admin_password)
                print(f"Added admin user with password: {args.admin_password}")
            else:
                self.vnc_server.add_user('admin', 'password')
                print("Added admin user with default password: password")
        
        # Start VNC server if requested
        if args.start_vnc:
            print(f"Starting VNC server on {args.host}:{args.port}...")
            if self.vnc_server.start():
                print("✅ VNC server started successfully")
            else:
                print("❌ Failed to start VNC server")
                return False
        
        # Start web GUI if requested
        if args.gui:
            print(f"Starting web GUI on {args.gui_host}:{args.gui_port}...")
            self.web_server = VNCWebServer(
                self.vnc_server, 
                host=args.gui_host, 
                port=args.gui_port
            )
            
            if self.web_server.start():
                print("✅ Web GUI started successfully")
                print(f"🌐 Open http://{args.gui_host}:{args.gui_port} in your browser")
            else:
                print("❌ Failed to start web GUI")
                return False
        
        # Print status
        self.print_status()
        
        # Keep running
        self.running = True
        try:
            if args.gui or args.start_vnc:
                print("\nPress Ctrl+C to stop the server")
                while self.running:
                    time.sleep(1)
            else:
                print("No services started. Use --start-vnc or --gui options.")
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.shutdown()
        
        return True
    
    def print_status(self):
        """Print current server status."""
        print("\n📊 Server Status:")
        print("-" * 30)
        
        if self.vnc_server:
            status = self.vnc_server.get_status()
            print(f"VNC Server: {'🟢 Running' if status['running'] else '🔴 Stopped'}")
            if status['running']:
                print(f"  Address: {status['host']}:{status['port']}")
                print(f"  Connections: {status['active_connections']}/{status['max_connections']}")
                print(f"  Authentication: {'Enabled' if status['use_auth'] else 'Disabled'}")
                print(f"  Screen Size: {status['screen_size'][0]}x{status['screen_size'][1]}")
        
        if self.web_server:
            print(f"Web GUI: {'🟢 Running' if self.web_server.running else '🔴 Stopped'}")
            if self.web_server.running:
                print(f"  URL: http://{self.web_server.host}:{self.web_server.port}")
        
        print()
    
    def shutdown(self):
        """Shutdown all services."""
        self.running = False
        
        if self.web_server:
            print("Stopping web GUI...")
            self.web_server.stop()
        
        if self.vnc_server:
            print("Stopping VNC server...")
            self.vnc_server.stop()
        
        print("✅ All services stopped")


def create_argument_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Python VNC Server with Web GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Start with web GUI only
  %(prog)s --start-vnc                        # Start VNC server and web GUI
  %(prog)s --start-vnc --no-gui               # Start VNC server without GUI
  %(prog)s --port 5901 --gui-port 8081        # Custom ports
  %(prog)s --no-auth                          # Disable authentication
  %(prog)s --width 1920 --height 1080         # Custom screen resolution
        """
    )
    
    # VNC Server options
    vnc_group = parser.add_argument_group('VNC Server Options')
    vnc_group.add_argument('--host', default='0.0.0.0',
                          help='VNC server host (default: 0.0.0.0)')
    vnc_group.add_argument('--port', type=int, default=5900,
                          help='VNC server port (default: 5900)')
    vnc_group.add_argument('--start-vnc', action='store_true',
                          help='Start VNC server immediately')
    vnc_group.add_argument('--max-connections', type=int, default=5,
                          help='Maximum concurrent connections (default: 5)')
    
    # Authentication options
    auth_group = parser.add_argument_group('Authentication Options')
    auth_group.add_argument('--auth', action='store_true', default=True,
                           help='Enable authentication (default: enabled)')
    auth_group.add_argument('--no-auth', action='store_false', dest='auth',
                           help='Disable authentication')
    auth_group.add_argument('--admin-password', default=None,
                           help='Set admin password (default: "password")')
    
    # Screen options
    screen_group = parser.add_argument_group('Screen Options')
    screen_group.add_argument('--width', type=int, default=1024,
                             help='Screen width (default: 1024)')
    screen_group.add_argument('--height', type=int, default=768,
                             help='Screen height (default: 768)')
    screen_group.add_argument('--fps', type=int, default=10,
                             help='Frame rate (default: 10)')
    
    # GUI options
    gui_group = parser.add_argument_group('Web GUI Options')
    gui_group.add_argument('--gui', action='store_true', default=True,
                          help='Start web GUI (default: enabled)')
    gui_group.add_argument('--no-gui', action='store_false', dest='gui',
                          help='Disable web GUI')
    gui_group.add_argument('--gui-host', default='127.0.0.1',
                          help='Web GUI host (default: 127.0.0.1)')
    gui_group.add_argument('--gui-port', type=int, default=8080,
                          help='Web GUI port (default: 8080)')
    
    # Other options
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    return parser


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    if args.port < 1 or args.port > 65535:
        print("Error: VNC port must be between 1 and 65535")
        return 1
    
    if args.gui_port < 1 or args.gui_port > 65535:
        print("Error: GUI port must be between 1 and 65535")
        return 1
    
    if args.max_connections < 1:
        print("Error: Max connections must be at least 1")
        return 1
    
    if args.width < 320 or args.height < 240:
        print("Error: Screen dimensions must be at least 320x240")
        return 1
    
    if args.fps < 1 or args.fps > 60:
        print("Error: Frame rate must be between 1 and 60")
        return 1
    
    # Create and run application
    app = VNCServerApp()
    
    try:
        success = app.run(args)
        return 0 if success else 1
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())