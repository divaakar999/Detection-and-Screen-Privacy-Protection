# QUICK REFERENCE GUIDE

## Command Cheat Sheet

### Basic Usage
```bash
# Run with default settings
python run.py

# Run with GUI
python run.py --gui

# Run in debug mode
python run.py --debug

# Run for specific duration (seconds)
python run.py --duration 300
```

### Advanced Options
```bash
# Run without screen overlay
python run.py --headless

# Use specific camera
python run.py --camera 1

# Set logging level
python run.py --log-level DEBUG

# Export logs
python run.py --export report.json

# Show help
python run.py --help
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_face_detector.py -v

# Generate coverage report
pytest --cov=src tests/

# Run with output
python -m pytest tests/ -s
```

### Configuration
```bash
# Edit settings
nano config/settings.py          # Linux/Mac
notepad config/settings.py       # Windows

# Edit environment
nano .env
```

---

## Configuration Quick Tips

### Improve Detection Accuracy
```python
# config/settings.py
FACE_DETECTION_CONFIDENCE = 0.7  # Increase threshold
MIN_FACES_FOR_ALERT = 3          # Require more faces
```

### Reduce Latency
```python
FRAME_SKIP = 2                   # Process fewer frames
WEBCAM_WIDTH = 480               # Lower resolution
WEBCAM_HEIGHT = 360
DETECTION_LATENCY_MS = 100       # Stricter target
```

### Increase Performance
```python
USE_GPU = True                   # Enable GPU acceleration
FRAME_SKIP = 3                   # Skip more frames
ENABLE_GAZE_ESTIMATION = False   # Disable if not needed
```

### Better Blur Effect
```python
BLUR_INTENSITY = 30              # Stronger blur
BLUR_OVERLAY_OPACITY = 0.95      # More opaque
BLUR_TRANSITION_SPEED = 50       # Faster transition
```

---

## Common Issues & Solutions

### Issue: High CPU Usage
**Solution:**
```python
FRAME_SKIP = 2  # Skip alternate frames
WEBCAM_WIDTH = 480
WEBCAM_HEIGHT = 360
```

### Issue: False Positives
**Solution:**
```python
FACE_DETECTION_CONFIDENCE = 0.7
MIN_FACES_FOR_ALERT = 3
GAZE_THRESHOLD = 0.6
```

### Issue: Camera Not Working
**Solution:**
```bash
# Try different camera index
python run.py --camera 0
python run.py --camera 1

# Check OpenCV
python -c "import cv2; print(cv2.__version__)"
```

### Issue: MediaPipe Errors
**Solution:**
```bash
# Reinstall MediaPipe
pip install --upgrade mediapipe --force-reinstall
```

---

## Performance Monitoring

### During Execution
- **FPS**: Should be 25-30
- **Alert**: Should respond within 100ms
- **Memory**: Monitor with Task Manager/top
- **CPU**: Should be 15-25%

### Export Metrics
```bash
python run.py --export metrics.json
```

### View Logs
```bash
# Windows
type logs\detection_events.jsonl

# Linux/Mac
cat logs/detection_events.jsonl

# Or use GUI to view in Logs tab
python run.py --gui
```

---

## Development Tips

### Debug Mode
```bash
# Enable with extra logging
python run.py --debug

# View all messages
python run.py --debug --log-level DEBUG
```

### Headless Testing
```bash
# Test without screen blur UI
python run.py --headless --duration 30

# Perfect for CI/CD pipelines
```

### Individual Component Testing
```python
# Test face detector
from src.face_detector import FaceDetector
detector = FaceDetector()
# ... test code

# Test gaze estimator
from src.gaze_estimator import GazeEstimator
estimator = GazeEstimator()
# ... test code

# Test other components separately
```

---

## Chrome Extension Setup

### Installation
1. Open `chrome://extensions/`
2. Toggle "Developer mode" ON
3. Click "Load unpacked"
4. Select `chrome-extension` folder

### Troubleshooting Extension
- Check popup.js for errors (right-click → Inspect)
- Verify background.js in extension details
- Check connection to localhost:8000
- Ensure content.js runs on meet.google.com

---

## Performance Baseline

### Expected Metrics
- **FPS**: 25-30 (640x480)
- **Latency**: 50-100ms
- **Memory**: 200-300MB
- **CPU**: 15-25%

### If Different
- Check CPU in Task Manager
- Verify GPU acceleration enabled
- Reduce resolution in settings
- Check for background processes

---

## File Locations

```
Logs:       logs/detection_events.jsonl
Config:     config/settings.py
Exported:   logs/detection_logs_YYYYMMDD_HHMMSS.json
Extension:  chrome-extension/
Tests:      tests/
```

---

## Keyboard Shortcuts

### During Execution
- **Ctrl+C** - Graceful shutdown
- **F12** - Toggle blur (configurable)

### GUI Mode
- Close window to stop
- Settings tab to configure
- Metrics tab for performance

---

## Best Practices

1. **Resolution**: Start with 640x480, adjust if needed
2. **Lighting**: Ensure good lighting for face detection
3. **Distance**: Keep camera 1-3 meters away
4. **Angles**: Webcam at eye level for best gaze detection
5. **Logging**: Enable for production, disable for testing

---

## Support Resources

- **Full Docs**: See README.md
- **Setup Guide**: See SETUP.md
- **Project Info**: See PROJECT_SUMMARY.md
- **Code Comments**: Check inline documentation
- **Test Examples**: See tests/ directory

---

## Version Info

**Current Version**: 1.0.0
**Python**: 3.8+
**Last Updated**: February 2024

---

*For detailed documentation, see README.md*
