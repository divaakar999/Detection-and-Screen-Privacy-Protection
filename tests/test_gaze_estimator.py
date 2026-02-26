"""
Unit tests for gaze estimation system
"""
import unittest
import numpy as np
from src.gaze_estimator import GazeEstimator


class TestGazeEstimator(unittest.TestCase):
    """Test gaze estimation functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test fixtures"""
        try:
            cls.estimator = GazeEstimator()
            cls.estimator_available = True
        except Exception as e:
            print(f"MediaPipe not available: {e}")
            cls.estimator_available = False
    
    @unittest.skipUnless(
        unittest.TestLoader().loadTestsFromName('src.gaze_estimator'),
        "MediaPipe not available"
    )
    def test_gaze_direction_classification(self):
        """Test gaze direction classification"""
        test_cases = [
            ((0.1, 0.1), 'center', True),
            ((-0.4, 0.0), 'left', False),
            ((0.4, 0.0), 'right', False),
            ((0.0, 0.4), 'down', False),
        ]
        
        for gaze_vector, expected_dir, expected_screen in test_cases:
            direction, is_screen = GazeEstimator._classify_gaze_direction(gaze_vector)
            self.assertEqual(direction, expected_dir)


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring"""
    
    def test_fps_calculation(self):
        """Test FPS calculation"""
        from src.utils import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Simulate consistent 30ms frame times (33 FPS)
        for _ in range(30):
            monitor.record_frame_time(33.33)
        
        fps = monitor.get_fps()
        
        # FPS should be around 30
        self.assertGreater(fps, 25)
        self.assertLess(fps, 35)


if __name__ == '__main__':
    unittest.main()
