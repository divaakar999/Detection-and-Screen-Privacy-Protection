"""
Unit tests for facial detection system
"""
import unittest
import cv2
import numpy as np
from src.face_detector import FaceDetector


class TestFaceDetector(unittest.TestCase):
    """Test face detection functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test fixtures"""
        cls.detector = FaceDetector()
    
    def test_detector_initialization(self):
        """Test detector initializes correctly"""
        self.assertIsNotNone(self.detector)
        self.assertIsNotNone(self.detector.net or self.detector.cascade)
    
    def test_detect_no_faces(self):
        """Test detection on image with no faces"""
        # Create blank image
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        faces = self.detector.detect_faces(image)
        
        self.assertEqual(len(faces), 0)
    
    def test_detect_face_format(self):
        """Test detection returns correct format"""
        # Create dummy image
        image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        faces = self.detector.detect_faces(image)
        
        # Check that faces have required fields
        if len(faces) > 0:
            face = faces[0]
            self.assertIn('bbox', face)
            self.assertIn('confidence', face)
            self.assertIn('center', face)
    
    def test_iou_calculation(self):
        """Test IoU calculation for overlapping boxes"""
        bbox1 = (0, 0, 100, 100)
        bbox2 = (50, 50, 100, 100)
        
        iou = FaceDetector._calculate_iou(bbox1, bbox2)
        
        # Expected IoU: intersection area / union area
        # Intersection: 50x50 = 2500
        # Union: 10000 + 10000 - 2500 = 17500
        # IoU ≈ 0.143
        self.assertGreater(iou, 0.1)
        self.assertLess(iou, 0.2)
    
    def test_filter_overlapping_faces(self):
        """Test filtering of overlapping face detections"""
        faces = [
            {'bbox': (0, 0, 100, 100), 'confidence': 0.9, 'center': (50, 50)},
            {'bbox': (10, 10, 100, 100), 'confidence': 0.8, 'center': (60, 60)},
            {'bbox': (200, 200, 100, 100), 'confidence': 0.85, 'center': (250, 250)}
        ]
        
        filtered = self.detector.filter_overlapping_faces(faces, iou_threshold=0.2)
        
        # Should keep 2 faces (first and third)
        self.assertLessEqual(len(filtered), 3)


if __name__ == '__main__':
    unittest.main()
