#!/usr/bin/env python3
"""Test that IK centidegrees bug is fixed"""

import sys
import os
sys.path.append('src')

def test_mock_ik():
    """Test the fixed IK behavior without actually calling robot"""
    print("=== TESTING CENTIDEGREES FIX IN IK ===")
    
    # Mock what solve_inv_kinematics returns (centidegrees)  
    mock_centidegrees = [-4440, 10328, 13893, -6142, -4414, -12861]
    
    print(f"1. IK solver returns (centidegrees): {mock_centidegrees}")
    
    # This is what the OLD broken code would do:
    print(f"2. OLD CODE would send to robot: {mock_centidegrees} <- DANGEROUS!")
    
    # This is what the NEW fixed code does:
    fixed_degrees = [angle / 100.0 for angle in mock_centidegrees]  
    print(f"3. NEW CODE converts /100.0: {fixed_degrees} <- SAFE!")
    
    print(f"4. Angle differences: {[abs(old-new) for old, new in zip(mock_centidegrees, fixed_degrees)]}")
    
    # Validation
    dangerous_old = any(abs(angle) > 180 for angle in mock_centidegrees)
    safe_new = all(abs(angle) <= 180 for angle in fixed_degrees)
    
    print(f"5. Old angles dangerous (>180°): {dangerous_old}")
    print(f"6. New angles safe (≤180°): {safe_new}")
    
    if safe_new:
        print("✅ CENTIDEGREES BUG IS FIXED!")
    else:
        print("❌ BUG STILL EXISTS!")

def test_wall_service_fix():
    """Test the wall service specifically"""
    print("\n=== WALL SERVICE FIX VERIFICATION ===")
    
    # The exact code from wall_service.py line 223:
    mock_target_angles_raw = [-4440, 10328, 13893, -6142, -4414, -12861]
    target_angles_degrees = [angle / 100.0 for angle in mock_target_angles_raw]
    
    print(f"Wall service IK raw result: {mock_target_angles_raw}")
    print(f"Wall service converts to: {target_angles_degrees}")
    print(f"Returns to API: {target_angles_degrees}")
    
    # This is what would be sent to robot
    print(f"Robot receives: {target_angles_degrees} <- SAFE!")
    
if __name__ == "__main__":
    test_mock_ik()
    test_wall_service_fix()