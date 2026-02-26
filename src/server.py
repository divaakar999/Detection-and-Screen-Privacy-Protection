"""
Flask server for Chrome Extension communication
Provides WebSocket API for detection system metrics
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import threading
from datetime import datetime
from typing import Dict, Any, List

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
detection_state = {
    'is_running': False,
    'metrics': {
        'face_count': 0,
        'fps': 0.0,
        'latency': 0,
        'alert_active': False
    },
    'last_alert': None,
    'blur_enabled': True,
    'gaze_enabled': True,
    'connections': []
}


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current detection status"""
    return jsonify(detection_state)


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get detailed metrics"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        **detection_state['metrics']
    })


@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update configuration"""
    data = request.json
    
    if 'blur_enabled' in data:
        detection_state['blur_enabled'] = data['blur_enabled']
    
    if 'gaze_enabled' in data:
        detection_state['gaze_enabled'] = data['gaze_enabled']
    
    # Broadcast to all connected clients
    socketio.emit('config_updated', detection_state, broadcast=True)
    
    return jsonify({'status': 'updated'})


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    detection_state['connections'].append(request.sid)
    emit('connected', {
        'status': 'connected',
        'state': detection_state
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')
    if request.sid in detection_state['connections']:
        detection_state['connections'].remove(request.sid)


@socketio.on('update_metrics')
def handle_metrics_update(data):
    """Receive metrics from detection system"""
    detection_state['metrics'] = data.get('metrics', {})
    
    if data.get('threat_detected'):
        detection_state['last_alert'] = {
            'timestamp': datetime.now().isoformat(),
            'face_count': data.get('face_count', 0)
        }
    
    # Broadcast to all connected clients
    emit('metrics_updated', {
        'metrics': detection_state['metrics'],
        'last_alert': detection_state['last_alert']
    }, broadcast=True)


def update_from_detection_system(system):
    """Called from detection system to update metrics"""
    def _update():
        while system.is_running:
            metrics = system.get_metrics()
            
            socketio.emit('metrics_updated', {
                'metrics': {
                    'face_count': metrics['face_count'],
                    'fps': metrics['performance']['fps'],
                    'latency': metrics['performance']['avg_frame_time_ms'],
                    'alert_active': system.current_alert_state
                }
            }, broadcast=True)
            
            threading.Event().wait(0.5)  # Update every 500ms
    
    threading.Thread(target=_update, daemon=True).start()


# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    print("Starting detection server on http://localhost:8000")
    socketio.run(app, host='0.0.0.0', port=8000, debug=False)
