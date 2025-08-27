import { useState, useEffect } from 'react';
import { useRobot } from '../contexts/RobotContext';
import { JointControl } from './JointControl';
import './RobotController.css';

export function RobotController() {
  const { state, updateCurrentAngles, setConnectionStatus } = useRobot();
  const [speed, setSpeed] = useState(50);
  const [isLoading, setIsLoading] = useState(false);

  // Get current position from robot on mount
  useEffect(() => {
    getCurrentPosition();
  }, []);

  const getCurrentPosition = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/joints/get_current');
      const data = await response.json();
      
      if (data.success) {
        updateCurrentAngles(data.angles);
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('disconnected');
        console.error('Failed to get current position:', data.message);
      }
    } catch (error) {
      setConnectionStatus('disconnected');
      console.error('Network error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const powerOff = async () => {
    try {
      const response = await fetch('/api/power_off', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (data.success) {
        console.log('Robot powered off');
      } else {
        console.error('Power off failed:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  const moveHome = async () => {
    try {
      const response = await fetch('/api/home', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (data.success) {
        console.log('Moved to home position');
        // Refresh current position after move
        setTimeout(getCurrentPosition, 1000);
      } else {
        console.error('Home move failed:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  const runDemo = async () => {
    try {
      const response = await fetch('/api/demo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (data.success) {
        console.log('Demo started');
        // Refresh current position after demo
        setTimeout(getCurrentPosition, 3000);
      } else {
        console.error('Demo failed:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  const extend = async () => {
    try {
      const response = await fetch('/api/extend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (data.success) {
        console.log('Robot extended');
        // Refresh current position after extend
        setTimeout(getCurrentPosition, 2000);
      } else {
        console.error('Extend failed:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  return (
    <div className="robot-controller">
      <div className="control-header">
        <h2>Manual Joint Control</h2>
        <div className="control-buttons">
          <button onClick={runDemo} className="btn-secondary">
            Run Demo
          </button>
          <button onClick={moveHome} className="btn-secondary">
            Home Position
          </button>
          <button onClick={extend} className="btn-secondary">
            Extend
          </button>
          <button 
            onClick={getCurrentPosition} 
            disabled={isLoading}
            className="btn-primary"
          >
            {isLoading ? 'Syncing...' : 'Sync Current'}
          </button>
          <button onClick={powerOff} className="btn-warning">
            Power Off
          </button>
        </div>
      </div>
      
      <div className="speed-control">
        <label className="speed-label">
          Speed: <span className="speed-value">{speed}%</span>
        </label>
        <input
          type="range"
          className="speed-slider"
          min="10"
          max="100"
          value={speed}
          onChange={(e) => setSpeed(parseInt(e.target.value))}
        />
      </div>

      {state.lastSavedPosition && (
        <div className="last-saved-info">
          <span>Last saved position: <strong>{state.lastSavedPosition.name}</strong></span>
        </div>
      )}

      <div className="joints-container">
        {Array.from({ length: 6 }, (_, i) => (
          <JointControl key={i} jointId={i} speed={speed} />
        ))}
      </div>
    </div>
  );
}