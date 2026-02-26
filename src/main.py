"""
Main application for shoulder surfing detection system
"""
import cv2
import sys
import threading
import time
from typing import Optional, Dict, Any
from pathlib import Path

from config.settings import (
    DETECTION_LATENCY_MS, FACE_DETECTION_CONFIDENCE, MIN_FACES_FOR_ALERT,
    WEBCAM_WIDTH, WEBCAM_HEIGHT, WEBCAM_FPS, FRAME_SKIP,
    ENABLE_GAZE_ESTIMATION, BLUR_SCREEN_ON_DETECTION, LOG_ENABLE_FILE,
    ENABLE_PERFORMANCE_METRICS
)

from src.face_detector import FaceDetector
from src.gaze_estimator import GazeEstimator
from src.screen_blur import ScreenBlurManager
from src.event_logger import logger
from src.utils import (
    WebcamManager, PerformanceMonitor, ImageProcessor,
    TimeCounter, ensure_dir_exists
)


class ShoulderSurfingDetectionSystem:
    """
    Main detection system coordinating face detection, gaze estimation,
    and screen blur
    """
    
    def __init__(self, use_gpu: bool = True, debug: bool = False):
        self.debug = debug
        self.is_running = False
        self.is_paused = False
        self.lock = threading.Lock()
        
        # Initialize components
        self.face_detector = FaceDetector(confidence_threshold=FACE_DETECTION_CONFIDENCE)
        self.gaze_estimator = GazeEstimator() if ENABLE_GAZE_ESTIMATION else None
        self.screen_blur_manager = ScreenBlurManager()
        self.webcam_manager = WebcamManager(
            width=WEBCAM_WIDTH,
            height=WEBCAM_HEIGHT,
            fps=WEBCAM_FPS
        )
        
        # Performance monitoring
        self.perf_monitor = PerformanceMonitor()
        
        # State tracking
        self.current_face_count = 0
        self.current_alert_state = False
        self.frame_counter = 0
        self.last_blur_time = 0
        self.consecutive_alerts = 0
        
        # Configuration
        self.min_faces_for_alert = MIN_FACES_FOR_ALERT
        self.gaze_enabled = ENABLE_GAZE_ESTIMATION
        self.blur_enabled = BLUR_SCREEN_ON_DETECTION
        
        # Ensure log directory exists
        ensure_dir_exists(Path("logs"))
        
        logger.logger.info("ShoulderSurfingDetectionSystem initialized")
    
    def start(self) -> bool:
        """
        Start the detection system
        
        Returns:
            True if successfully started, False otherwise
        """
        with self.lock:
            if self.is_running:
                logger.logger.warning("System already running")
                return False
            
            # Open webcam
            if not self.webcam_manager.open():
                logger.logger.error("Failed to open webcam")
                return False
            
            self.is_running = True
            logger.logger.info("Detection system started")
            
            # Log system initialization
            logger.log_detection('system_start', {
                'timestamp': time.time(),
                'camera_properties': self.webcam_manager.get_properties()
            })
            
            return True
    
    def stop(self) -> None:
        """Stop the detection system"""
        with self.lock:
            if not self.is_running:
                return
            
            self.is_running = False
            self.is_paused = False
            
            # Clean up resources
            self.webcam_manager.close()
            if self.gaze_estimator:
                self.gaze_estimator.release()
            
            self.screen_blur_manager.disable_blur()
            
            logger.log_detection('system_stop', {
                'timestamp': time.time(),
                'session_summary': logger.get_detection_summary()
            })
            
            logger.logger.info("Detection system stopped")
    
    def pause(self) -> None:
        """Pause detection (but keep system running)"""
        with self.lock:
            self.is_paused = True
            logger.logger.info("Detection paused")
    
    def resume(self) -> None:
        """Resume detection"""
        with self.lock:
            self.is_paused = False
            logger.logger.info("Detection resumed")
    
    def process_frame(self) -> Dict[str, Any]:
        """
        Process a single frame from webcam
        
        Returns:
            Dictionary with detection results and frame
        """
        timer = TimeCounter()
        timer.start()
        
        if not self.is_running:
            return {'success': False, 'error': 'System not running'}
        
        # Read frame from webcam
        ret, frame = self.webcam_manager.read_frame()
        if not ret:
            return {'success': False, 'error': 'Failed to read frame'}
        
        # Skip frames for performance
        self.frame_counter += 1
        if self.frame_counter % FRAME_SKIP != 0:
            return {'success': False, 'skipped': True}
        
        # Detect faces
        faces = self.face_detector.detect_faces(frame)
        self.current_face_count = len(faces)
        
        # Filter overlapping detections
        faces = self.face_detector.filter_overlapping_faces(faces)
        
        # Estimate gaze if enabled
        gaze_results = None
        if self.gaze_enabled and self.gaze_estimator:
            gaze_results = self.gaze_estimator.estimate_gaze(frame)
        
        # Determine alert state
        should_alert = self._should_trigger_alert(faces, gaze_results)
        
        # Update blur if enabled
        if self.blur_enabled:
            self._update_blur_state(should_alert)
        
        # Log detection if alert
        if should_alert and not self.is_paused:
            logger.log_detection('alert', {
                'face_count': len(faces),
                'gaze_threat': gaze_results is not None,
                'timestamp': time.time()
            })
        
        # Record frame processing time
        frame_time = timer.elapsed_ms()
        self.perf_monitor.record_frame_time(frame_time)
        
        return {
            'success': True,
            'frame': frame,
            'faces': faces,
            'gaze_results': gaze_results,
            'alert_state': should_alert,
            'face_count': len(faces),
            'processing_time_ms': frame_time
        }
    
    def _should_trigger_alert(self, faces: list, gaze_results: Optional[list]) -> bool:
        """
        Determine if alert should be triggered based on faces and gaze
        
        Rules:
        - Alert if 2+ faces detected
        - Alert if gaze is away from screen
        """
        if self.is_paused:
            return False
        
        # Rule 1: Multiple faces detected
        if len(faces) >= self.min_faces_for_alert:
            self.consecutive_alerts += 1
            return True
        else:
            self.consecutive_alerts = 0
        
        # Rule 2: Check gaze direction
        if gaze_results and self.gaze_enabled:
            for gaze in gaze_results:
                if not gaze.is_looking_at_screen and gaze.confidence > 0.6:
                    return True
        
        return False
    
    def _update_blur_state(self, should_blur: bool) -> None:
        """Update screen blur based on alert state"""
        current_time = time.time()
        
        if should_blur:
            if not self.current_alert_state:
                self.screen_blur_manager.enable_blur()
                self.current_alert_state = True
                self.last_blur_time = current_time
                logger.logger.warning("SCREEN BLUR ACTIVATED - Threat detected!")
        else:
            if self.current_alert_state:
                self.screen_blur_manager.disable_blur()
                self.current_alert_state = False
                logger.logger.info("Screen blur deactivated")
    
    def run(self, duration: Optional[float] = None) -> None:
        """
        Run detection loop
        
        Args:
            duration: Optional duration in seconds to run (None = indefinite)
        """
        if not self.start():
            logger.logger.error("Failed to start system")
            return
        
        start_time = time.time()
        
        try:
            while self.is_running:
                # Check duration
                if duration and (time.time() - start_time) > duration:
                    break
                
                # Process frame
                result = self.process_frame()
                
                # Debug output
                if self.debug and result.get('success'):
                    logger.logger.debug(
                        f"Faces: {result['face_count']}, "
                        f"Alert: {result['alert_state']}, "
                        f"Time: {result['processing_time_ms']:.2f}ms"
                    )
                
                # Check latency
                if result.get('processing_time_ms', 0) > DETECTION_LATENCY_MS:
                    logger.logger.warning(
                        f"High latency detected: {result['processing_time_ms']:.2f}ms"
                    )
                
                # Small delay to prevent busy waiting
                time.sleep(0.001)
        
        except KeyboardInterrupt:
            logger.logger.info("System interrupted by user")
        except Exception as e:
            logger.logger.error(f"Error in detection loop: {e}", exc_info=True)
        finally:
            self.stop()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        return {
            'performance': self.perf_monitor.get_metrics(),
            'face_detection': self.face_detector.get_performance_metrics(),
            'gaze_estimation': self.gaze_estimator.get_performance_metrics() if self.gaze_estimator else None,
            'detection_summary': logger.get_detection_summary(),
            'blur_active': self.current_alert_state,
            'frame_count': self.frame_counter
        }
    
    def export_report(self, filename: str = None) -> Path:
        """Export detection report"""
        return logger.export_logs(filename)
