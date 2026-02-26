"""
Utility functions for the shoulder surfing detection system
"""
import cv2
import numpy as np
import time
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import threading


class PerformanceMonitor:
    """Monitor system performance and latency"""
    
    def __init__(self, window_size: int = 30):
        self.frame_times = []
        self.detection_times = []
        self.window_size = window_size
        self.lock = threading.Lock()
    
    def record_frame_time(self, elapsed_ms: float) -> None:
        """Record frame processing time"""
        with self.lock:
            self.frame_times.append(elapsed_ms)
            if len(self.frame_times) > self.window_size:
                self.frame_times.pop(0)
    
    def record_detection_time(self, elapsed_ms: float) -> None:
        """Record detection processing time"""
        with self.lock:
            self.detection_times.append(elapsed_ms)
            if len(self.detection_times) > self.window_size:
                self.detection_times.pop(0)
    
    def get_avg_frame_time(self) -> float:
        """Get average frame processing time"""
        with self.lock:
            return np.mean(self.frame_times) if self.frame_times else 0.0
    
    def get_avg_detection_time(self) -> float:
        """Get average detection time"""
        with self.lock:
            return np.mean(self.detection_times) if self.detection_times else 0.0
    
    def get_fps(self) -> float:
        """Calculate FPS based on frame times"""
        avg_time = self.get_avg_frame_time()
        return 1000 / avg_time if avg_time > 0 else 0.0
    
    def get_metrics(self) -> Dict[str, float]:
        """Get all performance metrics"""
        return {
            'avg_frame_time_ms': self.get_avg_frame_time(),
            'avg_detection_time_ms': self.get_avg_detection_time(),
            'fps': self.get_fps()
        }


class ImageProcessor:
    """Image processing utilities"""
    
    @staticmethod
    def blur_image(image: np.ndarray, kernel_size: int = 25) -> np.ndarray:
        """
        Apply Gaussian blur to image
        
        Args:
            image: Input image
            kernel_size: Blur kernel size (must be odd)
        
        Returns:
            Blurred image
        """
        if kernel_size % 2 == 0:
            kernel_size += 1
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    
    @staticmethod
    def apply_blur_overlay(image: np.ndarray, blur_intensity: int = 25, 
                          opacity: float = 0.85) -> np.ndarray:
        """
        Apply semi-transparent blur overlay to image
        
        Args:
            image: Input image
            blur_intensity: Blur kernel size
            opacity: Overlay opacity (0-1)
        
        Returns:
            Image with blur overlay
        """
        blurred = ImageProcessor.blur_image(image, blur_intensity)
        result = cv2.addWeighted(blurred, opacity, image, 1 - opacity, 0)
        return result
    
    @staticmethod
    def pixelate_image(image: np.ndarray, pixel_size: int = 10) -> np.ndarray:
        """Apply pixelation effect to image"""
        h, w = image.shape[:2]
        temp = cv2.resize(image, (w // pixel_size, h // pixel_size))
        return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
    
    @staticmethod
    def resize_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
        """Resize image to specified dimensions"""
        return cv2.resize(image, (width, height))
    
    @staticmethod
    def draw_bounding_box(image: np.ndarray, face_bbox: Tuple[int, int, int, int],
                         confidence: float = 1.0, color: Tuple[int, int, int] = (0, 255, 0),
                         thickness: int = 2) -> np.ndarray:
        """
        Draw bounding box on image
        
        Args:
            image: Input image
            face_bbox: (x, y, width, height)
            confidence: Detection confidence
            color: Box color (BGR)
            thickness: Box line thickness
        
        Returns:
            Image with drawn box
        """
        x, y, w, h = face_bbox
        result = image.copy()
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        
        # Draw confidence score
        label = f"Conf: {confidence:.2f}"
        cv2.putText(result, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                   0.5, color, 2)
        
        return result
    
    @staticmethod
    def draw_gaze_indicator(image: np.ndarray, face_center: Tuple[int, int],
                           gaze_vector: Tuple[float, float],
                           length: int = 50, color: Tuple[int, int, int] = (255, 0, 0)) -> np.ndarray:
        """Draw gaze direction indicator"""
        result = image.copy()
        x, y = face_center
        gx, gy = gaze_vector
        
        # Normalize and scale
        magnitude = np.sqrt(gx**2 + gy**2)
        if magnitude > 0:
            gx, gy = (gx / magnitude * length, gy / magnitude * length)
        
        end_x = int(x + gx)
        end_y = int(y + gy)
        
        cv2.arrowedLine(result, (x, y), (end_x, end_y), color, 2, tipLength=0.3)
        return result


class TimeCounter:
    """Measure elapsed time"""
    
    def __init__(self):
        self.start_time = None
    
    def start(self) -> None:
        """Start timer"""
        self.start_time = time.perf_counter()
    
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds"""
        if self.start_time is None:
            return 0.0
        return (time.perf_counter() - self.start_time) * 1000
    
    def elapsed_sec(self) -> float:
        """Get elapsed time in seconds"""
        return self.elapsed_ms() / 1000


class WebcamManager:
    """Manage webcam capture and properties"""
    
    def __init__(self, camera_id: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.is_open = False
    
    def open(self) -> bool:
        """Open webcam"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Test if camera is available
            ret, _ = self.cap.read()
            if ret:
                self.is_open = True
                return True
            else:
                self.close()
                return False
        except Exception as e:
            print(f"Error opening camera: {e}")
            return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read frame from webcam"""
        if not self.is_open or self.cap is None:
            return False, None
        
        ret, frame = self.cap.read()
        return ret, frame
    
    def close(self) -> None:
        """Close webcam"""
        if self.cap is not None:
            self.cap.release()
            self.is_open = False
    
    def get_properties(self) -> Dict[str, Any]:
        """Get camera properties"""
        if not self.is_open or self.cap is None:
            return {}
        
        return {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'brightness': self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': self.cap.get(cv2.CAP_PROP_CONTRAST)
        }


def get_timestamp() -> str:
    """Get current timestamp as string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def ensure_dir_exists(path: Path) -> None:
    """Ensure directory exists, create if not"""
    path.mkdir(parents=True, exist_ok=True)
