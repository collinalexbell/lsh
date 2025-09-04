import { useState, useEffect } from 'react';
import './WallCalibration.css';

interface CalibrationPoint {
  id: number;
  name: string;
  robotPosition?: [number, number, number]; // Joint angles from robot
  screenPosition?: [number, number]; // Webcam coordinates (x, y pixels)
  worldPosition?: [number, number, number]; // 3D world coordinates (x, y, z in mm)
}

interface WallPlane {
  normal: [number, number, number]; // Plane normal vector
  point: [number, number, number];  // Point on the plane
  equation: [number, number, number, number]; // Ax + By + Cz + D = 0
}

interface WallCalibration {
  name: string;
  points: CalibrationPoint[];
  plane?: WallPlane & {
    local_x_axis?: [number, number, number];
    local_y_axis?: [number, number, number];
    orientation?: [number, number, number];
  };
  created: string;
  updated?: string;
  type?: string;
}

export function WallCalibration() {
  const [calibrations, setCalibrations] = useState<Record<string, WallCalibration>>({});
  const [currentCalibration, setCurrentCalibration] = useState<WallCalibration | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newCalibrationName, setNewCalibrationName] = useState('');
  const [message, setMessage] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeCalibration, setActiveCalibration] = useState<string>('');
  const [movementAmount, setMovementAmount] = useState(10); // mm

  useEffect(() => {
    loadCalibrations();
  }, []);

  const loadCalibrations = async () => {
    try {
      const response = await fetch('/api/wall/calibrations');
      const data = await response.json();
      if (data.success) {
        setCalibrations(data.calibrations || {});
      }
    } catch (error) {
      console.error('Failed to load wall calibrations:', error);
    }
  };

  const createNewCalibration = () => {
    if (!newCalibrationName.trim()) {
      setMessage('Please enter a calibration name');
      return;
    }

    const newCalibration: WallCalibration = {
      name: newCalibrationName.trim(),
      points: [
        { id: 1, name: 'Top Left' },
        { id: 2, name: 'Top Right' },
        { id: 3, name: 'Bottom Left' },
        { id: 4, name: 'Bottom Right' }
      ],
      created: new Date().toISOString()
    };

    setCurrentCalibration(newCalibration);
    setIsCreating(true);
    setNewCalibrationName('');
    setMessage('');
  };

  const createPlaneCalibration = async () => {
    if (!newCalibrationName.trim()) {
      setMessage('Please enter a calibration name');
      return;
    }

    try {
      const response = await fetch('/api/wall/create-plane-calibration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newCalibrationName.trim() })
      });

      const data = await response.json();
      if (data.success) {
        setMessage(`Plane calibration "${newCalibrationName.trim()}" created successfully!`);
        loadCalibrations();
        setNewCalibrationName('');
      } else {
        setMessage(`Failed to create plane calibration: ${data.message}`);
      }
    } catch (error) {
      setMessage(`Error creating plane calibration: ${error}`);
    }
  };

  const addCalibrationPoint = () => {
    if (!currentCalibration) return;
    
    const newPoint: CalibrationPoint = {
      id: currentCalibration.points.length + 1,
      name: `Point ${currentCalibration.points.length + 1}`
    };

    setCurrentCalibration({
      ...currentCalibration,
      points: [...currentCalibration.points, newPoint]
    });
  };

  const removeCalibrationPoint = (pointId: number) => {
    if (!currentCalibration) return;
    
    setCurrentCalibration({
      ...currentCalibration,
      points: currentCalibration.points.filter(p => p.id !== pointId)
    });
  };

  const captureRobotPosition = async (pointId: number) => {
    try {
      const response = await fetch('/api/status');
      const data = await response.json();
      
      if (data.connected && data.angles) {
        // Also get the 3D world position using forward kinematics
        const posResponse = await fetch('/api/end_effector/position');
        const posData = await posResponse.json();
        
        if (posData.success) {
          updateCalibrationPoint(pointId, {
            robotPosition: data.angles,
            worldPosition: posData.position
          });
          setMessage(`Captured robot position for point ${pointId}`);
        } else {
          setMessage('Failed to get end effector position');
        }
      } else {
        setMessage('Robot not connected or failed to get robot angles');
      }
    } catch (error) {
      setMessage(`Error capturing robot position: ${error}`);
    }
  };

  const captureScreenPosition = (pointId: number) => {
    // For now, prompt for manual coordinates - later we'll integrate with camera feed
    const x = parseFloat(prompt('Enter screen X coordinate (pixels):') || '0');
    const y = parseFloat(prompt('Enter screen Y coordinate (pixels):') || '0');
    
    if (x >= 0 && y >= 0) {
      updateCalibrationPoint(pointId, {
        screenPosition: [x, y]
      });
      setMessage(`Set screen position for point ${pointId}: (${x}, ${y})`);
    }
  };

  const updateCalibrationPoint = (pointId: number, updates: Partial<CalibrationPoint>) => {
    if (!currentCalibration) return;
    
    setCurrentCalibration({
      ...currentCalibration,
      points: currentCalibration.points.map(p => 
        p.id === pointId ? { ...p, ...updates } : p
      )
    });
  };

  const calculatePlane = async () => {
    if (!currentCalibration || currentCalibration.points.length < 3) {
      setMessage('Need at least 3 points to calculate plane');
      return;
    }

    // Check that all points have world positions
    const validPoints = currentCalibration.points.filter(p => p.worldPosition);
    if (validPoints.length < 3) {
      setMessage('Need at least 3 points with robot positions captured');
      return;
    }

    try {
      const response = await fetch('/api/wall/calculate-plane', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          points: validPoints.map(p => ({
            id: p.id,
            position: p.worldPosition
          }))
        })
      });

      const data = await response.json();
      if (data.success) {
        setCurrentCalibration({
          ...currentCalibration,
          plane: data.plane
        });
        setMessage(`Plane calculated successfully. Fit error: ${data.fitError?.toFixed(2)}mm`);
      } else {
        setMessage(`Failed to calculate plane: ${data.message}`);
      }
    } catch (error) {
      setMessage(`Error calculating plane: ${error}`);
    }
  };

  const saveCalibration = async () => {
    if (!currentCalibration) return;

    try {
      const response = await fetch('/api/wall/save-calibration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentCalibration)
      });

      const data = await response.json();
      if (data.success) {
        setMessage('Calibration saved successfully!');
        loadCalibrations();
        setCurrentCalibration(null);
        setIsCreating(false);
      } else {
        setMessage(`Failed to save calibration: ${data.message}`);
      }
    } catch (error) {
      setMessage(`Error saving calibration: ${error}`);
    }
  };

  const loadCalibration = (name: string) => {
    setCurrentCalibration(calibrations[name]);
    setIsCreating(true);
  };

  const deleteCalibration = async (name: string) => {
    if (!confirm(`Delete calibration "${name}"?`)) return;

    try {
      const response = await fetch('/api/wall/delete-calibration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });

      const data = await response.json();
      if (data.success) {
        setMessage(`Calibration "${name}" deleted`);
        loadCalibrations();
      } else {
        setMessage(`Failed to delete calibration: ${data.message}`);
      }
    } catch (error) {
      setMessage(`Error deleting calibration: ${error}`);
    }
  };

  const cancelCalibration = () => {
    setCurrentCalibration(null);
    setIsCreating(false);
    setNewCalibrationName('');
    setMessage('');
  };

  const moveInPlane = async (dx: number, dy: number) => {
    if (!activeCalibration) {
      setMessage('Please select an active calibration first');
      return;
    }

    try {
      const response = await fetch('/api/wall/move-in-plane', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          calibrationName: activeCalibration,
          dxLocal: dx,
          dyLocal: dy
        })
      });

      const data = await response.json();
      if (data.success) {
        setMessage(`Moved in plane: dx=${dx}mm, dy=${dy}mm`);
      } else {
        setMessage(`Movement failed: ${data.message}`);
      }
    } catch (error) {
      setMessage(`Error moving in plane: ${error}`);
    }
  };

  const activateCalibration = (name: string) => {
    setActiveCalibration(name);
    setMessage(`Activated calibration: ${name}`);
  };

  return (
    <div className="wall-calibration">
      <div className="calibration-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h3>Wall Calibration</h3>
        <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
      </div>

      {isExpanded && (
        <div className="calibration-content">
          {message && (
            <div className={`message ${message.includes('successfully') || message.includes('Captured') ? 'success' : 'error'}`}>
              {message}
            </div>
          )}

          {!isCreating ? (
            <div className="calibration-list">
              <div className="create-calibration">
                <div className="input-group">
                  <input
                    type="text"
                    value={newCalibrationName}
                    onChange={(e) => setNewCalibrationName(e.target.value)}
                    placeholder="Enter calibration name"
                    className="calibration-name-input"
                  />
                  <div className="create-buttons">
                    <button onClick={createPlaneCalibration} className="create-btn plane">
                      Create Plane Calibration
                    </button>
                    <button onClick={createNewCalibration} className="create-btn traditional">
                      Traditional Calibration
                    </button>
                  </div>
                </div>
              </div>

              {Object.keys(calibrations).length > 0 && (
                <div className="saved-calibrations">
                  <h4>Saved Calibrations</h4>
                  {Object.entries(calibrations).map(([name, calibration]) => (
                    <div key={name} className="calibration-item">
                      <div className="calibration-info">
                        <span className="calibration-name">{name}</span>
                        <span className="calibration-details">
                          {calibration.type === 'plane_based' ? 'Plane-based' : `${calibration.points.length} points`}
                          {calibration.plane && <span className="has-plane"> • Plane calculated</span>}
                          {activeCalibration === name && <span className="active-indicator"> • ACTIVE</span>}
                        </span>
                      </div>
                      <div className="calibration-actions">
                        {calibration.type === 'plane_based' ? (
                          <button 
                            onClick={() => activateCalibration(name)} 
                            className={`activate-btn ${activeCalibration === name ? 'active' : ''}`}
                          >
                            {activeCalibration === name ? 'Active' : 'Activate'}
                          </button>
                        ) : (
                          <button onClick={() => loadCalibration(name)} className="edit-btn">
                            Edit
                          </button>
                        )}
                        <button onClick={() => deleteCalibration(name)} className="delete-btn">
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeCalibration && (
                <div className="plane-movement-controls">
                  <h4>Plane Movement Controls</h4>
                  <div className="movement-info">
                    <span>Active Calibration: <strong>{activeCalibration}</strong></span>
                    <div className="movement-amount">
                      <label>Movement Amount (mm):</label>
                      <input
                        type="number"
                        value={movementAmount}
                        onChange={(e) => setMovementAmount(Number(e.target.value))}
                        min="1"
                        max="50"
                        className="amount-input"
                      />
                    </div>
                  </div>
                  
                  <div className="movement-grid">
                    <div className="movement-row">
                      <button 
                        onClick={() => moveInPlane(0, movementAmount)}
                        className="movement-btn up"
                      >
                        ↑ +Y
                      </button>
                    </div>
                    <div className="movement-row">
                      <button 
                        onClick={() => moveInPlane(-movementAmount, 0)}
                        className="movement-btn left"
                      >
                        ← -X
                      </button>
                      <button 
                        onClick={() => moveInPlane(movementAmount, 0)}
                        className="movement-btn right"
                      >
                        +X →
                      </button>
                    </div>
                    <div className="movement-row">
                      <button 
                        onClick={() => moveInPlane(0, -movementAmount)}
                        className="movement-btn down"
                      >
                        ↓ -Y
                      </button>
                    </div>
                  </div>
                  
                  <div className="diagonal-controls">
                    <button 
                      onClick={() => moveInPlane(-movementAmount, movementAmount)}
                      className="movement-btn diagonal"
                    >
                      ↖ -X +Y
                    </button>
                    <button 
                      onClick={() => moveInPlane(movementAmount, movementAmount)}
                      className="movement-btn diagonal"
                    >
                      ↗ +X +Y
                    </button>
                    <button 
                      onClick={() => moveInPlane(-movementAmount, -movementAmount)}
                      className="movement-btn diagonal"
                    >
                      ↙ -X -Y
                    </button>
                    <button 
                      onClick={() => moveInPlane(movementAmount, -movementAmount)}
                      className="movement-btn diagonal"
                    >
                      ↘ +X -Y
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="calibration-editor">
              <div className="editor-header">
                <h4>Calibrating: {currentCalibration?.name}</h4>
                <div className="editor-actions">
                  <button onClick={calculatePlane} className="calculate-btn">
                    Calculate Plane
                  </button>
                  <button onClick={saveCalibration} className="save-btn">
                    Save Calibration
                  </button>
                  <button onClick={cancelCalibration} className="cancel-btn">
                    Cancel
                  </button>
                </div>
              </div>

              <div className="calibration-points">
                <div className="points-header">
                  <h5>Calibration Points</h5>
                  <button onClick={addCalibrationPoint} className="add-point-btn">
                    + Add Point
                  </button>
                </div>

                <div className="points-list">
                  {currentCalibration?.points.map(point => (
                    <div key={point.id} className="point-item">
                      <div className="point-info">
                        <span className="point-name">{point.name}</span>
                        <div className="point-status">
                          <span className={`status-indicator ${point.robotPosition ? 'captured' : 'pending'}`}>
                            Robot: {point.robotPosition ? '✓' : '○'}
                          </span>
                          <span className={`status-indicator ${point.screenPosition ? 'captured' : 'pending'}`}>
                            Screen: {point.screenPosition ? '✓' : '○'}
                          </span>
                        </div>
                      </div>
                      
                      <div className="point-actions">
                        <button 
                          onClick={() => captureRobotPosition(point.id)}
                          className="capture-btn robot"
                        >
                          Capture Robot
                        </button>
                        <button 
                          onClick={() => captureScreenPosition(point.id)}
                          className="capture-btn screen"
                        >
                          Set Screen Coords
                        </button>
                        {currentCalibration.points.length > 3 && (
                          <button 
                            onClick={() => removeCalibrationPoint(point.id)}
                            className="remove-btn"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {currentCalibration?.plane && (
                <div className="plane-info">
                  <h5>Calculated Plane</h5>
                  <div className="plane-equation">
                    Normal: ({currentCalibration.plane.normal.map(n => n.toFixed(3)).join(', ')})
                  </div>
                  <div className="plane-equation">
                    Equation: {currentCalibration.plane.equation.map((c, i) => 
                      `${c >= 0 && i > 0 ? '+' : ''}${c.toFixed(3)}${['x', 'y', 'z', ''][i] || ''}`
                    ).join('')} = 0
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}