"""Position management API routes"""
from flask import Blueprint, request, jsonify

from ..services.position_service import position_service
from ..services.robot_controller import robot_controller
from ..models.robot_state import robot_state

position_bp = Blueprint('position', __name__)

@position_bp.route('/api/positions', methods=['GET'])
def get_positions():
    """Get all saved positions and config"""
    try:
        data = position_service.get_all_positions()
        return jsonify({
            'success': True,
            'positions': data['positions'],
            'config': data['config']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@position_bp.route('/api/positions/save', methods=['POST'])
def save_position():
    """Save current robot position with a name"""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Position name is required'})
        
        # Get current robot angles
        if not robot_controller.ensure_powered():
            return jsonify({'success': False, 'message': 'Robot not powered'})
        
        current_angles = robot_controller.get_angles()
        if current_angles is None:
            return jsonify({'success': False, 'message': 'Failed to read current position'})
        
        # Save position
        position_service.save_position(name, current_angles)
        
        return jsonify({
            'success': True, 
            'message': f'Position "{name}" saved successfully',
            'angles': current_angles
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to save position: {str(e)}'})

@position_bp.route('/api/positions/delete', methods=['POST'])
def delete_position():
    """Delete a saved position"""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Position name is required'})
        
        position_service.delete_position(name)
        
        return jsonify({'success': True, 'message': f'Position "{name}" deleted'})
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to delete position: {str(e)}'})

@position_bp.route('/api/positions/update_config', methods=['POST'])
def update_position_config():
    """Update position configuration (enabled/disabled for command center)"""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        enabled = data.get('enabled', True)
        
        if not name:
            return jsonify({'success': False, 'message': 'Position name is required'})
        
        position_service.update_position_config(name, enabled)
        
        return jsonify({
            'success': True, 
            'message': f'Position "{name}" {"enabled" if enabled else "disabled"}'
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to update config: {str(e)}'})

@position_bp.route('/api/positions/move_to/<position_name>', methods=['POST'])
def move_to_position(position_name):
    """Move robot to a saved position"""
    try:
        position_data = position_service.get_position(position_name)
        if not position_data:
            return jsonify({'success': False, 'message': f'Position "{position_name}" not found'})
        
        angles = position_data['angles']
        
        if not robot_controller.ensure_powered():
            return jsonify({'success': False, 'message': 'Robot not powered'})
        
        # Use the unified robot state system:
        # 1. Read current ideal state (if initialized)
        # 2. Move to new target position
        # 3. Update unified global state
        
        if robot_state.state_initialized:
            current_ideal = robot_state.get_ideal_angles()
            print(f"DEBUG: Position move from ideal state: {current_ideal} to {angles}")
        else:
            print(f"DEBUG: Position move initializing state to: {angles}")
        
        success = robot_controller.send_angles(angles, 80)  # Use moderate speed
        
        if success:
            # The send_angles call will update the unified target_angles via robot_controller
            # This automatically maintains the single global state for all movement types
            print(f"DEBUG: Position move completed - unified state updated to: {angles}")
            
            return jsonify({
                'success': True,
                'message': f'Moving to position "{position_name}"',
                'angles': angles
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to move to position'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})