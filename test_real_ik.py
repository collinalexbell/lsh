#!/usr/bin/env python3
"""Test MyCobot library IK with actual robot"""

import sys
import time
sys.path.append('src')

from services.robot_controller import robot_controller

def test_real_ik():
    """Test IK with actual robot - no movement, just calculations"""
    
    print("Testing MyCobot Library IK with Real Robot")
    print("=" * 50)
    
    if not robot_controller.is_connected():
        print("Robot not connected!")
        return
    
    # Get current position
    current_pos = robot_controller.get_end_effector_position()
    if not current_pos:
        print("Failed to get current position")
        return
        
    print(f"Current angles: {current_pos['joint_angles']}")
    print(f"Current position: {current_pos['position']}")
    print(f"Current orientation: {current_pos['orientation']}")
    
    # Test small movements from current position
    pos = current_pos['position']
    orient = current_pos['orientation']
    
    test_targets = [
        # Small translations
        ([pos[0] + 10, pos[1], pos[2]], orient, "Move +10mm X"),
        ([pos[0], pos[1] + 10, pos[2]], orient, "Move +10mm Y"),
        ([pos[0], pos[1], pos[2] + 10], orient, "Move +10mm Z"),
        ([pos[0] - 5, pos[1] - 5, pos[2]], orient, "Move -5mm X,Y"),
    ]
    
    for target_pos, target_orient, description in test_targets:
        print(f"\n{description}:")
        print(f"  Target: [{target_pos[0]:.1f}, {target_pos[1]:.1f}, {target_pos[2]:.1f}]")
        
        try:
            # Test if IK can solve this (without moving robot)
            target_coords = target_pos + target_orient
            current_angles = current_pos['joint_angles']
            
            # Use robot controller's internal MyCobot instance to test IK
            if hasattr(robot_controller, '_mc') and robot_controller._mc:
                ik_result = robot_controller._mc.solve_inv_kinematics(target_coords, current_angles)
                if ik_result and len(ik_result) == 6:
                    print(f"  IK Solution: {[round(a, 1) for a in ik_result]}")
                    
                    # Check joint limits
                    limits = [[-168,168],[-135,135],[-145,145],[-148,148],[-168,168],[-180,180]]
                    valid = True
                    for i, (angle, (min_limit, max_limit)) in enumerate(zip(ik_result, limits)):
                        if angle < min_limit or angle > max_limit:
                            print(f"    Joint {i+1} limit violation: {angle:.1f} not in [{min_limit}, {max_limit}]")
                            valid = False
                    
                    if valid:
                        print("    ✓ Solution within joint limits")
                    else:
                        print("    ✗ Solution violates joint limits")
                else:
                    print("  ✗ No IK solution found")
            else:
                print("  Robot controller not available")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_real_ik()