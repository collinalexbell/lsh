import { useState, useEffect } from 'react';
import './ProcedureManager.css';
import { EditProcedure } from './EditProcedure';

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

export function ProcedureManager() {
  const [procedures, setProcedures] = useState<Record<string, Procedure>>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [editingProcedure, setEditingProcedure] = useState<string | null>(null);

  // Load procedures on mount
  useEffect(() => {
    loadProcedures();
  }, []);

  const loadProcedures = async () => {
    try {
      const response = await fetch('/api/procedures');
      const data = await response.json();
      
      if (data.success) {
        setProcedures(data.procedures);
      }
    } catch (error) {
      console.error('Failed to load procedures:', error);
    }
  };

  const executeProcedure = async (name: string) => {
    try {
      setIsExecuting(true);
      const response = await fetch(`/api/procedures/execute/${name}`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        console.log(`Executing procedure: ${name}`);
      } else {
        console.error('Execution failed:', data.message);
        alert(`Failed to execute procedure: ${data.message}`);
      }
    } catch (error) {
      console.error('Network error:', error);
      alert('Network error while executing procedure');
    } finally {
      // Reset executing state after a delay to allow for procedure completion
      setTimeout(() => setIsExecuting(false), 2000);
    }
  };

  const deleteProcedure = async (name: string) => {
    if (!confirm(`Are you sure you want to delete procedure "${name}"?`)) {
      return;
    }

    try {
      const response = await fetch('/api/procedures/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name })
      });
      const data = await response.json();
      
      if (data.success) {
        console.log(`Deleted procedure: ${name}`);
        loadProcedures(); // Reload procedures
      } else {
        console.error('Delete failed:', data.message);
        alert(`Failed to delete procedure: ${data.message}`);
      }
    } catch (error) {
      console.error('Network error:', error);
      alert('Network error while deleting procedure');
    }
  };

  const stopExecution = async () => {
    try {
      const response = await fetch('/api/procedures/stop', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        setIsExecuting(false);
        console.log('Procedure execution stopped');
      }
    } catch (error) {
      console.error('Network error:', error);
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

  const allProcedures = Object.entries(procedures);

  if (allProcedures.length === 0) {
    return (
      <div className="procedure-manager">
        <h3>Saved Procedures</h3>
        <div className="no-procedures">
          No procedures saved yet. Use the Create Procedure section to build sequences.
        </div>
      </div>
    );
  }

  return (
    <div className="procedure-manager">
      <div className="procedure-header">
        <h3>Saved Procedures</h3>
        {isExecuting && (
          <button className="stop-btn" onClick={stopExecution}>
            ⏹️ Stop Execution
          </button>
        )}
      </div>
      
      <div className="procedure-list">
        {allProcedures.map(([name, procedure]) => (
          <div key={name} className="procedure-item">
            <div className="procedure-info">
              <div className="procedure-name">{name}</div>
              {procedure.description && (
                <div className="procedure-description">{procedure.description}</div>
              )}
              <div className="procedure-steps">
                <strong>Steps ({procedure.step_count}):</strong>
                <ol className="steps-list">
                  {procedure.steps.map((step, index) => (
                    <li key={index} className={`step-item step-${step.type}`}>
                      {formatStepDisplay(step)}
                    </li>
                  ))}
                </ol>
              </div>
              <div className="procedure-meta">
                Created: {new Date(procedure.created).toLocaleString()}
                {procedure.updated && (
                  <span> • Updated: {new Date(procedure.updated).toLocaleString()}</span>
                )}
              </div>
            </div>
            
            <div className="procedure-actions">
              <button
                className="execute-btn"
                onClick={() => executeProcedure(name)}
                disabled={isExecuting}
                title={`Execute procedure "${name}"`}
              >
                ▶️ Execute
              </button>
              <button
                className="edit-btn"
                onClick={() => setEditingProcedure(name)}
                title={`Edit procedure "${name}"`}
              >
                ✏️ Edit
              </button>
              <button
                className="delete-btn"
                onClick={() => deleteProcedure(name)}
                title={`Delete procedure "${name}"`}
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>

      {editingProcedure && procedures[editingProcedure] && (
        <EditProcedure
          procedureName={editingProcedure}
          procedure={procedures[editingProcedure]}
          isOpen={editingProcedure !== null}
          onClose={() => setEditingProcedure(null)}
          onSave={() => {
            loadProcedures();
            setEditingProcedure(null);
          }}
        />
      )}
    </div>
  );
}