"""Robot state management"""
from typing import List, Optional
from dataclasses import dataclass, field
import threading
import time

@dataclass
class RobotState:
    """Manages the current state of the robot"""
    # Joint angles (what we believe the robot should currently be at)
    ideal_angles: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    
    # Plane movement flag to know when to use ideal coordinates vs robot readings
    plane_mode_active: bool = False
    
    # Power and control state
    robot_powered: bool = False
    manual_control_active: bool = False
    state_initialized: bool = False
    
    # Recording state
    is_recording: bool = False
    is_playing: bool = False
    is_jiggling: bool = False
    recorded_moves: List[List[float]] = field(default_factory=list)
    
    # Camera state
    camera_active: bool = False
    is_recording_video: bool = False
    video_filename: Optional[str] = None
    
    # Thread safety
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        """Initialize state after creation"""
        self._lock = threading.Lock()

    def get_status_dict(self, connected: bool, angles: Optional[List[float]] = None) -> dict:
        """Get current status as dictionary for API responses"""
        with self._lock:
            return {
                'connected': connected,
                'angles': angles or self.ideal_angles.copy(),
                'is_recording': self.is_recording,
                'is_playing': self.is_playing,
                'is_jiggling': self.is_jiggling,
                'is_recording_video': self.is_recording_video,
                'recorded_moves_count': len(self.recorded_moves),
                'joint_limits': self._get_joint_limits()
            }
    
    def _get_joint_limits(self):
        """Get joint limits from config"""
        from ..utils.config import ANGLE_LIMITS
        return ANGLE_LIMITS
    
    def update_ideal_angles(self, angles: List[float]):
        """Update ideal angles thread-safely"""
        with self._lock:
            self.ideal_angles = angles.copy()
            self.state_initialized = True
    
    def update_joint_angle(self, joint_id: int, angle: float):
        """Update a single joint angle"""
        with self._lock:
            if 0 <= joint_id < len(self.ideal_angles):
                self.ideal_angles[joint_id] = angle
                self.state_initialized = True
    
    def get_ideal_angles(self) -> List[float]:
        """Get current ideal angles thread-safely"""
        with self._lock:
            return self.ideal_angles.copy()
    
    def get_ideal_cartesian(self, robot_controller) -> Optional[List[float]]:
        """Get ideal Cartesian coordinates from ideal angles using forward kinematics"""
        with self._lock:
            if not self.state_initialized:
                return None
            try:
                # Use MyCobot's forward kinematics to calculate cartesian from ideal angles
                # NEVER query the robot - only use the ideal state
                coords = robot_controller._mc.angles_to_coords(self.ideal_angles)
                if coords and len(coords) >= 6:
                    return coords
                else:
                    print(f"DEBUG: Forward kinematics failed for ideal angles: {self.ideal_angles}")
                    return None
            except Exception as e:
                print(f"DEBUG: Error calculating ideal cartesian from angles {self.ideal_angles}: {e}")
                return None
    
    def set_plane_mode(self, active: bool):
        """Set plane movement mode"""
        with self._lock:
            self.plane_mode_active = active
    
    
    def set_power_state(self, powered: bool):
        """Set robot power state"""
        with self._lock:
            self.robot_powered = powered
    
    def set_manual_control(self, active: bool):
        """Set manual control state"""
        with self._lock:
            self.manual_control_active = active
    
    def is_busy(self) -> bool:
        """Check if robot is currently busy with operations"""
        with self._lock:
            return self.is_recording or self.is_playing or self.is_jiggling
    
    def set_recording_state(self, recording: bool):
        """Set recording state"""
        with self._lock:
            self.is_recording = recording
            if recording:
                self.recorded_moves.clear()
    
    def add_recorded_move(self, angles: List[float]):
        """Add a move to recorded choreography"""
        with self._lock:
            self.recorded_moves.append(angles.copy())
    
    def get_recorded_moves(self) -> List[List[float]]:
        """Get recorded moves safely"""
        with self._lock:
            return [move.copy() for move in self.recorded_moves]
    
    def clear_recorded_moves(self):
        """Clear all recorded moves"""
        with self._lock:
            self.recorded_moves.clear()
    
    def set_playing_state(self, playing: bool):
        """Set choreography playing state"""
        with self._lock:
            self.is_playing = playing
    
    def set_jiggling_state(self, jiggling: bool):
        """Set jiggling state"""
        with self._lock:
            self.is_jiggling = jiggling
    
    def set_video_recording_state(self, recording: bool, filename: Optional[str] = None):
        """Set video recording state"""
        with self._lock:
            self.is_recording_video = recording
            self.video_filename = filename
    
    def reset_to_safe_state(self):
        """Reset to safe state (stop all operations)"""
        with self._lock:
            self.is_recording = False
            self.is_playing = False
            self.is_jiggling = False
            self.manual_control_active = False

# Global state instance
robot_state = RobotState()