/**
 * VNC GUI Components
 * Reusable UI components for VNC viewer and server
 */

class VNCViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.protocol = new VNCProtocol();
        this.canvas = null;
        this.ctx = null;
        this.isConnected = false;
        
        this.setupEventHandlers();
        this.createUI();
    }

    createUI() {
        this.container.innerHTML = `
            <div class="vnc-viewer">
                <div class="toolbar">
                    <div class="connection-panel">
                        <input type="text" id="host-input" placeholder="Host (e.g., 192.168.1.100)" value="localhost">
                        <input type="number" id="port-input" placeholder="Port" value="5900" min="1" max="65535">
                        <button id="connect-btn" class="primary">Connect</button>
                        <button id="disconnect-btn" class="secondary" disabled>Disconnect</button>
                    </div>
                    <div class="status-panel">
                        <span id="status">Disconnected</span>
                        <span id="connection-info"></span>
                    </div>
                </div>
                
                <div class="viewer-controls">
                    <button id="ctrl-alt-del-btn" disabled>Ctrl+Alt+Del</button>
                    <button id="fullscreen-btn" disabled>Fullscreen</button>
                    <button id="refresh-btn" disabled>Refresh</button>
                    <label>
                        <input type="checkbox" id="view-only-checkbox"> View Only
                    </label>
                </div>
                
                <div class="canvas-container">
                    <canvas id="vnc-canvas" width="1024" height="768"></canvas>
                    <div id="loading-overlay" class="loading-overlay hidden">
                        <div class="spinner"></div>
                        <div>Connecting...</div>
                    </div>
                </div>
                
                <div class="info-panel">
                    <div class="stats">
                        <span>Resolution: <span id="resolution">1024x768</span></span>
                        <span>FPS: <span id="fps">0</span></span>
                        <span>Bandwidth: <span id="bandwidth">0 KB/s</span></span>
                    </div>
                </div>
            </div>
        `;

        this.setupCanvas();
        this.bindEvents();
    }

    setupCanvas() {
        this.canvas = document.getElementById('vnc-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Enable image smoothing for better quality
        this.ctx.imageSmoothingEnabled = true;
        this.ctx.imageSmoothingQuality = 'high';
    }

    bindEvents() {
        // Connection controls
        document.getElementById('connect-btn').addEventListener('click', () => this.connect());
        document.getElementById('disconnect-btn').addEventListener('click', () => this.disconnect());
        
        // Special keys
        document.getElementById('ctrl-alt-del-btn').addEventListener('click', () => this.sendCtrlAltDel());
        document.getElementById('fullscreen-btn').addEventListener('click', () => this.toggleFullscreen());
        document.getElementById('refresh-btn').addEventListener('click', () => this.refresh());
        
        // Canvas events for remote control
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.canvas.addEventListener('keyup', (e) => this.handleKeyUp(e));
        
        // Make canvas focusable for keyboard events
        this.canvas.tabIndex = 0;
    }

    setupEventHandlers() {
        this.protocol.on('connecting', () => {
            this.updateStatus('Connecting...', 'connecting');
            this.showLoading(true);
        });

        this.protocol.on('connected', (data) => {
            this.isConnected = true;
            this.updateStatus(`Connected to ${data.host}:${data.port}`, 'connected');
            this.showLoading(false);
            this.enableControls(true);
            this.startFramebufferUpdates();
        });

        this.protocol.on('disconnected', () => {
            this.isConnected = false;
            this.updateStatus('Disconnected', 'disconnected');
            this.enableControls(false);
        });

        this.protocol.on('error', (error) => {
            this.updateStatus(`Error: ${error.message}`, 'error');
            this.showLoading(false);
            this.enableControls(false);
        });

        this.protocol.on('framebuffer_update', (imageData) => {
            this.updateFramebuffer(imageData);
        });
    }

    async connect() {
        const host = document.getElementById('host-input').value;
        const port = parseInt(document.getElementById('port-input').value);
        
        if (!host) {
            alert('Please enter a host address');
            return;
        }
        
        await this.protocol.connect(host, port);
    }

    disconnect() {
        this.protocol.disconnect();
    }

    updateStatus(message, status) {
        const statusElement = document.getElementById('status');
        statusElement.textContent = message;
        statusElement.className = status || '';
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.toggle('hidden', !show);
    }

    enableControls(enabled) {
        document.getElementById('connect-btn').disabled = enabled;
        document.getElementById('disconnect-btn').disabled = !enabled;
        document.getElementById('ctrl-alt-del-btn').disabled = !enabled;
        document.getElementById('fullscreen-btn').disabled = !enabled;
        document.getElementById('refresh-btn').disabled = !enabled;
    }

    updateFramebuffer(imageData) {
        if (!this.ctx || !imageData) return;
        
        this.ctx.putImageData(imageData, 0, 0);
        this.updateStats();
    }

    startFramebufferUpdates() {
        if (!this.isConnected) return;
        
        this.protocol.requestFramebufferUpdate(false);
        
        // Request updates periodically
        this.updateInterval = setInterval(() => {
            if (this.isConnected) {
                this.protocol.requestFramebufferUpdate(true);
            }
        }, 50); // 20 FPS
    }

    handleMouseDown(e) {
        if (!this.isConnected || document.getElementById('view-only-checkbox').checked) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const buttonMask = this.getButtonMask(e);
        
        this.protocol.sendPointerEvent(x, y, buttonMask);
        this.canvas.focus();
    }

    handleMouseUp(e) {
        if (!this.isConnected || document.getElementById('view-only-checkbox').checked) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        this.protocol.sendPointerEvent(x, y, 0);
    }

    handleMouseMove(e) {
        if (!this.isConnected || document.getElementById('view-only-checkbox').checked) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const buttonMask = e.buttons;
        
        this.protocol.sendPointerEvent(x, y, buttonMask);
    }

    handleKeyDown(e) {
        if (!this.isConnected || document.getElementById('view-only-checkbox').checked) return;
        
        e.preventDefault();
        this.protocol.sendKeyEvent(e.key, true);
    }

    handleKeyUp(e) {
        if (!this.isConnected || document.getElementById('view-only-checkbox').checked) return;
        
        e.preventDefault();
        this.protocol.sendKeyEvent(e.key, false);
    }

    getButtonMask(e) {
        let mask = 0;
        if (e.buttons & 1) mask |= 1; // Left button
        if (e.buttons & 2) mask |= 4; // Right button
        if (e.buttons & 4) mask |= 2; // Middle button
        return mask;
    }

    sendCtrlAltDel() {
        if (!this.isConnected) return;
        
        this.protocol.sendKeyEvent('Control', true);
        this.protocol.sendKeyEvent('Alt', true);
        this.protocol.sendKeyEvent('Delete', true);
        
        setTimeout(() => {
            this.protocol.sendKeyEvent('Delete', false);
            this.protocol.sendKeyEvent('Alt', false);
            this.protocol.sendKeyEvent('Control', false);
        }, 100);
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            this.canvas.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }

    refresh() {
        if (!this.isConnected) return;
        this.protocol.requestFramebufferUpdate(false);
    }

    updateStats() {
        // Update FPS counter
        if (!this.lastFrameTime) this.lastFrameTime = Date.now();
        const now = Date.now();
        const fps = Math.round(1000 / (now - this.lastFrameTime));
        document.getElementById('fps').textContent = fps;
        this.lastFrameTime = now;
        
        // Update resolution
        document.getElementById('resolution').textContent = `${this.canvas.width}x${this.canvas.height}`;
        
        // Simulate bandwidth (in a real implementation, this would be calculated from actual data)
        const bandwidth = Math.floor(Math.random() * 100) + 50;
        document.getElementById('bandwidth').textContent = `${bandwidth} KB/s`;
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        this.disconnect();
    }
}

// VNC Server GUI
class VNCServer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.isRunning = false;
        this.connections = [];
        
        this.createUI();
        this.bindEvents();
    }

    createUI() {
        this.container.innerHTML = `
            <div class="vnc-server">
                <div class="server-header">
                    <h2>VNC Server</h2>
                    <div class="server-controls">
                        <button id="start-server-btn" class="primary">Start Server</button>
                        <button id="stop-server-btn" class="secondary" disabled>Stop Server</button>
                    </div>
                </div>
                
                <div class="server-config">
                    <div class="config-row">
                        <label for="server-port">Port:</label>
                        <input type="number" id="server-port" value="5900" min="1" max="65535">
                    </div>
                    <div class="config-row">
                        <label for="server-password">Password:</label>
                        <input type="password" id="server-password" placeholder="Optional">
                    </div>
                    <div class="config-row">
                        <label>
                            <input type="checkbox" id="allow-view-only"> Allow view-only connections
                        </label>
                    </div>
                </div>
                
                <div class="server-status">
                    <div class="status-item">
                        <span class="label">Status:</span>
                        <span id="server-status" class="status">Stopped</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Local IP:</span>
                        <span id="local-ip">-</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Connected Clients:</span>
                        <span id="client-count">0</span>
                    </div>
                </div>
                
                <div class="connections-panel">
                    <h3>Active Connections</h3>
                    <div id="connections-list" class="connections-list">
                        <div class="no-connections">No active connections</div>
                    </div>
                </div>
                
                <div class="server-logs">
                    <h3>Server Logs</h3>
                    <div id="log-output" class="log-output"></div>
                    <button id="clear-logs-btn">Clear Logs</button>
                </div>
            </div>
        `;
    }

    bindEvents() {
        document.getElementById('start-server-btn').addEventListener('click', () => this.startServer());
        document.getElementById('stop-server-btn').addEventListener('click', () => this.stopServer());
        document.getElementById('clear-logs-btn').addEventListener('click', () => this.clearLogs());
    }

    startServer() {
        const port = parseInt(document.getElementById('server-port').value);
        const password = document.getElementById('server-password').value;
        
        this.isRunning = true;
        this.updateServerStatus('Running', 'running');
        this.enableControls();
        
        this.log(`Server started on port ${port}`);
        if (password) {
            this.log('Password protection enabled');
        }
        
        // Get local IP (simulated)
        document.getElementById('local-ip').textContent = '192.168.1.100';
        
        // Simulate incoming connections
        setTimeout(() => {
            this.addConnection('192.168.1.50', 'Client-001');
        }, 3000);
        
        setTimeout(() => {
            this.addConnection('192.168.1.75', 'Client-002');
        }, 8000);
    }

    stopServer() {
        this.isRunning = false;
        this.updateServerStatus('Stopped', 'stopped');
        this.enableControls();
        
        this.log('Server stopped');
        this.clearConnections();
        document.getElementById('local-ip').textContent = '-';
    }

    updateServerStatus(status, className) {
        const statusElement = document.getElementById('server-status');
        statusElement.textContent = status;
        statusElement.className = `status ${className}`;
    }

    enableControls() {
        document.getElementById('start-server-btn').disabled = this.isRunning;
        document.getElementById('stop-server-btn').disabled = !this.isRunning;
        document.getElementById('server-port').disabled = this.isRunning;
        document.getElementById('server-password').disabled = this.isRunning;
    }

    addConnection(ip, clientId) {
        if (!this.isRunning) return;
        
        const connection = {
            id: clientId,
            ip: ip,
            connectTime: new Date(),
            viewOnly: document.getElementById('allow-view-only').checked
        };
        
        this.connections.push(connection);
        this.updateConnectionsList();
        this.log(`New connection from ${ip} (${clientId})`);
    }

    removeConnection(clientId) {
        const index = this.connections.findIndex(conn => conn.id === clientId);
        if (index !== -1) {
            const connection = this.connections[index];
            this.connections.splice(index, 1);
            this.updateConnectionsList();
            this.log(`Connection from ${connection.ip} (${clientId}) disconnected`);
        }
    }

    updateConnectionsList() {
        const listElement = document.getElementById('connections-list');
        document.getElementById('client-count').textContent = this.connections.length;
        
        if (this.connections.length === 0) {
            listElement.innerHTML = '<div class="no-connections">No active connections</div>';
            return;
        }
        
        listElement.innerHTML = this.connections.map(conn => `
            <div class="connection-item">
                <div class="connection-info">
                    <strong>${conn.id}</strong>
                    <span>${conn.ip}</span>
                    <span>Connected: ${conn.connectTime.toLocaleTimeString()}</span>
                    ${conn.viewOnly ? '<span class="view-only">View Only</span>' : ''}
                </div>
                <button onclick="vncServer.removeConnection('${conn.id}')" class="disconnect-btn">Disconnect</button>
            </div>
        `).join('');
    }

    clearConnections() {
        this.connections = [];
        this.updateConnectionsList();
    }

    log(message) {
        const logOutput = document.getElementById('log-output');
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${message}`;
        
        logOutput.appendChild(logEntry);
        logOutput.scrollTop = logOutput.scrollHeight;
    }

    clearLogs() {
        document.getElementById('log-output').innerHTML = '';
    }
}

// Export for both Node.js and browser environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VNCViewer, VNCServer };
} else {
    window.VNCViewer = VNCViewer;
    window.VNCServer = VNCServer;
}