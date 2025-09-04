#!/usr/bin/env python3
"""Test inverse kinematics calculations"""

import sys
sys.path.append('src')

from utils.kinematics import MyCobot320Kinematics

def test_ik_roundtrip():
    """Test IK by doing forward->inverse->forward kinematics"""
    
    ik = MyCobot320Kinematics()
    print("Testing MyCobot320 Inverse Kinematics")
    print("=" * 50)
    
    # Test angles (realistic robot poses)
    test_cases = [
        [0, 0, 0, 0, 0, 0],           # Home position
        [30, -45, 60, -15, 90, 0],    # Typical working pose
        [-20, 30, -40, 45, -60, 15],  # Another working pose
        [45, -30, 45, 0, -45, 30],    # Different configuration
    ]
    
    for i, test_angles in enumerate(test_cases):
        print(f"\nTest Case {i+1}: {test_angles}")
        print("-" * 30)
        
        # Step 1: Forward kinematics
        try:
            pos, orient = ik.forward_kinematics(test_angles)
            print(f"Forward Kinematics:")
            print(f"  Position: [{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}] mm")
            print(f"  Orientation: [{orient[0]:.2f}, {orient[1]:.2f}, {orient[2]:.2f}] deg")
        except Exception as e:
            print(f"  Forward kinematics failed: {e}")
            continue
            
        # Step 2: Inverse kinematics
        try:
            ik_angles = ik.inverse_kinematics(pos, orient, test_angles)
            if ik_angles is None:
                print(f"  Inverse kinematics failed: No solution found")
                continue
            print(f"IK Result: [{ik_angles[0]:.2f}, {ik_angles[1]:.2f}, {ik_angles[2]:.2f}, {ik_angles[3]:.2f}, {ik_angles[4]:.2f}, {ik_angles[5]:.2f}]")
        except Exception as e:
            print(f"  Inverse kinematics failed: {e}")
            continue
            
        # Step 3: Forward kinematics on IK result
        try:
            verify_pos, verify_orient = ik.forward_kinematics(ik_angles)
            print(f"Verification FK:")
            print(f"  Position: [{verify_pos[0]:.2f}, {verify_pos[1]:.2f}, {verify_pos[2]:.2f}] mm")
            print(f"  Orientation: [{verify_orient[0]:.2f}, {verify_orient[1]:.2f}, {verify_orient[2]:.2f}] deg")
        except Exception as e:
            print(f"  Verification failed: {e}")
            continue
            
        # Step 4: Calculate errors
        pos_error = [(verify_pos[j] - pos[j]) for j in range(3)]
        orient_error = [(verify_orient[j] - orient[j]) for j in range(3)]
        angle_error = [(ik_angles[j] - test_angles[j]) for j in range(6)]
        
        pos_error_mag = sum(abs(e) for e in pos_error)
        orient_error_mag = sum(abs(e) for e in orient_error)
        angle_error_mag = sum(abs(e) for e in angle_error)
        
        print(f"Errors:")
        print(f"  Position error: {pos_error_mag:.3f} mm total")
        print(f"  Orientation error: {orient_error_mag:.3f} deg total") 
        print(f"  Angle difference: {angle_error_mag:.3f} deg total")
        
        # Success criteria
        success = (pos_error_mag < 1.0 and orient_error_mag < 1.0)
        print(f"  Result: {'✓ PASS' if success else '✗ FAIL'}")

if __name__ == "__main__":
    test_ik_roundtrip()