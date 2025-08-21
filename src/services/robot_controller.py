"""Robot hardware controller - abstraction layer for MyCobot320"""
import time
import threading
from typing import List, Optional
from pymycobot import MyCobot320

from ..models.robot_state import robot_state
from ..utils.config import ROBOT_PORT, ROBOT_BAUDRATE, HOME_POSITION, EXTEND_POSITION
from ..utils.validation import clamp_angles, validate_angles_array

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
            
            with self._connection_lock:
                self._mc.send_angles(safe_angles, speed)
            
            robot_state.update_target_angles(safe_angles)
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
        
        success = self.send_angles(HOME_POSITION, 100)
        if success:
            time.sleep(6)  # Allow movement to complete
            robot_state.update_target_angles(HOME_POSITION)
            robot_state.set_manual_control(False)
        
        return success
    
    def move_to_extend(self) -> bool:
        """Move robot to extend position"""
        if not self.ensure_powered():
            return False
        
        success = self.send_angles(EXTEND_POSITION, 100)
        if success:
            time.sleep(4)  # Allow movement to complete
            robot_state.update_target_angles(EXTEND_POSITION)
            robot_state.set_manual_control(False)
        
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
                robot_state.update_target_angles(current_angles)
        
        robot_state.set_manual_control(True)
        robot_state.update_joint_angle(joint_id, angle)
        
        # Send updated angles to robot
        target_angles = robot_state.get_target_angles()
        return self.send_angles(target_angles, speed)
    
    def get_current_status(self) -> dict:
        """Get current robot status"""
        if not self.is_connected():
            return robot_state.get_status_dict(False)
        
        # During manual control, use internal state to avoid feedback loops
        if robot_state.manual_control_active and robot_state.state_initialized:
            angles = robot_state.get_target_angles()
        else:
            # Only read from robot when not in manual control
            angles = self.get_angles()
            if angles is None:
                return robot_state.get_status_dict(False)
        
        return robot_state.get_status_dict(True, angles)
    
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