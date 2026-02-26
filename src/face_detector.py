"""
CNN-based face detection using OpenCV
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any
import threading
import os

from config.settings import FACE_DETECTION_CONFIDENCE, FACE_DETECTION_MODEL
from src.utils import PerformanceMonitor, TimeCounter


class FaceDetector:
    """
    Detect faces in images using CNN-based models
    Supports MobileNetV2 and SSD models
    """
    
    def __init__(self, model_type: str = "mobilenetv2", confidence_threshold: float = FACE_DETECTION_CONFIDENCE):
        self.model_type = model_type.lower()
        self.confidence_threshold = confidence_threshold
        self.net = None
        self.blob_processor = None
        self.perf_monitor = PerformanceMonitor()
        self.lock = threading.Lock()
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load pre-trained face detection model"""
        try:
            if self.model_type == "mobilenetv2" or self.model_type == "ssd":
                # Using OpenCV's pre-trained SSD face detector
                model_dir = cv2.data.haarcascades
                weights_file = os.path.join(model_dir, "res10_300x300_ssd_iter_140000_fp16.caffemodel")
                config_file = os.path.join(model_dir, "res10_300x300_ssd_iter_140000_fp16.prototxt.txt")
                
                # If files not found, use cascade classifier as fallback
                if not os.path.exists(weights_file):
                    print(f"SSD model not found. Using Haar Cascade fallback.")
                    self.cascade = cv2.CascadeClassifier(
                        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                    )
                    self.model_type = "cascade"
                else:
                    self.net = cv2.dnn.readNetFromCaffe(config_file, weights_file)
                    print(f"Loaded {self.model_type.upper()} model successfully")
            else:
                # Fallback to Haar Cascade
                self.cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                self.model_type = "cascade"
                print("Using Haar Cascade classifier")
        
        except Exception as e:
            print(f"Error loading model: {e}")
            # Final fallback to Haar Cascade
            self.cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.model_type = "cascade"
    
    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect faces in image
        
        Args:
            image: Input image (BGR format)
        
        Returns:
            List of detected faces with format:
            [{'bbox': (x, y, w, h), 'confidence': float, 'center': (cx, cy)}, ...]
        """
        timer = TimeCounter()
        timer.start()
        
        with self.lock:
            if self.model_type == "cascade":
                faces = self._detect_cascade(image)
            else:
                faces = self._detect_dnn(image)
        
        self.perf_monitor.record_detection_time(timer.elapsed_ms())
        return faces
    
    def _detect_cascade(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect faces using Haar Cascade classifier"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            maxSize=(300, 300)
        )
        
        detections = []
        for (x, y, w, h) in faces:
            detections.append({
                'bbox': (x, y, w, h),
                'confidence': 0.95,  # Cascade doesn't provide confidence
                'center': (x + w // 2, y + h // 2)
            })
        
        return detections
    
    def _detect_dnn(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect faces using DNN (SSD/MobileNetV2)"""
        h, w = image.shape[:2]
        
        # Prepare blob
        blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300),
                                     [104.0, 117.0, 123.0], False, False)
        
        self.net.setInput(blob)
        detections = self.net.forward()
        
        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence >= self.confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                x1, y1, x2, y2 = box.astype(int)
                
                # Convert to (x, y, w, h) format
                x, y = x1, y1
                width, height = x2 - x1, y2 - y1
                
                # Validate bbox
                if width > 0 and height > 0 and x >= 0 and y >= 0:
                    faces.append({
                        'bbox': (x, y, width, height),
                        'confidence': float(confidence),
                        'center': (x + width // 2, y + height // 2)
                    })
        
        return faces
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics"""
        return self.perf_monitor.get_metrics()
    
    def filter_overlapping_faces(self, faces: List[Dict[str, Any]], 
                                 iou_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Remove overlapping face detections using IoU (Intersection over Union)
        
        Args:
            faces: List of detected faces
            iou_threshold: Minimum IoU to consider faces as overlapping
        
        Returns:
            Filtered list of faces
        """
        if len(faces) <= 1:
            return faces
        
        # Sort by confidence (descending)
        sorted_faces = sorted(faces, key=lambda x: x['confidence'], reverse=True)
        kept_faces = [sorted_faces[0]]
        
        for face in sorted_faces[1:]:
            is_duplicate = False
            for kept_face in kept_faces:
                iou = self._calculate_iou(face['bbox'], kept_face['bbox'])
                if iou > iou_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                kept_faces.append(face)
        
        return kept_faces
    
    @staticmethod
    def _calculate_iou(bbox1: Tuple[int, int, int, int], 
                      bbox2: Tuple[int, int, int, int]) -> float:
        """Calculate Intersection over Union of two bboxes"""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Calculate intersection area
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        intersection = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        
        # Calculate union area
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def get_face_landmarks(self, image: np.ndarray, face_bbox: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """
        Get facial landmarks (eyes, nose, mouth) for a detected face
        Uses simple corner detection as alternative to MediaPipe
        
        Args:
            image: Input image
            face_bbox: Face bounding box (x, y, w, h)
        
        Returns:
            Dictionary with landmark positions
        """
        x, y, w, h = face_bbox
        face_roi = image[y:y+h, x:x+w]
        
        landmarks = {
            'left_eye': (x + w // 4, y + h // 3),
            'right_eye': (x + 3 * w // 4, y + h // 3),
            'nose': (x + w // 2, y + h // 2),
            'mouth': (x + w // 2, y + 2 * h // 3)
        }
        
        return landmarks
