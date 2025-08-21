// Shared utility functions
class ApiClient {
    static async call(endpoint, method = 'POST') {
        try {
            const response = await fetch(endpoint, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            const data = await response.json();
            
            if (data.success) {
                MessageHandler.show(data.message, 'success');
            } else {
                MessageHandler.show(data.message, 'error');
            }
            
            return data;
        } catch (error) {
            MessageHandler.show('Network error: ' + error.message, 'error');
            return { success: false, message: error.message };
        }
    }
}

class MessageHandler {
    static show(text, type = 'success') {
        const messageEl = document.getElementById('message');
        if (messageEl) {
            messageEl.textContent = text;
            messageEl.className = `message ${type}`;
            messageEl.style.display = 'block';
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 3000);
        }
    }
}

class SocketManager {
    constructor() {
        this.socket = null;
        this.init();
    }

    init() {
        try {
            if (typeof io !== 'undefined') {
                this.socket = io();
                
                this.socket.on('connect', () => {
                    console.log('Connected to server');
                    this.socket.emit('request_status');
                });
                
                this.socket.on('status_update', (data) => {
                    if (window.statusManager) {
                        window.statusManager.update(data);
                    }
                });
            } else {
                console.warn('Socket.IO not available, using polling mode');
                this.socket = null;
            }
        } catch (e) {
            console.error('Socket.IO initialization failed:', e);
            this.socket = null;
        }
    }

    emit(event, data) {
        if (this.socket && this.socket.connected) {
            this.socket.emit(event, data);
        }
    }

    requestStatus() {
        if (this.socket && this.socket.connected) {
            this.socket.emit('request_status');
        } else {
            // Fallback to API polling
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (window.statusManager) {
                        window.statusManager.update(data);
                    }
                })
                .catch(error => console.log('Status update failed:', error));
        }
    }
}