import { useRobot } from '../contexts/RobotContext';
import { JOINT_LIMITS, JOINT_NAMES } from '../types/robot';
import './JointControl.css';

interface JointControlProps {
  jointId: number;
  speed: number;
}

export function JointControl({ jointId, speed }: JointControlProps) {
  const { state, updateCurrentAngles } = useRobot();
  const { currentAngles, lastSavedPosition } = state;
  
  const currentAngle = currentAngles[jointId] || 0;
  const limits = JOINT_LIMITS[jointId];
  const jointName = JOINT_NAMES[jointId];
  
  const handleSliderChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const newAngle = parseFloat(event.target.value);
    
    // Update UI immediately
    const newAngles = [...currentAngles];
    newAngles[jointId] = newAngle;
    updateCurrentAngles(newAngles);
    
    // Send to robot
    try {
      const response = await fetch('/api/joint/move', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          joint_id: jointId,
          angle: newAngle,
          speed: speed
        })
      });
      
      const data = await response.json();
      if (data.success && data.angles) {
        updateCurrentAngles(data.angles);
      } else if (!data.success) {
        console.error('Joint move failed:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };
  
  const handleResetToSaved = async () => {
    if (!lastSavedPosition || lastSavedPosition.angles[jointId] === undefined) {
      alert('No saved position available for this joint');
      return;
    }
    
    const savedAngle = lastSavedPosition.angles[jointId];
    
    // Update UI immediately
    const newAngles = [...currentAngles];
    newAngles[jointId] = savedAngle;
    updateCurrentAngles(newAngles);
    
    // Send to robot
    try {
      const response = await fetch('/api/joint/move', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          joint_id: jointId,
          angle: savedAngle,
          speed: speed
        })
      });
      
      const data = await response.json();
      if (data.success) {
        if (data.angles) {
          updateCurrentAngles(data.angles);
        }
        console.log(`Joint ${jointId + 1} reset to saved position (${savedAngle.toFixed(1)}°)`);
      } else {
        console.error('Reset failed:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };
  
  return (
    <div className="joint-control">
      <div className="joint-header">
        <span className="joint-name">Joint {jointId + 1} ({jointName})</span>
        <span className="joint-value">{currentAngle.toFixed(1)}°</span>
        {lastSavedPosition && (
          <button 
            className="reset-joint-btn"
            onClick={handleResetToSaved}
            title={`Reset to ${lastSavedPosition.name} (${lastSavedPosition.angles[jointId]?.toFixed(1)}°)`}
          >
            RESET
          </button>
        )}
      </div>
      <input
        type="range"
        className="joint-slider"
        min={limits.min}
        max={limits.max}
        value={currentAngle}
        step="0.5"
        onChange={handleSliderChange}
      />
      <div className="joint-limits">
        <span>{limits.min}°</span>
        <span>{limits.max}°</span>
      </div>
    </div>
  );
}