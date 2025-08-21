// Main application controller
class StatusManager {
    constructor() {
        this.isManualControl = false;
        this.manualControlTimeout = null;
    }

    update(status) {
        this.updateConnection(status);
        this.updateAngles(status);
        this.updateJointLimits(status);
        this.updateStatusIndicators(status);
        this.updateButtonStates(status);
    }

    updateConnection(status) {
        const indicator = document.getElementById('connection-indicator');
        const connectionStatus = document.getElementById('connection-status');
        
        if (indicator && connectionStatus) {
            if (status.connected) {
                indicator.className = 'status-indicator connected';
                connectionStatus.textContent = 'Connected';
            } else {
                indicator.className = 'status-indicator disconnected';
                connectionStatus.textContent = 'Disconnected';
            }
        }
    }

    updateAngles(status) {
        if (!status.angles) return;

        // Update status display
        for (let i = 0; i < 6; i++) {
            const angleEl = document.getElementById(`angle-${i}`);
            if (angleEl) {
                angleEl.textContent = `${status.angles[i]?.toFixed(1) || 0}°`;
            }
        }

        // Update robot control sliders if not in manual control
        if (!this.isManualControl && window.robotController) {
            window.robotController.updateAngles(status.angles);
        }
    }

    updateJointLimits(status) {
        if (status.joint_limits && window.robotController) {
            window.robotController.setJointLimits(status.joint_limits);
        }
    }

    updateStatusIndicators(status) {
        const updates = [
            { id: 'recording-status', value: status.is_recording ? 'Recording' : 'Idle' },
            { id: 'playing-status', value: status.is_playing ? 'Playing' : 'Idle' },
            { id: 'jiggling-status', value: status.is_jiggling ? 'Jiggling' : 'Idle' },
            { id: 'video-recording-status', value: status.is_recording_video ? 'Recording' : 'Idle' },
            { id: 'moves-count', value: status.recorded_moves_count || 0 }
        ];

        updates.forEach(({ id, value }) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }

    updateButtonStates(status) {
        const buttons = {
            'start-recording-btn': { disabled: status.is_recording || status.is_playing || status.is_jiggling },
            'capture-btn': { disabled: !status.is_recording },
            'stop-recording-btn': { disabled: !status.is_recording },
            'play-btn': { disabled: status.is_playing || status.is_recording || status.is_jiggling || status.recorded_moves_count === 0 },
            'stop-play-btn': { disabled: !status.is_playing },
            'start-jiggle-btn': { disabled: status.is_jiggling || status.is_recording || status.is_playing || status.recorded_moves_count === 0 },
            'stop-jiggle-btn': { disabled: !status.is_jiggling }
        };

        Object.entries(buttons).forEach(([id, props]) => {
            const btn = document.getElementById(id);
            if (btn) {
                Object.assign(btn, props);
            }
        });
    }

    setManualControl(active) {
        this.isManualControl = active;
        clearTimeout(this.manualControlTimeout);
        
        if (active) {
            this.manualControlTimeout = setTimeout(() => {
                this.isManualControl = false;
            }, 3000);
        }
    }
}

// Basic robot commands
class BasicControls {
    static runDemo() { return ApiClient.call('/api/demo'); }
    static moveHome() { return ApiClient.call('/api/home'); }
    static extend() { return ApiClient.call('/api/extend'); }
    static powerOff() {
        if (confirm('Are you sure you want to power off the robot?')) {
            return ApiClient.call('/api/robot/power_off');
        }
    }
}

// Recording controls
class RecordingControls {
    static startRecording() { return ApiClient.call('/api/record/start'); }
    static capturePosition() { return ApiClient.call('/api/record/capture'); }
    static stopRecording() { return ApiClient.call('/api/record/stop'); }
    
    static playChoreography() { return ApiClient.call('/api/choreography/play'); }
    static stopChoreography() { return ApiClient.call('/api/choreography/stop'); }
    static clearChoreography() {
        if (confirm('Are you sure you want to clear all recorded moves?')) {
            return ApiClient.call('/api/choreography/clear');
        }
    }
    
    static startJiggling() { return ApiClient.call('/api/jiggle/start'); }
    static stopJiggling() { return ApiClient.call('/api/jiggle/stop'); }
}

// Global instances
window.statusManager = new StatusManager();
window.socketManager = new SocketManager();

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Main application initialized');
    
    // Initialize robot controller if on main page
    if (document.getElementById('joint-controls')) {
        window.robotController = new RobotController();
    }
    
    // Initialize camera controller if video elements exist
    if (document.getElementById('video-stream') || document.getElementById('camera-feed')) {
        window.cameraController = new CameraController();
    }
    
    // Start status updates
    setInterval(() => {
        window.socketManager.requestStatus();
    }, 2000);
});

// Expose functions globally for onclick handlers
window.runDemo = BasicControls.runDemo;
window.moveHome = BasicControls.moveHome;
window.extend = BasicControls.extend;
window.powerOff = BasicControls.powerOff;

window.startRecording = RecordingControls.startRecording;
window.capturePosition = RecordingControls.capturePosition;
window.stopRecording = RecordingControls.stopRecording;
window.playChoreography = RecordingControls.playChoreography;
window.stopChoreography = RecordingControls.stopChoreography;
window.clearChoreography = RecordingControls.clearChoreography;
window.startJiggling = RecordingControls.startJiggling;
window.stopJiggling = RecordingControls.stopJiggling;