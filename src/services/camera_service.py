"""Camera and video recording service"""
import cv2
import os
import base64
import datetime
import threading
import time
from typing import Optional, Generator

from ..models.robot_state import robot_state
from ..utils.config import CAMERA_DEVICE, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS, VIDEOS_DIR, VIDEO_CODEC, VIDEO_FPS

class CameraService:
    """Handles camera operations and video recording"""
    
    def __init__(self):
        self._camera: Optional[cv2.VideoCapture] = None
        self._video_writer: Optional[cv2.VideoWriter] = None
        self._last_frame = None
        self._stream_active = False
        self._ensure_videos_dir()
    
    def _ensure_videos_dir(self):
        """Ensure videos directory exists"""
        os.makedirs(VIDEOS_DIR, exist_ok=True)
    
    def init_camera(self) -> Optional[cv2.VideoCapture]:
        """Initialize camera if not already initialized"""
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
        
        if self._camera is not None:
            self._camera.release()
            self._camera = None
        
        return True
    
    def generate_frames(self) -> Generator[bytes, None, None]:
        """Generate camera frames for streaming"""            
        try:
            camera = self.init_camera()
            if not camera:
                print("Camera not available for streaming")
                return
            
            robot_state.camera_active = True
            print("Camera streaming started")
            
            # Limit streaming to 15 FPS for better performance
            target_fps = 15
            frame_interval = 1.0 / target_fps
            last_frame_time = 0
            frame_count = 0
            
            while robot_state.camera_active:
                current_time = time.time()
                
                if not camera.isOpened():
                    print("Camera closed, stopping stream")
                    break
                
                success, frame = camera.read()
                if not success:
                    print(f"Failed to read frame {frame_count}")
                    print(f"Camera isOpened: {camera.isOpened()}")
                    print(f"Camera backend: {camera.getBackendName()}")
                    
                    # Try to reinitialize camera once
                    print("Attempting to reinitialize camera...")
                    camera.release()
                    self._camera = None
                    camera = self.init_camera()
                    if camera and camera.isOpened():
                        print("Camera reinitialized successfully")
                        success, frame = camera.read()
                        if not success:
                            print("Camera reinit failed - still can't read frames")
                            break
                    else:
                        print("Camera reinit failed - camera unavailable")
                        break
                
                frame_count += 1
                
                # Store frame reference for screenshot use
                self._last_frame = frame
                
                # Write frame to video if recording
                if robot_state.is_recording_video and self._video_writer is not None:
                    self._video_writer.write(frame)
                
                # Rate limiting - only send frames at target FPS
                if current_time - last_frame_time >= frame_interval:
                    try:
                        # Encode frame for streaming with lower quality for speed
                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                        if ret:
                            frame_bytes = buffer.tobytes()
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                            last_frame_time = current_time
                        else:
                            print(f"Failed to encode frame {frame_count}")
                    except GeneratorExit:
                        print("Client disconnected from video stream")
                        break
                    except Exception as e:
                        print(f"Error yielding frame {frame_count}: {e}")
                        break
                
                # Small delay to prevent CPU spinning
                time.sleep(0.01)
            
            print(f"Camera streaming ended after {frame_count} frames")
            
        except Exception as e:
            print(f"Camera streaming error: {e}")
        finally:
            robot_state.camera_active = False
    
    def take_screenshot(self) -> Optional[str]:
        """Take a screenshot using stored frame from video stream - NEVER touch camera directly"""
        print("=== SCREENSHOT START ===")
        print(f"robot_state.camera_active: {robot_state.camera_active}")
        print(f"_last_frame is None: {self._last_frame is None}")
        
        if self._last_frame is None:
            print("No frame available for screenshot - video stream not active")
            return None
        
        try:
            print("Encoding stored frame for screenshot (NOT touching camera)")
            # Create a copy of the frame to be completely safe
            frame_copy = self._last_frame.copy()
            
            # Encode the copied frame
            success, buffer = cv2.imencode('.jpg', frame_copy, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not success:
                print("Failed to encode frame")
                return None
            
            print("Screenshot encoded successfully")
            print(f"robot_state.camera_active after screenshot: {robot_state.camera_active}")
            print("=== SCREENSHOT END ===")
            return f'data:image/jpeg;base64,{base64.b64encode(buffer).decode("utf-8")}'
        except Exception as e:
            print(f"Screenshot failed with error: {e}")
            print("=== SCREENSHOT END (ERROR) ===")
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