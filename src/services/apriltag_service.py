"""AprilTag detection and distance measurement service"""
import cv2
import numpy as np
import math
import apriltag
from typing import List, Dict, Optional, Tuple

class AprilTagService:
    """Handles AprilTag detection and distance calculation"""
    
    def __init__(self):
        # ONN 1440p webcam estimated parameters
        # Based on 85-degree field of view and 1440p resolution
        self.image_width = 640  # Current streaming resolution from camera service
        self.image_height = 480
        
        # Calculate focal length from field of view
        # For 85-degree diagonal FOV at 640x480
        diagonal_pixels = math.sqrt(self.image_width**2 + self.image_height**2)  # ~800 pixels
        fov_rad = math.radians(85)
        self.focal_length = diagonal_pixels / (2 * math.tan(fov_rad / 2))  # ~480 pixels
        
        # Camera intrinsic parameters (estimated)
        self.fx = self.focal_length  # Focal length in pixels (x)
        self.fy = self.focal_length  # Focal length in pixels (y)  
        self.cx = self.image_width / 2  # Principal point x
        self.cy = self.image_height / 2  # Principal point y
        
        # Camera intrinsic matrix
        self.camera_matrix = np.array([
            [self.fx, 0, self.cx],
            [0, self.fy, self.cy],
            [0, 0, 1]
        ], dtype=np.float64)
        
        # Distortion coefficients (assuming minimal distortion for webcam)
        self.dist_coeffs = np.array([0.1, -0.2, 0, 0, 0], dtype=np.float64)
        
        # AprilTag detector - Use all standard families and optimize for detection
        self.detector = apriltag.Detector(apriltag.DetectorOptions(
            families='tag36h11 tag25h9 tag16h5',  # Standard families that work
            border=1,
            nthreads=4,
            quad_decimate=0.8,  # Lower decimation for better small tag detection
            quad_blur=0.0,
            refine_edges=True,
            refine_decode=True,  # Enable decode refinement for better accuracy
            refine_pose=True
        ))
        
        # Standard AprilTag size (you can adjust this)
        self.tag_size_meters = 0.05  # 5cm tags (common size)
        
        print(f"AprilTag service initialized:")
        print(f"  Camera resolution: {self.image_width}x{self.image_height}")
        print(f"  Estimated focal length: {self.focal_length:.1f} pixels")
        print(f"  Tag size: {self.tag_size_meters*1000:.0f}mm")
    
    def detect_tags(self, image: np.ndarray) -> List[Dict]:
        """
        Detect AprilTags in image and calculate distances
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            List of detected tags with position and distance info
        """
        # Convert to grayscale for AprilTag detection
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Detect AprilTags
        detections = self.detector.detect(gray)
        
        results = []
        
        for detection in detections:
            tag_info = {
                'tag_id': detection.tag_id,
                'center': detection.center.tolist(),
                'corners': detection.corners.tolist(),
                'hamming': detection.hamming,
                'decision_margin': detection.decision_margin
            }
            
            # Calculate distance using tag size and camera parameters
            distance = self._calculate_distance(detection)
            if distance is not None:
                tag_info['distance_meters'] = distance
                tag_info['distance_cm'] = distance * 100
                tag_info['distance_inches'] = distance * 39.3701
            
            # Calculate pose (rotation and translation)
            pose = self._calculate_pose(detection)
            if pose is not None:
                tag_info['pose'] = pose
                
            results.append(tag_info)
        
        return results
    
    def _calculate_distance(self, detection) -> Optional[float]:
        """Calculate distance to AprilTag using perspective geometry"""
        try:
            # Get the four corners of the detected tag
            corners = detection.corners
            
            # Calculate the pixel width and height of the tag
            # Use opposite corners for more accurate measurement
            corner1, corner2, corner3, corner4 = corners
            
            # Calculate distances between opposite corners
            pixel_width = np.linalg.norm(corner2 - corner1)
            pixel_height = np.linalg.norm(corner3 - corner2) 
            
            # Use the average of width and height for distance calculation
            pixel_size = (pixel_width + pixel_height) / 2
            
            # Distance formula: distance = (real_size * focal_length) / pixel_size
            distance = (self.tag_size_meters * self.focal_length) / pixel_size
            
            return distance
            
        except Exception as e:
            print(f"Error calculating distance: {e}")
            return None
    
    def _calculate_pose(self, detection) -> Optional[Dict]:
        """Calculate 3D pose of AprilTag"""
        try:
            # Define 3D points of the tag in tag coordinate system
            # Tag is assumed to be on XY plane with Z=0
            half_size = self.tag_size_meters / 2
            object_points = np.array([
                [-half_size, -half_size, 0],  # Bottom left
                [ half_size, -half_size, 0],  # Bottom right
                [ half_size,  half_size, 0],  # Top right
                [-half_size,  half_size, 0]   # Top left
            ], dtype=np.float64)
            
            # 2D image points (corners of detected tag)
            image_points = detection.corners.astype(np.float64)
            
            # Solve PnP to get rotation and translation vectors
            success, rvec, tvec = cv2.solvePnP(
                object_points,
                image_points,
                self.camera_matrix,
                self.dist_coeffs
            )
            
            if success:
                # Convert rotation vector to rotation matrix
                rmat, _ = cv2.Rodrigues(rvec)
                
                return {
                    'translation': tvec.flatten().tolist(),
                    'rotation_vector': rvec.flatten().tolist(),
                    'rotation_matrix': rmat.tolist(),
                    'distance_from_pose': float(np.linalg.norm(tvec))
                }
                
        except Exception as e:
            print(f"Error calculating pose: {e}")
            
        return None
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw AprilTag detections on image with distance information"""
        result_image = image.copy()
        
        for detection in detections:
            # Draw tag outline
            corners = np.array(detection['corners'], dtype=int)
            cv2.polylines(result_image, [corners], True, (0, 255, 0), 2)
            
            # Draw center point
            center = tuple(map(int, detection['center']))
            cv2.circle(result_image, center, 5, (255, 0, 0), -1)
            
            # Draw tag ID
            tag_id = detection['tag_id']
            cv2.putText(result_image, f"ID: {tag_id}", 
                       (center[0] - 30, center[1] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw distance if available
            if 'distance_cm' in detection:
                distance_cm = detection['distance_cm']
                distance_text = f"{distance_cm:.1f}cm"
                cv2.putText(result_image, distance_text,
                           (center[0] - 30, center[1] + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # Draw coordinate axes if pose is available
            if 'pose' in detection:
                self._draw_axes(result_image, detection['pose'])
        
        return result_image
    
    def _draw_axes(self, image: np.ndarray, pose: Dict):
        """Draw 3D coordinate axes on the tag"""
        try:
            # Define axis points in tag coordinate system
            axis_length = self.tag_size_meters
            axis_points = np.array([
                [0, 0, 0],  # Origin
                [axis_length, 0, 0],  # X axis (red)
                [0, axis_length, 0],  # Y axis (green) 
                [0, 0, -axis_length]  # Z axis (blue)
            ], dtype=np.float64)
            
            # Project 3D points to 2D
            rvec = np.array(pose['rotation_vector'])
            tvec = np.array(pose['translation'])
            
            projected_points, _ = cv2.projectPoints(
                axis_points, rvec, tvec, self.camera_matrix, self.dist_coeffs
            )
            
            # Convert to integer coordinates
            projected_points = projected_points.reshape(-1, 2).astype(int)
            origin = tuple(projected_points[0])
            
            # Draw axes
            cv2.arrowedLine(image, origin, tuple(projected_points[1]), (0, 0, 255), 3)  # X - Red
            cv2.arrowedLine(image, origin, tuple(projected_points[2]), (0, 255, 0), 3)  # Y - Green
            cv2.arrowedLine(image, origin, tuple(projected_points[3]), (255, 0, 0), 3)  # Z - Blue
            
        except Exception as e:
            print(f"Error drawing axes: {e}")
    
    def update_tag_size(self, size_meters: float):
        """Update the expected tag size for distance calculations"""
        self.tag_size_meters = size_meters
        print(f"Updated tag size to {size_meters*1000:.0f}mm")
    
    def calibrate_camera(self, calibration_images: List[np.ndarray]) -> bool:
        """
        Calibrate camera using checkerboard images (optional improvement)
        This could be used to get more accurate camera parameters
        """
        # This would implement camera calibration using checkerboard patterns
        # For now, we use estimated parameters
        pass

# Global service instance
apriltag_service = AprilTagService()