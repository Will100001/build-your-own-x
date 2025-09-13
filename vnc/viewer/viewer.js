/**
 * VNC Viewer Application Logic
 */

const { ipcRenderer } = require('electron');

class VNCViewerApplication {
    constructor() {
        this.viewer = null;
        this.isElectron = typeof require !== 'undefined';
        this.zoomLevel = 1;
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
        // Initialize VNC viewer
        this.viewer = new VNCViewer('vnc-app');
        
        // Setup Electron-specific features
        if (this.isElectron) {
            this.setupElectronIntegration();
        }
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Setup zoom functionality
        this.setupZoomControls();
        
        console.log('VNC Viewer Application initialized');
    }

    setupElectronIntegration() {
        // Handle menu events from main process
        ipcRenderer.on('menu-new-connection', () => {
            this.newConnection();
        });

        ipcRenderer.on('menu-connect', () => {
            this.connect();
        });

        ipcRenderer.on('menu-disconnect', () => {
            this.disconnect();
        });

        ipcRenderer.on('menu-ctrl-alt-del', () => {
            this.sendCtrlAltDel();
        });

        ipcRenderer.on('menu-refresh', () => {
            this.refresh();
        });

        ipcRenderer.on('menu-zoom-in', () => {
            this.zoomIn();
        });

        ipcRenderer.on('menu-zoom-out', () => {
            this.zoomOut();
        });

        ipcRenderer.on('menu-reset-zoom', () => {
            this.resetZoom();
        });

        // Handle window controls
        window.minimizeWindow = () => {
            ipcRenderer.send('app-minimize');
        };

        window.closeWindow = () => {
            ipcRenderer.send('app-close');
        };

        // Handle application errors
        this.viewer.protocol.on('error', (error) => {
            ipcRenderer.send('show-error', 'Connection Error', error.message);
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Prevent default browser shortcuts when connected
            if (this.viewer && this.viewer.isConnected) {
                // Allow Electron menu shortcuts to work
                if (e.ctrlKey || e.metaKey) {
                    switch (e.key) {
                        case 'n':
                        case 'N':
                            if (e.ctrlKey || e.metaKey) {
                                e.preventDefault();
                                this.newConnection();
                            }
                            break;
                        case 'd':
                        case 'D':
                            if (e.ctrlKey || e.metaKey) {
                                e.preventDefault();
                                this.disconnect();
                            }
                            break;
                        case 'Enter':
                            if (e.ctrlKey || e.metaKey) {
                                e.preventDefault();
                                this.connect();
                            }
                            break;
                    }
                }
                
                // Handle F-keys
                switch (e.key) {
                    case 'F5':
                        e.preventDefault();
                        this.refresh();
                        break;
                    case 'F11':
                        e.preventDefault();
                        this.toggleFullscreen();
                        break;
                }
            }
        });
    }

    setupZoomControls() {
        // Add zoom controls to the toolbar
        const toolbar = document.querySelector('.toolbar');
        if (toolbar) {
            const zoomControls = document.createElement('div');
            zoomControls.className = 'zoom-controls';
            zoomControls.innerHTML = `
                <button id="zoom-out-btn" title="Zoom Out">−</button>
                <span id="zoom-level">100%</span>
                <button id="zoom-in-btn" title="Zoom In">+</button>
                <button id="zoom-reset-btn" title="Reset Zoom">1:1</button>
            `;
            
            toolbar.appendChild(zoomControls);
            
            // Bind zoom events
            document.getElementById('zoom-in-btn').addEventListener('click', () => this.zoomIn());
            document.getElementById('zoom-out-btn').addEventListener('click', () => this.zoomOut());
            document.getElementById('zoom-reset-btn').addEventListener('click', () => this.resetZoom());
        }
    }

    newConnection() {
        // Clear existing connection
        if (this.viewer && this.viewer.isConnected) {
            this.viewer.disconnect();
        }
        
        // Reset form
        document.getElementById('host-input').value = '';
        document.getElementById('port-input').value = '5900';
        document.getElementById('host-input').focus();
    }

    connect() {
        if (this.viewer) {
            this.viewer.connect();
        }
    }

    disconnect() {
        if (this.viewer) {
            this.viewer.disconnect();
        }
    }

    sendCtrlAltDel() {
        if (this.viewer) {
            this.viewer.sendCtrlAltDel();
        }
    }

    refresh() {
        if (this.viewer) {
            this.viewer.refresh();
        }
    }

    toggleFullscreen() {
        if (this.viewer) {
            this.viewer.toggleFullscreen();
        }
    }

    zoomIn() {
        this.zoomLevel = Math.min(this.zoomLevel * 1.2, 3);
        this.applyZoom();
    }

    zoomOut() {
        this.zoomLevel = Math.max(this.zoomLevel / 1.2, 0.3);
        this.applyZoom();
    }

    resetZoom() {
        this.zoomLevel = 1;
        this.applyZoom();
    }

    applyZoom() {
        const canvas = document.getElementById('vnc-canvas');
        if (canvas) {
            canvas.style.transform = `scale(${this.zoomLevel})`;
            canvas.style.transformOrigin = 'top left';
        }
        
        // Update zoom display
        const zoomDisplay = document.getElementById('zoom-level');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${Math.round(this.zoomLevel * 100)}%`;
        }
    }

    // Save and load connection settings
    saveConnection(host, port, name) {
        if (this.isElectron) {
            const connections = this.getConnections();
            connections.push({ host, port, name, lastUsed: Date.now() });
            localStorage.setItem('vncConnections', JSON.stringify(connections));
        }
    }

    getConnections() {
        if (this.isElectron) {
            const connections = localStorage.getItem('vncConnections');
            return connections ? JSON.parse(connections) : [];
        }
        return [];
    }

    loadConnection(connection) {
        document.getElementById('host-input').value = connection.host;
        document.getElementById('port-input').value = connection.port;
    }
}

// Initialize the application
const app = new VNCViewerApplication();
app.init();