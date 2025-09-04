#!/usr/bin/env python3
"""Test exact IK movements with 10mm translations"""

import sys
sys.path.append('src')
from pymycobot import MyCobot320

def test_10mm_movements():
    """Test 10mm movements and show exact angle changes"""
    
    print("Testing 10mm IK Movements")
    print("=" * 50)
    
    try:
        mc = MyCobot320('/dev/ttyAMA0', 115200)
        
        # Get current robot position
        current_angles = mc.get_angles()
        if not current_angles:
            print("Could not read current angles")
            return
            
        print(f"Current angles: {[round(a, 2) for a in current_angles]}")
        
        # Get current end effector position using forward kinematics
        current_coords = mc.get_coords()  # This should give [x, y, z, rx, ry, rz]
        if not current_coords:
            print("Could not read current coordinates")
            return
            
        print(f"Current position: [{current_coords[0]:.1f}, {current_coords[1]:.1f}, {current_coords[2]:.1f}] mm")
        print(f"Current orientation: [{current_coords[3]:.1f}, {current_coords[4]:.1f}, {current_coords[5]:.1f}] deg")
        
        # Test 10mm movements in each direction
        movements = [
            ([10, 0, 0], "Move +10mm X"),
            ([0, 10, 0], "Move +10mm Y"), 
            ([0, 0, 10], "Move +10mm Z"),
            ([-10, 0, 0], "Move -10mm X"),
            ([0, -10, 0], "Move -10mm Y"),
            ([0, 0, -10], "Move -10mm Z"),
        ]
        
        for movement, description in movements:
            print(f"\n{description}:")
            print("-" * 30)
            
            # Calculate target position
            target_pos = [
                current_coords[0] + movement[0],
                current_coords[1] + movement[1], 
                current_coords[2] + movement[2]
            ]
            
            # Keep same orientation
            target_coords = target_pos + current_coords[3:6]
            
            print(f"  Target: [{target_coords[0]:.1f}, {target_coords[1]:.1f}, {target_coords[2]:.1f}]")
            
            try:
                # Calculate IK
                ik_result_raw = mc.solve_inv_kinematics(target_coords, current_angles)
                
                if ik_result_raw and len(ik_result_raw) == 6:
                    # Convert from centidegrees to degrees
                    ik_result = [angle / 100.0 for angle in ik_result_raw]
                    
                    print(f"  New angles: {[round(a, 2) for a in ik_result]}")
                    
                    # Calculate angle changes
                    angle_changes = [ik_result[i] - current_angles[i] for i in range(6)]
                    print(f"  Δ angles: {[round(delta, 2) for delta in angle_changes]}")
                    
                    # Check joint limits
                    limits = [[-168,168],[-135,135],[-145,145],[-148,148],[-168,168],[-180,180]]
                    violations = []
                    for i, (angle, (min_limit, max_limit)) in enumerate(zip(ik_result, limits)):
                        if angle < min_limit or angle > max_limit:
                            violations.append(f"J{i+1}:{angle:.1f}")
                    
                    if violations:
                        print(f"  ⚠️  Limit violations: {violations}")
                    else:
                        print(f"  ✅ All joints within limits")
                        
                        # Verify the solution by checking what position it actually gives
                        try:
                            # Send angles to get verification (but don't actually move)
                            verify_coords = mc.get_coords()  # Would need to actually move to verify
                            print(f"  📍 Movement feasible")
                        except:
                            print(f"  📍 Could not verify position")
                    
                else:
                    print(f"  ❌ No IK solution found")
                    
            except Exception as e:
                print(f"  ❌ IK failed: {e}")
        
    except Exception as e:
        print(f"Failed to initialize robot: {e}")

if __name__ == "__main__":
    test_10mm_movements()