"""Wall calibration service for plane fitting and coordinate mapping"""
import json
import numpy as np
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

# Removed kinematics import - using MyCobot library directly
from .robot_controller import robot_controller
from ..models.robot_state import robot_state


class WallService:
    """Service for managing wall calibrations and coordinate transformations"""
    
    def __init__(self, calibration_file: str = 'wall_calibrations.json'):
        self.calibration_file = Path(calibration_file)
        self.calibrations = self._load_calibrations()
    
    def _load_calibrations(self) -> Dict[str, Dict[str, Any]]:
        """Load wall calibrations from file"""
        if not self.calibration_file.exists():
            return {}
        
        try:
            with open(self.calibration_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Error loading calibrations from {self.calibration_file}")
            return {}
    
    def _save_calibrations(self):
        """Save wall calibrations to file"""
        try:
            with open(self.calibration_file, 'w') as f:
                json.dump(self.calibrations, f, indent=2)
        except IOError as e:
            raise ValueError(f"Failed to save calibrations: {e}")
    
    def get_all_calibrations(self) -> Dict[str, Dict[str, Any]]:
        """Get all saved calibrations"""
        return self.calibrations.copy()
    
    def get_calibration(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific calibration by name"""
        return self.calibrations.get(name)
    
    def save_calibration(self, name: str, points: List[Dict[str, Any]], plane: Optional[Dict[str, Any]] = None):
        """Save a wall calibration"""
        if not name.strip():
            raise ValueError("Calibration name cannot be empty")
        
        if len(points) < 3:
            raise ValueError("At least 3 calibration points required")
        
        calibration = {
            'name': name,
            'points': points,
            'plane': plane,
            'created': self.calibrations.get(name, {}).get('created', datetime.now().isoformat()),
            'updated': datetime.now().isoformat()
        }
        
        self.calibrations[name] = calibration
        self._save_calibrations()
    
    def delete_calibration(self, name: str):
        """Delete a wall calibration"""
        if name not in self.calibrations:
            raise ValueError(f"Calibration '{name}' does not exist")
        
        del self.calibrations[name]
        self._save_calibrations()
    
    def calculate_best_fit_plane(self, positions: List[List[float]]) -> Tuple[Dict[str, List[float]], float]:
        """
        Calculate best-fit plane using least squares method
        
        Args:
            positions: List of 3D positions [[x, y, z], ...]
            
        Returns:
            Tuple of (plane_dict, fit_error)
            plane_dict contains: normal, point, equation
        """
        if len(positions) < 3:
            raise ValueError("At least 3 points required for plane fitting")
        
        # Convert to numpy array
        points = np.array(positions, dtype=float)
        
        # Center the points around their centroid
        centroid = np.mean(points, axis=0)
        centered_points = points - centroid
        
        # Perform SVD to find the best-fit plane
        # The plane normal is the right singular vector corresponding to the smallest singular value
        _, _, vh = np.linalg.svd(centered_points)
        normal = vh[-1]  # Last row of V^T is the normal vector
        
        # Ensure normal points in a consistent direction (e.g., positive Z if possible)
        if normal[2] < 0:
            normal = -normal
        
        # The plane equation is: normal · (P - centroid) = 0
        # Expanded: normal[0]*x + normal[1]*y + normal[2]*z + D = 0
        # where D = -normal · centroid
        D = -np.dot(normal, centroid)
        plane_equation = [float(normal[0]), float(normal[1]), float(normal[2]), float(D)]
        
        # Calculate fit error (RMS distance from points to plane)
        distances = []
        for point in points:
            # Distance from point to plane: |ax + by + cz + d| / sqrt(a² + b² + c²)
            dist = abs(np.dot(normal, point) + D) / np.linalg.norm(normal)
            distances.append(dist)
        
        fit_error = float(np.sqrt(np.mean(np.array(distances)**2)))
        
        plane_dict = {
            'normal': normal.tolist(),
            'point': centroid.tolist(),
            'equation': plane_equation
        }
        
        return plane_dict, fit_error
    
    def create_plane_calibration(self, name: str, current_angles: List[float]) -> dict:
        """
        Create a simple plane calibration based on current end effector orientation
        Args:
            name: Name for the calibration
            current_angles: Current robot joint angles in degrees
        Returns:
            Calibration dictionary
        """
        if not name.strip():
            raise ValueError("Calibration name cannot be empty")
        
        # Get the working plane from current ideal state, not robot coordinates
        if not robot_state.state_initialized:
            # Initialize from robot only if state not set
            current_angles = robot_controller.get_angles()
            if current_angles:
                robot_state.update_ideal_angles(current_angles)
            else:
                return None
        
        # Get ideal coordinates from state
        ideal_coords = robot_state.get_ideal_cartesian(robot_controller)
        if not ideal_coords or len(ideal_coords) != 6:
            return None
        coords = ideal_coords
        
        # Calculate proper plane coordinate system from end effector orientation
        import numpy as np
        position, orientation = coords[:3], coords[3:]
        
        # MyCobot orientation is typically [rx, ry, rz] in degrees
        # For a proper plane calculation, we need to understand the end effector's actual orientation
        rx, ry, rz = np.radians(orientation)  # Convert degrees to radians
        
        print(f"DEBUG: Creating plane calibration - Position: {position}, Orientation: {orientation}")
        
        # TEST MULTIPLE ROTATION ORDERS - MyCobot documentation is unclear
        # Let's try different conventions to see which gives sensible results
        
        # Create rotation matrices
        Rx = np.array([[1, 0, 0],
                      [0, np.cos(rx), -np.sin(rx)],
                      [0, np.sin(rx), np.cos(rx)]])
        
        Ry = np.array([[np.cos(ry), 0, np.sin(ry)],
                      [0, 1, 0],
                      [-np.sin(ry), 0, np.cos(ry)]])
        
        Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                      [np.sin(rz), np.cos(rz), 0],
                      [0, 0, 1]])
        
        # Test different rotation orders
        R_xyz = Rx @ Ry @ Rz  # XYZ intrinsic
        R_zyx = Rz @ Ry @ Rx  # ZYX intrinsic (common for robotics)
        R_zxy = Rz @ Rx @ Ry  # ZXY intrinsic
        
        print(f"DEBUG: Testing rotation orders:")
        print(f"  XYZ: X={R_xyz[:, 0]}, Y={R_xyz[:, 1]}, Z={R_xyz[:, 2]}")
        print(f"  ZYX: X={R_zyx[:, 0]}, Y={R_zyx[:, 1]}, Z={R_zyx[:, 2]}")
        print(f"  ZXY: X={R_zxy[:, 0]}, Y={R_zxy[:, 1]}, Z={R_zxy[:, 2]}")
        
        # For now, use ZYX which is common for end effector orientations
        R = R_zyx
        
        # Extract the normal (Z-axis) from the rotation matrix
        # This defines the plane orientation based on end effector
        normal = R[:, 2]  # End effector's Z-axis direction (normal to working plane)
        
        # Calculate ground-parallel X-axis by projecting the end effector's X-axis onto the horizontal plane
        end_effector_x = R[:, 0]  # End effector's X-axis
        
        # Project onto horizontal plane by removing Z component
        horizontal_x = np.array([end_effector_x[0], end_effector_x[1], 0])
        
        # If the projection is too small (pointing nearly vertical), use world X-axis as fallback
        if np.linalg.norm(horizontal_x) < 0.1:
            horizontal_x = np.array([1, 0, 0])  # World X-axis
        else:
            horizontal_x = horizontal_x / np.linalg.norm(horizontal_x)  # Normalize
        
        # Calculate Y-axis as cross product of normal and X-axis to ensure orthogonal coordinate system
        local_y_axis = np.cross(normal, horizontal_x)
        local_y_axis = local_y_axis / np.linalg.norm(local_y_axis)  # Normalize
        
        # Re-calculate X-axis to ensure perfect orthogonality (in case normal wasn't perfectly perpendicular to horizontal)
        local_x_axis = np.cross(local_y_axis, normal)
        local_x_axis = local_x_axis / np.linalg.norm(local_x_axis)  # Normalize
        
        # Convert to lists for storage
        local_x_axis = local_x_axis.tolist()
        local_y_axis = local_y_axis.tolist()
        normal = normal.tolist()
        
        print(f"DEBUG: End effector X-axis: {end_effector_x.tolist()}")
        print(f"DEBUG: Ground-parallel X-axis: {local_x_axis}")
        print(f"DEBUG: Calculated plane axes - X: {local_x_axis}, Y: {local_y_axis}, Normal: {normal}")
        
        plane_info = {
            'point': position,
            'normal': normal,
            'local_x_axis': local_x_axis,
            'local_y_axis': local_y_axis,
            'orientation': orientation
        }
        
        # Create calibration point at current ideal position
        # Use ideal coordinates from state, not robot queries
        current_pos, current_orient = coords[:3], coords[3:]
        
        calibration_point = {
            'id': 1,
            'name': 'Reference Point',
            'robotPosition': robot_state.get_ideal_angles(),
            'worldPosition': current_pos,
            'screenPosition': None  # Will be set by user if needed
        }
        
        calibration = {
            'name': name,
            'points': [calibration_point],
            'plane': {
                'normal': plane_info['normal'],
                'point': plane_info['point'],
                'local_x_axis': plane_info['local_x_axis'],
                'local_y_axis': plane_info['local_y_axis'],
                'orientation': plane_info['orientation']
            },
            'created': self.calibrations.get(name, {}).get('created', datetime.now().isoformat()),
            'updated': datetime.now().isoformat(),
            'type': 'plane_based'
        }
        
        self.calibrations[name] = calibration
        self._save_calibrations()
        
        return calibration
    
    def move_in_plane(self, calibration_name: str, dx_local: float, dy_local: float, 
                     robot_controller) -> Optional[List[float]]:
        """
        Move in the calibrated plane using ideal coordinate tracking
        Args:
            calibration_name: Name of the calibration to use
            dx_local: Movement along local X-axis in mm
            dy_local: Movement along local Y-axis in mm
            robot_controller: Robot controller instance for IK access
        Returns:
            New joint angles or None if movement not possible
        """
        calibration = self.get_calibration(calibration_name)
        if not calibration:
            raise ValueError(f"Calibration '{calibration_name}' not found")
        
        try:
            # Use unified global robot state - all movements use single source of truth
            print(f"DEBUG: Plane movement - plane_mode_active={robot_state.plane_mode_active}, state_initialized={robot_state.state_initialized}")
            
            # Simplified approach: always get current robot position for plane movements
            # The key is that we use target_angles for IK, but get position from robot
            if robot_state.state_initialized:
                current_angles = robot_state.get_ideal_angles()
                print(f"DEBUG: Using target angles from unified state: {current_angles}")
            else:
                current_angles = robot_controller.get_angles()
                if current_angles:
                    robot_state.update_ideal_angles(current_angles)
                    robot_state.set_manual_control(True)
                    robot_state.set_plane_mode(True)
                print(f"DEBUG: Initialized unified state with robot angles: {current_angles}")
            
            # Get current ideal position from state - this is our reference point
            ideal_coords = robot_state.get_ideal_cartesian(robot_controller)
            if not ideal_coords or len(ideal_coords) != 6 or not current_angles:
                print("DEBUG: Could not get ideal coordinates or angles")
                return None
                
            current_pos, current_orient = ideal_coords[:3], ideal_coords[3:]
            print(f"DEBUG: Plane movement from ideal position: {current_pos}, using ideal angles: {current_angles}")
            
            # Get plane vectors from calibration
            plane = calibration.get('plane')
            if not plane:
                raise ValueError("Calibration does not have plane information")
            
            import numpy as np
            local_x = np.array(plane['local_x_axis'])
            local_y = np.array(plane['local_y_axis'])
            normal = np.array(plane['normal'])
            current_pos_np = np.array(current_pos)
            
            # Validate coordinate system orthogonality
            dot_xy = np.dot(local_x, local_y)
            dot_xn = np.dot(local_x, normal)
            dot_yn = np.dot(local_y, normal)
            
            if abs(dot_xy) > 0.1 or abs(dot_xn) > 0.1 or abs(dot_yn) > 0.1:
                print(f"WARNING: Non-orthogonal coordinate system detected!")
                print(f"  X·Y = {dot_xy:.3f} (should be ~0)")
                print(f"  X·N = {dot_xn:.3f} (should be ~0)")  
                print(f"  Y·N = {dot_yn:.3f} (should be ~0)")
                
            # Ensure axes are normalized
            x_mag = np.linalg.norm(local_x)
            y_mag = np.linalg.norm(local_y)
            n_mag = np.linalg.norm(normal)
            
            if abs(x_mag - 1.0) > 0.1 or abs(y_mag - 1.0) > 0.1 or abs(n_mag - 1.0) > 0.1:
                print(f"WARNING: Non-normalized axes detected!")
                print(f"  |X| = {x_mag:.3f} (should be ~1)")
                print(f"  |Y| = {y_mag:.3f} (should be ~1)")
                print(f"  |N| = {n_mag:.3f} (should be ~1)")
                
                # Normalize the axes
                local_x = local_x / x_mag if x_mag > 1e-6 else local_x
                local_y = local_y / y_mag if y_mag > 1e-6 else local_y
            
            # Calculate movement in world coordinates using the plane's local coordinate system
            world_movement = dx_local * local_x + dy_local * local_y
            target_pos = (current_pos_np + world_movement).tolist()
            
            print(f"DEBUG: Plane axes - X: {local_x.tolist()}, Y: {local_y.tolist()}")
            print(f"DEBUG: Local movement: dx={dx_local}, dy={dy_local}")
            print(f"DEBUG: World movement vector: {world_movement.tolist()}")
            print(f"DEBUG: Is this global translation? X=[1,0,0]={np.allclose(local_x, [1,0,0])}, Y=[0,1,0]={np.allclose(local_y, [0,1,0])}")
            
            print(f"Plane movement: dx={dx_local}mm, dy={dy_local}mm")
            print(f"From {current_pos} to {target_pos}")
            
            # Use MyCobot's built-in inverse kinematics
            target_coords = target_pos + current_orient  # Keep same orientation
            print(f"DEBUG: Target coordinates: {target_coords}")
            print(f"DEBUG: Current angles: {current_angles}")
            
            target_angles = robot_controller._mc.solve_inv_kinematics(target_coords, current_angles)
            
            if target_angles is None or len(target_angles) != 6:
                print("MyCobot IK failed for plane movement")
                return None
            
            # Convert from centidegrees to degrees
            target_angles_degrees = [angle / 100.0 for angle in target_angles]
            print(f"DEBUG: IK result (raw centidegrees): {target_angles}")
            print(f"DEBUG: IK result (degrees): {target_angles_degrees}")
            
            # Update unified global robot state with new ideal position
            robot_state.update_ideal_angles(target_angles_degrees)
            print(f"DEBUG: Updated unified robot state - angles: {target_angles_degrees}")
            print(f"DEBUG: Calculated target cartesian: {target_coords}")
            
            print("MyCobot IK succeeded for plane movement")
            return target_angles_degrees
            
        except Exception as e:
            print(f"Error in plane movement: {e}")
            return None

    def map_screen_to_world(self, calibration_name: str, screen_coords: List[float]) -> Tuple[List[float], List[float]]:
        """
        Map screen coordinates to world coordinates using calibrated plane
        
        Args:
            calibration_name: Name of the calibration to use
            screen_coords: [x, y] screen coordinates in pixels
            
        Returns:
            Tuple of (world_position, robot_angles)
        """
        calibration = self.get_calibration(calibration_name)
        if not calibration:
            raise ValueError(f"Calibration '{calibration_name}' not found")
        
        if not calibration.get('plane'):
            raise ValueError(f"Calibration '{calibration_name}' does not have a calculated plane")
        
        points = calibration['points']
        plane = calibration['plane']
        
        # Find points with both screen and world coordinates
        valid_points = []
        for point in points:
            if point.get('screenPosition') and point.get('worldPosition'):
                valid_points.append(point)
        
        if len(valid_points) < 4:
            raise ValueError("Need at least 4 points with both screen and world coordinates for mapping")
        
        # Extract screen and world coordinates
        screen_points = np.array([point['screenPosition'] for point in valid_points], dtype=float)
        world_points = np.array([point['worldPosition'] for point in valid_points], dtype=float)
        
        # Use bilinear interpolation or homography depending on the number of points
        if len(valid_points) == 4:
            # Try bilinear interpolation if points form a rectangle
            world_position = self._bilinear_interpolation(
                screen_coords, screen_points, world_points
            )
        else:
            # Use least squares for more than 4 points
            world_position = self._least_squares_mapping(
                screen_coords, screen_points, world_points, plane
            )
        
        # Calculate robot angles using inverse kinematics
        # For now, use a default orientation - later this could be calibrated too
        default_orientation = [0, 0, 0]  # degrees
        # Disabled: Custom IK removed - using MyCobot built-in
        target_coords = world_position + robot_orientation
        robot_angles_raw = robot_controller._mc.solve_inv_kinematics(target_coords, [0,0,0,0,0,0])
        if robot_angles_raw and len(robot_angles_raw) == 6:
            robot_angles = [angle / 100.0 for angle in robot_angles_raw]  # Convert centidegrees
        else:
            robot_angles = None
        # robot_angles = mycobot_kinematics.inverse_kinematics(world_position, default_orientation)
        
        if robot_angles is None:
            raise ValueError("Could not calculate robot angles for the target position")
        
        return world_position, robot_angles
    
    def _bilinear_interpolation(self, target_screen: List[float], screen_points: np.ndarray, 
                               world_points: np.ndarray) -> List[float]:
        """
        Perform bilinear interpolation for 4-point rectangular mapping
        """
        # Assume points are ordered as: top-left, top-right, bottom-left, bottom-right
        # For now, use a simple approach - later this could be improved
        
        # Normalize screen coordinates to unit square [0,1] x [0,1]
        screen_min = np.min(screen_points, axis=0)
        screen_max = np.max(screen_points, axis=0)
        screen_size = screen_max - screen_min
        
        if np.any(screen_size <= 0):
            raise ValueError("Screen points do not form a valid rectangle")
        
        normalized_target = (np.array(target_screen) - screen_min) / screen_size
        u, v = normalized_target
        
        # Clamp to [0, 1]
        u = max(0, min(1, u))
        v = max(0, min(1, v))
        
        # Simple bilinear interpolation using the first 4 points
        world_min = np.min(world_points[:4], axis=0)
        world_max = np.max(world_points[:4], axis=0)
        
        # Interpolate in world coordinates
        world_position = world_min + np.array([u, v, u * v]) * (world_max - world_min)
        
        return world_position.tolist()
    
    def _least_squares_mapping(self, target_screen: List[float], screen_points: np.ndarray,
                              world_points: np.ndarray, plane: Dict[str, Any]) -> List[float]:
        """
        Map screen coordinates to world coordinates using least squares fitting
        """
        # For simplicity, use linear interpolation based on distance weighting
        screen_target = np.array(target_screen)
        
        # Calculate distances from target to all calibration points
        distances = np.linalg.norm(screen_points - screen_target, axis=1)
        
        # Avoid division by zero
        distances = np.maximum(distances, 1e-6)
        
        # Inverse distance weighting
        weights = 1.0 / distances
        weights = weights / np.sum(weights)
        
        # Weighted average of world positions
        world_position = np.average(world_points, axis=0, weights=weights)
        
        # Project the result onto the calibrated plane to ensure it lies on the wall
        plane_normal = np.array(plane['normal'])
        plane_point = np.array(plane['point'])
        
        # Project world_position onto the plane
        point_to_plane = world_position - plane_point
        projection_length = np.dot(point_to_plane, plane_normal)
        projected_position = world_position - projection_length * plane_normal
        
        return projected_position.tolist()


# Global instance
wall_service = WallService()