# 🌐 Web App - Shoulder Surfing Detection

A modern web-based interface for real-time shoulder surfing detection and screen privacy protection.

## 🚀 Quick Start

### 1. Start the Web Server

```bash
python web_server.py
```

Or using the main entry point:

```bash
python run.py --web
```

### 2. Open in Browser

Visit: **http://localhost:5000**

## 🎯 Features

### Real-Time Detection
- **Live Video Stream**: Direct webcam feed processed in real-time
- **Face Detection**: Identifies faces in the video frame
- **Threat Detection**: Alerts when multiple faces detected
- **Gaze Analysis**: Monitors viewing direction

### Metrics & Monitoring
- **Face Count**: Real-time count of detected faces
- **FPS**: Frames per second processing rate
- **Latency**: Frame processing latency in milliseconds
- **Threat Status**: Current threat alert status

### Alert System
- **Visual Alerts**: Large on-screen notifications when threat detected
- **Audio Alerts**: Configurable beep sound
- **Alert History**: Keeps track of all detected threats
- **Timestamp Logging**: Each event logged with precise timestamp

### Configuration
- **Enable/Disable Blur**: Toggle screen blur protection
- **Enable/Disable Gaze**: Toggle gaze analysis
- **Sensitivity Control**: Adjust threat detection sensitivity (1-10)
- **Alert Volume**: Control audio alert volume (0-100%)

### Data Export
- **Export Metrics**: Download session data as JSON
- **System Logs**: Real-time system activity log
- **Alert History**: Track all detected threats

## 🎮 Usage

### Starting the Webcam
1. Click **"▶ Start Webcam"** button
2. Allow browser to access your camera
3. Video feed will appear in the video canvas
4. System will start monitoring

### Viewing Metrics
- **Faces Detected**: Number of faces in current frame
- **FPS**: Processing frames per second
- **Latency**: Time to process each frame
- **Threat Status**: Safe or Alert status

### Configuring Settings
1. **Screen Blur**: Toggle to enable/disable blur on threats
2. **Gaze Analysis**: Toggle to enable/disable viewing direction analysis
3. **Sensitivity**: Drag slider to adjust detection sensitivity
4. **Alert Volume**: Drag slider to adjust alert sound volume

### Monitoring Alerts
1. **Alert Section**: Shows threat information when detected
2. **Alert History**: Scroll through all detected threats
3. **Clear History**: Remove all alert history

### Viewing Logs
- Real-time system logs showing all events
- Timestamps automatically included
- Clear logs button to reset history

### Exporting Data
1. Click **"📥 Export Metrics"** button
2. JSON file automatically downloads with:
   - Current metrics
   - Configuration settings
   - Alert history
   - System logs

## 📊 API Endpoints

### GET Endpoints

- `GET /api/health` - Server health check
- `GET /api/status` - Current system status
- `GET /api/metrics` - Detailed metrics
- `GET /api/config` - Current configuration

### POST Endpoints

- `POST /api/start` - Start detection system
- `POST /api/stop` - Stop detection system

### PUT Endpoints

- `PUT /api/config` - Update configuration
  ```json
  {
    "blur_enabled": true,
    "gaze_enabled": true,
    "sensitivity": 5
  }
  ```

## 🔌 WebSocket Events

### Client → Server

- `process_frame` - Send video frame for processing
- `update_config` - Update configuration settings

### Server → Client

- `metrics_updated` - Metrics update notification
- `threat_detected` - Threat detected alert
- `config_updated` - Configuration changed notification
- `system_started` - System started notification
- `system_stopped` - System stopped notification
- `connected` - Initial connection confirmation

## 🛠️ Technical Details

### Frontend
- **HTML5**: Modern semantic markup
- **CSS3**: Responsive dark theme styling
- **JavaScript**: Real-time event handling
- **Canvas API**: Video rendering and overlay
- **Web Audio API**: Alert sounds
- **Socket.IO**: Real-time WebSocket communication

### Backend
- **Flask**: Python web framework
- **Flask-CORS**: Cross-origin resource sharing
- **Flask-SocketIO**: WebSocket communication
- **Threading**: Asynchronous event handling

### Compatibility
- **Browsers**: Chrome, Firefox, Safari, Edge
- **OS**: Windows, macOS, Linux
- **Python**: 3.7+

## ⚙️ Configuration

Configuration persists across the session and can be updated via:

1. **Web UI Toggles**: Interactive controls
2. **API Calls**: Programmatic updates
3. **WebSocket**: Real-time configuration

## 📱 Responsive Design

The web app is fully responsive and works on:
- **Desktop**: Full feature set
- **Tablet**: Optimized layout
- **Mobile**: Touch-friendly controls (limited by camera access)

## 🔐 Security & Privacy

- **Local Processing**: All processing done locally, no cloud uploads
- **Secure WebSocket**: Support for WSS (wss://) connections
- **CORS Protected**: Configurable cross-origin policies
- **No Data Storage**: Temporary data only, nothing persisted to disk

## 🐛 Troubleshooting

### Camera Not Working
- Check browser camera permissions
- Try a different browser
- Ensure no other app is using the camera

### No Connection
- Check server is running on port 5000
- Verify localhost:5000 is accessible
- Check browser console for errors

### Performance Issues
- Reduce sensitivity setting
- Lower resolution (check browser settings)
- Close other browser tabs
- Check system resources

### Audio Not Working
- Check browser audio settings
- Verify audio permissions granted
- Adjust alert volume slider

## 📚 Documentation

For more information:
- See `README.md` for system architecture
- See `SETUP.md` for installation
- See `QUICK_REFERENCE.md` for command help

## 🎯 Next Steps

1. **Explore Settings**: Try different sensitivity levels
2. **Test Detection**: Introduce multiple people to frame
3. **Monitor Metrics**: Watch FPS and latency metrics
4. **Export Data**: Try downloading metrics for analysis
5. **Integrate**: Add to your own application via API/WebSocket

---

**Shoulder Surfing Detection System v1.0** | 🔒 Privacy Protection | 🌐 Web-Based
