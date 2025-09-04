"""Procedure management API routes"""
import threading
import time
from flask import Blueprint, request, jsonify

from ..services.procedure_service import procedure_service
from ..services.position_service import position_service
from ..services.robot_controller import robot_controller
from ..models.robot_state import robot_state

procedure_bp = Blueprint('procedure', __name__)

@procedure_bp.route('/api/procedures', methods=['GET'])
def get_procedures():
    """Get all saved procedures"""
    try:
        procedures = procedure_service.get_all_procedures()
        return jsonify({
            'success': True,
            'procedures': procedures
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@procedure_bp.route('/api/procedures/save', methods=['POST'])
def save_procedure():
    """Save a new procedure"""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        steps = data.get('steps', [])
        description = data.get('description', '')
        
        if not name:
            return jsonify({'success': False, 'message': 'Procedure name is required'})
        
        if not steps:
            return jsonify({'success': False, 'message': 'Procedure must have at least one step'})
        
        # Validate that all position steps reference existing positions
        for i, step in enumerate(steps):
            if step.get('type') == 'position':
                position_name = step.get('data')
                if not position_service.position_exists(position_name):
                    return jsonify({
                        'success': False, 
                        'message': f'Step {i+1}: Position "{position_name}" does not exist'
                    })
        
        procedure_service.save_procedure(name, steps, description)
        
        return jsonify({
            'success': True, 
            'message': f'Procedure "{name}" saved successfully'
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to save procedure: {str(e)}'})

@procedure_bp.route('/api/procedures/delete', methods=['POST'])
def delete_procedure():
    """Delete a saved procedure"""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Procedure name is required'})
        
        procedure_service.delete_procedure(name)
        
        return jsonify({'success': True, 'message': f'Procedure "{name}" deleted'})
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to delete procedure: {str(e)}'})

@procedure_bp.route('/api/procedures/update', methods=['POST'])
def update_procedure():
    """Update an existing procedure"""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        steps = data.get('steps', [])
        description = data.get('description', '')
        
        if not name:
            return jsonify({'success': False, 'message': 'Procedure name is required'})
        
        if not steps:
            return jsonify({'success': False, 'message': 'Procedure must have at least one step'})
        
        # Validate that all position steps reference existing positions
        for i, step in enumerate(steps):
            if step.get('type') == 'position':
                position_name = step.get('data')
                if not position_service.position_exists(position_name):
                    return jsonify({
                        'success': False, 
                        'message': f'Step {i+1}: Position "{position_name}" does not exist'
                    })
        
        procedure_service.update_procedure(name, steps, description)
        
        return jsonify({
            'success': True, 
            'message': f'Procedure "{name}" updated successfully'
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to update procedure: {str(e)}'})

@procedure_bp.route('/api/procedures/execute/<procedure_name>', methods=['POST'])
def execute_procedure(procedure_name):
    """Execute a saved procedure"""
    try:
        procedure = procedure_service.get_procedure(procedure_name)
        if not procedure:
            return jsonify({'success': False, 'message': f'Procedure "{procedure_name}" not found'})
        
        if robot_state.is_busy():
            return jsonify({'success': False, 'message': 'Robot is currently busy with another operation'})
        
        if not robot_controller.ensure_powered():
            return jsonify({'success': False, 'message': 'Robot not powered'})
        
        # Execute procedure in background thread
        def execute_steps():
            robot_state.set_playing_state(True)
            try:
                steps = procedure['steps']
                for i, step in enumerate(steps):
                    if not robot_state.is_playing:  # Check if execution was stopped
                        break
                    
                    step_type = step['type']
                    step_data = step['data']
                    
                    if step_type == 'position':
                        # Get position data
                        position_data = position_service.get_position(step_data)
                        if position_data:
                            print(f"Procedure {procedure_name}: Moving to position {step_data}")
                            robot_controller.send_angles(position_data['angles'], 80)
                            time.sleep(2)  # Wait for movement to complete
                        else:
                            print(f"Procedure {procedure_name}: Position {step_data} not found, skipping")
                    
                    elif step_type == 'delay':
                        print(f"Procedure {procedure_name}: Waiting {step_data} seconds")
                        time.sleep(step_data)
                
            except Exception as e:
                print(f"Error executing procedure {procedure_name}: {e}")
            finally:
                robot_state.set_playing_state(False)
        
        threading.Thread(target=execute_steps, daemon=True).start()
        
        return jsonify({
            'success': True,
            'message': f'Executing procedure "{procedure_name}"'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@procedure_bp.route('/api/procedures/stop', methods=['POST'])
def stop_procedure():
    """Stop procedure execution"""
    robot_state.set_playing_state(False)
    return jsonify({'success': True, 'message': 'Procedure execution stopped'})