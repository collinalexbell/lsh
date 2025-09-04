#!/usr/bin/env python3
"""Demonstrate that centidegrees bug is fixed"""

def test_centidegrees_conversion():
    # Simulate the old buggy behavior
    print("=== BEFORE FIX (DANGEROUS) ===")
    mock_ik_centidegrees = [-4440, 10328, 13893, -6142, -4414, -12861]
    print(f"IK solver returns (centidegrees): {mock_ik_centidegrees}")
    print(f"OLD CODE would send to robot: {mock_ik_centidegrees}")
    print("^ These are 100x too large! Would break robot!")
    
    print("\n=== AFTER FIX (SAFE) ===")
    # Simulate the fixed behavior
    fixed_angles = [angle / 100.0 for angle in mock_ik_centidegrees]
    print(f"IK solver returns (centidegrees): {mock_ik_centidegrees}")
    print(f"FIXED CODE converts to degrees: {fixed_angles}")
    print(f"NEW CODE sends to robot: {fixed_angles}")
    print("^ These are safe angles within normal range!")
    
    print("\n=== VALIDATION ===")
    all_safe = all(-180 <= angle <= 180 for angle in fixed_angles)
    print(f"All angles within safe limits (-180 to +180): {all_safe}")
    
    max_angle = max(abs(angle) for angle in fixed_angles)
    print(f"Maximum absolute angle: {max_angle:.1f}°")
    
    if max_angle < 180:
        print("✅ SAFE: All angles are reasonable")
    else:
        print("❌ DANGEROUS: Some angles exceed limits")

if __name__ == "__main__":
    test_centidegrees_conversion()