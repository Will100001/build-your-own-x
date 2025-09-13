const { app, BrowserWindow, Menu, dialog, ipcMain } = require('electron');
const path = require('path');

class VNCViewerApp {
    constructor() {
        this.mainWindow = null;
        this.isDev = process.argv.includes('--dev');
    }

    async createWindow() {
        // Create the browser window
        this.mainWindow = new BrowserWindow({
            width: 1200,
            height: 900,
            minWidth: 800,
            minHeight: 600,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: false,
                enableRemoteModule: true
            },
            icon: path.join(__dirname, 'assets', 'icon.png'),
            title: 'VNC Viewer',
            show: false
        });

        // Load the viewer HTML file
        await this.mainWindow.loadFile('viewer.html');

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

        // Create application menu
        this.createMenu();
    }

    createMenu() {
        const template = [
            {
                label: 'File',
                submenu: [
                    {
                        label: 'New Connection',
                        accelerator: 'CmdOrCtrl+N',
                        click: () => {
                            this.mainWindow.webContents.send('menu-new-connection');
                        }
                    },
                    {
                        label: 'Connection Manager',
                        accelerator: 'CmdOrCtrl+M',
                        click: () => {
                            this.showConnectionManager();
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
                        label: 'Fullscreen',
                        accelerator: 'F11',
                        click: () => {
                            const isFullScreen = this.mainWindow.isFullScreen();
                            this.mainWindow.setFullScreen(!isFullScreen);
                        }
                    },
                    {
                        label: 'Toggle Developer Tools',
                        accelerator: 'F12',
                        click: () => {
                            this.mainWindow.webContents.toggleDevTools();
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'Zoom In',
                        accelerator: 'CmdOrCtrl+Plus',
                        click: () => {
                            this.mainWindow.webContents.send('menu-zoom-in');
                        }
                    },
                    {
                        label: 'Zoom Out',
                        accelerator: 'CmdOrCtrl+-',
                        click: () => {
                            this.mainWindow.webContents.send('menu-zoom-out');
                        }
                    },
                    {
                        label: 'Reset Zoom',
                        accelerator: 'CmdOrCtrl+0',
                        click: () => {
                            this.mainWindow.webContents.send('menu-reset-zoom');
                        }
                    }
                ]
            },
            {
                label: 'Connection',
                submenu: [
                    {
                        label: 'Connect',
                        accelerator: 'CmdOrCtrl+Enter',
                        click: () => {
                            this.mainWindow.webContents.send('menu-connect');
                        }
                    },
                    {
                        label: 'Disconnect',
                        accelerator: 'CmdOrCtrl+D',
                        click: () => {
                            this.mainWindow.webContents.send('menu-disconnect');
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'Send Ctrl+Alt+Del',
                        accelerator: 'CmdOrCtrl+Alt+Delete',
                        click: () => {
                            this.mainWindow.webContents.send('menu-ctrl-alt-del');
                        }
                    },
                    {
                        label: 'Refresh Screen',
                        accelerator: 'F5',
                        click: () => {
                            this.mainWindow.webContents.send('menu-refresh');
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

    showConnectionManager() {
        dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: 'Connection Manager',
            message: 'Connection Manager',
            detail: 'This feature would show saved connections and allow managing them.',
            buttons: ['OK']
        });
    }

    showAbout() {
        dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: 'About VNC Viewer',
            message: 'VNC Viewer v1.0.0',
            detail: 'A cross-platform VNC viewer application built with Electron.\n\nFeatures:\n• Remote desktop access\n• Cross-platform compatibility\n• Secure connections\n• User-friendly interface',
            buttons: ['OK']
        });
    }

    showHelp() {
        dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: 'Help',
            message: 'VNC Viewer Help',
            detail: 'Quick Start:\n\n1. Enter the host IP address or hostname\n2. Set the port (default: 5900)\n3. Click Connect\n4. Enter password if required\n\nKeyboard Shortcuts:\n• Ctrl+N: New Connection\n• Ctrl+D: Disconnect\n• F11: Fullscreen\n• F5: Refresh Screen',
            buttons: ['OK']
        });
    }

    setupIPC() {
        // Handle application events from renderer
        ipcMain.on('app-minimize', () => {
            if (this.mainWindow) {
                this.mainWindow.minimize();
            }
        });

        ipcMain.on('app-close', () => {
            if (this.mainWindow) {
                this.mainWindow.close();
            }
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

        // Security: Prevent new window creation
        app.on('web-contents-created', (event, contents) => {
            contents.on('new-window', (event) => {
                event.preventDefault();
            });
        });
    }
}

// Initialize and start the application
const vncViewerApp = new VNCViewerApp();
vncViewerApp.init();