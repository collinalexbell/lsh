"""Wall calibration API routes"""
from flask import Blueprint, request, jsonify

from ..services.wall_service import wall_service
from ..services.robot_controller import robot_controller
from ..models.robot_state import robot_state

wall_bp = Blueprint('wall', __name__)

@wall_bp.route('/api/wall/calibrations', methods=['GET'])
def get_wall_calibrations():
    """Get all wall calibrations"""
    try:
        calibrations = wall_service.get_all_calibrations()
        return jsonify({
            'success': True,
            'calibrations': calibrations
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@wall_bp.route('/api/wall/save-calibration', methods=['POST'])
def save_wall_calibration():
    """Save a wall calibration"""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        points = data.get('points', [])
        plane = data.get('plane')
        
        if not name:
            return jsonify({'success': False, 'message': 'Calibration name is required'})
        
        if len(points) < 3:
            return jsonify({'success': False, 'message': 'At least 3 calibration points required'})
        
        wall_service.save_calibration(name, points, plane)
        
        return jsonify({
            'success': True,
            'message': f'Wall calibration "{name}" saved successfully'
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to save calibration: {str(e)}'})

@wall_bp.route('/api/wall/delete-calibration', methods=['POST'])
def delete_wall_calibration():
    """Delete a wall calibration"""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Calibration name is required'})
        
        wall_service.delete_calibration(name)
        
        return jsonify({'success': True, 'message': f'Calibration "{name}" deleted'})
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to delete calibration: {str(e)}'})

@wall_bp.route('/api/wall/calculate-plane', methods=['POST'])
def calculate_plane():
    """Calculate best-fit plane from calibration points using least squares"""
    try:
        data = request.json or {}
        points = data.get('points', [])
        
        if len(points) < 3:
            return jsonify({'success': False, 'message': 'At least 3 points required to calculate plane'})
        
        # Extract 3D positions from points
        positions = []
        for point in points:
            position = point.get('position')
            if position and len(position) == 3:
                positions.append(position)
        
        if len(positions) < 3:
            return jsonify({'success': False, 'message': 'At least 3 valid positions required'})
        
        plane, fit_error = wall_service.calculate_best_fit_plane(positions)
        
        return jsonify({
            'success': True,
            'plane': plane,
            'fitError': fit_error,
            'message': f'Plane calculated from {len(positions)} points'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@wall_bp.route('/api/wall/map-point', methods=['POST'])
def map_screen_to_world():
    """Map screen coordinates to world coordinates using calibrated plane"""
    try:
        data = request.json or {}
        calibration_name = data.get('calibrationName', '').strip()
        screen_coords = data.get('screenCoords')  # [x, y] in pixels
        
        if not calibration_name:
            return jsonify({'success': False, 'message': 'Calibration name is required'})
        
        if not screen_coords or len(screen_coords) != 2:
            return jsonify({'success': False, 'message': 'Valid screen coordinates [x, y] required'})
        
        world_position, robot_angles = wall_service.map_screen_to_world(
            calibration_name, screen_coords
        )
        
        return jsonify({
            'success': True,
            'worldPosition': world_position,
            'robotAngles': robot_angles,
            'message': f'Mapped screen coords {screen_coords} to world position'
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@wall_bp.route('/api/wall/get-calibration/<calibration_name>', methods=['GET'])
def get_wall_calibration(calibration_name):
    """Get a specific wall calibration"""
    try:
        calibration = wall_service.get_calibration(calibration_name)
        if not calibration:
            return jsonify({'success': False, 'message': f'Calibration "{calibration_name}" not found'})
        
        return jsonify({
            'success': True,
            'calibration': calibration
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@wall_bp.route('/api/wall/create-plane-calibration', methods=['POST'])
def create_plane_calibration():
    """Create a plane calibration based on current end effector orientation"""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Calibration name is required'})
        
        if not robot_controller.is_connected():
            return jsonify({'success': False, 'message': 'Robot not connected'})
        
        # Use ideal angles from unified state instead of reading from robot
        if not robot_state.state_initialized:
            # Initialize from robot only if state not set
            current_angles = robot_controller.get_angles()
            if current_angles:
                robot_state.update_ideal_angles(current_angles)
            else:
                return jsonify({'success': False, 'message': 'Could not get current robot angles'})
        
        current_angles = robot_state.get_ideal_angles()
        
        calibration = wall_service.create_plane_calibration(name, current_angles)
        
        return jsonify({
            'success': True,
            'calibration': calibration,
            'message': f'Plane calibration "{name}" created based on current orientation'
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to create calibration: {str(e)}'})

@wall_bp.route('/api/wall/move-in-plane', methods=['POST'])
def move_in_plane():
    """Move in the calibrated plane using local coordinates"""
    try:
        data = request.json or {}
        calibration_name = data.get('calibrationName', '').strip()
        dx_local = data.get('dxLocal', 0.0)  # Movement in local X (mm)
        dy_local = data.get('dyLocal', 0.0)  # Movement in local Y (mm)
        
        if not calibration_name:
            return jsonify({'success': False, 'message': 'Calibration name is required'})
        
        if not robot_controller.is_connected():
            return jsonify({'success': False, 'message': 'Robot not connected'})
        
        # Wall service will handle getting ideal angles to avoid feedback loops
        new_angles = wall_service.move_in_plane(calibration_name, dx_local, dy_local, robot_controller)
        
        if new_angles is None:
            return jsonify({'success': False, 'message': 'Could not calculate valid movement in plane'})
        
        # Send angles to robot now that centidegrees bug is fixed
        # send_angles() will automatically update target angles in robot state
        robot_controller.send_angles(new_angles, speed=50)
        
        return jsonify({
            'success': True,
            'newAngles': new_angles,
            'message': f'Moved in plane: dx={dx_local}mm, dy={dy_local}mm'
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Movement failed: {str(e)}'})

@wall_bp.route('/api/wall/get-current-plane', methods=['GET'])
def get_current_plane():
    """Get the current working plane based on end effector orientation"""
    try:
        if not robot_controller.is_connected():
            return jsonify({'success': False, 'message': 'Robot not connected'})
        
        current_angles = robot_controller.get_angles()
        if not current_angles:
            return jsonify({'success': False, 'message': 'Could not get current robot angles'})
        
        # Disabled: Custom kinematics removed
        coords = robot_controller._mc.get_coords()
        if not coords or len(coords) != 6:
            return jsonify({'success': False, 'message': 'Could not get current coordinates'})
        
        plane_info = {
            'point': coords[:3],  # [x, y, z]
            'normal': [0, 0, 1],  # Default to XY plane
            'local_x_axis': [1, 0, 0],
            'local_y_axis': [0, 1, 0], 
            'orientation': coords[3:]  # [rx, ry, rz]
        }
        
        return jsonify({
            'success': True,
            'plane': plane_info,
            'currentAngles': current_angles
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})