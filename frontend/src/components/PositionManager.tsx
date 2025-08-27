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

  const enabledPositions = Object.entries(savedPositions).filter(
    ([name]) => positionConfig[name]?.enabled
  );

  if (enabledPositions.length === 0) {
    return (
      <div className="position-manager">
        <h3>Saved Positions</h3>
        <div className="no-positions">
          No positions available. Use the Positions page to create and enable positions.
        </div>
      </div>
    );
  }

  return (
    <div className="position-manager">
      <h3>Saved Positions</h3>
      <div className="position-buttons">
        {enabledPositions.map(([name, data]) => (
          <button
            key={name}
            className="position-btn"
            onClick={() => moveToPosition(name)}
            title={`Move to ${name}: [${data.angles.map(a => a.toFixed(1)).join(', ')}]`}
          >
            {name}
            <div className="position-angles">
              [{data.angles.map(a => a.toFixed(1)).join(', ')}]
            </div>
          </button>
        ))}
      </div>
      <div className="position-info">
        Moving to a saved position will enable individual servo reset buttons.
      </div>
    </div>
  );
}