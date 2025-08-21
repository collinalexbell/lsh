"""Input validation utilities"""
from typing import List, Tuple, Optional

def clamp_angles(angles: List[float], limits: List[Tuple[float, float]]) -> List[float]:
    """Clamp angles to their respective joint limits"""
    clamped = []
    for i, angle in enumerate(angles):
        if i < len(limits):
            min_a, max_a = limits[i]
            clamped.append(max(min(angle, max_a), min_a))
        else:
            clamped.append(angle)
    return clamped

def validate_joint_id(joint_id: int) -> bool:
    """Validate joint ID is in valid range (0-5)"""
    return isinstance(joint_id, int) and 0 <= joint_id <= 5

def validate_angle(angle: float, joint_id: int, limits: List[Tuple[float, float]]) -> bool:
    """Validate angle is within joint limits"""
    if not isinstance(angle, (int, float)):
        return False
    
    if joint_id < 0 or joint_id >= len(limits):
        return False
    
    min_angle, max_angle = limits[joint_id]
    return min_angle <= angle <= max_angle

def validate_angles_array(angles: List[float]) -> bool:
    """Validate angles array has correct length and types"""
    if not isinstance(angles, list):
        return False
    
    if len(angles) != 6:
        return False
    
    return all(isinstance(angle, (int, float)) for angle in angles)

def validate_speed(speed: int) -> bool:
    """Validate speed is in valid range"""
    return isinstance(speed, int) and 1 <= speed <= 100

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove path separators and other potentially dangerous characters
    safe_chars = '-_.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(c for c in filename if c in safe_chars)

def validate_position_name(name: str) -> bool:
    """Validate position name"""
    if not isinstance(name, str):
        return False
    
    name = name.strip()
    if not name or len(name) > 50:
        return False
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    return not any(char in name for char in invalid_chars)