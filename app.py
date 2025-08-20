from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
from pymycobot import MyCobot320
import time
import threading
import json
import cv2

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mycobot-web-controller-secret-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize MyCobot320
mc = MyCobot320("/dev/ttyAMA0", 115200)

# Global variables
recorded_moves = []
is_recording = False
is_playing = False
is_jiggling = False

# Webcam variables
camera = None
camera_active = False

# Video recording variables
video_writer = None
is_recording_video = False
video_filename = None

# Power management
robot_powered = False
manual_control_active = False

# Internal joint angle state (what we want the robot to be at)
target_angles = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
state_initialized = False

# MyCobot320 joint limits (degrees)
ANGLE_LIMITS = [
    (-168, 168),  # Joint 1
    (-135, 135),  # Joint 2
    (-145, 145),  # Joint 3
    (-148, 148),  # Joint 4
    (-168, 168),  # Joint 5
    (-180, 180),  # Joint 6
]

def clamp_angles(angles):
    clamped = []
    for i, angle in enumerate(angles):
        min_a, max_a = ANGLE_LIMITS[i]
        clamped.append(max(min(angle, max_a), min_a))
    return clamped

def ensure_robot_powered():
    """Ensure robot is powered on and ready for commands"""
    global robot_powered
    if not robot_powered:
        mc.power_on()
        time.sleep(0.5)  # Give time for power up
        robot_powered = True

def robot_power_off():
    """Turn off robot power"""
    global robot_powered
    mc.power_off()
    robot_powered = False

def get_robot_status():
    global manual_control_active, target_angles, state_initialized, is_recording_video
    try:
        # During manual control, use internal state to avoid feedback loops
        if manual_control_active and state_initialized:
            angles = target_angles
        else:
            # Only read from robot when not in manual control
            angles = mc.get_angles()
            
        return {
            'connected': True,
            'angles': angles,
            'is_recording': is_recording,
            'is_playing': is_playing,
            'is_jiggling': is_jiggling,
            'is_recording_video': is_recording_video,
            'recorded_moves_count': len(recorded_moves),
            'joint_limits': ANGLE_LIMITS
        }
    except:
        return {
            'connected': False,
            'angles': [0, 0, 0, 0, 0, 0],
            'is_recording': is_recording,
            'is_playing': is_playing,
            'is_jiggling': is_jiggling,
            'is_recording_video': is_recording_video,
            'recorded_moves_count': len(recorded_moves),
            'joint_limits': ANGLE_LIMITS
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify(get_robot_status())

@app.route('/api/demo', methods=['POST'])
def demo():
    try:
        global target_angles, state_initialized, manual_control_active
        ensure_robot_powered()
        extend()
        time.sleep(4)  # Increased from 2 to 4 seconds to allow movement to complete
        home()
        time.sleep(6)  # Increased from 2 to 6 seconds to allow movement to complete
        
        # Sync internal state with final position (home)
        target_angles = [7.11, -135, 142.91, 36.56, 83.67, -0.79]  # Home position
        state_initialized = True
        manual_control_active = False  # Reset manual control mode
        
        robot_power_off()  # Demo powers off when complete
        return jsonify({'success': True, 'message': 'Demo completed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/home', methods=['POST'])
def home_endpoint():
    try:
        global target_angles, state_initialized, manual_control_active
        ensure_robot_powered()
        
        # Get current position first to "wake up" the robot
        current_angles = mc.get_angles()
        time.sleep(0.2)
        
        # Now move to home
        home()
        time.sleep(6)  # Increased from 2 to 6 seconds to allow movement to complete
        
        # Sync internal state with robot after home movement
        target_angles = [7.11, -135, 142.91, 36.56, 83.67, -0.79]  # Home position
        state_initialized = True
        manual_control_active = False  # Reset manual control mode
        
        return jsonify({'success': True, 'message': 'Robot moved to home position'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/extend', methods=['POST'])
def extend_endpoint():
    try:
        global target_angles, state_initialized, manual_control_active
        ensure_robot_powered()
        extend()
        time.sleep(4)  # Increased from 2 to 4 seconds to allow movement to complete
        
        # Sync internal state with robot after extend movement
        target_angles = [0, 0, 0, 0, 0, 0]  # Extend position
        state_initialized = True
        manual_control_active = False  # Reset manual control mode
        
        return jsonify({'success': True, 'message': 'Robot extended'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/record/start', methods=['POST'])
def start_recording():
    global is_recording, recorded_moves
    is_recording = True
    recorded_moves = []
    # Don't power off - let user move robot manually
    socketio.emit('status_update', get_robot_status())
    return jsonify({'success': True, 'message': 'Recording started'})

@app.route('/api/record/capture', methods=['POST'])
def capture_position():
    global recorded_moves
    if not is_recording:
        return jsonify({'success': False, 'message': 'Not currently recording'})
    
    try:
        ensure_robot_powered()
        angles = mc.get_angles()
        recorded_moves.append(clamp_angles(angles))
        # Don't power off - let user continue positioning
        socketio.emit('status_update', get_robot_status())
        return jsonify({'success': True, 'message': f'Position captured: {angles}', 'angles': angles})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/record/stop', methods=['POST'])
def stop_recording():
    global is_recording, target_angles, state_initialized, manual_control_active
    is_recording = False
    try:
        ensure_robot_powered()
        home()
        time.sleep(6)  # Increased from 1 to 6 seconds to allow movement to complete
        
        # Sync internal state after going home
        target_angles = [7.11, -135, 142.91, 36.56, 83.67, -0.79]  # Home position
        state_initialized = True
        manual_control_active = False  # Reset manual control mode
        
    except:
        pass
    socketio.emit('status_update', get_robot_status())
    return jsonify({'success': True, 'message': 'Recording stopped', 'moves_count': len(recorded_moves)})

@app.route('/api/choreography/play', methods=['POST'])
def play_choreography():
    global is_playing
    if len(recorded_moves) == 0:
        return jsonify({'success': False, 'message': 'No choreography recorded'})
    
    def play_moves():
        global is_playing
        is_playing = True
        socketio.emit('status_update', get_robot_status())
        try:
            ensure_robot_powered()
            for position in recorded_moves:
                if not is_playing:
                    break
                mc.send_angles(position, 100)
                time.sleep(1)
        finally:
            home()
            time.sleep(6)  # Increased from 2 to 6 seconds to allow movement to complete
            
            # Sync internal state after choreography (ends at home)
            global target_angles, state_initialized, manual_control_active
            target_angles = [7.11, -135, 142.91, 36.56, 83.67, -0.79]  # Home position
            state_initialized = True
            manual_control_active = False  # Reset manual control mode
            
            is_playing = False
            socketio.emit('status_update', get_robot_status())
    
    threading.Thread(target=play_moves, daemon=True).start()
    return jsonify({'success': True, 'message': 'Playing choreography'})

@app.route('/api/choreography/stop', methods=['POST'])
def stop_choreography():
    global is_playing
    is_playing = False
    return jsonify({'success': True, 'message': 'Choreography stopped'})

@app.route('/api/jiggle/start', methods=['POST'])
def start_jiggling():
    global is_jiggling
    if len(recorded_moves) == 0:
        return jsonify({'success': False, 'message': 'No moves recorded for jiggling'})
    
    def jiggle():
        global is_jiggling
        is_jiggling = True
        socketio.emit('status_update', get_robot_status())
        try:
            ensure_robot_powered()
            while is_jiggling:
                for angles in recorded_moves:
                    if not is_jiggling:
                        break
                    mc.send_angles(angles, 100)
                    time.sleep(1)
        finally:
            # Don't power off - let user decide when to power off
            is_jiggling = False
            socketio.emit('status_update', get_robot_status())
    
    threading.Thread(target=jiggle, daemon=True).start()
    return jsonify({'success': True, 'message': 'Jiggling started'})

@app.route('/api/jiggle/stop', methods=['POST'])
def stop_jiggling():
    global is_jiggling
    is_jiggling = False
    return jsonify({'success': True, 'message': 'Jiggling stopped'})

@app.route('/api/choreography/clear', methods=['POST'])
def clear_choreography():
    global recorded_moves
    recorded_moves = []
    socketio.emit('status_update', get_robot_status())
    return jsonify({'success': True, 'message': 'Choreography cleared'})

# Webcam streaming functions
def init_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture('/dev/video0')
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
    return camera

def generate_frames():
    global camera_active, is_recording_video, video_writer
    camera_active = True
    camera = init_camera()
    
    while camera_active:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Write frame to video if recording
            if is_recording_video and video_writer is not None:
                video_writer.write(frame)
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    camera_active = False

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera/start', methods=['POST'])
def start_camera():
    global camera_active
    camera_active = True
    return jsonify({'success': True, 'message': 'Camera started'})

@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    global camera_active, camera
    camera_active = False
    if camera is not None:
        camera.release()
        camera = None
    return jsonify({'success': True, 'message': 'Camera stopped'})

@app.route('/api/camera/screenshot', methods=['POST'])
def take_screenshot():
    global camera
    try:
        if camera is None:
            camera = init_camera()
        
        if camera is None:
            return jsonify({'success': False, 'message': 'Camera not available'})
        
        success, frame = camera.read()
        if not success:
            return jsonify({'success': False, 'message': 'Failed to capture frame'})
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            return jsonify({'success': False, 'message': 'Failed to encode frame'})
        
        # Convert to base64 for web transmission
        import base64
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True, 
            'message': 'Screenshot captured',
            'image': f'data:image/jpeg;base64,{frame_base64}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/video/start', methods=['POST'])
def start_video_recording():
    global video_writer, is_recording_video, video_filename, camera
    try:
        if is_recording_video:
            return jsonify({'success': False, 'message': 'Already recording video'})
        
        if camera is None:
            camera = init_camera()
        
        if camera is None:
            return jsonify({'success': False, 'message': 'Camera not available'})
        
        # Create video filename with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f'robot_video_{timestamp}.mp4'
        video_path = f'/home/er/lsh/videos/{video_filename}'
        
        # Create videos directory if it doesn't exist
        import os
        os.makedirs('/home/er/lsh/videos', exist_ok=True)
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))
        
        if not video_writer.isOpened():
            return jsonify({'success': False, 'message': 'Failed to initialize video writer'})
        
        is_recording_video = True
        return jsonify({
            'success': True, 
            'message': 'Video recording started',
            'filename': video_filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/video/stop', methods=['POST'])
def stop_video_recording():
    global video_writer, is_recording_video, video_filename
    try:
        if not is_recording_video:
            return jsonify({'success': False, 'message': 'Not currently recording video'})
        
        is_recording_video = False
        
        if video_writer is not None:
            video_writer.release()
            video_writer = None
        
        return jsonify({
            'success': True, 
            'message': 'Video recording stopped',
            'filename': video_filename
        })
        
    except Exception as e:
        is_recording_video = False
        if video_writer is not None:
            video_writer.release()
            video_writer = None
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/video/download/<filename>')
def download_video(filename):
    try:
        import os
        from flask import send_file
        video_path = f'/home/er/lsh/videos/{filename}'
        
        if not os.path.exists(video_path):
            return jsonify({'success': False, 'message': 'Video file not found'}), 404
        
        return send_file(video_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Manual joint control endpoints
@app.route('/api/joint/move', methods=['POST'])
def move_joint():
    try:
        global manual_control_active, robot_powered, target_angles, state_initialized
        data = request.json
        joint_id = data.get('joint_id')  # 0-5 for joints 1-6
        angle = data.get('angle')
        speed = data.get('speed', 50)  # Default speed
        
        if joint_id is None or angle is None:
            return jsonify({'success': False, 'message': 'Missing joint_id or angle'})
        
        # Clamp angle to joint limits
        min_angle, max_angle = ANGLE_LIMITS[joint_id]
        angle = max(min(angle, max_angle), min_angle)
        
        # Only power on once at the start of manual control
        if not robot_powered:
            mc.power_on()
            time.sleep(0.5)  # Give time for power up
            robot_powered = True
        
        # Initialize internal state from robot if not done yet
        if not state_initialized:
            target_angles = list(mc.get_angles())  # Read once to initialize
            state_initialized = True
        
        manual_control_active = True
        
        # Update ONLY the internal state for the specified joint
        target_angles[joint_id] = angle
        
        # Send the internal state - no delays, no reading back
        mc.send_angles(target_angles, speed)
        
        return jsonify({
            'success': True, 
            'message': f'Joint {joint_id + 1} moved to {angle:.1f}°',
            'angles': target_angles
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/joints/move_all', methods=['POST'])
def move_all_joints():
    try:
        data = request.json
        angles = data.get('angles')
        speed = data.get('speed', 50)
        
        if not angles or len(angles) != 6:
            return jsonify({'success': False, 'message': 'Invalid angles array'})
        
        # Clamp all angles to joint limits
        clamped_angles = clamp_angles(angles)
        
        ensure_robot_powered()
        mc.send_angles(clamped_angles, speed)
        
        socketio.emit('status_update', get_robot_status())
        return jsonify({
            'success': True,
            'message': 'All joints moved',
            'angles': clamped_angles
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/joints/get_current', methods=['GET'])
def get_current_joints():
    try:
        global target_angles, state_initialized
        ensure_robot_powered()
        
        # Read from robot and update internal state
        robot_angles = mc.get_angles()
        target_angles = list(robot_angles)
        state_initialized = True
        
        return jsonify({
            'success': True,
            'angles': target_angles,
            'limits': ANGLE_LIMITS
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'angles': [0, 0, 0, 0, 0, 0]})

@app.route('/api/robot/power_off', methods=['POST'])
def power_off_endpoint():
    try:
        global manual_control_active
        robot_power_off()
        manual_control_active = False
        return jsonify({'success': True, 'message': 'Robot powered off'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def home():
    mc.send_angles([7.11, -135, 142.91, 36.56, 83.67, -0.79], 100)

def extend():
    mc.send_angles([0, 0, 0, 0, 0, 0], 100)

@socketio.on('connect')
def handle_connect():
    emit('status_update', get_robot_status())

@socketio.on('request_status')
def handle_status_request():
    emit('status_update', get_robot_status())

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)