"""Robot control API routes"""
import threading
import time
from flask import Blueprint, request, jsonify
from flask_socketio import emit

from ..services.robot_controller import robot_controller
from ..models.robot_state import robot_state
from ..utils.validation import validate_joint_id, validate_angle, validate_speed, validate_angles_array

robot_bp = Blueprint('robot', __name__)

@robot_bp.route('/api/status')
def get_status():
    """Get robot status"""
    return jsonify(robot_controller.get_current_status())

@robot_bp.route('/api/demo', methods=['POST'])
def demo():
    """Run demo sequence"""
    try:
        success = robot_controller.run_demo()
        
        if success:
            return jsonify({'success': True, 'message': 'Demo completed'})
        else:
            return jsonify({'success': False, 'message': 'Demo failed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@robot_bp.route('/api/home', methods=['POST'])
def home():
    """Move robot to home position"""
    try:
        success = robot_controller.move_to_home()
        
        if success:
            return jsonify({'success': True, 'message': 'Robot moved to home position'})
        else:
            return jsonify({'success': False, 'message': 'Failed to move to home position'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@robot_bp.route('/api/extend', methods=['POST'])
def extend():
    """Move robot to extend position"""
    try:
        success = robot_controller.move_to_extend()
        
        if success:
            return jsonify({'success': True, 'message': 'Robot extended'})
        else:
            return jsonify({'success': False, 'message': 'Failed to extend robot'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@robot_bp.route('/api/robot/power_off', methods=['POST'])
def power_off():
    """Power off robot"""
    try:
        success = robot_controller.power_off()
        
        if success:
            return jsonify({'success': True, 'message': 'Robot powered off'})
        else:
            return jsonify({'success': False, 'message': 'Failed to power off robot'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@robot_bp.route('/api/power_off', methods=['POST'])
def power_off_legacy():
    """Power off robot (legacy route for frontend compatibility)"""
    return power_off()

# Joint control endpoints
@robot_bp.route('/api/joint/move', methods=['POST'])
def move_joint():
    """Move a single joint"""
    try:
        data = request.json or {}
        joint_id = data.get('joint_id')
        angle = data.get('angle')
        speed = data.get('speed', 50)
        
        # Validation
        if joint_id is None or angle is None:
            return jsonify({'success': False, 'message': 'Missing joint_id or angle'})
        
        if not validate_joint_id(joint_id):
            return jsonify({'success': False, 'message': 'Invalid joint_id'})
        
        if not validate_speed(speed):
            return jsonify({'success': False, 'message': 'Invalid speed'})
        
        # Clamp angle to joint limits
        from ..utils.config import ANGLE_LIMITS
        min_angle, max_angle = ANGLE_LIMITS[joint_id]
        angle = max(min(angle, max_angle), min_angle)
        
        success = robot_controller.move_joint(joint_id, angle, speed)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Joint {joint_id + 1} moved to {angle:.1f}°',
                'angles': robot_state.get_ideal_angles()
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to move joint'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@robot_bp.route('/api/joints/move_all', methods=['POST'])
def move_all_joints():
    """Move all joints to specified angles"""
    try:
        data = request.json or {}
        angles = data.get('angles')
        speed = data.get('speed', 50)
        
        if not validate_angles_array(angles):
            return jsonify({'success': False, 'message': 'Invalid angles array'})
        
        if not validate_speed(speed):
            return jsonify({'success': False, 'message': 'Invalid speed'})
        
        success = robot_controller.send_angles(angles, speed)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'All joints moved',
                'angles': robot_state.get_ideal_angles()
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to move joints'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@robot_bp.route('/api/joints/get_current', methods=['GET'])
def get_current_joints():
    """Get current joint angles from robot"""
    try:
        if not robot_controller.ensure_powered():
            return jsonify({'success': False, 'message': 'Robot not powered', 'angles': [0, 0, 0, 0, 0, 0]})
        
        angles = robot_controller.get_angles()
        if angles is None:
            return jsonify({'success': False, 'message': 'Failed to read angles', 'angles': [0, 0, 0, 0, 0, 0]})
        
        robot_state.update_ideal_angles(angles)
        
        from ..utils.config import ANGLE_LIMITS
        return jsonify({
            'success': True,
            'angles': angles,
            'limits': ANGLE_LIMITS
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'angles': [0, 0, 0, 0, 0, 0]})

# Recording endpoints
@robot_bp.route('/api/record/start', methods=['POST'])
def start_recording():
    """Start recording robot movements"""
    robot_state.set_recording_state(True)
    return jsonify({'success': True, 'message': 'Recording started'})

@robot_bp.route('/api/record/capture', methods=['POST'])
def capture_position():
    """Capture current position during recording"""
    if not robot_state.is_recording:
        return jsonify({'success': False, 'message': 'Not currently recording'})
    
    try:
        if not robot_controller.ensure_powered():
            return jsonify({'success': False, 'message': 'Robot not powered'})
        
        angles = robot_controller.get_angles()
        if angles is None:
            return jsonify({'success': False, 'message': 'Failed to read angles'})
        
        from ..utils.config import ANGLE_LIMITS
        from ..utils.validation import clamp_angles
        safe_angles = clamp_angles(angles, ANGLE_LIMITS)
        
        robot_state.add_recorded_move(safe_angles)
        
        return jsonify({
            'success': True, 
            'message': f'Position captured: {angles}', 
            'angles': angles
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@robot_bp.route('/api/record/stop', methods=['POST'])
def stop_recording():
    """Stop recording"""
    robot_state.set_recording_state(False)
    
    # Move to home position
    robot_controller.move_to_home()
    
    moves_count = len(robot_state.get_recorded_moves())
    return jsonify({'success': True, 'message': 'Recording stopped', 'moves_count': moves_count})

# Choreography endpoints
@robot_bp.route('/api/choreography/play', methods=['POST'])
def play_choreography():
    """Play recorded choreography"""
    recorded_moves = robot_state.get_recorded_moves()
    if len(recorded_moves) == 0:
        return jsonify({'success': False, 'message': 'No choreography recorded'})
    
    def play_moves():
        robot_state.set_playing_state(True)
        try:
            if robot_controller.ensure_powered():
                for position in recorded_moves:
                    if not robot_state.is_playing:
                        break
                    robot_controller.send_angles(position, 100)
                    time.sleep(1)
        finally:
            robot_controller.move_to_home()
            robot_state.set_playing_state(False)
    
    threading.Thread(target=play_moves, daemon=True).start()
    return jsonify({'success': True, 'message': 'Playing choreography'})

@robot_bp.route('/api/choreography/stop', methods=['POST'])
def stop_choreography():
    """Stop choreography playback"""
    robot_state.set_playing_state(False)
    return jsonify({'success': True, 'message': 'Choreography stopped'})

@robot_bp.route('/api/choreography/clear', methods=['POST'])
def clear_choreography():
    """Clear recorded choreography"""
    robot_state.clear_recorded_moves()
    return jsonify({'success': True, 'message': 'Choreography cleared'})

# Jiggling endpoints
@robot_bp.route('/api/jiggle/start', methods=['POST'])
def start_jiggling():
    """Start jiggling (continuous playback)"""
    recorded_moves = robot_state.get_recorded_moves()
    if len(recorded_moves) == 0:
        return jsonify({'success': False, 'message': 'No moves recorded for jiggling'})
    
    def jiggle():
        robot_state.set_jiggling_state(True)
        try:
            if robot_controller.ensure_powered():
                while robot_state.is_jiggling:
                    for angles in recorded_moves:
                        if not robot_state.is_jiggling:
                            break
                        robot_controller.send_angles(angles, 100)
                        time.sleep(1)
        finally:
            robot_state.set_jiggling_state(False)
    
    threading.Thread(target=jiggle, daemon=True).start()
    return jsonify({'success': True, 'message': 'Jiggling started'})

@robot_bp.route('/api/jiggle/stop', methods=['POST'])
def stop_jiggling():
    """Stop jiggling"""
    robot_state.set_jiggling_state(False)
    return jsonify({'success': True, 'message': 'Jiggling stopped'})

# End effector control endpoints
@robot_bp.route('/api/end_effector/position', methods=['GET'])
def get_end_effector_position():
    """Get current end effector position and orientation"""
    try:
        position_data = robot_controller.get_end_effector_position()
        if position_data is None:
            return jsonify({'success': False, 'message': 'Failed to get end effector position'})
        
        return jsonify({
            'success': True,
            'position': position_data['position'],
            'orientation': position_data['orientation'],
            'joint_angles': position_data['joint_angles']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@robot_bp.route('/api/end_effector/move', methods=['POST'])
def move_end_effector():
    """Move end effector to target cartesian position"""
    try:
        data = request.json or {}
        target_pos = data.get('position')  # [x, y, z] in mm
        target_orient = data.get('orientation')  # [rx, ry, rz] in degrees
        
        if target_pos is None or target_orient is None:
            return jsonify({'success': False, 'message': 'Position and orientation required'})
        
        if len(target_pos) != 3 or len(target_orient) != 3:
            return jsonify({'success': False, 'message': 'Position and orientation must have 3 values each'})
        
        success = robot_controller.move_end_effector_cartesian(target_pos, target_orient)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'End effector moved to position {target_pos}',
                'position': target_pos,
                'orientation': target_orient
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to move end effector'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@robot_bp.route('/api/end_effector/translate', methods=['POST'])
def translate_end_effector():
    """Translate end effector by specified amounts"""
    try:
        data = request.json or {}
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        dz = data.get('dz', 0)
        
        if dx == 0 and dy == 0 and dz == 0:
            return jsonify({'success': False, 'message': 'At least one translation amount must be non-zero'})
        
        # Validate translation amounts (limit to reasonable values)
        max_translation = 100  # mm
        if abs(dx) > max_translation or abs(dy) > max_translation or abs(dz) > max_translation:
            return jsonify({'success': False, 'message': f'Translation amounts must be <= {max_translation}mm'})
        
        success = robot_controller.translate_end_effector(dx, dy, dz)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'End effector translated by dx={dx}, dy={dy}, dz={dz}mm',
                'translation': {'dx': dx, 'dy': dy, 'dz': dz}
            })
        else:
            return jsonify({'success': False, 'message': 'Translation failed - target may be unreachable'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})