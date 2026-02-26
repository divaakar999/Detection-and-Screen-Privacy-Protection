"""
Integration tests for the entire system
"""
import unittest
import tempfile
from pathlib import Path
from src.main import ShoulderSurfingDetectionSystem


class TestSystemIntegration(unittest.TestCase):
    """Integration tests for full system"""
    
    def setUp(self):
        """Setup before each test"""
        self.system = ShoulderSurfingDetectionSystem(debug=True)
    
    def tearDown(self):
        """Cleanup after each test"""
        if self.system.is_running:
            self.system.stop()
    
    def test_system_initialization(self):
        """Test system initializes correctly"""
        self.assertIsNotNone(self.system)
        self.assertFalse(self.system.is_running)
        self.assertEqual(self.system.current_face_count, 0)
    
    def test_system_start_stop(self):
        """Test starting and stopping system"""
        # Start system
        result = self.system.start()
        self.assertTrue(result)
        self.assertTrue(self.system.is_running)
        
        # Stop system
        self.system.stop()
        self.assertFalse(self.system.is_running)
    
    def test_pause_resume(self):
        """Test pausing and resuming detection"""
        self.system.start()
        
        # Pause
        self.system.pause()
        self.assertTrue(self.system.is_paused)
        
        # Resume
        self.system.resume()
        self.assertFalse(self.system.is_paused)
        
        self.system.stop()
    
    def test_metrics_export(self):
        """Test exporting metrics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = self.system.export_report(f"{tmpdir}/test_export.json")
            self.assertTrue(Path(export_path).exists())


if __name__ == '__main__':
    unittest.main()
