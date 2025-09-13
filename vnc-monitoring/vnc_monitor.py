#!/usr/bin/env python3
"""
VNC Server Monitoring Agent

This script monitors the VNC server process and automatically restarts it if it's not running.
It provides real-time tracking and updates for the VNC server status.
"""

import os
import sys
import time
import logging
import subprocess
import signal
from typing import Optional


class VNCMonitor:
    """VNC Server monitoring and management class."""
    
    def __init__(self, vnc_command: str = "vncserver", display: str = ":1", 
                 check_interval: int = 30, log_file: str = "/var/log/vnc_monitor.log"):
        """
        Initialize VNC Monitor.
        
        Args:
            vnc_command: Command to start VNC server
            display: VNC display number (e.g., ":1")
            check_interval: Time in seconds between checks
            log_file: Path to log file
        """
        self.vnc_command = vnc_command
        self.display = display
        self.check_interval = check_interval
        self.log_file = log_file
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def is_vnc_running(self) -> bool:
        """
        Check if VNC server is running on the specified display.
        
        Returns:
            True if VNC server is running, False otherwise
        """
        try:
            # Check for VNC process using display
            result = subprocess.run(
                ["pgrep", "-f", f"Xvnc.*{self.display}"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error checking VNC status: {e}")
            return False
    
    def get_vnc_pid(self) -> Optional[int]:
        """
        Get the PID of the VNC server process.
        
        Returns:
            PID of VNC server or None if not found
        """
        try:
            result = subprocess.run(
                ["pgrep", "-f", f"Xvnc.*{self.display}"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split('\n')[0])
        except Exception as e:
            self.logger.error(f"Error getting VNC PID: {e}")
        return None
    
    def start_vnc_server(self) -> bool:
        """
        Start the VNC server.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            self.logger.info(f"Starting VNC server on display {self.display}")
            
            # Kill existing VNC server on this display first
            self.stop_vnc_server()
            
            # Start new VNC server
            result = subprocess.run(
                [self.vnc_command, self.display],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"VNC server started successfully on display {self.display}")
                return True
            else:
                self.logger.error(f"Failed to start VNC server: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception starting VNC server: {e}")
            return False
    
    def stop_vnc_server(self):
        """Stop the VNC server on the specified display."""
        try:
            # First try graceful shutdown
            subprocess.run([self.vnc_command, "-kill", self.display], 
                         capture_output=True, text=True)
            
            # Wait a moment for graceful shutdown
            time.sleep(2)
            
            # Force kill if still running
            pid = self.get_vnc_pid()
            if pid:
                self.logger.info(f"Force killing VNC server with PID {pid}")
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                
                # Final force kill if still running
                if self.is_vnc_running():
                    os.kill(pid, signal.SIGKILL)
                    
        except Exception as e:
            self.logger.error(f"Error stopping VNC server: {e}")
    
    def monitor(self):
        """Main monitoring loop."""
        self.logger.info("VNC Monitor starting...")
        self.running = True
        
        while self.running:
            try:
                if not self.is_vnc_running():
                    self.logger.warning(f"VNC server not running on display {self.display}")
                    
                    if self.start_vnc_server():
                        self.logger.info("VNC server restarted successfully")
                    else:
                        self.logger.error("Failed to restart VNC server")
                else:
                    pid = self.get_vnc_pid()
                    self.logger.debug(f"VNC server running on display {self.display} (PID: {pid})")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in monitoring loop: {e}")
                time.sleep(self.check_interval)
        
        self.logger.info("VNC Monitor stopped")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VNC Server Monitoring Agent")
    parser.add_argument("--display", default=":1", 
                       help="VNC display number (default: :1)")
    parser.add_argument("--interval", type=int, default=30,
                       help="Check interval in seconds (default: 30)")
    parser.add_argument("--log-file", default="/var/log/vnc_monitor.log",
                       help="Log file path (default: /var/log/vnc_monitor.log)")
    parser.add_argument("--vnc-command", default="vncserver",
                       help="VNC server command (default: vncserver)")
    parser.add_argument("--daemon", action="store_true",
                       help="Run as daemon (fork to background)")
    
    args = parser.parse_args()
    
    # Create monitor instance
    monitor = VNCMonitor(
        vnc_command=args.vnc_command,
        display=args.display,
        check_interval=args.interval,
        log_file=args.log_file
    )
    
    if args.daemon:
        # Fork to background
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process exits
                sys.exit(0)
        except OSError as e:
            print(f"Fork failed: {e}")
            sys.exit(1)
        
        # Child process continues
        os.setsid()
        os.umask(0)
    
    # Start monitoring
    monitor.monitor()


if __name__ == "__main__":
    main()