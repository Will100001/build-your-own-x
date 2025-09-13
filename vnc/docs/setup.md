# Setup Guide

This guide will help you set up the VNC Server and Viewer on different platforms.

## System Requirements

### General Requirements
- Python 3.8 or higher
- 2GB RAM minimum (4GB recommended)
- Network connection
- Administrative privileges for installation

### Platform-Specific Requirements

#### Windows
- Windows 10 or higher (64-bit recommended)
- Visual C++ Redistributable 2019 or higher
- Windows Defender or antivirus with real-time protection disabled during setup

#### Linux
- Ubuntu 20.04+ / Debian 10+ / CentOS 8+ / Fedora 32+
- X11 display server (Wayland support limited)
- python3-dev and python3-pip packages

#### macOS
- macOS 10.15 (Catalina) or higher
- Xcode Command Line Tools
- Homebrew (recommended)

#### Android
- Android 7.0 (API level 24) or higher
- ARMv7 or ARM64 processor
- 100MB free storage space

## Installation

### Option 1: From Source (All Platforms)

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/codecrafters-io/build-your-own-x.git
   cd build-your-own-x/vnc
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the applications**
   ```bash
   # Start VNC Server
   python server/vnc_server.py --port 5900 --password mypassword
   
   # Start VNC Viewer (in another terminal)
   python viewer/vnc_viewer.py
   ```

### Option 2: Pre-built Binaries

#### Windows
1. Download the Windows installer from the releases page
2. Run `VNC-Setup.exe` as Administrator
3. Follow the installation wizard
4. Launch from Start Menu or Desktop shortcuts

#### Linux
1. Download the Linux tarball from the releases page
2. Extract to desired location:
   ```bash
   tar -xzf vnc-linux-x64.tar.gz
   cd vnc-linux-x64
   ```
3. Run the applications:
   ```bash
   ./vnc-server
   ./vnc-viewer
   ```

#### Android
1. Download the APK file from the releases page
2. Enable "Unknown sources" in Android settings
3. Install the APK file
4. Launch "VNC Viewer" from the app drawer

## Initial Configuration

### VNC Server Configuration

Create a configuration file `~/.vnc/config` (or `%USERPROFILE%\.vnc\config` on Windows):

```ini
[server]
port = 5900
password = your_secure_password
max_clients = 5
screen_update_rate = 30

[security]
authentication = vnc_auth
allow_hosts = 192.168.1.0/24,127.0.0.1

[encoding]
preferred_encoding = zrle
compression_level = 6
jpeg_quality = 75
```

### VNC Viewer Configuration

Create a configuration file `~/.vnc/viewer.conf`:

```ini
[connection]
default_host = localhost
default_port = 5900
auto_reconnect = true
keep_alive_interval = 30

[display]
scaling_mode = fit_window
color_depth = 24
cursor_local = true

[input]
keyboard_layout = us
mouse_sensitivity = 1.0
```

## Firewall Configuration

### Windows Firewall
1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Click "Change Settings" and then "Allow another app..."
4. Add the VNC Server executable
5. Check both "Private" and "Public" if needed

### Linux iptables
```bash
# Allow VNC port 5900
sudo iptables -A INPUT -p tcp --dport 5900 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

### Linux ufw (Ubuntu)
```bash
sudo ufw allow 5900/tcp
```

### macOS
1. Open System Preferences > Security & Privacy > Firewall
2. Click "Firewall Options"
3. Add the VNC Server application
4. Set to "Allow incoming connections"

## Network Configuration

### Port Forwarding (for external access)
If you want to access your VNC server from outside your local network:

1. Access your router's configuration page
2. Navigate to Port Forwarding settings
3. Add a rule:
   - External Port: 5900 (or different for security)
   - Internal Port: 5900
   - Internal IP: Your computer's local IP
   - Protocol: TCP

**Security Warning**: Only do this if you have a strong password and understand the security implications.

### SSH Tunneling (Recommended for external access)
Instead of direct port forwarding, use SSH tunneling:

```bash
# On the client machine:
ssh -L 5900:localhost:5900 user@your-server.com

# Then connect VNC viewer to localhost:5900
```

## Troubleshooting Setup Issues

### Common Issues

#### "Permission denied" on Linux
```bash
sudo chown -R $USER:$USER ~/.vnc
chmod 600 ~/.vnc/config
```

#### "Module not found" errors
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### "Screen capture not working" on Linux
```bash
# Install additional dependencies
sudo apt-get install python3-tk python3-dev
```

#### "Connection refused"
1. Check if the server is running: `netstat -an | grep 5900`
2. Verify firewall settings
3. Check server logs for error messages

#### High CPU usage
1. Reduce screen update rate in server configuration
2. Use more efficient encoding (ZRLE instead of Raw)
3. Reduce color depth if acceptable

### Getting Help

1. Check the troubleshooting guide: `docs/troubleshooting.md`
2. Review server and client logs
3. Test with local connections first
4. Verify all dependencies are installed correctly

## Next Steps

After successful setup:
1. Read the usage guide: `docs/usage.md`
2. Configure automatic startup (optional): `docs/autostart.md`
3. Set up SSL/TLS encryption (recommended): `docs/security.md`
4. Explore advanced features: `docs/advanced.md`