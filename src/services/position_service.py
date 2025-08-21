"""Position management service"""
import json
import os
import time
from typing import Dict, Any, Optional

from ..utils.config import POSITIONS_FILE, CONFIG_FILE
from ..utils.validation import validate_position_name

class PositionService:
    """Manages saved robot positions"""
    
    def __init__(self):
        self._saved_positions: Dict[str, Any] = {}
        self._position_config: Dict[str, Any] = {}
        self.load_positions()
    
    def load_positions(self):
        """Load saved positions from files"""
        try:
            if os.path.exists(POSITIONS_FILE):
                with open(POSITIONS_FILE, 'r') as f:
                    self._saved_positions = json.load(f)
            
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    self._position_config = json.load(f)
                    
            print(f"Loaded {len(self._saved_positions)} saved positions")
        except Exception as e:
            print(f"Error loading saved positions: {e}")
            self._saved_positions = {}
            self._position_config = {}
    
    def save_to_files(self):
        """Save positions to files"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(POSITIONS_FILE), exist_ok=True)
            
            with open(POSITIONS_FILE, 'w') as f:
                json.dump(self._saved_positions, f, indent=2)
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self._position_config, f, indent=2)
                
        except Exception as e:
            print(f"Error saving positions: {e}")
            raise
    
    def get_all_positions(self) -> Dict[str, Any]:
        """Get all saved positions"""
        return {
            'positions': self._saved_positions.copy(),
            'config': self._position_config.copy()
        }
    
    def save_position(self, name: str, angles: list) -> bool:
        """Save a new position"""
        if not validate_position_name(name):
            raise ValueError("Invalid position name")
        
        name = name.strip()
        
        if name in self._saved_positions:
            raise ValueError(f'Position "{name}" already exists')
        
        # Validate angles
        if not isinstance(angles, list) or len(angles) != 6:
            raise ValueError("Invalid angles array")
        
        if not all(isinstance(angle, (int, float)) for angle in angles):
            raise ValueError("All angles must be numbers")
        
        # Clamp angles to limits
        from ..utils.config import ANGLE_LIMITS
        from ..utils.validation import clamp_angles
        safe_angles = clamp_angles(angles, ANGLE_LIMITS)
        
        # Save position
        self._saved_positions[name] = {
            'angles': safe_angles,
            'created': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add to config as enabled by default
        self._position_config[name] = {'enabled': True}
        
        self.save_to_files()
        return True
    
    def delete_position(self, name: str) -> bool:
        """Delete a saved position"""
        if name not in self._saved_positions:
            raise ValueError(f'Position "{name}" not found')
        
        del self._saved_positions[name]
        
        if name in self._position_config:
            del self._position_config[name]
        
        self.save_to_files()
        return True
    
    def get_position(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific position"""
        return self._saved_positions.get(name)
    
    def update_position_config(self, name: str, enabled: bool) -> bool:
        """Update position configuration"""
        if name not in self._saved_positions:
            raise ValueError(f'Position "{name}" not found')
        
        self._position_config[name] = {'enabled': enabled}
        self.save_to_files()
        return True
    
    def get_enabled_positions(self) -> Dict[str, Any]:
        """Get positions that are enabled in command center"""
        enabled = {}
        for name, data in self._saved_positions.items():
            if self._position_config.get(name, {}).get('enabled', False):
                enabled[name] = data
        return enabled
    
    def position_exists(self, name: str) -> bool:
        """Check if position exists"""
        return name in self._saved_positions
    
    def get_position_count(self) -> int:
        """Get number of saved positions"""
        return len(self._saved_positions)

# Global service instance
position_service = PositionService()