# VNC Monitoring Agent

A robust Python-based monitoring agent that ensures your VNC (Virtual Network Computing) server stays running with automatic restart capabilities and real-time status tracking.

## Features

- **Automatic VNC Server Monitoring**: Continuously monitors VNC server process
- **Auto-restart Functionality**: Automatically restarts VNC server if it stops or crashes
- **Systemd Integration**: Runs as a system service with proper logging and management
- **Configurable Monitoring**: Customizable check intervals and display settings
- **Comprehensive Logging**: Detailed logging for troubleshooting and monitoring
- **Signal Handling**: Graceful shutdown on system signals
- **Security Hardened**: Systemd service with security restrictions

## Requirements

- Python 3.6 or higher
- VNC Server (TigerVNC, TightVNC, or similar)
- Systemd (for service management)
- Root privileges (for system service installation)

## Quick Installation

1. **Clone or download the VNC monitoring files**
2. **Run the installation script**:
   ```bash
   sudo ./install.sh
   ```
3. **Start the service**:
   ```bash
   sudo systemctl start vnc-monitor
   ```

## Manual Installation

### 1. Install Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip tigervnc-standalone-server
```

**CentOS/RHEL/Fedora:**
```bash
# CentOS/RHEL
sudo yum install python3 python3-pip tigervnc-server

# Fedora
sudo dnf install python3 python3-pip tigervnc-server
```

### 2. Copy Files

```bash
# Create installation directory
sudo mkdir -p /opt/vnc-monitoring

# Copy Python script and configuration
sudo cp vnc_monitor.py /opt/vnc-monitoring/
sudo cp vnc_monitor.conf /opt/vnc-monitoring/
sudo chmod +x /opt/vnc-monitoring/vnc_monitor.py

# Copy systemd service file
sudo cp vnc-monitor.service /etc/systemd/system/
```

### 3. Enable and Start Service

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable vnc-monitor

# Start the service
sudo systemctl start vnc-monitor
```

## Configuration

Edit the configuration file at `/opt/vnc-monitoring/vnc_monitor.conf`:

```bash
# VNC Display number (e.g., :1, :2, etc.)
VNC_DISPLAY=:1

# Check interval in seconds
CHECK_INTERVAL=30

# VNC server command
VNC_COMMAND=vncserver

# Log file location
LOG_FILE=/var/log/vnc_monitor.log

# Run as daemon
DAEMON=true
```

## Usage

### Service Management

```bash
# Start the service
sudo systemctl start vnc-monitor

# Stop the service
sudo systemctl stop vnc-monitor

# Restart the service
sudo systemctl restart vnc-monitor

# Check service status
sudo systemctl status vnc-monitor

# Enable service to start on boot
sudo systemctl enable vnc-monitor

# Disable service from starting on boot
sudo systemctl disable vnc-monitor
```

### Manual Execution

You can also run the monitor script directly for testing:

```bash
# Run with default settings
python3 vnc_monitor.py

# Run with custom display and interval
python3 vnc_monitor.py --display :2 --interval 60

# Run as daemon
python3 vnc_monitor.py --daemon

# Show help
python3 vnc_monitor.py --help
```

### Command Line Options

- `--display DISPLAY`: VNC display number (default: :1)
- `--interval INTERVAL`: Check interval in seconds (default: 30)
- `--log-file LOG_FILE`: Log file path (default: /var/log/vnc_monitor.log)
- `--vnc-command VNC_COMMAND`: VNC server command (default: vncserver)
- `--daemon`: Run as daemon (fork to background)

## Monitoring and Logs

### View Real-time Logs

```bash
# View service logs
sudo journalctl -u vnc-monitor -f

# View log file directly
sudo tail -f /var/log/vnc_monitor.log
```

### Log Levels

The monitoring agent logs the following events:
- **INFO**: Normal operation and status updates
- **WARNING**: VNC server not running (before restart attempt)
- **ERROR**: Failed restart attempts or system errors
- **DEBUG**: Detailed process information (when debug logging is enabled)

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure the script is run with appropriate permissions
   - Check that log directory is writable

2. **VNC Server Won't Start**
   - Verify VNC server is properly installed
   - Check VNC server configuration
   - Ensure display number is not already in use

3. **Service Won't Start**
   - Check systemd service status: `sudo systemctl status vnc-monitor`
   - Review logs: `sudo journalctl -u vnc-monitor`
   - Verify file permissions and paths

### Debug Mode

Run the script manually to see detailed output:

```bash
python3 vnc_monitor.py --interval 10 --log-file /tmp/vnc_debug.log
```

## Security Considerations

The systemd service runs with several security restrictions:
- `NoNewPrivileges=true`: Prevents privilege escalation
- `PrivateTmp=true`: Uses private temporary directory
- `ProtectSystem=strict`: Read-only access to most system directories
- `ProtectHome=true`: No access to user home directories
- Limited capabilities and file system access

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop vnc-monitor
sudo systemctl disable vnc-monitor

# Remove files
sudo rm /etc/systemd/system/vnc-monitor.service
sudo rm -rf /opt/vnc-monitoring

# Reload systemd
sudo systemctl daemon-reload
```

Or use the installation script:

```bash
sudo ./install.sh --uninstall
```

## License

This VNC monitoring agent is part of the "Build Your Own X" project and is provided as educational material for learning system monitoring and service management concepts.