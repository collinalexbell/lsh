import { useEffect } from 'react';
import { useRobot } from '../contexts/RobotContext';
import './PositionManager.css';

export function PositionManager() {
  const { state, setSavedPositions, setLastSavedPosition } = useRobot();
  const { savedPositions, positionConfig } = state;

  // Load positions on mount
  useEffect(() => {
    loadPositions();
  }, []);

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

  const moveToPosition = async (name: string) => {
    try {
      const response = await fetch(`/api/positions/move_to/${name}`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        // Track this as the last saved position for servo reset
        if (savedPositions[name]) {
          setLastSavedPosition(name, savedPositions[name].angles);
        }
        console.log(`Moved to position: ${name}`);
      } else {
        console.error('Move failed:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  const deletePosition = async (name: string) => {
    if (!confirm(`Are you sure you want to delete position "${name}"?`)) {
      return;
    }

    try {
      const response = await fetch('/api/positions/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name })
      });
      const data = await response.json();
      
      if (data.success) {
        console.log(`Deleted position: ${name}`);
        // Reload positions to refresh the list
        loadPositions();
      } else {
        console.error('Delete failed:', data.message);
        alert(`Failed to delete position: ${data.message}`);
      }
    } catch (error) {
      console.error('Network error:', error);
      alert('Network error while deleting position');
    }
  };

  const allPositions = Object.entries(savedPositions);
  const enabledPositions = allPositions.filter(
    ([name]) => positionConfig[name]?.enabled
  );

  if (allPositions.length === 0) {
    return (
      <div className="position-manager">
        <h3>Saved Positions</h3>
        <div className="no-positions">
          No positions saved yet. Use the Save Position section to create positions.
        </div>
      </div>
    );
  }

  return (
    <div className="position-manager">
      <h3>Saved Positions</h3>
      <div className="position-buttons">
        {allPositions.map(([name, data]) => {
          const isEnabled = positionConfig[name]?.enabled;
          return (
            <div key={name} className="position-item">
              <button
                className={`position-btn ${isEnabled ? 'enabled' : 'disabled'}`}
                onClick={() => moveToPosition(name)}
                disabled={!isEnabled}
                title={`Move to ${name}: [${data.angles.map(a => a.toFixed(1)).join(', ')}]`}
              >
                {name}
                <div className="position-angles">
                  [{data.angles.map(a => a.toFixed(1)).join(', ')}]
                </div>
              </button>
              <button
                className="delete-btn"
                onClick={() => deletePosition(name)}
                title={`Delete position "${name}"`}
              >
                🗑️
              </button>
            </div>
          );
        })}
      </div>
      <div className="position-info">
        {enabledPositions.length > 0 && (
          <p>Moving to an enabled position will allow individual servo reset.</p>
        )}
        <p>Only enabled positions can be used for movement.</p>
      </div>
    </div>
  );
}