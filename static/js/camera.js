// Camera and video recording functionality
class CameraController {
    constructor() {
        this.currentVideoFilename = null;
        this.init();
    }

    init() {
        // Initialize camera controls
        console.log('Camera controller initialized');
    }

    async startCamera() {
        const videoStream = document.getElementById('video-stream');
        const videoPlaceholder = document.getElementById('video-placeholder');
        const startBtn = document.getElementById('start-camera-btn');
        const stopBtn = document.getElementById('stop-camera-btn');
        const screenshotBtn = document.getElementById('screenshot-btn');
        const startVideoBtn = document.getElementById('start-video-btn');
        
        const data = await ApiClient.call('/api/camera/start');
        if (data.success) {
            videoPlaceholder.style.display = 'none';
            videoStream.style.display = 'block';
            startBtn.disabled = true;
            stopBtn.disabled = false;
            screenshotBtn.disabled = false;
            startVideoBtn.disabled = false;
        }
    }

    async stopCamera() {
        const videoStream = document.getElementById('video-stream');
        const videoPlaceholder = document.getElementById('video-placeholder');
        const startBtn = document.getElementById('start-camera-btn');
        const stopBtn = document.getElementById('stop-camera-btn');
        const screenshotBtn = document.getElementById('screenshot-btn');
        const startVideoBtn = document.getElementById('start-video-btn');
        const stopVideoBtn = document.getElementById('stop-video-btn');
        
        // Stop video recording if active
        if (!stopVideoBtn.disabled) {
            this.stopVideoRecording();
        }
        
        const data = await ApiClient.call('/api/camera/stop');
        if (data.success) {
            videoStream.style.display = 'none';
            videoPlaceholder.style.display = 'flex';
            startBtn.disabled = false;
            stopBtn.disabled = true;
            screenshotBtn.disabled = true;
            startVideoBtn.disabled = true;
        }
    }

    async takeScreenshot() {
        try {
            const response = await fetch('/api/camera/screenshot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            const data = await response.json();
            
            if (data.success) {
                // Create download link
                const link = document.createElement('a');
                link.href = data.image;
                link.download = `screenshot_${new Date().toISOString().replace(/[:.]/g, '-')}.jpg`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                MessageHandler.show('Screenshot captured and downloaded!', 'success');
            } else {
                MessageHandler.show('Screenshot failed: ' + data.message, 'error');
            }
        } catch (error) {
            MessageHandler.show('Network error: ' + error.message, 'error');
        }
    }

    async startVideoRecording() {
        const startVideoBtn = document.getElementById('start-video-btn');
        const stopVideoBtn = document.getElementById('stop-video-btn');
        const videoStatus = document.getElementById('video-status');
        
        try {
            const response = await fetch('/api/video/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            const data = await response.json();
            
            if (data.success) {
                this.currentVideoFilename = data.filename;
                startVideoBtn.disabled = true;
                stopVideoBtn.disabled = false;
                videoStatus.textContent = `Recording: ${data.filename}`;
                videoStatus.style.color = '#FF9800';
                MessageHandler.show('Video recording started!', 'success');
            } else {
                MessageHandler.show('Failed to start video recording: ' + data.message, 'error');
            }
        } catch (error) {
            MessageHandler.show('Network error: ' + error.message, 'error');
        }
    }

    async stopVideoRecording() {
        const startVideoBtn = document.getElementById('start-video-btn');
        const stopVideoBtn = document.getElementById('stop-video-btn');
        const videoStatus = document.getElementById('video-status');
        
        try {
            const response = await fetch('/api/video/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            const data = await response.json();
            
            if (data.success) {
                startVideoBtn.disabled = false;
                stopVideoBtn.disabled = true;
                videoStatus.innerHTML = `Recording stopped. <a href="/api/video/download/${data.filename}" download style="color: #4CAF50;">Download ${data.filename}</a>`;
                videoStatus.style.color = '#4CAF50';
                MessageHandler.show('Video recording stopped! Click link to download.', 'success');
                this.currentVideoFilename = null;
            } else {
                MessageHandler.show('Failed to stop video recording: ' + data.message, 'error');
            }
        } catch (error) {
            MessageHandler.show('Network error: ' + error.message, 'error');
        }
    }
}

// Expose functions globally for onclick handlers
window.startCamera = function() {
    if (window.cameraController) {
        window.cameraController.startCamera();
    }
};

window.stopCamera = function() {
    if (window.cameraController) {
        window.cameraController.stopCamera();
    }
};

window.takeScreenshot = function() {
    if (window.cameraController) {
        window.cameraController.takeScreenshot();
    }
};

window.startVideoRecording = function() {
    if (window.cameraController) {
        window.cameraController.startVideoRecording();
    }
};

window.stopVideoRecording = function() {
    if (window.cameraController) {
        window.cameraController.stopVideoRecording();
    }
};