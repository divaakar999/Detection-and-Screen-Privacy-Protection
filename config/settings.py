"""
Configuration settings for the Shoulder Surfing Detection System
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Detection Thresholds
FACE_DETECTION_CONFIDENCE = 0.5
GAZE_THRESHOLD = 0.4  # Threshold for detecting gaze away from screen
MIN_FACES_FOR_ALERT = 2  # Number of faces to trigger alert

# Performance Settings
DETECTION_LATENCY_MS = 200  # Max allowed latency
FRAME_SKIP = 1  # Process every nth frame (for performance)
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480
WEBCAM_FPS = 30

# Screen Blur Settings
BLUR_INTENSITY = 25  # Blur kernel size
BLUR_OVERLAY_OPACITY = 0.85
BLUR_TRANSITION_SPEED = 100  # ms to transition blur

# Model Settings
FACE_DETECTION_MODEL = "mobilenetv2"  # Options: mobilenetv2, ssd, yolov3
MEDIAPIPE_MODEL_PATH = "face_landmarker_lite.task"
MAX_FACES = 5  # Maximum faces to track

# Logging Settings
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "detection_events.log"
LOG_LEVEL = "INFO"
LOG_ENABLE_FILE = True
LOG_ENABLE_CONSOLE = True
LOG_MAX_FILE_SIZE = 10485760  # 10MB

# Chrome Extension Settings
EXTENSION_PORT = 8000
EXTENSION_DEBUG = False
CHROME_EXTENSION_ID = "your-extension-id-here"

# System Settings
USE_GPU = True  # Use GPU if available
SYSTEM_HOTKEY = "F12"  # Hotkey to toggle overlay
AUTO_START = False
MINIMIZE_TO_TRAY = True

# Directory Paths
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"

# Feature Flags
ENABLE_GAZE_ESTIMATION = True
ENABLE_HEAD_POSE = True
ENABLE_CHROME_EXTENSION = True
ENABLE_EVENT_LOGGING = True
ENABLE_PERFORMANCE_METRICS = True

# Privacy Settings
BLUR_SCREEN_ON_DETECTION = True
LOG_DETECTIONS = True
RETENTION_DAYS = 30  # How many days to keep logs

# API Settings
GOOGLE_MEET_INTEGRATION = True
SOCKET_IO_NAMESPACE = "/shoulder-surfing"
