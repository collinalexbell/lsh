import { useState, useEffect } from 'react';
import './EditProcedure.css';

interface ProcedureStep {
  type: 'position' | 'delay';
  data: string | number;
}

interface Procedure {
  steps: ProcedureStep[];
  description: string;
  created: string;
  updated?: string;
  step_count: number;
}

interface EditProcedureProps {
  procedureName: string;
  procedure: Procedure;
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
}

export function EditProcedure({ procedureName, procedure, isOpen, onClose, onSave }: EditProcedureProps) {
  const [steps, setSteps] = useState<ProcedureStep[]>([]);
  const [description, setDescription] = useState('');
  const [availablePositions, setAvailablePositions] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (isOpen && procedure) {
      setSteps([...procedure.steps]);
      setDescription(procedure.description || '');
      loadAvailablePositions();
    }
  }, [isOpen, procedure]);

  const loadAvailablePositions = async () => {
    try {
      const response = await fetch('/api/positions');
      const data = await response.json();
      if (data.success) {
        setAvailablePositions(Object.keys(data.positions));
      }
    } catch (error) {
      console.error('Failed to load positions:', error);
    }
  };

  const addPositionStep = (positionName: string) => {
    setSteps([...steps, { type: 'position', data: positionName }]);
  };

  const addDelayStep = () => {
    const delay = parseFloat(prompt('Enter delay in seconds:') || '1');
    if (delay > 0) {
      setSteps([...steps, { type: 'delay', data: delay }]);
    }
  };

  const updateStep = (index: number, field: 'type' | 'data', value: any) => {
    const newSteps = [...steps];
    if (field === 'type') {
      newSteps[index] = {
        type: value,
        data: value === 'position' ? (availablePositions[0] || '') : 1
      };
    } else {
      newSteps[index].data = value;
    }
    setSteps(newSteps);
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index));
  };

  const moveStep = (index: number, direction: 'up' | 'down') => {
    if ((direction === 'up' && index === 0) || (direction === 'down' && index === steps.length - 1)) {
      return;
    }
    
    const newSteps = [...steps];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    [newSteps[index], newSteps[targetIndex]] = [newSteps[targetIndex], newSteps[index]];
    setSteps(newSteps);
  };

  const saveProcedure = async () => {
    if (steps.length === 0) {
      setMessage('Procedure must have at least one step');
      return;
    }

    setIsSaving(true);
    setMessage('');

    try {
      const response = await fetch('/api/procedures/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: procedureName,
          steps,
          description
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage(`Procedure "${procedureName}" updated successfully!`);
        setTimeout(() => {
          onSave();
          onClose();
        }, 1500);
      } else {
        setMessage(`Failed to update procedure: ${data.message}`);
      }
    } catch (error) {
      setMessage(`Error: ${error}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content edit-procedure-modal">
        <div className="modal-header">
          <h3>Edit Procedure: {procedureName}</h3>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {message && (
            <div className={`message ${message.includes('success') ? 'success' : 'error'}`}>
              {message}
            </div>
          )}

          <div className="form-group">
            <label>Description:</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description for this procedure"
              rows={3}
            />
          </div>

          <div className="steps-section">
            <div className="steps-header">
              <h4>Procedure Steps</h4>
            </div>

            {steps.length === 0 ? (
              <div className="no-steps">
                No steps added yet. Use the buttons below to add position moves or delays.
              </div>
            ) : (
              <div className="steps-list">
                {steps.map((step, index) => (
                  <div key={index} className={`step-item step-${step.type}`}>
                    <div className="step-number">{index + 1}</div>
                    
                    <div className="step-controls">
                      <select
                        value={step.type}
                        onChange={(e) => updateStep(index, 'type', e.target.value)}
                      >
                        <option value="position">Move to Position</option>
                        <option value="delay">Delay</option>
                      </select>
                      
                      {step.type === 'position' ? (
                        <select
                          value={step.data as string}
                          onChange={(e) => updateStep(index, 'data', e.target.value)}
                        >
                          {availablePositions.map(pos => (
                            <option key={pos} value={pos}>{pos}</option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type="number"
                          value={step.data as number}
                          onChange={(e) => updateStep(index, 'data', parseFloat(e.target.value) || 1)}
                          min="0.1"
                          step="0.1"
                          placeholder="Seconds"
                        />
                      )}
                    </div>
                    
                    <div className="step-actions">
                      <button 
                        onClick={() => moveStep(index, 'up')}
                        disabled={index === 0}
                        title="Move up"
                      >
                        ↑
                      </button>
                      <button 
                        onClick={() => moveStep(index, 'down')}
                        disabled={index === steps.length - 1}
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
            )}

            <div className="add-steps-section">
              <h4>Add New Steps</h4>
              <div className="step-buttons">
                <div className="position-buttons">
                  <span className="button-group-label">Positions:</span>
                  {availablePositions.map(pos => (
                    <button
                      key={pos}
                      onClick={() => addPositionStep(pos)}
                      className="add-position-btn"
                      title={`Add position step: ${pos}`}
                    >
                      + {pos}
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
          </div>
        </div>

        <div className="modal-footer">
          <button className="cancel-btn" onClick={onClose}>Cancel</button>
          <button 
            className="save-btn" 
            onClick={saveProcedure}
            disabled={isSaving || steps.length === 0}
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}