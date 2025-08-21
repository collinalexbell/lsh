"""Camera and video recording service"""
import cv2
import os
import base64
import datetime
import threading
from typing import Optional, Generator

from ..models.robot_state import robot_state
from ..utils.config import CAMERA_DEVICE, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS, VIDEOS_DIR, VIDEO_CODEC, VIDEO_FPS

class CameraService:
    """Handles camera operations and video recording"""
    
    def __init__(self):
        self._camera: Optional[cv2.VideoCapture] = None
        self._video_writer: Optional[cv2.VideoWriter] = None
        self._camera_lock = threading.Lock()
        self._ensure_videos_dir()
    
    def _ensure_videos_dir(self):
        """Ensure videos directory exists"""
        os.makedirs(VIDEOS_DIR, exist_ok=True)
    
    def init_camera(self) -> Optional[cv2.VideoCapture]:
        """Initialize camera if not already initialized"""
        with self._camera_lock:
            if self._camera is None:
                try:
                    self._camera = cv2.VideoCapture(CAMERA_DEVICE)
                    self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                    self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                    self._camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
                    print(f"Camera initialized: {CAMERA_DEVICE}")
                except Exception as e:
                    print(f"Failed to initialize camera: {e}")
                    self._camera = None
            return self._camera
    
    def is_camera_available(self) -> bool:
        """Check if camera is available"""
        camera = self.init_camera()
        return camera is not None and camera.isOpened()
    
    def start_camera(self) -> bool:
        """Start camera streaming"""
        if not self.is_camera_available():
            return False
        
        robot_state.camera_active = True
        return True
    
    def stop_camera(self) -> bool:
        """Stop camera and release resources"""
        robot_state.camera_active = False
        
        # Stop video recording if active
        if robot_state.is_recording_video:
            self.stop_video_recording()
        
        with self._camera_lock:
            if self._camera is not None:
                self._camera.release()
                self._camera = None
        
        return True
    
    def generate_frames(self) -> Generator[bytes, None, None]:
        """Generate camera frames for streaming"""
        camera = self.init_camera()
        if not camera:
            return
        
        robot_state.camera_active = True
        
        while robot_state.camera_active:
            with self._camera_lock:
                if not camera.isOpened():
                    break
                
                success, frame = camera.read()
                if not success:
                    break
                
                # Write frame to video if recording
                if robot_state.is_recording_video and self._video_writer is not None:
                    self._video_writer.write(frame)
                
                # Encode frame for streaming
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        robot_state.camera_active = False
    
    def take_screenshot(self) -> Optional[str]:
        """Take a screenshot and return base64 encoded image"""
        camera = self.init_camera()
        if not camera:
            return None
        
        try:
            with self._camera_lock:
                success, frame = camera.read()
                if not success:
                    return None
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    return None
                
                # Convert to base64
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                return f'data:image/jpeg;base64,{frame_base64}'
                
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return None
    
    def start_video_recording(self) -> Optional[str]:
        """Start video recording, returns filename if successful"""
        if robot_state.is_recording_video:
            return None
        
        camera = self.init_camera()
        if not camera:
            return None
        
        try:
            # Create filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'robot_video_{timestamp}.mp4'
            video_path = os.path.join(VIDEOS_DIR, filename)
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
            self._video_writer = cv2.VideoWriter(
                video_path, fourcc, VIDEO_FPS, (CAMERA_WIDTH, CAMERA_HEIGHT)
            )
            
            if not self._video_writer.isOpened():
                self._video_writer = None
                return None
            
            robot_state.set_video_recording_state(True, filename)
            print(f"Video recording started: {filename}")
            return filename
            
        except Exception as e:
            print(f"Failed to start video recording: {e}")
            robot_state.set_video_recording_state(False)
            if self._video_writer:
                self._video_writer.release()
                self._video_writer = None
            return None
    
    def stop_video_recording(self) -> Optional[str]:
        """Stop video recording, returns filename if successful"""
        if not robot_state.is_recording_video:
            return None
        
        filename = robot_state.video_filename
        robot_state.set_video_recording_state(False)
        
        try:
            if self._video_writer is not None:
                self._video_writer.release()
                self._video_writer = None
            
            print(f"Video recording stopped: {filename}")
            return filename
            
        except Exception as e:
            print(f"Failed to stop video recording: {e}")
            return filename  # Return filename even if cleanup failed
    
    def get_video_path(self, filename: str) -> Optional[str]:
        """Get full path to video file"""
        if not filename:
            return None
        
        # Sanitize filename for security
        from ..utils.validation import sanitize_filename
        safe_filename = sanitize_filename(filename)
        
        if not safe_filename.endswith('.mp4'):
            return None
        
        video_path = os.path.join(VIDEOS_DIR, safe_filename)
        
        if os.path.exists(video_path):
            return video_path
        
        return None

# Global service instance
camera_service = CameraService()