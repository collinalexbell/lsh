import { useState } from 'react';
import { useRobot } from '../contexts/RobotContext';
import './SavePosition.css';

export function SavePosition() {
  const { state, setSavedPositions } = useRobot();
  const [positionName, setPositionName] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const saveCurrentPosition = async () => {
    const name = positionName.trim();
    
    if (!name) {
      alert('Position name is required');
      return;
    }

    if (state.savedPositions[name]) {
      alert(`Position "${name}" already exists`);
      return;
    }

    setIsSaving(true);
    try {
      const response = await fetch('/api/positions/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name })
      });
      const data = await response.json();
      
      if (data.success) {
        // Reload positions to get the updated list
        await loadPositions();
        setPositionName('');
        console.log(`Position "${name}" saved successfully`);
      } else {
        console.error('Save failed:', data.message);
        alert('Failed to save position: ' + data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
      alert('Network error while saving position');
    } finally {
      setIsSaving(false);
    }
  };

  const loadPositions = async () => {
    try {
      const response = await fetch('/api/positions');
      const data = await response.json();
      
      if (data.success) {
        setSavedPositions(data.positions, data.config);
      }
    } catch (error) {
      console.error('Failed to load positions:', error);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      saveCurrentPosition();
    }
  };

  return (
    <div className="save-position">
      <h3>Save Current Position</h3>
      <p className="save-description">
        Move the robot to the desired position using the manual controls above, 
        then save it here with a descriptive name.
      </p>
      
      <div className="save-position-form">
        <input
          type="text"
          className="position-input"
          placeholder="Enter position name (e.g., 'Camera View')"
          value={positionName}
          onChange={(e) => setPositionName(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isSaving}
        />
        <button
          onClick={saveCurrentPosition}
          disabled={isSaving || !positionName.trim()}
          className="btn-primary"
        >
          {isSaving ? 'Saving...' : 'Save Position'}
        </button>
      </div>

      <div className="current-angles">
        <strong>Current angles:</strong>
        <div className="angles-display">
          {state.currentAngles.map((angle, index) => (
            <span key={index} className="angle-value">
              J{index + 1}: {angle.toFixed(1)}°
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}