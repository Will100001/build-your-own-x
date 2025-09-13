# Troubleshooting Guide

This guide helps resolve common issues with the VNC Server and Viewer.

## Connection Issues

### "Connection refused" Error

**Symptoms:**
- Client cannot connect to server
- Error message: "Connection refused" or "No route to host"

**Solutions:**
1. **Check if server is running:**
   ```bash
   netstat -an | grep 5900  # Check if port is listening
   ps aux | grep vnc_server  # Check if process is running
   ```

2. **Verify server configuration:**
   ```bash
   # Start with verbose logging
   python server/vnc_server.py --verbose --host 0.0.0.0 --port 5900
   ```

3. **Check firewall settings:**
   ```bash
   # Linux
   sudo ufw status
   sudo ufw allow 5900/tcp
   
   # Windows
   # Check Windows Defender Firewall settings
   ```

4. **Test with localhost first:**
   ```bash
   # Server
   python server/vnc_server.py --host localhost --port 5900
   
   # Client (from same machine)
   python viewer/vnc_viewer.py --host localhost --port 5900
   ```

### "Authentication failed" Error

**Symptoms:**
- Connection established but authentication fails
- Server rejects client after password entry

**Solutions:**
1. **Check password configuration:**
   ```bash
   # Server with specific password
   python server/vnc_server.py --password "your_password"
   ```

2. **Verify client password:**
   - Ensure client is using the same password as server
   - Check for typos or case sensitivity

3. **Try without authentication:**
   ```bash
   # Server without password (for testing)
   python server/vnc_server.py --password ""
   ```

### "Protocol error" or "Handshake failed"

**Symptoms:**
- Connection starts but fails during protocol negotiation
- Error messages about protocol versions

**Solutions:**
1. **Check network stability:**
   ```bash
   ping server_ip  # Test basic connectivity
   traceroute server_ip  # Check network path
   ```

2. **Verify compatible versions:**
   - Both client and server should use RFB 3.8
   - Check for any version conflicts

3. **Test with minimal configuration:**
   ```bash
   python server/vnc_server.py --host localhost --port 5901
   python viewer/vnc_viewer.py --host localhost --port 5901
   ```

## Performance Issues

### Slow Screen Updates

**Symptoms:**
- Long delays between screen changes
- Laggy mouse/keyboard input
- Poor responsiveness

**Solutions:**
1. **Reduce screen resolution:**
   ```bash
   # Linux
   xrandr --output HDMI-1 --mode 1024x768
   ```

2. **Optimize encoding:**
   - Use more efficient encodings (ZRLE, RRE)
   - Reduce color depth if acceptable

3. **Network optimization:**
   ```bash
   # Check network latency
   ping -c 10 server_ip
   
   # Monitor bandwidth usage
   iftop  # Linux
   ```

4. **Close unnecessary applications:**
   - Reduce CPU usage on server machine
   - Free up memory for better performance

### High CPU Usage

**Symptoms:**
- Server process consuming high CPU
- System becomes unresponsive
- Fan noise increases

**Solutions:**
1. **Monitor resource usage:**
   ```bash
   # Linux
   top -p $(pgrep -f vnc_server)
   
   # Windows
   tasklist | findstr python
   ```

2. **Reduce update frequency:**
   - Modify server to send updates less frequently
   - Use incremental updates when possible

3. **Optimize screen capture:**
   - Use efficient screen capture methods
   - Implement change detection to avoid unnecessary updates

### Memory Leaks

**Symptoms:**
- Memory usage constantly increasing
- System runs out of memory over time
- Application crashes after extended use

**Solutions:**
1. **Monitor memory usage:**
   ```bash
   # Linux
   ps aux | grep vnc_server
   valgrind --tool=memcheck python server/vnc_server.py
   ```

2. **Restart server periodically:**
   - Implement automatic restart mechanism
   - Monitor memory usage and restart when needed

3. **Check for resource cleanup:**
   - Ensure proper cleanup of client connections
   - Close image resources after use

## Display Issues

### Black Screen or No Display

**Symptoms:**
- Viewer shows black screen
- No visual content transmitted
- Connection appears successful but no display

**Solutions:**
1. **Check screen capture permissions:**
   ```bash
   # macOS - grant screen recording permission
   # System Preferences > Security & Privacy > Privacy > Screen Recording
   ```

2. **Verify display server:**
   ```bash
   # Linux - check X11 display
   echo $DISPLAY
   xdpyinfo
   ```

3. **Test screen capture manually:**
   ```python
   from PIL import ImageGrab
   img = ImageGrab.grab()
   img.save("test_capture.png")
   ```

### Color Display Issues

**Symptoms:**
- Wrong colors displayed
- Color corruption or artifacts
- Incorrect color depth

**Solutions:**
1. **Check pixel format:**
   - Verify client and server pixel format compatibility
   - Test with different color depths (16-bit, 24-bit, 32-bit)

2. **Update graphics drivers:**
   - Ensure latest drivers are installed
   - Check for compatibility issues

### Resolution Problems

**Symptoms:**
- Display appears scaled incorrectly
- Viewer window too small/large
- Aspect ratio issues

**Solutions:**
1. **Check screen resolution:**
   ```bash
   # Linux
   xdpyinfo | grep dimensions
   
   # Windows
   systeminfo | findstr Resolution
   ```

2. **Adjust viewer scaling:**
   - Use viewer's scaling options
   - Fit window to content or scale to fit

## Platform-Specific Issues

### Windows Issues

#### "DLL not found" Errors
```bash
# Install Visual C++ Redistributable
# Download from Microsoft website
```

#### Permission Denied
```bash
# Run as Administrator
# Add exception to antivirus software
```

#### Windows Defender Blocking
```bash
# Add exception for VNC executables
# Disable real-time protection temporarily
```

### Linux Issues

#### X11 Permission Denied
```bash
# Allow X11 access
xhost +localhost

# Run as correct user
sudo -u $USER python server/vnc_server.py
```

#### Missing Dependencies
```bash
# Install missing packages
sudo apt-get install python3-tk python3-dev
sudo apt-get install libx11-dev libxext-dev
```

#### Wayland Compatibility
```bash
# Switch to X11 session
# Or use XWayland compatibility layer
export GDK_BACKEND=x11
```

### Android Issues

#### App Crashes on Startup
- Check Android version compatibility (API 24+)
- Verify APK installation was successful
- Check device logs: `adb logcat`

#### Network Permission Issues
```xml
<!-- Ensure network permissions in AndroidManifest.xml -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

#### Touch Input Problems
- Calibrate touch sensitivity
- Check screen scaling settings
- Verify touch event handling

## Network Issues

### Port Already in Use

**Symptoms:**
- Server fails to start
- Error: "Address already in use"

**Solutions:**
```bash
# Find process using port 5900
lsof -i :5900  # Linux/macOS
netstat -ano | findstr :5900  # Windows

# Kill process using port
kill -9 PID  # Linux/macOS
taskkill /PID PID /F  # Windows

# Use different port
python server/vnc_server.py --port 5901
```

### NAT/Router Issues

**Symptoms:**
- Local connections work but remote connections fail
- Connections timeout from external networks

**Solutions:**
1. **Configure port forwarding:**
   - Access router configuration (usually 192.168.1.1)
   - Forward port 5900 to server machine
   - Use different external port for security

2. **Use SSH tunneling:**
   ```bash
   ssh -L 5900:localhost:5900 user@server_ip
   ```

3. **VPN solution:**
   - Set up VPN between client and server networks
   - Use VPN IP addresses for connections

## Debugging Tools

### Enable Verbose Logging
```bash
# Server with debug output
python server/vnc_server.py --verbose

# Client with debug output
python viewer/vnc_viewer.py --verbose
```

### Network Debugging
```bash
# Monitor network traffic
tcpdump -i any port 5900

# Check connectivity
telnet server_ip 5900
nc -zv server_ip 5900
```

### Process Monitoring
```bash
# Linux
strace -p $(pgrep -f vnc_server)
htop

# Windows
Process Monitor (ProcMon)
Performance Monitor (PerfMon)
```

### Log Analysis
```bash
# Check system logs
tail -f /var/log/syslog  # Linux
Get-EventLog System | Where-Object {$_.Source -eq "VNC"}  # Windows PowerShell
```

## Getting Help

### Collecting Debug Information

When reporting issues, include:

1. **System information:**
   ```bash
   # Linux
   uname -a
   python3 --version
   
   # Windows
   systeminfo
   python --version
   ```

2. **Error messages:**
   - Complete error output
   - Server and client logs
   - Any stack traces

3. **Network configuration:**
   - IP addresses
   - Port numbers
   - Firewall settings
   - Router configuration

4. **Reproduction steps:**
   - Exact command used
   - Configuration files
   - Steps to reproduce the issue

### Community Resources

- Check GitHub issues for similar problems
- Review documentation for configuration examples
- Test with minimal configuration first
- Verify all dependencies are installed correctly

### Emergency Troubleshooting

If VNC becomes completely unresponsive:

1. **Force stop processes:**
   ```bash
   pkill -f vnc_server  # Linux
   taskkill /IM python.exe /F  # Windows
   ```

2. **Reset network configuration:**
   ```bash
   # Linux
   sudo systemctl restart networking
   
   # Windows
   ipconfig /release && ipconfig /renew
   ```

3. **Reboot system:**
   - Last resort for persistent issues
   - Check system logs after reboot