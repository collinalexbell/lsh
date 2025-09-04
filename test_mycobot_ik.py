#!/usr/bin/env python3
"""Test MyCobot library's built-in inverse kinematics"""

import sys
sys.path.append('src')

from pymycobot import MyCobot320
from utils.config import ROBOT_PORT, ROBOT_BAUDRATE
from utils.kinematics import MyCobot320Kinematics

def test_library_ik():
    """Test MyCobot's built-in IK vs custom implementation"""
    
    print("Testing MyCobot Library vs Custom IK")
    print("=" * 50)
    
    # Initialize both
    try:
        mc = MyCobot320(ROBOT_PORT, ROBOT_BAUDRATE)
        custom_ik = MyCobot320Kinematics()
        print("✓ Both libraries initialized")
    except Exception as e:
        print(f"Failed to initialize MyCobot: {e}")
        return
    
    # Test cases - realistic poses near center of workspace
    test_cases = [
        [0, 0, 0, 0, 0, 0],                    # Home position
        [10, -20, 30, -10, 45, 0],            # Small movements
        [-15, 15, -25, 20, -30, 15],          # Another small pose
    ]
    
    for i, test_angles in enumerate(test_cases):
        print(f"\nTest Case {i+1}: {test_angles}")
        print("-" * 40)
        
        # Step 1: Get position using custom forward kinematics
        try:
            pos, orient = custom_ik.forward_kinematics(test_angles)
            print(f"Forward Kinematics:")
            print(f"  Position: [{pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}] mm")
            print(f"  Orientation: [{orient[0]:.1f}, {orient[1]:.1f}, {orient[2]:.1f}] deg")
        except Exception as e:
            print(f"  Custom FK failed: {e}")
            continue
            
        # Step 2: Test MyCobot library's inverse kinematics
        try:
            target_coords = pos + orient  # [x, y, z, rx, ry, rz]
            print(f"Target coords: {target_coords}")
            
            library_ik_angles = mc.solve_inv_kinematics(target_coords, test_angles)
            if library_ik_angles is None:
                print(f"  Library IK: No solution found")
            else:
                print(f"  Library IK: {[round(a, 2) for a in library_ik_angles]}")
        except Exception as e:
            print(f"  Library IK failed: {e}")
            library_ik_angles = None
            
        # Step 3: Test custom inverse kinematics  
        try:
            custom_ik_angles = custom_ik.inverse_kinematics(pos, orient, test_angles)
            if custom_ik_angles is None:
                print(f"  Custom IK: No solution found")
            else:
                print(f"  Custom IK: {[round(a, 2) for a in custom_ik_angles]}")
        except Exception as e:
            print(f"  Custom IK failed: {e}")
            custom_ik_angles = None
            
        # Step 4: Compare results
        if library_ik_angles and custom_ik_angles:
            diff = [abs(library_ik_angles[j] - custom_ik_angles[j]) for j in range(6)]
            total_diff = sum(diff)
            print(f"  Angle differences: {[round(d, 2) for d in diff]}")
            print(f"  Total difference: {total_diff:.2f} degrees")
            
            # Verify library solution
            try:
                verify_pos, verify_orient = custom_ik.forward_kinematics(library_ik_angles)
                pos_error = sum(abs(verify_pos[j] - pos[j]) for j in range(3))
                orient_error = sum(abs(verify_orient[j] - orient[j]) for j in range(3))
                print(f"  Library IK error: {pos_error:.2f}mm position, {orient_error:.2f}° orientation")
            except:
                print(f"  Library IK verification failed")

if __name__ == "__main__":
    test_library_ik()