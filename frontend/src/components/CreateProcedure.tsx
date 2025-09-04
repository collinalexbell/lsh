import { useState } from 'react';
import { useRobot } from '../contexts/RobotContext';
import './CreateProcedure.css';

interface ProcedureStep {
  type: 'position' | 'delay';
  data: string | number;
}

export function CreateProcedure() {
  const { state } = useRobot();
  const { savedPositions } = state;
  const [procedureName, setProcedureName] = useState('');
  const [description, setDescription] = useState('');
  const [steps, setSteps] = useState<ProcedureStep[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);

  const addPositionStep = (positionName: string) => {
    setSteps([...steps, { type: 'position', data: positionName }]);
  };

  const addDelayStep = () => {
    const delay = parseFloat(prompt('Enter delay in seconds:') || '1');
    if (delay > 0) {
      setSteps([...steps, { type: 'delay', data: delay }]);
    }
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index));
  };

  const moveStepUp = (index: number) => {
    if (index > 0) {
      const newSteps = [...steps];
      [newSteps[index - 1], newSteps[index]] = [newSteps[index], newSteps[index - 1]];
      setSteps(newSteps);
    }
  };

  const moveStepDown = (index: number) => {
    if (index < steps.length - 1) {
      const newSteps = [...steps];
      [newSteps[index], newSteps[index + 1]] = [newSteps[index + 1], newSteps[index]];
      setSteps(newSteps);
    }
  };

  const saveProcedure = async () => {
    if (!procedureName.trim()) {
      alert('Please enter a procedure name');
      return;
    }

    if (steps.length === 0) {
      alert('Please add at least one step');
      return;
    }

    try {
      const response = await fetch('/api/procedures/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: procedureName,
          description: description,
          steps: steps
        })
      });

      const data = await response.json();

      if (data.success) {
        alert(`Procedure "${procedureName}" saved successfully!`);
        // Reset form
        setProcedureName('');
        setDescription('');
        setSteps([]);
        setIsExpanded(false);
      } else {
        alert(`Failed to save procedure: ${data.message}`);
      }
    } catch (error) {
      console.error('Network error:', error);
      alert('Network error while saving procedure');
    }
  };

  const clearSteps = () => {
    if (confirm('Clear all steps?')) {
      setSteps([]);
    }
  };

  const formatStepDisplay = (step: ProcedureStep): string => {
    if (step.type === 'position') {
      return `Move to: ${step.data}`;
    } else if (step.type === 'delay') {
      return `Wait: ${step.data}s`;
    }
    return 'Unknown step';
  };

  const enabledPositions = Object.entries(savedPositions).filter(
    ([, data]) => data // Could add enabled check here if needed
  );

  return (
    <div className="create-procedure">
      <div className="create-procedure-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h3>Create Procedure</h3>
        <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
      </div>
      
      {isExpanded && (
        <div className="create-procedure-content">
          <div className="procedure-form">
            <div className="form-group">
              <label>Procedure Name:</label>
              <input
                type="text"
                value={procedureName}
                onChange={(e) => setProcedureName(e.target.value)}
                placeholder="Enter procedure name"
                className="procedure-input"
              />
            </div>

            <div className="form-group">
              <label>Description (optional):</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what this procedure does"
                className="procedure-textarea"
                rows={2}
              />
            </div>

            <div className="form-group">
              <label>Add Steps:</label>
              <div className="step-buttons">
                <div className="position-buttons">
                  <span className="button-group-label">Positions:</span>
                  {enabledPositions.map(([name]) => (
                    <button
                      key={name}
                      onClick={() => addPositionStep(name)}
                      className="add-position-btn"
                      title={`Add position step: ${name}`}
                    >
                      + {name}
                    </button>
                  ))}
                </div>
                <button
                  onClick={addDelayStep}
                  className="add-delay-btn"
                  title="Add delay step"
                >
                  + Add Delay
                </button>
              </div>
            </div>

            {steps.length > 0 && (
              <div className="form-group">
                <div className="steps-header">
                  <label>Procedure Steps ({steps.length}):</label>
                  <button onClick={clearSteps} className="clear-btn">
                    Clear All
                  </button>
                </div>
                <div className="steps-list">
                  {steps.map((step, index) => (
                    <div key={index} className="step-item">
                      <span className="step-number">{index + 1}.</span>
                      <span className={`step-content step-${step.type}`}>
                        {formatStepDisplay(step)}
                      </span>
                      <div className="step-controls">
                        <button
                          onClick={() => moveStepUp(index)}
                          disabled={index === 0}
                          className="move-btn"
                          title="Move up"
                        >
                          ↑
                        </button>
                        <button
                          onClick={() => moveStepDown(index)}
                          disabled={index === steps.length - 1}
                          className="move-btn"
                          title="Move down"
                        >
                          ↓
                        </button>
                        <button
                          onClick={() => removeStep(index)}
                          className="remove-btn"
                          title="Remove step"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="form-actions">
              <button
                onClick={saveProcedure}
                className="save-procedure-btn"
                disabled={!procedureName.trim() || steps.length === 0}
              >
                Save Procedure
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}