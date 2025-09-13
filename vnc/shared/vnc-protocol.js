/**
 * VNC Protocol Implementation
 * A simplified implementation of the VNC (Virtual Network Computing) protocol
 */

class VNCProtocol {
    constructor() {
        this.state = 'disconnected';
        this.width = 1024;
        this.height = 768;
        this.buffer = null;
        this.callbacks = {};
    }

    // Event handling
    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }

    emit(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => callback(data));
        }
    }

    // VNC Protocol Constants
    static PROTOCOL_VERSION = '003.008';
    static MESSAGE_TYPES = {
        FRAMEBUFFER_UPDATE_REQUEST: 3,
        KEY_EVENT: 4,
        POINTER_EVENT: 5,
        CLIENT_CUT_TEXT: 6,
        FRAMEBUFFER_UPDATE: 0,
        SET_COLOR_MAP_ENTRIES: 1,
        BELL: 2,
        SERVER_CUT_TEXT: 3
    };

    // Initialize connection
    async connect(host, port = 5900) {
        try {
            this.state = 'connecting';
            this.emit('connecting', { host, port });
            
            // Simulate connection process
            await this.delay(1000);
            
            this.state = 'connected';
            this.emit('connected', { host, port });
            
            // Initialize framebuffer
            this.initializeFramebuffer();
            
            return true;
        } catch (error) {
            this.state = 'error';
            this.emit('error', error);
            return false;
        }
    }

    // Initialize framebuffer
    initializeFramebuffer() {
        this.buffer = new ImageData(this.width, this.height);
        // Fill with a default pattern
        for (let i = 0; i < this.buffer.data.length; i += 4) {
            this.buffer.data[i] = 50;     // R
            this.buffer.data[i + 1] = 50; // G
            this.buffer.data[i + 2] = 100; // B
            this.buffer.data[i + 3] = 255; // A
        }
        this.emit('framebuffer_update', this.buffer);
    }

    // Send key event
    sendKeyEvent(key, pressed) {
        if (this.state !== 'connected') return;
        
        const keyCode = this.getKeyCode(key);
        this.emit('key_event', { key, keyCode, pressed });
    }

    // Send pointer event
    sendPointerEvent(x, y, buttonMask) {
        if (this.state !== 'connected') return;
        
        this.emit('pointer_event', { x, y, buttonMask });
    }

    // Send clipboard text
    sendClipboardText(text) {
        if (this.state !== 'connected') return;
        
        this.emit('clipboard_text', { text });
    }

    // Request framebuffer update
    requestFramebufferUpdate(incremental = false, x = 0, y = 0, width = null, height = null) {
        if (this.state !== 'connected') return;
        
        width = width || this.width;
        height = height || this.height;
        
        this.emit('framebuffer_update_request', { incremental, x, y, width, height });
        
        // Simulate response
        setTimeout(() => {
            this.simulateFramebufferUpdate(x, y, width, height);
        }, 100);
    }

    // Simulate framebuffer update (for demo purposes)
    simulateFramebufferUpdate(x, y, width, height) {
        if (!this.buffer) return;
        
        // Add some random pixels to show activity
        for (let i = 0; i < 100; i++) {
            const px = Math.floor(Math.random() * this.width);
            const py = Math.floor(Math.random() * this.height);
            const index = (py * this.width + px) * 4;
            
            this.buffer.data[index] = Math.floor(Math.random() * 255);
            this.buffer.data[index + 1] = Math.floor(Math.random() * 255);
            this.buffer.data[index + 2] = Math.floor(Math.random() * 255);
        }
        
        this.emit('framebuffer_update', this.buffer);
    }

    // Get key code mapping
    getKeyCode(key) {
        const keyMap = {
            'Enter': 65293,
            'Backspace': 65288,
            'Tab': 65289,
            'Escape': 65307,
            'Space': 32,
            'ArrowLeft': 65361,
            'ArrowUp': 65362,
            'ArrowRight': 65363,
            'ArrowDown': 65364
        };
        
        return keyMap[key] || key.charCodeAt(0);
    }

    // Disconnect
    disconnect() {
        this.state = 'disconnected';
        this.emit('disconnected');
    }

    // Utility function for delays
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export for both Node.js and browser environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VNCProtocol;
} else {
    window.VNCProtocol = VNCProtocol;
}