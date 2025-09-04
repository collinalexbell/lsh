#!/usr/bin/env python3
"""Test wall calibration with debug output"""

import sys
sys.path.append('src')

from services.wall_service import WallService
from services.robot_controller import RobotController
from models.robot_state import robot_state

def test_wall_movement():
    """Test wall movement calculations with debug output"""
    
    # Initialize services
    wall_service = WallService()
    robot_controller = RobotController('/dev/ttyAMA0', 115200)
    
    if not robot_controller.is_connected():
        print("Robot not connected")
        return
    
    # Get current angles
    current_angles = robot_controller.get_angles()
    if current_angles is None:
        print("Could not get current angles")
        return
        
    print(f"Current robot angles: {current_angles}")
    
    # Create a simple test calibration
    test_calibration = {
        'name': 'test_debug',
        'type': 'plane',
        'point': [100.0, 200.0, -50.0],  # Position in front of robot
        'local_x_axis': [1.0, 0.0, 0.0],  # X direction
        'local_y_axis': [0.0, 1.0, 0.0],  # Y direction  
        'orientation': [-179.0, -1.0, 50.0]  # Similar to current orientation
    }
    
    wall_service.calibrations['test_debug'] = test_calibration
    
    print("\nTesting 5mm movement in X direction:")
    result = wall_service.move_in_plane('test_debug', 5.0, 0.0, current_angles, robot_controller)
    
    if result:
        print(f"SUCCESS: New angles calculated: {result}")
        print(f"Angle differences: {[result[i] - current_angles[i] for i in range(6)]}")
    else:
        print("FAILED: Could not calculate movement")

if __name__ == "__main__":
    test_wall_movement()