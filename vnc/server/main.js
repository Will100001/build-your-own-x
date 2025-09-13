const { app, BrowserWindow, Menu, dialog, ipcMain, Tray, nativeImage } = require('electron');
const path = require('path');

class VNCServerApp {
    constructor() {
        this.mainWindow = null;
        this.tray = null;
        this.isDev = process.argv.includes('--dev');
        this.isServerRunning = false;
    }

    async createWindow() {
        // Create the browser window
        this.mainWindow = new BrowserWindow({
            width: 900,
            height: 700,
            minWidth: 600,
            minHeight: 500,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: false,
                enableRemoteModule: true
            },
            icon: path.join(__dirname, 'assets', 'icon.png'),
            title: 'VNC Server',
            show: false
        });

        // Load the server HTML file
        await this.mainWindow.loadFile('server.html');

        // Show window when ready
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();
            
            if (this.isDev) {
                this.mainWindow.webContents.openDevTools();
            }
        });

        // Handle window closed
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });

        // Handle minimize to tray
        this.mainWindow.on('minimize', (event) => {
            if (this.isServerRunning) {
                event.preventDefault();
                this.mainWindow.hide();
                this.showTrayNotification('VNC Server is running in the background');
            }
        });

        // Create application menu
        this.createMenu();
        
        // Create system tray
        this.createTray();
    }

    createMenu() {
        const template = [
            {
                label: 'Server',
                submenu: [
                    {
                        label: 'Start Server',
                        accelerator: 'CmdOrCtrl+S',
                        click: () => {
                            this.mainWindow.webContents.send('menu-start-server');
                        }
                    },
                    {
                        label: 'Stop Server',
                        accelerator: 'CmdOrCtrl+T',
                        click: () => {
                            this.mainWindow.webContents.send('menu-stop-server');
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'Server Settings',
                        accelerator: 'CmdOrCtrl+Comma',
                        click: () => {
                            this.showServerSettings();
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'Quit',
                        accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
                        click: () => {
                            app.quit();
                        }
                    }
                ]
            },
            {
                label: 'View',
                submenu: [
                    {
                        label: 'Minimize to Tray',
                        accelerator: 'CmdOrCtrl+M',
                        click: () => {
                            this.mainWindow.hide();
                        }
                    },
                    {
                        label: 'Toggle Developer Tools',
                        accelerator: 'F12',
                        click: () => {
                            this.mainWindow.webContents.toggleDevTools();
                        }
                    }
                ]
            },
            {
                label: 'Connections',
                submenu: [
                    {
                        label: 'View Active Connections',
                        accelerator: 'CmdOrCtrl+A',
                        click: () => {
                            this.mainWindow.webContents.send('menu-show-connections');
                        }
                    },
                    {
                        label: 'Disconnect All',
                        accelerator: 'CmdOrCtrl+Shift+D',
                        click: () => {
                            this.mainWindow.webContents.send('menu-disconnect-all');
                        }
                    }
                ]
            },
            {
                label: 'Help',
                submenu: [
                    {
                        label: 'About',
                        click: () => {
                            this.showAbout();
                        }
                    },
                    {
                        label: 'Help',
                        accelerator: 'F1',
                        click: () => {
                            this.showHelp();
                        }
                    }
                ]
            }
        ];

        const menu = Menu.buildFromTemplate(template);
        Menu.setApplicationMenu(menu);
    }

    createTray() {
        // Create tray icon
        const trayIcon = nativeImage.createFromPath(path.join(__dirname, 'assets', 'tray-icon.png'));
        this.tray = new Tray(trayIcon);
        
        // Create tray context menu
        const contextMenu = Menu.buildFromTemplate([
            {
                label: 'Show VNC Server',
                click: () => {
                    this.mainWindow.show();
                    this.mainWindow.focus();
                }
            },
            {
                label: 'Start Server',
                click: () => {
                    this.mainWindow.webContents.send('menu-start-server');
                }
            },
            {
                label: 'Stop Server',
                click: () => {
                    this.mainWindow.webContents.send('menu-stop-server');
                }
            },
            { type: 'separator' },
            {
                label: 'Quit',
                click: () => {
                    app.quit();
                }
            }
        ]);
        
        this.tray.setContextMenu(contextMenu);
        this.tray.setToolTip('VNC Server');
        
        // Handle tray click
        this.tray.on('click', () => {
            if (this.mainWindow.isVisible()) {
                this.mainWindow.hide();
            } else {
                this.mainWindow.show();
                this.mainWindow.focus();
            }
        });
    }

    showTrayNotification(message) {
        if (this.tray) {
            this.tray.displayBalloon({
                title: 'VNC Server',
                content: message
            });
        }
    }

    showServerSettings() {
        dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: 'Server Settings',
            message: 'Server Settings',
            detail: 'This feature would allow configuring:\n• Security settings\n• Performance options\n• Network configuration\n• Access controls\n• Logging preferences',
            buttons: ['OK']
        });
    }

    showAbout() {
        dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: 'About VNC Server',
            message: 'VNC Server v1.0.0',
            detail: 'A cross-platform VNC server application built with Electron.\n\nFeatures:\n• Remote desktop sharing\n• Cross-platform compatibility\n• Secure connections\n• Connection monitoring\n• System tray integration',
            buttons: ['OK']
        });
    }

    showHelp() {
        dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: 'Help',
            message: 'VNC Server Help',
            detail: 'Quick Start:\n\n1. Configure port and password\n2. Click Start Server\n3. Share your IP address with clients\n4. Monitor connections in real-time\n\nKeyboard Shortcuts:\n• Ctrl+S: Start Server\n• Ctrl+T: Stop Server\n• Ctrl+M: Minimize to Tray\n• Ctrl+A: View Connections',
            buttons: ['OK']
        });
    }

    setupIPC() {
        // Handle application events from renderer
        ipcMain.on('server-started', () => {
            this.isServerRunning = true;
            this.updateTrayIcon(true);
            this.showTrayNotification('VNC Server started successfully');
        });

        ipcMain.on('server-stopped', () => {
            this.isServerRunning = false;
            this.updateTrayIcon(false);
            this.showTrayNotification('VNC Server stopped');
        });

        ipcMain.on('new-connection', (event, clientInfo) => {
            this.showTrayNotification(`New connection from ${clientInfo.ip}`);
        });

        ipcMain.on('connection-ended', (event, clientInfo) => {
            this.showTrayNotification(`Connection from ${clientInfo.ip} ended`);
        });

        ipcMain.on('show-error', (event, title, message) => {
            dialog.showErrorBox(title, message);
        });

        ipcMain.on('show-info', (event, title, message) => {
            dialog.showMessageBox(this.mainWindow, {
                type: 'info',
                title: title,
                message: message,
                buttons: ['OK']
            });
        });
    }

    updateTrayIcon(running) {
        if (this.tray) {
            const iconName = running ? 'tray-icon-active.png' : 'tray-icon.png';
            const iconPath = path.join(__dirname, 'assets', iconName);
            
            try {
                const icon = nativeImage.createFromPath(iconPath);
                this.tray.setImage(icon);
                this.tray.setToolTip(running ? 'VNC Server (Running)' : 'VNC Server (Stopped)');
            } catch (error) {
                console.log('Could not update tray icon:', error.message);
            }
        }
    }

    async init() {
        // Handle app ready
        app.whenReady().then(() => {
            this.createWindow();
            this.setupIPC();
        });

        // Handle window closed (macOS)
        app.on('window-all-closed', () => {
            if (process.platform !== 'darwin') {
                app.quit();
            }
        });

        // Handle app activate (macOS)
        app.on('activate', () => {
            if (BrowserWindow.getAllWindows().length === 0) {
                this.createWindow();
            }
        });

        // Handle before quit
        app.on('before-quit', () => {
            if (this.isServerRunning) {
                // Stop server before quitting
                this.mainWindow.webContents.send('menu-stop-server');
            }
        });

        // Security: Prevent new window creation
        app.on('web-contents-created', (event, contents) => {
            contents.on('new-window', (event) => {
                event.preventDefault();
            });
        });
    }
}

// Initialize and start the application
const vncServerApp = new VNCServerApp();
vncServerApp.init();