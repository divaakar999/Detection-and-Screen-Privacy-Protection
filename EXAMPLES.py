"""
Example usage of the Shoulder Surfing Detection System
"""

# Example 1: Basic Usage
from src.main import ShoulderSurfingDetectionSystem

# Create system instance
system = ShoulderSurfingDetectionSystem(debug=True)

# Start detection
system.start()

# Process frames continuously
while system.is_running:
    result = system.process_frame()
    if result.get('success'):
        print(f"Faces: {result['face_count']}, Alert: {result['alert_state']}")

# Stop system
system.stop()


# Example 2: With Duration
system = ShoulderSurfingDetectionSystem()
system.run(duration=60)  # Run for 60 seconds


# Example 3: Face Detection Only
from src.face_detector import FaceDetector
import cv2

detector = FaceDetector()
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if ret:
        faces = detector.detect_faces(frame)
        print(f"Detected {len(faces)} faces")
        
        # Draw bounding boxes
        for face in faces:
            x, y, w, h = face['bbox']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        cv2.imshow('Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()


# Example 4: Gaze Estimation Only
from src.gaze_estimator import GazeEstimator

estimator = GazeEstimator()
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if ret:
        gaze_results = estimator.estimate_gaze(frame)
        
        for gaze in gaze_results:
            print(f"Gaze: {gaze.gaze_direction}, Looking at screen: {gaze.is_looking_at_screen}")
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
estimator.release()
cv2.destroyAllWindows()


# Example 5: Custom Configuration
from config.settings import *

# Modify settings
custom_settings = {
    'FACE_DETECTION_CONFIDENCE': 0.7,
    'MIN_FACES_FOR_ALERT': 3,
    'BLUR_INTENSITY': 30,
    'BLUR_OVERLAY_OPACITY': 0.95
}

# Create and run with custom config
system = ShoulderSurfingDetectionSystem(debug=True)
system.min_faces_for_alert = custom_settings['MIN_FACES_FOR_ALERT']
system.screen_blur_manager.set_blur_intensity(custom_settings['BLUR_INTENSITY'])

system.run(duration=120)


# Example 6: Metrics and Logging
from src.event_logger import logger

system = ShoulderSurfingDetectionSystem()
system.start()

# Process some frames
for i in range(100):
    system.process_frame()

# Get metrics
metrics = system.get_metrics()
print(f"FPS: {metrics['performance']['fps']:.1f}")
print(f"Processing Time: {metrics['performance']['avg_frame_time_ms']:.2f}ms")
print(f"Total Detections: {metrics['detection_summary']['total_detections']}")
print(f"Total Alerts: {metrics['detection_summary']['total_alerts']}")

# Export logs
export_path = system.export_report('my_report.json')
print(f"Report exported to: {export_path}")

system.stop()


# Example 7: GUI Mode
from src.gui import launch_gui

system = ShoulderSurfingDetectionSystem()
launch_gui(system)


# Example 8: Pause/Resume
system = ShoulderSurfingDetectionSystem()
system.start()

# Run for 10 seconds
for i in range(300):
    system.process_frame()

# Pause
system.pause()
print("Detection paused")

# Resume after some time
system.resume()
print("Detection resumed")

system.stop()


# Example 9: Testing Mode (Headless)
import time

system = ShoulderSurfingDetectionSystem()
system.blur_enabled = False  # Disable blur for testing
system.start()

start_time = time.time()
frame_count = 0

while (time.time() - start_time) < 30:  # Run for 30 seconds
    result = system.process_frame()
    if result.get('success'):
        frame_count += 1

system.stop()

# Print results
metrics = system.get_metrics()
elapsed = time.time() - start_time
average_fps = metrics['performance']['fps']

print(f"\n=== Test Results ===")
print(f"Duration: {elapsed:.1f}s")
print(f"Frames: {frame_count}")
print(f"Average FPS: {average_fps:.1f f}")
print(f"Latency: {metrics['performance']['avg_frame_time_ms']:.2f}ms")


# Example 10: Chrome Extension Server
from src.server import app, socketio

if __name__ == '__main__':
    # Start Flask server
    socketio.run(app, host='0.0.0.0', port=8000, debug=False)
