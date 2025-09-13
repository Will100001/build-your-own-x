/**
 * VNC Server Application Logic
 */

const { ipcRenderer } = require('electron');

class VNCServerApplication {
    constructor() {
        this.server = null;
        this.isElectron = typeof require !== 'undefined';
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        // Initialize VNC server
        this.server = new VNCServer('vnc-server-app');
        
        // Setup Electron-specific features
        if (this.isElectron) {
            this.setupElectronIntegration();
        }
        
        // Setup quick actions
        this.setupQuickActions();
        
        // Setup server event handlers
        this.setupServerEvents();
        
        // Make server instance globally available for onclick handlers
        window.vncServer = this.server;
        
        console.log('VNC Server Application initialized');
    }

    setupElectronIntegration() {
        // Handle menu events from main process
        ipcRenderer.on('menu-start-server', () => {
            this.startServer();
        });

        ipcRenderer.on('menu-stop-server', () => {
            this.stopServer();
        });

        ipcRenderer.on('menu-show-connections', () => {
            this.showConnections();
        });

        ipcRenderer.on('menu-disconnect-all', () => {
            this.disconnectAll();
        });

        // Handle window controls
        window.minimizeWindow = () => {
            // Don't actually close, just minimize to tray
            const { remote } = require('electron');
            remote.getCurrentWindow().minimize();
        };

        window.closeWindow = () => {
            const { remote } = require('electron');
            remote.getCurrentWindow().close();
        };
    }

    setupQuickActions() {
        // Quick start button
        document.getElementById('quick-start-btn').addEventListener('click', () => {
            this.quickStart();
        });

        // Quick stop button
        document.getElementById('quick-stop-btn').addEventListener('click', () => {
            this.stopServer();
        });

        // Configure firewall button
        document.getElementById('open-firewall-btn').addEventListener('click', () => {
            this.configureFirewall();
        });

        // Share connection info button
        document.getElementById('share-info-btn').addEventListener('click', () => {
            this.shareConnectionInfo();
        });
    }

    setupServerEvents() {
        // Listen for server state changes
        const originalStartServer = this.server.startServer.bind(this.server);
        const originalStopServer = this.server.stopServer.bind(this.server);

        this.server.startServer = () => {
            originalStartServer();
            this.onServerStarted();
        };

        this.server.stopServer = () => {
            originalStopServer();
            this.onServerStopped();
        };

        // Listen for connection events
        const originalAddConnection = this.server.addConnection.bind(this.server);
        const originalRemoveConnection = this.server.removeConnection.bind(this.server);

        this.server.addConnection = (ip, clientId) => {
            originalAddConnection(ip, clientId);
            this.onNewConnection({ ip, clientId });
        };

        this.server.removeConnection = (clientId) => {
            const connection = this.server.connections.find(conn => conn.id === clientId);
            originalRemoveConnection(clientId);
            if (connection) {
                this.onConnectionEnded(connection);
            }
        };
    }

    quickStart() {
        // Set default values and start server
        document.getElementById('server-port').value = '5900';
        document.getElementById('server-password').value = '';
        document.getElementById('allow-view-only').checked = true;
        
        this.startServer();
    }

    startServer() {
        if (this.server) {
            this.server.startServer();
        }
    }

    stopServer() {
        if (this.server) {
            this.server.stopServer();
        }
    }

    onServerStarted() {
        // Update UI
        document.getElementById('server-status-title').textContent = 'Running';
        document.getElementById('quick-start-btn').disabled = true;
        document.getElementById('quick-stop-btn').disabled = false;
        document.getElementById('share-info-btn').disabled = false;

        // Notify main process
        if (this.isElectron) {
            ipcRenderer.send('server-started');
        }

        // Show connection information
        this.showConnectionInfo();
    }

    onServerStopped() {
        // Update UI
        document.getElementById('server-status-title').textContent = 'Stopped';
        document.getElementById('quick-start-btn').disabled = false;
        document.getElementById('quick-stop-btn').disabled = true;
        document.getElementById('share-info-btn').disabled = true;

        // Notify main process
        if (this.isElectron) {
            ipcRenderer.send('server-stopped');
        }
    }

    onNewConnection(clientInfo) {
        // Notify main process
        if (this.isElectron) {
            ipcRenderer.send('new-connection', clientInfo);
        }

        // Show desktop notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('New VNC Connection', {
                body: `Client ${clientInfo.clientId} connected from ${clientInfo.ip}`,
                icon: '../shared/assets/icon.png'
            });
        }
    }

    onConnectionEnded(clientInfo) {
        // Notify main process
        if (this.isElectron) {
            ipcRenderer.send('connection-ended', clientInfo);
        }
    }

    showConnections() {
        // Scroll to connections panel
        const connectionsPanel = document.querySelector('.connections-panel');
        if (connectionsPanel) {
            connectionsPanel.scrollIntoView({ behavior: 'smooth' });
        }
    }

    disconnectAll() {
        if (this.server && this.server.connections) {
            // Disconnect all connections
            const connections = [...this.server.connections];
            connections.forEach(connection => {
                this.server.removeConnection(connection.id);
            });

            this.server.log('All connections disconnected by administrator');
        }
    }

    configureFirewall() {
        if (this.isElectron) {
            const { shell } = require('electron');
            
            // Show firewall configuration dialog
            const { dialog } = require('electron').remote;
            dialog.showMessageBox({
                type: 'info',
                title: 'Firewall Configuration',
                message: 'Configure Windows Firewall',
                detail: 'To allow VNC connections, you need to:\n\n1. Open Windows Firewall settings\n2. Add an exception for port 5900\n3. Allow the VNC Server application\n\nWould you like to open the Windows Firewall settings?',
                buttons: ['Open Firewall Settings', 'Show Manual Instructions', 'Cancel']
            }).then((result) => {
                if (result.response === 0) {
                    // Open Windows Firewall settings
                    shell.openExternal('ms-settings:network-firewall');
                } else if (result.response === 1) {
                    this.showManualFirewallInstructions();
                }
            });
        }
    }

    showManualFirewallInstructions() {
        if (this.isElectron) {
            const { dialog } = require('electron').remote;
            dialog.showMessageBox({
                type: 'info',
                title: 'Manual Firewall Configuration',
                message: 'Windows Firewall Configuration Steps',
                detail: 'Manual steps to configure Windows Firewall:\n\n1. Press Win+R and type "firewall.cpl"\n2. Click "Advanced settings" on the left\n3. Right-click "Inbound Rules" and select "New Rule"\n4. Select "Port" and click Next\n5. Select "TCP" and enter "5900" as the port\n6. Select "Allow the connection"\n7. Apply to all network types\n8. Name the rule "VNC Server"\n\nAlternatively, run this command as Administrator:\nnetsh advfirewall firewall add rule name="VNC Server" dir=in action=allow protocol=TCP localport=5900',
                buttons: ['OK']
            });
        }
    }

    shareConnectionInfo() {
        if (!this.server || !this.server.isRunning) {
            return;
        }

        const port = document.getElementById('server-port').value;
        const localIP = document.getElementById('local-ip').textContent;
        const hasPassword = document.getElementById('server-password').value !== '';

        const connectionInfo = `VNC Server Connection Information:

Server Address: ${localIP}
Port: ${port}
Password: ${hasPassword ? 'Required' : 'None'}

Connection String: ${localIP}:${port}

Instructions for clients:
1. Open VNC Viewer
2. Enter server address: ${localIP}:${port}
${hasPassword ? '3. Enter the password when prompted' : '3. No password required'}
4. Click Connect`;

        if (this.isElectron) {
            const { clipboard, dialog } = require('electron').remote;
            
            dialog.showMessageBox({
                type: 'info',
                title: 'Connection Information',
                message: 'VNC Server Connection Details',
                detail: connectionInfo,
                buttons: ['Copy to Clipboard', 'OK']
            }).then((result) => {
                if (result.response === 0) {
                    clipboard.writeText(connectionInfo);
                    this.server.log('Connection information copied to clipboard');
                }
            });
        } else {
            // Fallback for non-Electron environments
            if (navigator.clipboard) {
                navigator.clipboard.writeText(connectionInfo).then(() => {
                    alert('Connection information copied to clipboard');
                });
            } else {
                alert(connectionInfo);
            }
        }
    }

    showConnectionInfo() {
        const port = document.getElementById('server-port').value;
        const localIP = document.getElementById('local-ip').textContent;
        
        this.server.log(`Server is accessible at ${localIP}:${port}`);
        this.server.log('Share this information with clients to connect');

        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }

    // Get local IP address (simplified version)
    async getLocalIPAddress() {
        try {
            // This is a simplified method - in a real implementation,
            // you'd want to get the actual network interface IP
            const response = await fetch('https://api.ipify.org?format=json');
            const data = await response.json();
            return data.ip;
        } catch (error) {
            // Fallback to localhost
            return 'localhost';
        }
    }
}

// Initialize the application
const app = new VNCServerApplication();
app.init();