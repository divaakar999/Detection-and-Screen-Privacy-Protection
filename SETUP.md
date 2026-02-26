# SETUP GUIDE

## Quick Start Guide

This guide will help you get started with the Shoulder Surfing Detection system.

### Prerequisites
- Python 3.8+
- Webcam
- 4GB+ RAM
- Windows/Linux/macOS

### Installation (5 minutes)

1. **Clone the project**
   ```bash
   cd "Detection and Screen Privacy Protection"
   ```

2. **Create Virtual Environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Installation**
   ```bash
   python -c "import cv2, mediapipe, PyQt5; print('✓ All dependencies installed')"
   ```

### Running the System

#### Option 1: CLI Mode (Recommended for First-Time)
```bash
python run.py --debug
```

#### Option 2: GUI Mode (User-Friendly)
```bash
python run.py --gui
```

#### Option 3: Headless Mode (Testing)
```bash
python run.py --headless --duration 60
```

### What You'll See

When running:
1. **Console Output**: Real-time detection logs
2. **Face Count**: Number of faces detected
3. **Alert Status**: THREAT DETECTED when multiple people in frame
4. **FPS**: Processing speed (target: 25-30)

### First Test Steps

1. **Solo Test** (No one else visible)
   ```
   Expected: Faces: 1, Alert: OFF
   ```

2. **Threat Test** (Have another person enter frame)
   ```
   Expected: Faces: 2, Alert: ON
   Screen should blur
   ```

3. **Recovery Test** (Person leaves)
   ```
   Expected: Alert: OFF, Blur removed
   ```

### Configure Settings

Edit `config/settings.py` for:
- Detection sensitivity
- Blur intensity
- Feature toggles
- Logging levels

### Chrome Extension Setup

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `chrome-extension` folder
5. Test with Google Meet

### Troubleshooting

**Camera not found?**
```bash
python run.py --camera 1  # Try camera index 1
```

**High latency?**
- Reduce resolution in settings
- Close other applications
- Enable CUDA if available

**False positives?**
- Increase `FACE_DETECTION_CONFIDENCE` to 0.7
- Increase `MIN_FACES_FOR_ALERT` to 3

### Next Steps

1. **Explore the Code**
   - `src/main.py` - Core system
   - `src/face_detector.py` - Detection logic
   - `src/gaze_estimator.py` - Gaze tracking

2. **Run Tests**
   ```bash
   python -m pytest tests/ -v
   ```

3. **Export Logs**
   ```bash
   python run.py --export report.json
   ```

4. **Enable GPU** (Optional)
   - Install CUDA/cuDNN
   - Set `USE_GPU = True` in settings

### Performance Tips

- Use GPU for faster processing
- Reduce frame resolution for higher FPS
- Enable frame skipping for latency reduction
- Close unnecessary applications

### Support

Check README.md for:
- Full API documentation
- Configuration options
- Performance benchmarks
- Advanced features

---
Happy detecting! 🔒
