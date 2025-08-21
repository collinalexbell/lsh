"""Camera and video recording API routes"""
import os
from flask import Blueprint, jsonify, Response, send_file

from ..services.camera_service import camera_service

camera_bp = Blueprint('camera', __name__)

@camera_bp.route('/api/camera/start', methods=['POST'])
def start_camera():
    """Start camera streaming"""
    try:
        success = camera_service.start_camera()
        
        if success:
            return jsonify({'success': True, 'message': 'Camera started'})
        else:
            return jsonify({'success': False, 'message': 'Camera not available'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@camera_bp.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    """Stop camera streaming"""
    try:
        camera_service.stop_camera()
        return jsonify({'success': True, 'message': 'Camera stopped'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@camera_bp.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(camera_service.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@camera_bp.route('/api/camera/screenshot', methods=['POST'])
def take_screenshot():
    """Take a screenshot"""
    try:
        image_data = camera_service.take_screenshot()
        
        if image_data:
            return jsonify({
                'success': True, 
                'message': 'Screenshot captured',
                'image': image_data
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to capture screenshot'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@camera_bp.route('/api/video/start', methods=['POST'])
def start_video_recording():
    """Start video recording"""
    try:
        filename = camera_service.start_video_recording()
        
        if filename:
            return jsonify({
                'success': True, 
                'message': 'Video recording started',
                'filename': filename
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to start video recording'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@camera_bp.route('/api/video/stop', methods=['POST'])
def stop_video_recording():
    """Stop video recording"""
    try:
        filename = camera_service.stop_video_recording()
        
        if filename:
            return jsonify({
                'success': True, 
                'message': 'Video recording stopped',
                'filename': filename
            })
        else:
            return jsonify({'success': False, 'message': 'Not currently recording video'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@camera_bp.route('/api/video/download/<filename>')
def download_video(filename):
    """Download video file"""
    try:
        video_path = camera_service.get_video_path(filename)
        
        if not video_path:
            return jsonify({'success': False, 'message': 'Video file not found'}), 404
        
        return send_file(video_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500