import React, { useState, useEffect } from 'react';
import './EndEffectorController.css';

interface EndEffectorPosition {
  position: [number, number, number];
  orientation: [number, number, number];
  joint_angles: number[];
}

const EndEffectorController: React.FC = () => {
  const [position, setPosition] = useState<EndEffectorPosition | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  // const [translationAmount, setTranslationAmount] = useState<number>(10); // Commented out with translation controls
  
  // Manual coordinate inputs
  const [manualX, setManualX] = useState<number>(0);
  const [manualY, setManualY] = useState<number>(0);
  const [manualZ, setManualZ] = useState<number>(0);
  const [manualRx, setManualRx] = useState<number>(0);
  const [manualRy, setManualRy] = useState<number>(0);
  const [manualRz, setManualRz] = useState<number>(0);

  const fetchCurrentPosition = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/end_effector/position');
      const data = await response.json();
      
      if (data.success && data.position && data.orientation) {
        const posData: EndEffectorPosition = {
          position: data.position,
          orientation: data.orientation,
          joint_angles: data.joint_angles
        };
        setPosition(posData);
        
        // Update manual inputs with current position
        setManualX(Math.round(data.position[0] * 10) / 10);
        setManualY(Math.round(data.position[1] * 10) / 10);
        setManualZ(Math.round(data.position[2] * 10) / 10);
        setManualRx(Math.round(data.orientation[0] * 10) / 10);
        setManualRy(Math.round(data.orientation[1] * 10) / 10);
        setManualRz(Math.round(data.orientation[2] * 10) / 10);
        
        setMessage('Position updated successfully');
      } else {
        setMessage(`Failed to get position: ${data.message}`);
      }
    } catch (error) {
      setMessage(`Error: ${error}`);
    }
    setLoading(false);
  };

  // Commented out with translation controls
  // const translateEndEffector = async (dx: number, dy: number, dz: number) => {
  //   setLoading(true);
  //   try {
  //     const response = await fetch('/api/end_effector/translate', {
  //       method: 'POST',
  //       headers: {
  //         'Content-Type': 'application/json',
  //       },
  //       body: JSON.stringify({ dx, dy, dz }),
  //     });
  //     
  //     const data = await response.json();
  //     setMessage(data.message);
  //     
  //     if (data.success) {
  //       // Refresh position after successful translation
  //       setTimeout(fetchCurrentPosition, 1000);
  //     }
  //   } catch (error) {
  //     setMessage(`Error: ${error}`);
  //   }
  //   setLoading(false);
  // };

  const moveToManualPosition = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/end_effector/move', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          position: [manualX, manualY, manualZ],
          orientation: [manualRx, manualRy, manualRz]
        }),
      });
      
      const data = await response.json();
      setMessage(data.message);
      
      if (data.success) {
        setTimeout(fetchCurrentPosition, 1000);
      }
    } catch (error) {
      setMessage(`Error: ${error}`);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchCurrentPosition();
  }, []);

  return (
    <div className="end-effector-controller">
      <div className="controller-header">
        <h3>End Effector Controls</h3>
        <button 
          onClick={fetchCurrentPosition} 
          disabled={loading}
          className="refresh-btn"
        >
          {loading ? '🔄' : '↻'} Refresh Position
        </button>
      </div>

      {message && (
        <div className={`message ${message.includes('failed') || message.includes('Failed') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      {position && (
        <div className="position-display">
          <h4>Current Position</h4>
          <div className="position-grid">
            <div className="position-section">
              <h5>Position (mm)</h5>
              <div className="coord-display">
                <span>X: {position.position[0].toFixed(1)}</span>
                <span>Y: {position.position[1].toFixed(1)}</span>
                <span>Z: {position.position[2].toFixed(1)}</span>
              </div>
            </div>
            <div className="position-section">
              <h5>Orientation (°)</h5>
              <div className="coord-display">
                <span>Rx: {position.orientation[0].toFixed(1)}</span>
                <span>Ry: {position.orientation[1].toFixed(1)}</span>
                <span>Rz: {position.orientation[2].toFixed(1)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Translation controls commented out - using procedures instead
      <div className="translation-controls">
        <h4>Translation Controls</h4>
        
        <div className="amount-selector">
          <label>Translation Amount (mm):</label>
          <select 
            value={translationAmount} 
            onChange={(e) => setTranslationAmount(Number(e.target.value))}
          >
            <option value={5}>±5mm</option>
            <option value={10}>±10mm</option>
            <option value={25}>±25mm</option>
          </select>
        </div>

        <div className="axis-controls">
          <div className="axis-group">
            <h5>X-Axis</h5>
            <button 
              onClick={() => translateEndEffector(-translationAmount, 0, 0)} 
              disabled={loading}
              className="translate-btn negative"
            >
              -X ({translationAmount}mm)
            </button>
            <button 
              onClick={() => translateEndEffector(translationAmount, 0, 0)} 
              disabled={loading}
              className="translate-btn positive"
            >
              +X ({translationAmount}mm)
            </button>
          </div>

          <div className="axis-group">
            <h5>Y-Axis</h5>
            <button 
              onClick={() => translateEndEffector(0, -translationAmount, 0)} 
              disabled={loading}
              className="translate-btn negative"
            >
              -Y ({translationAmount}mm)
            </button>
            <button 
              onClick={() => translateEndEffector(0, translationAmount, 0)} 
              disabled={loading}
              className="translate-btn positive"
            >
              +Y ({translationAmount}mm)
            </button>
          </div>

          <div className="axis-group z-axis">
            <h5>Z-Axis (For Dipping)</h5>
            <button 
              onClick={() => translateEndEffector(0, 0, -translationAmount)} 
              disabled={loading}
              className="translate-btn negative dip-btn"
            >
              ⬇ Dip Down ({translationAmount}mm)
            </button>
            <button 
              onClick={() => translateEndEffector(0, 0, translationAmount)} 
              disabled={loading}
              className="translate-btn positive lift-btn"
            >
              ⬆ Lift Up ({translationAmount}mm)
            </button>
          </div>
        </div>
      </div>
      */}

      <div className="manual-controls">
        <h4>Manual Position Control</h4>
        <div className="manual-grid">
          <div className="manual-section">
            <h5>Position (mm)</h5>
            <div className="input-group">
              <label>X:</label>
              <input 
                type="number" 
                value={manualX} 
                onChange={(e) => setManualX(Number(e.target.value))}
                step="0.1"
              />
            </div>
            <div className="input-group">
              <label>Y:</label>
              <input 
                type="number" 
                value={manualY} 
                onChange={(e) => setManualY(Number(e.target.value))}
                step="0.1"
              />
            </div>
            <div className="input-group">
              <label>Z:</label>
              <input 
                type="number" 
                value={manualZ} 
                onChange={(e) => setManualZ(Number(e.target.value))}
                step="0.1"
              />
            </div>
          </div>

          <div className="manual-section">
            <h5>Orientation (°)</h5>
            <div className="input-group">
              <label>Rx:</label>
              <input 
                type="number" 
                value={manualRx} 
                onChange={(e) => setManualRx(Number(e.target.value))}
                step="0.1"
              />
            </div>
            <div className="input-group">
              <label>Ry:</label>
              <input 
                type="number" 
                value={manualRy} 
                onChange={(e) => setManualRy(Number(e.target.value))}
                step="0.1"
              />
            </div>
            <div className="input-group">
              <label>Rz:</label>
              <input 
                type="number" 
                value={manualRz} 
                onChange={(e) => setManualRz(Number(e.target.value))}
                step="0.1"
              />
            </div>
          </div>
        </div>
        
        <button 
          onClick={moveToManualPosition} 
          disabled={loading}
          className="move-btn"
        >
          Move to Position
        </button>
      </div>
    </div>
  );
};

export default EndEffectorController;