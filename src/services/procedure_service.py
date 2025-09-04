"""Procedure management service - sequences of positions"""
import json
import os
import time
from typing import Dict, List, Any, Optional

from ..utils.config import PROCEDURES_FILE
from ..utils.validation import validate_position_name

class ProcedureService:
    """Manages saved robot procedures (sequences of positions)"""
    
    def __init__(self):
        self._saved_procedures: Dict[str, Any] = {}
        self.load_procedures()
    
    def load_procedures(self):
        """Load saved procedures from file"""
        try:
            if os.path.exists(PROCEDURES_FILE):
                with open(PROCEDURES_FILE, 'r') as f:
                    self._saved_procedures = json.load(f)
                    
            print(f"Loaded {len(self._saved_procedures)} saved procedures")
        except Exception as e:
            print(f"Error loading saved procedures: {e}")
            self._saved_procedures = {}
    
    def save_to_file(self):
        """Save procedures to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(PROCEDURES_FILE), exist_ok=True)
            
            with open(PROCEDURES_FILE, 'w') as f:
                json.dump(self._saved_procedures, f, indent=2)
                
        except Exception as e:
            print(f"Error saving procedures: {e}")
            raise
    
    def get_all_procedures(self) -> Dict[str, Any]:
        """Get all saved procedures"""
        return self._saved_procedures.copy()
    
    def save_procedure(self, name: str, steps: List[Dict[str, Any]], description: str = "") -> bool:
        """Save a new procedure
        
        Args:
            name: Name of the procedure
            steps: List of steps, each containing:
                - type: 'position' or 'delay'
                - data: position name (for position) or seconds (for delay)
            description: Optional description
        """
        if not validate_position_name(name):
            raise ValueError("Invalid procedure name")
        
        name = name.strip()
        
        if name in self._saved_procedures:
            raise ValueError(f'Procedure "{name}" already exists')
        
        # Validate steps
        if not isinstance(steps, list) or len(steps) == 0:
            raise ValueError("Steps must be a non-empty list")
        
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"Step {i+1} must be an object")
            
            step_type = step.get('type')
            if step_type not in ['position', 'delay']:
                raise ValueError(f"Step {i+1}: Invalid type '{step_type}'. Must be 'position' or 'delay'")
            
            if 'data' not in step:
                raise ValueError(f"Step {i+1}: Missing 'data' field")
            
            if step_type == 'position' and not isinstance(step['data'], str):
                raise ValueError(f"Step {i+1}: Position data must be a string")
            
            if step_type == 'delay':
                delay = step['data']
                if not isinstance(delay, (int, float)) or delay <= 0:
                    raise ValueError(f"Step {i+1}: Delay must be a positive number")
        
        # Save procedure
        self._saved_procedures[name] = {
            'steps': steps,
            'description': description.strip(),
            'created': time.strftime('%Y-%m-%d %H:%M:%S'),
            'step_count': len(steps)
        }
        
        self.save_to_file()
        return True
    
    def delete_procedure(self, name: str) -> bool:
        """Delete a saved procedure"""
        if name not in self._saved_procedures:
            raise ValueError(f'Procedure "{name}" not found')
        
        del self._saved_procedures[name]
        self.save_to_file()
        return True
    
    def get_procedure(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific procedure"""
        return self._saved_procedures.get(name)
    
    def procedure_exists(self, name: str) -> bool:
        """Check if procedure exists"""
        return name in self._saved_procedures
    
    def get_procedure_count(self) -> int:
        """Get number of saved procedures"""
        return len(self._saved_procedures)
    
    def update_procedure(self, name: str, steps: List[Dict[str, Any]], description: str = "") -> bool:
        """Update an existing procedure"""
        if name not in self._saved_procedures:
            raise ValueError(f'Procedure "{name}" not found')
        
        # Validate steps (same validation as save_procedure)
        if not isinstance(steps, list) or len(steps) == 0:
            raise ValueError("Steps must be a non-empty list")
        
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"Step {i+1} must be an object")
            
            step_type = step.get('type')
            if step_type not in ['position', 'delay']:
                raise ValueError(f"Step {i+1}: Invalid type '{step_type}'. Must be 'position' or 'delay'")
            
            if 'data' not in step:
                raise ValueError(f"Step {i+1}: Missing 'data' field")
            
            if step_type == 'position' and not isinstance(step['data'], str):
                raise ValueError(f"Step {i+1}: Position data must be a string")
            
            if step_type == 'delay':
                delay = step['data']
                if not isinstance(delay, (int, float)) or delay <= 0:
                    raise ValueError(f"Step {i+1}: Delay must be a positive number")
        
        # Update procedure (preserve original created date)
        original_created = self._saved_procedures[name].get('created', time.strftime('%Y-%m-%d %H:%M:%S'))
        self._saved_procedures[name] = {
            'steps': steps,
            'description': description.strip(),
            'created': original_created,
            'updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'step_count': len(steps)
        }
        
        self.save_to_file()
        return True

# Global service instance
procedure_service = ProcedureService()