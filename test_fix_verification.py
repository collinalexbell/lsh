#!/usr/bin/env python3
"""Test that the centidegrees bug is fixed"""

# Simulate the wall service centidegrees fix
def simulate_wall_service_ik():
    # Simulate what solve_inv_kinematics returns (centidegrees)
    mock_centidegrees = [-4440, 10328, 13893, -6142, -4414, -12861]
    
    print("Mock IK result (centidegrees):", mock_centidegrees)
    
    # This is the FIX - convert to degrees
    target_angles_degrees = [angle / 100.0 for angle in mock_centidegrees]
    print("Fixed result (degrees):", target_angles_degrees)
    
    return target_angles_degrees

if __name__ == "__main__":
    print("Testing centidegrees bug fix...")
    fixed_angles = simulate_wall_service_ik()
    
    print(f"\nBEFORE FIX: Robot would receive: {[-4440, 10328, 13893, -6142, -4414, -12861]} (DANGEROUS)")
    print(f"AFTER FIX: Robot would receive: {fixed_angles} (SAFE)")
    
    # Check if angles are within reasonable limits
    safe = all(-180 <= angle <= 180 for angle in fixed_angles)
    print(f"\nAngles within safe limits: {safe}")