// Robot joint control functionality
class RobotController {
    constructor() {
        this.currentAngles = [0, 0, 0, 0, 0, 0];
        this.lastSavedAngles = null;
        this.lastSavedPositionName = null;
        this.jointLimits = [[-168, 168], [-135, 135], [-145, 145], [-148, 148], [-168, 168], [-180, 180]];
        this.jointNames = ['Base', 'Shoulder', 'Elbow', 'Wrist 1', 'Wrist 2', 'Wrist 3'];
        this.init();
    }

    init() {
        this.initSpeedControl();
        this.loadLastSavedPosition(); // Load first
        this.initJointControls(); // Then create controls
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
                    <button class="reset-joint-btn" id="reset-joint-${i}" 
                            onclick="window.robotController.resetJointToSaved(${i})"
                            style="display: none"
                            title="Reset to last saved position">↺</button>
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

    setLastSavedPosition(positionName, angles) {
        this.lastSavedPositionName = positionName;
        this.lastSavedAngles = [...angles]; // Make a copy
        this.updateResetButtons();
        
        // Persist to localStorage
        try {
            localStorage.setItem('lastSavedPosition', JSON.stringify({
                name: positionName,
                angles: angles,
                timestamp: Date.now()
            }));
        } catch (e) {
            console.log('Could not save to localStorage:', e);
        }
    }

    loadLastSavedPosition() {
        try {
            const saved = localStorage.getItem('lastSavedPosition');
            if (saved) {
                const data = JSON.parse(saved);
                // Only use if less than 24 hours old
                if (Date.now() - data.timestamp < 24 * 60 * 60 * 1000) {
                    this.lastSavedPositionName = data.name;
                    this.lastSavedAngles = data.angles;
                    this.updateResetButtons();
                } else {
                    localStorage.removeItem('lastSavedPosition');
                }
            }
        } catch (e) {
            console.log('Could not load from localStorage:', e);
        }
    }

    updateResetButtons() {
        console.log('Updating reset buttons, lastSavedAngles:', this.lastSavedAngles);
        for (let i = 0; i < 6; i++) {
            const resetBtn = document.getElementById(`reset-joint-${i}`);
            console.log(`Reset button ${i}:`, resetBtn);
            if (resetBtn) {
                if (this.lastSavedAngles) {
                    resetBtn.style.display = 'inline-block';
                    resetBtn.title = `Reset to last saved position (${this.lastSavedPositionName || 'Unknown'})`;
                    console.log(`Showing reset button ${i}`);
                } else {
                    resetBtn.style.display = 'none';
                    console.log(`Hiding reset button ${i}`);
                }
            } else {
                console.log(`Reset button ${i} not found in DOM`);
            }
        }
    }

    resetJointToSaved(jointId) {
        if (!this.lastSavedAngles || this.lastSavedAngles[jointId] === undefined) {
            MessageHandler.show('No saved position available for this joint', 'error');
            return;
        }

        const savedAngle = this.lastSavedAngles[jointId];
        const speed = document.getElementById('speed-slider').value;

        // Update slider and display
        const slider = document.getElementById(`joint-slider-${jointId}`);
        const valueDisplay = document.getElementById(`joint-value-${jointId}`);
        if (slider) slider.value = savedAngle;
        if (valueDisplay) valueDisplay.textContent = `${savedAngle.toFixed(1)}°`;

        // Set manual control mode
        window.statusManager.setManualControl(true);

        // Send to robot
        fetch('/api/joint/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                joint_id: jointId,
                angle: savedAngle,
                speed: parseInt(speed)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.currentAngles[jointId] = savedAngle;
                MessageHandler.show(`Joint ${jointId + 1} reset to saved position (${savedAngle.toFixed(1)}°)`, 'success');
                if (data.angles) {
                    this.currentAngles = data.angles;
                }
            } else {
                MessageHandler.show(data.message, 'error');
            }
        })
        .catch(error => {
            MessageHandler.show('Network error: ' + error.message, 'error');
        });
    }
}

// Expose globally
window.getCurrentPosition = function() {
    if (window.robotController) {
        window.robotController.getCurrentPosition();
    }
};

// Debug function to test buttons
window.testResetButtons = function() {
    console.log('Testing reset buttons...');
    if (window.robotController) {
        // Set fake saved position for testing
        window.robotController.setLastSavedPosition('Test', [0, 0, 0, 0, 0, 0]);
        console.log('Reset buttons should now be visible');
    }
};