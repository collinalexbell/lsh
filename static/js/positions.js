// Position management functionality
class PositionManager {
    constructor() {
        this.positions = {};
        this.config = {};
        this.init();
    }

    async init() {
        await this.loadPositions();
        this.renderPositions();
    }

    async loadPositions() {
        try {
            const response = await fetch('/api/positions');
            const data = await response.json();
            
            if (data.success) {
                this.positions = data.positions;
                this.config = data.config;
            }
        } catch (error) {
            console.error('Failed to load positions:', error);
        }
    }

    async savePosition(name) {
        if (!name || !name.trim()) {
            MessageHandler.show('Position name is required', 'error');
            return;
        }

        if (this.positions[name]) {
            MessageHandler.show(`Position "${name}" already exists`, 'error');
            return;
        }

        try {
            const response = await fetch('/api/positions/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: name.trim() })
            });
            const data = await response.json();
            
            if (data.success) {
                await this.loadPositions();
                this.renderPositions();
                
                // Clear input
                const input = document.getElementById('position-name-input');
                if (input) input.value = '';
                
                MessageHandler.show(data.message, 'success');
            } else {
                MessageHandler.show(data.message, 'error');
            }
        } catch (error) {
            MessageHandler.show('Network error: ' + error.message, 'error');
        }
    }

    async deletePosition(name) {
        if (!confirm(`Are you sure you want to delete position "${name}"?`)) {
            return;
        }

        try {
            const response = await fetch('/api/positions/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name })
            });
            const data = await response.json();
            
            if (data.success) {
                await this.loadPositions();
                this.renderPositions();
                MessageHandler.show(data.message, 'success');
            } else {
                MessageHandler.show(data.message, 'error');
            }
        } catch (error) {
            MessageHandler.show('Network error: ' + error.message, 'error');
        }
    }

    async togglePosition(name, enabled) {
        try {
            const response = await fetch('/api/positions/update_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, enabled })
            });
            const data = await response.json();
            
            if (data.success) {
                this.config[name] = { enabled };
                MessageHandler.show(data.message, 'success');
            } else {
                MessageHandler.show(data.message, 'error');
            }
        } catch (error) {
            MessageHandler.show('Network error: ' + error.message, 'error');
        }
    }

    async moveToPosition(name) {
        try {
            const response = await fetch(`/api/positions/move_to/${name}`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                MessageHandler.show(data.message, 'success');
                
                // Track this position as the last saved position for individual servo reset
                if (this.positions[name] && window.robotController) {
                    window.robotController.setLastSavedPosition(name, this.positions[name].angles);
                }
                
                // Update status if available
                if (window.socketManager) {
                    window.socketManager.requestStatus();
                }
            } else {
                MessageHandler.show(data.message, 'error');
            }
        } catch (error) {
            MessageHandler.show('Network error: ' + error.message, 'error');
        }
    }

    renderPositions() {
        // Render positions list (for positions page)
        const positionsList = document.getElementById('positions-list');
        if (positionsList) {
            this.renderPositionsList(positionsList);
        }

        // Render command center buttons (for command center page)
        const commandButtons = document.getElementById('command-buttons');
        if (commandButtons) {
            this.renderCommandButtons(commandButtons);
        }
    }

    renderPositionsList(container) {
        if (Object.keys(this.positions).length === 0) {
            container.innerHTML = '<div class="no-positions">No positions saved</div>';
            return;
        }

        container.innerHTML = Object.entries(this.positions).map(([name, data]) => `
            <div class="position-item">
                <div class="position-header">
                    <h3>${name}</h3>
                    <div class="position-actions">
                        <button onclick="window.positionManager.moveToPosition('${name}')" class="btn-primary">
                            Move To
                        </button>
                        <button onclick="window.positionManager.deletePosition('${name}')" class="btn-danger">
                            Delete
                        </button>
                    </div>
                </div>
                <div class="position-details">
                    <div class="position-info">
                        <span>Created: ${data.created}</span>
                        <span>Angles: [${data.angles.map(a => a.toFixed(1)).join(', ')}]</span>
                    </div>
                    <div class="position-toggle">
                        <label>
                            <input type="checkbox" 
                                   ${this.config[name]?.enabled ? 'checked' : ''} 
                                   onchange="window.positionManager.togglePosition('${name}', this.checked)">
                            Show in Command Center
                        </label>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderCommandButtons(container) {
        const enabledPositions = Object.entries(this.positions).filter(
            ([name]) => this.config[name]?.enabled
        );

        if (enabledPositions.length === 0) {
            container.innerHTML = '<div class="no-positions">No positions enabled for command center</div>';
            return;
        }

        container.innerHTML = enabledPositions.map(([name, data]) => `
            <button class="position-btn" onclick="window.positionManager.moveToPosition('${name}')">
                ${name}
                <div class="position-angles">[${data.angles.map(a => a.toFixed(1)).join(', ')}]</div>
            </button>
        `).join('');
    }
}

// Initialize position manager on appropriate pages
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('positions-list') || document.getElementById('command-buttons')) {
        window.positionManager = new PositionManager();
    }
});

// Expose functions globally
window.saveCurrentPosition = function() {
    const input = document.getElementById('position-name-input');
    if (input && window.positionManager) {
        window.positionManager.savePosition(input.value);
    }
};