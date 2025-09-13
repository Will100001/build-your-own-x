#!/usr/bin/env python3
"""
Web-based GUI for VNC Server
Provides a web interface for controlling and monitoring the VNC server.
"""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import logging

from vnc_server import VNCServer


class VNCWebGUI(BaseHTTPRequestHandler):
    """HTTP request handler for VNC server web interface."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.serve_main_page()
        elif path == '/api/status':
            self.serve_status_api()
        elif path == '/api/logs':
            self.serve_logs_api()
        elif path == '/api/users':
            self.serve_users_api()
        elif path == '/api/config':
            self.serve_config_api()
        elif path.startswith('/static/'):
            self.serve_static_file(path)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        if path == '/api/control':
            self.handle_control_api(post_data)
        elif path == '/api/users':
            self.handle_users_api(post_data)
        elif path == '/api/config':
            self.handle_config_api(post_data)
        elif path == '/api/disconnect':
            self.handle_disconnect_api(post_data)
        else:
            self.send_error(404)
    
    def serve_main_page(self):
        """Serve the main HTML interface."""
        html_content = self.get_main_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_status_api(self):
        """Serve server status as JSON."""
        status = self.server.vnc_server.get_status()
        self.send_json_response(status)
    
    def serve_logs_api(self):
        """Serve connection logs as JSON."""
        logs = self.server.vnc_server.get_connection_log(limit=50)
        self.send_json_response({'logs': logs})
    
    def serve_users_api(self):
        """Serve user list as JSON."""
        users = self.server.vnc_server.list_users()
        self.send_json_response({'users': users})
    
    def serve_config_api(self):
        """Serve configuration as JSON."""
        config = self.server.vnc_server.config.copy()
        self.send_json_response({'config': config})
    
    def handle_control_api(self, post_data):
        """Handle server control commands."""
        try:
            data = json.loads(post_data)
            action = data.get('action')
            
            if action == 'start':
                success = self.server.vnc_server.start()
                self.send_json_response({'success': success, 'message': 'Server started' if success else 'Failed to start server'})
            
            elif action == 'stop':
                self.server.vnc_server.stop()
                self.send_json_response({'success': True, 'message': 'Server stopped'})
            
            elif action == 'restart':
                self.server.vnc_server.stop()
                time.sleep(1)
                success = self.server.vnc_server.start()
                self.send_json_response({'success': success, 'message': 'Server restarted' if success else 'Failed to restart server'})
            
            else:
                self.send_json_response({'success': False, 'message': 'Unknown action'})
                
        except json.JSONDecodeError:
            self.send_json_response({'success': False, 'message': 'Invalid JSON'})
    
    def handle_users_api(self, post_data):
        """Handle user management."""
        try:
            data = json.loads(post_data)
            action = data.get('action')
            
            if action == 'add':
                username = data.get('username')
                password = data.get('password')
                if username and password:
                    success = self.server.vnc_server.add_user(username, password)
                    message = 'User added successfully' if success else 'Failed to add user'
                    self.send_json_response({'success': success, 'message': message})
                else:
                    self.send_json_response({'success': False, 'message': 'Username and password required'})
            
            elif action == 'remove':
                username = data.get('username')
                if username:
                    success = self.server.vnc_server.remove_user(username)
                    message = 'User removed successfully' if success else 'Failed to remove user'
                    self.send_json_response({'success': success, 'message': message})
                else:
                    self.send_json_response({'success': False, 'message': 'Username required'})
            
            else:
                self.send_json_response({'success': False, 'message': 'Unknown action'})
                
        except json.JSONDecodeError:
            self.send_json_response({'success': False, 'message': 'Invalid JSON'})
    
    def handle_config_api(self, post_data):
        """Handle configuration updates."""
        try:
            data = json.loads(post_data)
            config = data.get('config', {})
            
            # Validate configuration values
            valid_keys = ['screen_width', 'screen_height', 'frame_rate', 'compression', 'encryption']
            filtered_config = {k: v for k, v in config.items() if k in valid_keys}
            
            if filtered_config:
                self.server.vnc_server.configure(**filtered_config)
                self.send_json_response({'success': True, 'message': 'Configuration updated'})
            else:
                self.send_json_response({'success': False, 'message': 'No valid configuration provided'})
                
        except json.JSONDecodeError:
            self.send_json_response({'success': False, 'message': 'Invalid JSON'})
    
    def handle_disconnect_api(self, post_data):
        """Handle client disconnection."""
        try:
            data = json.loads(post_data)
            address = data.get('address')
            
            if address:
                success = self.server.vnc_server.disconnect_client(address)
                message = 'Client disconnected' if success else 'Client not found'
                self.send_json_response({'success': success, 'message': message})
            else:
                self.send_json_response({'success': False, 'message': 'Address required'})
                
        except json.JSONDecodeError:
            self.send_json_response({'success': False, 'message': 'Invalid JSON'})
    
    def send_json_response(self, data):
        """Send JSON response."""
        json_data = json.dumps(data)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def get_main_html(self):
        """Generate the main HTML interface."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VNC Server Control Panel</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .section h3 {
            margin-top: 0;
            color: #555;
        }
        .button {
            background-color: #007bff;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        .button:hover {
            background-color: #0056b3;
        }
        .button.danger {
            background-color: #dc3545;
        }
        .button.danger:hover {
            background-color: #c82333;
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .status.running {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.stopped {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-group input, .form-group select {
            width: 200px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .log-entry {
            padding: 5px;
            border-bottom: 1px solid #eee;
            font-family: monospace;
            font-size: 12px;
        }
        .connection-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border: 1px solid #ddd;
            margin-bottom: 5px;
            border-radius: 4px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
        }
        .refresh-btn {
            float: right;
            background-color: #28a745;
        }
        .refresh-btn:hover {
            background-color: #218838;
        }
        .message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            display: none;
        }
        .message.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ VNC Server Control Panel</h1>
            <p>Manage your Python VNC Server</p>
        </div>

        <div id="message" class="message"></div>

        <!-- Server Status -->
        <div class="section">
            <h3>Server Status <button class="button refresh-btn" onclick="refreshStatus()">↻ Refresh</button></h3>
            <div id="server-status" class="status stopped">
                Loading...
            </div>
            <div>
                <button class="button" onclick="startServer()">▶️ Start Server</button>
                <button class="button danger" onclick="stopServer()">⏹️ Stop Server</button>
                <button class="button" onclick="restartServer()">🔄 Restart Server</button>
            </div>
        </div>

        <!-- Configuration -->
        <div class="section">
            <h3>Configuration</h3>
            <div class="form-group">
                <label>Screen Width:</label>
                <input type="number" id="screen-width" value="1024" min="640" max="3840">
            </div>
            <div class="form-group">
                <label>Screen Height:</label>
                <input type="number" id="screen-height" value="768" min="480" max="2160">
            </div>
            <div class="form-group">
                <label>Frame Rate (FPS):</label>
                <input type="number" id="frame-rate" value="10" min="1" max="60">
            </div>
            <button class="button" onclick="updateConfig()">💾 Update Configuration</button>
        </div>

        <!-- User Management -->
        <div class="section">
            <h3>User Management</h3>
            <div>
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" id="new-username" placeholder="Enter username">
                </div>
                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" id="new-password" placeholder="Enter password">
                </div>
                <button class="button" onclick="addUser()">➕ Add User</button>
            </div>
            
            <h4>Current Users</h4>
            <table id="users-table">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Created At</th>
                        <th>Last Login</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="users-list">
                    <tr><td colspan="4">Loading...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- Active Connections -->
        <div class="section">
            <h3>Active Connections</h3>
            <div id="connections-list">
                <p>Loading...</p>
            </div>
        </div>

        <!-- Connection Logs -->
        <div class="section">
            <h3>Connection Logs</h3>
            <div id="logs-container" style="height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;">
                <p>Loading...</p>
            </div>
        </div>
    </div>

    <script>
        let refreshInterval;

        function showMessage(text, type = 'success') {
            const messageEl = document.getElementById('message');
            messageEl.textContent = text;
            messageEl.className = `message ${type}`;
            messageEl.style.display = 'block';
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 5000);
        }

        async function apiCall(url, method = 'GET', data = null) {
            try {
                const options = {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    }
                };
                
                if (data) {
                    options.body = JSON.stringify(data);
                }

                const response = await fetch(url, options);
                return await response.json();
            } catch (error) {
                console.error('API call failed:', error);
                showMessage('API call failed: ' + error.message, 'error');
                return null;
            }
        }

        async function refreshStatus() {
            const status = await apiCall('/api/status');
            if (status) {
                updateStatusDisplay(status);
                updateConnectionsList(status.connections);
            }
        }

        function updateStatusDisplay(status) {
            const statusEl = document.getElementById('server-status');
            if (status.running) {
                statusEl.className = 'status running';
                statusEl.innerHTML = `
                    <strong>🟢 Server Running</strong><br>
                    Host: ${status.host}:${status.port}<br>
                    Active Connections: ${status.active_connections}/${status.max_connections}<br>
                    Authentication: ${status.use_auth ? 'Enabled' : 'Disabled'}<br>
                    Screen Size: ${status.screen_size[0]}x${status.screen_size[1]}
                `;
            } else {
                statusEl.className = 'status stopped';
                statusEl.innerHTML = '<strong>🔴 Server Stopped</strong>';
            }

            // Update config form
            document.getElementById('screen-width').value = status.config.screen_width;
            document.getElementById('screen-height').value = status.config.screen_height;
            document.getElementById('frame-rate').value = status.config.frame_rate;
        }

        function updateConnectionsList(connections) {
            const container = document.getElementById('connections-list');
            if (!connections || connections.length === 0) {
                container.innerHTML = '<p>No active connections</p>';
                return;
            }

            container.innerHTML = connections.map(conn => `
                <div class="connection-item">
                    <div>
                        <strong>${conn.address}</strong><br>
                        Authenticated: ${conn.authenticated ? '✅' : '❌'}<br>
                        Status: ${conn.running ? 'Connected' : 'Disconnected'}
                    </div>
                    <button class="button danger" onclick="disconnectClient('${conn.address}')">
                        🚫 Disconnect
                    </button>
                </div>
            `).join('');
        }

        async function startServer() {
            const result = await apiCall('/api/control', 'POST', { action: 'start' });
            if (result) {
                showMessage(result.message, result.success ? 'success' : 'error');
                refreshStatus();
            }
        }

        async function stopServer() {
            const result = await apiCall('/api/control', 'POST', { action: 'stop' });
            if (result) {
                showMessage(result.message, result.success ? 'success' : 'error');
                refreshStatus();
            }
        }

        async function restartServer() {
            const result = await apiCall('/api/control', 'POST', { action: 'restart' });
            if (result) {
                showMessage(result.message, result.success ? 'success' : 'error');
                refreshStatus();
            }
        }

        async function updateConfig() {
            const config = {
                screen_width: parseInt(document.getElementById('screen-width').value),
                screen_height: parseInt(document.getElementById('screen-height').value),
                frame_rate: parseInt(document.getElementById('frame-rate').value)
            };

            const result = await apiCall('/api/config', 'POST', { config });
            if (result) {
                showMessage(result.message, result.success ? 'success' : 'error');
            }
        }

        async function addUser() {
            const username = document.getElementById('new-username').value;
            const password = document.getElementById('new-password').value;

            if (!username || !password) {
                showMessage('Username and password are required', 'error');
                return;
            }

            const result = await apiCall('/api/users', 'POST', {
                action: 'add',
                username: username,
                password: password
            });

            if (result) {
                showMessage(result.message, result.success ? 'success' : 'error');
                if (result.success) {
                    document.getElementById('new-username').value = '';
                    document.getElementById('new-password').value = '';
                    refreshUsers();
                }
            }
        }

        async function removeUser(username) {
            if (!confirm(`Are you sure you want to remove user "${username}"?`)) {
                return;
            }

            const result = await apiCall('/api/users', 'POST', {
                action: 'remove',
                username: username
            });

            if (result) {
                showMessage(result.message, result.success ? 'success' : 'error');
                if (result.success) {
                    refreshUsers();
                }
            }
        }

        async function refreshUsers() {
            const data = await apiCall('/api/users');
            if (data && data.users) {
                updateUsersList(data.users);
            }
        }

        function updateUsersList(users) {
            const tbody = document.getElementById('users-list');
            
            if (Object.keys(users).length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">No users found</td></tr>';
                return;
            }

            tbody.innerHTML = Object.entries(users).map(([username, info]) => `
                <tr>
                    <td>${username}</td>
                    <td>${info.created_at ? new Date(info.created_at * 1000).toLocaleString() : 'N/A'}</td>
                    <td>${info.last_login ? new Date(info.last_login * 1000).toLocaleString() : 'Never'}</td>
                    <td>
                        <button class="button danger" onclick="removeUser('${username}')">
                            🗑️ Remove
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        async function disconnectClient(address) {
            const result = await apiCall('/api/disconnect', 'POST', { address });
            if (result) {
                showMessage(result.message, result.success ? 'success' : 'error');
                refreshStatus();
            }
        }

        async function refreshLogs() {
            const data = await apiCall('/api/logs');
            if (data && data.logs) {
                updateLogs(data.logs);
            }
        }

        function updateLogs(logs) {
            const container = document.getElementById('logs-container');
            
            if (logs.length === 0) {
                container.innerHTML = '<p>No logs available</p>';
                return;
            }

            container.innerHTML = logs.reverse().map(log => `
                <div class="log-entry">
                    <strong>${log.timestamp}</strong> - ${log.event_type} - ${log.address || 'N/A'} - ${JSON.stringify(log.details)}
                </div>
            `).join('');
            
            // Scroll to top to show latest logs
            container.scrollTop = 0;
        }

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            refreshStatus();
            refreshUsers();
            refreshLogs();
            
            // Auto-refresh every 5 seconds
            refreshInterval = setInterval(() => {
                refreshStatus();
                refreshLogs();
            }, 5000);
        });

        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        });
    </script>
</body>
</html>'''


class VNCWebServer:
    """Web server for VNC GUI."""
    
    def __init__(self, vnc_server: VNCServer, host: str = '127.0.0.1', port: int = 8080):
        self.vnc_server = vnc_server
        self.host = host
        self.port = port
        self.httpd = None
        self.server_thread = None
        self.running = False
        
        # Setup logging
        self.logger = logging.getLogger('VNCWebServer')
    
    def start(self) -> bool:
        """Start the web server."""
        try:
            # Create HTTP server
            VNCWebGUI.server = self  # Make VNC server accessible to request handler
            self.httpd = HTTPServer((self.host, self.port), VNCWebGUI)
            
            # Start server in thread
            self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.running = True
            self.logger.info(f"VNC Web GUI started on http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
            return False
    
    def stop(self):
        """Stop the web server."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.running = False
            self.logger.info("VNC Web GUI stopped")


if __name__ == "__main__":
    # Test the web GUI
    from vnc_server import create_test_server
    
    print("Creating VNC Server and Web GUI...")
    
    vnc_server = create_test_server()
    web_gui = VNCWebServer(vnc_server, host='127.0.0.1', port=8080)
    
    try:
        print("Starting web GUI...")
        if web_gui.start():
            print(f"Web GUI is running on http://{web_gui.host}:{web_gui.port}")
            print("You can now control the VNC server through the web interface")
            
            # Keep running
            while True:
                time.sleep(1)
                
        else:
            print("Failed to start web GUI")
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        web_gui.stop()
        vnc_server.stop()
        print("Stopped")
    except Exception as e:
        print(f"Error: {e}")
        web_gui.stop()
        vnc_server.stop()