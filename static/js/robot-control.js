// Robot joint control functionality
class RobotController {
    constructor() {
        this.currentAngles = [0, 0, 0, 0, 0, 0];
        this.jointLimits = [[-168, 168], [-135, 135], [-145, 145], [-148, 148], [-168, 168], [-180, 180]];
        this.jointNames = ['Base', 'Shoulder', 'Elbow', 'Wrist 1', 'Wrist 2', 'Wrist 3'];
        this.init();
    }

    init() {
        this.initSpeedControl();
        this.initJointControls();
        this.getCurrentPosition();
    }

    initSpeedControl() {
        const speedSlider = document.getElementById('speed-slider');
        const speedValue = document.getElementById('speed-value');
        
        if (speedSlider && speedValue) {
            speedSlider.oninput = function() {
                speedValue.textContent = this.value;
            };
        }
    }

    initJointControls() {
        const controlsContainer = document.getElementById('joint-controls');
        
        if (!controlsContainer) {
            console.error('joint-controls container not found');
            return;
        }
        
        controlsContainer.innerHTML = '';
        
        for (let i = 0; i < 6; i++) {
            const [minAngle, maxAngle] = this.jointLimits[i];
            const currentAngle = this.currentAngles[i] || 0;
            const jointDiv = document.createElement('div');
            jointDiv.className = 'joint-control';
            jointDiv.innerHTML = `
                <div class="joint-header">
                    <span class="joint-name">Joint ${i + 1} (${this.jointNames[i]})</span>
                    <span class="joint-value" id="joint-value-${i}">${currentAngle.toFixed(1)}°</span>
                </div>
                <input type="range" 
                       id="joint-slider-${i}" 
                       class="joint-slider"
                       min="${minAngle}" 
                       max="${maxAngle}" 
                       value="${currentAngle}" 
                       step="0.5"
                       oninput="window.robotController.moveJoint(${i}, this.value)">
                <div class="joint-limits">
                    <span>${minAngle}°</span>
                    <span>${maxAngle}°</span>
                </div>
            `;
            controlsContainer.appendChild(jointDiv);
        }
    }

    moveJoint(jointId, angle) {
        const speed = document.getElementById('speed-slider').value;
        const angleValue = parseFloat(angle);
        
        // Set manual control mode
        window.statusManager.setManualControl(true);
        
        // Update display immediately
        document.getElementById(`joint-value-${jointId}`).textContent = `${angleValue.toFixed(1)}°`;
        this.currentAngles[jointId] = angleValue;
        
        // Send to robot
        fetch('/api/joint/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                joint_id: jointId,
                angle: angleValue,
                speed: parseInt(speed)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                MessageHandler.show(data.message, 'error');
            } else if (data.angles) {
                this.currentAngles = data.angles;
            }
        })
        .catch(error => {
            MessageHandler.show('Network error: ' + error.message, 'error');
        });
    }

    async getCurrentPosition() {
        // Reset manual control mode
        window.statusManager.setManualControl(false);
        
        try {
            const response = await fetch('/api/joints/get_current');
            const data = await response.json();
            
            if (data.success) {
                this.currentAngles = data.angles;
                this.updateSliders();
                MessageHandler.show('Current position synchronized', 'success');
            } else {
                MessageHandler.show('Failed to get current position: ' + data.message, 'error');
            }
        } catch (error) {
            MessageHandler.show('Network error: ' + error.message, 'error');
        }
    }

    updateAngles(angles) {
        this.currentAngles = angles;
        this.updateSliders();
    }

    updateSliders() {
        for (let i = 0; i < 6; i++) {
            const slider = document.getElementById(`joint-slider-${i}`);
            const value = document.getElementById(`joint-value-${i}`);
            if (slider && value && this.currentAngles[i] !== undefined) {
                slider.value = this.currentAngles[i] || 0;
                value.textContent = `${(this.currentAngles[i] || 0).toFixed(1)}°`;
            }
        }
    }

    setJointLimits(limits) {
        this.jointLimits = limits;
        // Reinitialize controls with new limits
        this.initJointControls();
    }
}

// Expose globally
window.getCurrentPosition = function() {
    if (window.robotController) {
        window.robotController.getCurrentPosition();
    }
};