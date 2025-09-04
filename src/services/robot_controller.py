"""Robot hardware controller - abstraction layer for MyCobot320"""
import time
import threading
from typing import List, Optional
from pymycobot import MyCobot320

from ..models.robot_state import robot_state
from ..utils.config import ROBOT_PORT, ROBOT_BAUDRATE, HOME_POSITION, EXTEND_POSITION
from ..utils.validation import clamp_angles, validate_angles_array
# Removed kinematics import - using MyCobot library directly

class RobotController:
    """Hardware abstraction for MyCobot320"""
    
    def __init__(self):
        self._mc: Optional[MyCobot320] = None
        self._connection_lock = threading.Lock()
        self._init_robot()
    
    def _init_robot(self):
        """Initialize robot connection"""
        try:
            self._mc = MyCobot320(ROBOT_PORT, ROBOT_BAUDRATE)
            print(f"Robot initialized on {ROBOT_PORT} at {ROBOT_BAUDRATE} baud")
        except Exception as e:
            print(f"Failed to initialize robot: {e}")
            self._mc = None
    
    def is_connected(self) -> bool:
        """Check if robot is connected"""
        return self._mc is not None
    
    def ensure_powered(self) -> bool:
        """Ensure robot is powered on"""
        if not self.is_connected():
            return False
        
        try:
            if not robot_state.robot_powered:
                self._mc.power_on()
                time.sleep(0.5)  # Give time for power up
                robot_state.set_power_state(True)
            return True
        except Exception as e:
            print(f"Failed to power on robot: {e}")
            return False
    
    def power_off(self) -> bool:
        """Turn off robot power"""
        if not self.is_connected():
            return False
        
        try:
            self._mc.power_off()
            robot_state.set_power_state(False)
            robot_state.set_manual_control(False)
            return True
        except Exception as e:
            print(f"Failed to power off robot: {e}")
            return False
    
    def get_angles(self) -> Optional[List[float]]:
        """Get current joint angles from robot"""
        if not self.is_connected():
            return None
        
        try:
            with self._connection_lock:
                angles = self._mc.get_angles()
                # Check if we got a valid list of angles
                if angles is None or not isinstance(angles, list) or len(angles) != 6:
                    print(f"Invalid angles received: {angles}")
                    return None
                return angles
        except Exception as e:
            print(f"Failed to get angles: {e}")
            return None
    
    def send_angles(self, angles: List[float], speed: int = 50) -> bool:
        """Send angles to robot"""
        if not self.is_connected():
            return False
        
        if not validate_angles_array(angles):
            return False
        
        try:
            # Clamp angles to limits
            from ..utils.config import ANGLE_LIMITS
            safe_angles = clamp_angles(angles, ANGLE_LIMITS)
            
            # Debug flag to disable robot movement for safety testing
            import os
            DEBUG_DISABLE_MOVEMENT = os.getenv('DEBUG_DISABLE_MOVEMENT', 'False').lower() == 'true'
            
            if DEBUG_DISABLE_MOVEMENT:
                print(f"DEBUG: WOULD SEND ANGLES TO ROBOT: {safe_angles} at speed {speed}")
            else:
                with self._connection_lock:
                    self._mc.send_angles(safe_angles, speed)
            
            robot_state.update_ideal_angles(safe_angles)
            return True
        except Exception as e:
            print(f"Failed to send angles: {e}")
            return False
    
    def move_to_home(self) -> bool:
        """Move robot to home position"""
        if not self.ensure_powered():
            return False
        
        # Get current position first to "wake up" the robot
        current_angles = self.get_angles()
        if current_angles:
            time.sleep(0.2)
        
        # Read current ideal state and move to home
        if robot_state.state_initialized:
            current_ideal = robot_state.get_ideal_angles()
            print(f"DEBUG: Home move from ideal state: {current_ideal} to {HOME_POSITION}")
        
        success = self.send_angles(HOME_POSITION, 100)
        if success:
            time.sleep(6)  # Allow movement to complete
            robot_state.update_ideal_angles(HOME_POSITION)
            robot_state.set_manual_control(False)
            print(f"DEBUG: Home move completed - unified state updated")
        
        return success
    
    def move_to_extend(self) -> bool:
        """Move robot to extend position"""
        if not self.ensure_powered():
            return False
        
        # Read current ideal state and move to extend  
        if robot_state.state_initialized:
            current_ideal = robot_state.get_ideal_angles()
            print(f"DEBUG: Extend move from ideal state: {current_ideal} to {EXTEND_POSITION}")
        
        success = self.send_angles(EXTEND_POSITION, 100)
        if success:
            time.sleep(4)  # Allow movement to complete
            robot_state.update_ideal_angles(EXTEND_POSITION)
            robot_state.set_manual_control(False)
            print(f"DEBUG: Extend move completed - unified state updated")
        
        return success
    
    def move_joint(self, joint_id: int, angle: float, speed: int = 50) -> bool:
        """Move a single joint to specified angle"""
        if not self.ensure_powered():
            return False
        
        if not (0 <= joint_id <= 5):
            return False
        
        # Initialize state from robot if not done yet
        if not robot_state.state_initialized:
            current_angles = self.get_angles()
            if current_angles:
                robot_state.update_ideal_angles(current_angles)
        
        robot_state.set_manual_control(True)
        robot_state.update_joint_angle(joint_id, angle)
        
        # Send updated angles to robot
        target_angles = robot_state.get_ideal_angles()
        return self.send_angles(target_angles, speed)
    
    def get_current_status(self) -> dict:
        """Get current robot status"""
        if not self.is_connected():
            return robot_state.get_status_dict(False)
        
        # During manual control, use internal state to avoid feedback loops
        if robot_state.manual_control_active and robot_state.state_initialized:
            angles = robot_state.get_ideal_angles()
        else:
            # Only read from robot when not in manual control
            angles = self.get_angles()
            if angles is None:
                return robot_state.get_status_dict(False)
        
        return robot_state.get_status_dict(True, angles)
    
    def get_end_effector_position(self) -> Optional[dict]:
        """Get current end effector position and orientation"""
        if not self.is_connected():
            return None
        
        try:
            angles = self.get_angles()
            if angles is None:
                return None
            
            # Use MyCobot's built-in get_coords instead of custom kinematics
            coords = self._mc.get_coords()  # Returns [x, y, z, rx, ry, rz]
            if coords is None or len(coords) != 6:
                return None
            position = coords[:3]  # [x, y, z] 
            orientation = coords[3:]  # [rx, ry, rz]
            
            return {
                'position': position,  # [x, y, z] in mm
                'orientation': orientation,  # [rx, ry, rz] in degrees
                'joint_angles': angles
            }
        except Exception as e:
            print(f"Failed to get end effector position: {e}")
            return None
    
    def move_end_effector_cartesian(self, target_pos: List[float], target_orient: List[float]) -> bool:
        """Move end effector to target cartesian position and orientation using MyCobot's built-in IK"""
        if not self.ensure_powered():
            return False
        
        try:
            # Get current angles for IK initial guess
            current_angles = self.get_angles()
            if current_angles is None:
                return False
            
            # Combine position and orientation into target coordinates [x, y, z, rx, ry, rz]
            target_coords = target_pos + target_orient
            
            # Use MyCobot's built-in inverse kinematics
            target_angles_raw = self._mc.solve_inv_kinematics(target_coords, current_angles)
            if target_angles_raw is None or len(target_angles_raw) != 6:
                print("No IK solution found")
                return False
            
            # Convert from centidegrees to degrees
            target_angles = [angle / 100.0 for angle in target_angles_raw]
            
            # Send angles to robot
            return self.send_angles(target_angles, 50)
            
        except Exception as e:
            print(f"Failed to move end effector: {e}")
            return False
    
    def translate_end_effector(self, dx: float, dy: float, dz: float) -> bool:
        """Translate end effector by specified amounts in mm"""
        if not self.ensure_powered():
            return False
        
        try:
            # Get current angles
            current_angles = self.get_angles()
            if current_angles is None:
                return False
            
            # Get current position
            current_coords = self._mc.get_coords()
            if current_coords is None or len(current_coords) != 6:
                print("Could not get current coordinates")
                return False
                
            # Calculate target position
            target_pos = [current_coords[0] + dx, current_coords[1] + dy, current_coords[2] + dz]
            target_coords = target_pos + current_coords[3:6]  # Keep same orientation
            
            # Use MyCobot's built-in inverse kinematics  
            target_angles_raw = self._mc.solve_inv_kinematics(target_coords, current_angles)
            if target_angles_raw is None or len(target_angles_raw) != 6:
                print("Translation not possible - no IK solution")
                return False
                
            # Convert from centidegrees to degrees
            target_angles = [angle / 100.0 for angle in target_angles_raw]
            
            # Update state for manual control
            robot_state.set_manual_control(True)
            for i, angle in enumerate(target_angles):
                robot_state.update_joint_angle(i, angle)
            
            # Send angles to robot
            return self.send_angles(target_angles, 30)  # Slower speed for precise movements
            
        except Exception as e:
            print(f"Failed to translate end effector: {e}")
            return False

    def run_demo(self) -> bool:
        """Run demo sequence"""
        if not self.ensure_powered():
            return False
        
        try:
            # Extend
            if not self.move_to_extend():
                return False
            
            # Home  
            if not self.move_to_home():
                return False
            
            # Power off after demo
            self.power_off()
            return True
        except Exception as e:
            print(f"Demo failed: {e}")
            return False

# Global controller instance
robot_controller = RobotController()