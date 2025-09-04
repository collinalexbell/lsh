"""AprilTag detection API routes"""
import cv2
import numpy as np
from flask import Blueprint, jsonify, request, Response
from io import BytesIO
import base64

from ..services.apriltag_service import apriltag_service
from ..services.camera_service import camera_service

apriltag_bp = Blueprint('apriltag', __name__)

@apriltag_bp.route('/api/apriltag/detect', methods=['POST'])
def detect_apriltags():
    """Detect AprilTags in current camera frame"""
    try:
        # Get current frame from camera service
        if camera_service._last_frame is None:
            return jsonify({'success': False, 'message': 'No camera frame available'})
        
        frame = camera_service._last_frame.copy()
        
        # Detect AprilTags
        detections = apriltag_service.detect_tags(frame)
        
        return jsonify({
            'success': True,
            'detections': detections,
            'count': len(detections)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@apriltag_bp.route('/api/apriltag/image')
def get_apriltag_image():
    """Get camera image with AprilTag detections overlaid"""
    try:
        # Get current frame from camera service
        if camera_service._last_frame is None:
            return jsonify({'success': False, 'message': 'No camera frame available'})
        
        frame = camera_service._last_frame.copy()
        
        # Detect AprilTags
        detections = apriltag_service.detect_tags(frame)
        
        # Draw detections on image
        annotated_image = apriltag_service.draw_detections(frame, detections)
        
        # Encode image as JPEG
        ret, buffer = cv2.imencode('.jpg', annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ret:
            return jsonify({'success': False, 'message': 'Failed to encode image'})
        
        # Convert to base64
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': f'data:image/jpeg;base64,{img_base64}',
            'detections': detections,
            'count': len(detections)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@apriltag_bp.route('/api/apriltag/config', methods=['GET'])
def get_apriltag_config():
    """Get current AprilTag detection configuration"""
    try:
        config = {
            'tag_size_meters': apriltag_service.tag_size_meters,
            'tag_size_mm': apriltag_service.tag_size_meters * 1000,
            'camera_resolution': {
                'width': apriltag_service.image_width,
                'height': apriltag_service.image_height
            },
            'focal_length': apriltag_service.focal_length,
            'camera_matrix': apriltag_service.camera_matrix.tolist()
        }
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@apriltag_bp.route('/api/apriltag/config', methods=['POST'])
def update_apriltag_config():
    """Update AprilTag detection configuration"""
    try:
        data = request.json or {}
        
        # Update tag size if provided
        if 'tag_size_mm' in data:
            tag_size_mm = float(data['tag_size_mm'])
            apriltag_service.update_tag_size(tag_size_mm / 1000.0)  # Convert to meters
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated',
            'tag_size_mm': apriltag_service.tag_size_meters * 1000
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@apriltag_bp.route('/api/apriltag/stream')
def apriltag_stream():
    """Video stream with AprilTag detection overlay"""
    
    def generate():
        try:
            while True:
                # Get current frame from camera service
                if camera_service._last_frame is None:
                    continue
                    
                frame = camera_service._last_frame.copy()
                
                # Detect AprilTags
                detections = apriltag_service.detect_tags(frame)
                
                # Draw detections on image
                annotated_image = apriltag_service.draw_detections(frame, detections)
                
                # Encode frame for streaming
                ret, buffer = cv2.imencode('.jpg', annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                           
        except Exception as e:
            print(f"AprilTag stream error: {e}")
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@apriltag_bp.route('/api/apriltag/calibrate', methods=['POST'])
def calibrate_distance():
    """Calibrate distance measurement using known distance"""
    try:
        data = request.json or {}
        actual_distance_cm = data.get('actual_distance_cm')
        
        if not actual_distance_cm:
            return jsonify({'success': False, 'message': 'actual_distance_cm required'})
        
        # Get current detections
        if camera_service._last_frame is None:
            return jsonify({'success': False, 'message': 'No camera frame available'})
        
        frame = camera_service._last_frame.copy()
        detections = apriltag_service.detect_tags(frame)
        
        if not detections:
            return jsonify({'success': False, 'message': 'No AprilTags detected for calibration'})
        
        # Use first detection for calibration
        detection = detections[0]
        measured_distance_cm = detection.get('distance_cm', 0)
        
        # Calculate correction factor
        if measured_distance_cm > 0:
            correction_factor = actual_distance_cm / measured_distance_cm
            
            # Update focal length based on correction
            apriltag_service.focal_length *= correction_factor
            apriltag_service.fx = apriltag_service.focal_length
            apriltag_service.fy = apriltag_service.focal_length
            
            # Update camera matrix
            apriltag_service.camera_matrix[0, 0] = apriltag_service.fx
            apriltag_service.camera_matrix[1, 1] = apriltag_service.fy
            
            return jsonify({
                'success': True,
                'message': 'Distance calibrated',
                'correction_factor': correction_factor,
                'old_focal_length': apriltag_service.focal_length / correction_factor,
                'new_focal_length': apriltag_service.focal_length,
                'measured_distance_cm': measured_distance_cm,
                'actual_distance_cm': actual_distance_cm
            })
        else:
            return jsonify({'success': False, 'message': 'Could not measure distance'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})