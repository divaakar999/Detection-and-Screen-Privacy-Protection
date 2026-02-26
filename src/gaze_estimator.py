"""
Gaze estimation and head pose detection using MediaPipe
"""
import cv2
import numpy as np
import mediapipe as mp
from typing import Tuple, Dict, Any, Optional, List
from dataclasses import dataclass
import threading

from config.settings import GAZE_THRESHOLD, ENABLE_HEAD_POSE, ENABLE_GAZE_ESTIMATION
from src.utils import TimeCounter, PerformanceMonitor


@dataclass
class GazeData:
    """Container for gaze estimation data"""
    gaze_vector: Tuple[float, float]  # (x, y) direction
    gaze_direction: str  # 'left', 'right', 'center', 'down'
    confidence: float
    is_looking_at_screen: bool
    eye_openness: float  # 0-1


class GazeEstimator:
    """
    Estimate gaze direction and head pose using MediaPipe Face Mesh
    """
    
    # Face mesh landmark indices
    LEFT_EYE = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]
    LEFT_IRIS = [468, 469, 470, 471, 472]
    RIGHT_IRIS = [473, 474, 475, 476, 477]
    NOSE = [1, 2, 4]
    FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
    
    def __init__(self, static_image_mode: bool = False, max_num_faces: int = 5):
        self.static_image_mode = static_image_mode
        self.max_num_faces = max_num_faces
        self.perf_monitor = PerformanceMonitor()
        self.lock = threading.Lock()
        
        # Initialize MediaPipe
        try:
            import mediapipe as mp
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=static_image_mode,
                max_num_faces=max_num_faces,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            print("MediaPipe Face Mesh initialized successfully")
        except Exception as e:
            print(f"Error initializing MediaPipe: {e}")
            print("Gaze estimation will be disabled")
            self.face_mesh = None
    
    def estimate_gaze(self, image: np.ndarray, face_bbox: Optional[Tuple[int, int, int, int]] = None) -> List[GazeData]:
        """
        Estimate gaze direction for all faces in image
        
        Args:
            image: Input image (BGR)
            face_bbox: Optional specific face bounding box to analyze
        
        Returns:
            List of GazeData for each detected face
        """
        timer = TimeCounter()
        timer.start()
        
        if self.face_mesh is None:
            return []
        
        with self.lock:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_image)
            
            gaze_data_list = []
            
            if results.multi_face_landmarks:
                h, w, _ = image.shape
                
                for face_landmarks in results.multi_face_landmarks:
                    gaze_data = self._process_face_landmarks(face_landmarks, h, w)
                    gaze_data_list.append(gaze_data)
            
            self.perf_monitor.record_detection_time(timer.elapsed_ms())
            return gaze_data_list
    
    def _process_face_landmarks(self, face_landmarks, h: int, w: int) -> GazeData:
        """Process face landmarks to extract gaze information"""
        landmarks = face_landmarks.landmark
        
        # Get eye positions
        left_eye = self._get_eye_center(landmarks, self.LEFT_EYE, h, w)
        right_eye = self._get_eye_center(landmarks, self.RIGHT_EYE, h, w)
        
        # Get iris positions
        left_iris = self._get_iris_center(landmarks, self.LEFT_IRIS, h, w)
        right_iris = self._get_iris_center(landmarks, self.RIGHT_IRIS, h, w)
        
        # Calculate gaze vectors
        left_gaze = (left_iris[0] - left_eye[0], left_iris[1] - left_eye[1])
        right_gaze = (right_iris[0] - right_eye[0], right_iris[1] - right_eye[1])
        
        # Average gaze vector
        avg_gaze = ((left_gaze[0] + right_gaze[0]) / 2, (left_gaze[1] + right_gaze[1]) / 2)
        
        # Normalize gaze vector
        gaze_mag = np.sqrt(avg_gaze[0]**2 + avg_gaze[1]**2)
        if gaze_mag > 0:
            normalized_gaze = (avg_gaze[0] / gaze_mag, avg_gaze[1] / gaze_mag)
        else:
            normalized_gaze = (0, 0)
        
        # Determine gaze direction
        gaze_direction, is_looking_at_screen = self._classify_gaze_direction(normalized_gaze)
        
        # Calculate eye openness
        eye_openness = self._calculate_eye_openness(landmarks)
        
        # Confidence based on head pose and tracking
        confidence = self._calculate_confidence(landmarks)
        
        return GazeData(
            gaze_vector=normalized_gaze,
            gaze_direction=gaze_direction,
            confidence=confidence,
            is_looking_at_screen=is_looking_at_screen,
            eye_openness=eye_openness
        )
    
    @staticmethod
    def _get_eye_center(landmarks, eye_indices: List[int], h: int, w: int) -> Tuple[int, int]:
        """Calculate center point of eye"""
        positions = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in eye_indices]
        center_x = int(np.mean([p[0] for p in positions]))
        center_y = int(np.mean([p[1] for p in positions]))
        return (center_x, center_y)
    
    @staticmethod
    def _get_iris_center(landmarks, iris_indices: List[int], h: int, w: int) -> Tuple[int, int]:
        """Calculate center point of iris"""
        positions = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in iris_indices]
        center_x = int(np.mean([p[0] for p in positions]))
        center_y = int(np.mean([p[1] for p in positions]))
        return (center_x, center_y)
    
    @staticmethod
    def _classify_gaze_direction(gaze_vector: Tuple[float, float]) -> Tuple[str, bool]:
        """
        Classify gaze direction based on gaze vector
        
        Returns:
            (direction, is_looking_at_screen)
        """
        gx, gy = gaze_vector
        
        # Determine if looking at screen (small lateral movement, slight downward)
        is_centered = abs(gx) < 0.3 and abs(gy) < 0.5
        
        if abs(gx) > abs(gy):
            # Primarily horizontal gaze
            if gx < -0.25:
                return 'left', False
            elif gx > 0.25:
                return 'right', False
            else:
                return 'center', is_centered
        else:
            # Primarily vertical gaze
            if gy > 0.25:
                return 'down', False
            else:
                return 'center', is_centered
    
    @staticmethod
    def _calculate_eye_openness(landmarks) -> float:
        """Calculate how open the eyes are (0-1)"""
        # Use vertical distance between upper and lower eyelids
        left_eye_top_y = landmarks[159].y
        left_eye_bottom_y = landmarks[145].y
        
        right_eye_top_y = landmarks[386].y
        right_eye_bottom_y = landmarks[374].y
        
        left_openness = abs(left_eye_top_y - left_eye_bottom_y)
        right_openness = abs(right_eye_top_y - right_eye_bottom_y)
        
        avg_openness = (left_openness + right_openness) / 2
        # Normalize to 0-1 range
        return min(1.0, max(0.0, avg_openness * 3))
    
    @staticmethod
    def _calculate_confidence(landmarks) -> float:
        """Calculate confidence of gaze estimation"""
        # Average confidence of key landmarks
        key_landmarks = [33, 160, 158, 133, 362, 385, 387, 263, 468, 469, 472, 473, 476, 477]
        confidences = [landmarks[i].z for i in key_landmarks if i < len(landmarks)]
        
        return np.mean(confidences) if confidences else 0.5
    
    def detect_head_pose(self, face_landmarks) -> Dict[str, float]:
        """
        Estimate head pose (pitch, yaw, roll) from face landmarks
        
        Returns:
            Dictionary with 'pitch', 'yaw', 'roll' angles in degrees
        """
        landmarks = face_landmarks.landmark
        
        # Use face oval points for head pose estimation
        face_points = np.array([(landmarks[i].x, landmarks[i].y) for i in self.FACE_OVAL])
        
        # Simplified head pose estimation using face aspect ratio
        face_height = max(landmarks[i].y for i in self.FACE_OVAL) - min(landmarks[i].y for i in self.FACE_OVAL)
        face_width = max(landmarks[i].x for i in self.FACE_OVAL) - min(landmarks[i].x for i in self.FACE_OVAL)
        
        pitch = 0  # Simplified - would need 3D pose estimation
        yaw = 0
        roll = 0
        
        return {'pitch': pitch, 'yaw': yaw, 'roll': roll}
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics"""
        return self.perf_monitor.get_metrics()
    
    def release(self) -> None:
        """Release resources"""
        if self.face_mesh is not None:
            self.face_mesh.close()
