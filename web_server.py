"""
Web App Server for Shoulder Surfing Detection
Serves the web interface and handles real-time WebSocket communication
"""
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import os
import threading
from datetime import datetime
from pathlib import Path

# Create Flask app
app = Flask(__name__, 
            static_folder=os.path.join(os.path.dirname(__file__), 'web_app'),
            template_folder=os.path.join(os.path.dirname(__file__), 'web_app'))

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

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
    'sensitivity': 5,
    'connections': [],
    'session_start': None,
    'alerts_count': 0
}

# Detection system reference
detection_system = None


# ========== STATIC ROUTES ==========
@app.route('/')
def index():
    """Serve main web app"""
    try:
        return render_template('index.html')
    except:
        # Fallback: serve raw HTML
        with open(os.path.join(os.path.dirname(__file__), 'web_app', 'index.html'), 'r') as f:
            return f.read()


@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files (CSS, JS)"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'web_app', path)
        with open(file_path, 'r') as f:
            if path.endswith('.css'):
                return f.read(), 200, {'Content-Type': 'text/css; charset=utf-8'}
            elif path.endswith('.js'):
                return f.read(), 200, {'Content-Type': 'application/javascript; charset=utf-8'}
        return f.read()
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== API ROUTES ==========
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': (datetime.now() - detection_state['session_start']).total_seconds() if detection_state['session_start'] else 0
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current detection status"""
    return jsonify({
        'running': detection_state['is_running'],
        'metrics': detection_state['metrics'],
        'config': {
            'blur_enabled': detection_state['blur_enabled'],
            'gaze_enabled': detection_state['gaze_enabled'],
            'sensitivity': detection_state['sensitivity']
        },
        'connections': len(detection_state['connections']),
        'alerts_count': detection_state['alerts_count']
    })


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get detailed metrics"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'metrics': detection_state['metrics'],
        'system_info': {
            'running': detection_state['is_running'],
            'session_duration': (datetime.now() - detection_state['session_start']).total_seconds() if detection_state['session_start'] else 0,
            'total_alerts': detection_state['alerts_count']
        }
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'blur_enabled': detection_state['blur_enabled'],
        'gaze_enabled': detection_state['gaze_enabled'],
        'sensitivity': detection_state['sensitivity']
    })


@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update configuration"""
    try:
        data = request.json
        
        if 'blur_enabled' in data:
            detection_state['blur_enabled'] = data['blur_enabled']
        
        if 'gaze_enabled' in data:
            detection_state['gaze_enabled'] = data['gaze_enabled']
        
        if 'sensitivity' in data:
            detection_state['sensitivity'] = int(data['sensitivity'])
        
        # Update detection system if available
        if detection_system:
            detection_system.config.blur_enabled = detection_state['blur_enabled']
            detection_system.config.gaze_enabled = detection_state['gaze_enabled']
        
        # Broadcast to all clients
        socketio.emit('config_updated', {
            'status': 'updated',
            'config': {
                'blur_enabled': detection_state['blur_enabled'],
                'gaze_enabled': detection_state['gaze_enabled'],
                'sensitivity': detection_state['sensitivity']
            }
        }, broadcast=True)
        
        return jsonify({'status': 'success', 'message': 'Configuration updated'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/start', methods=['POST'])
def start_system():
    """Start detection system"""
    detection_state['is_running'] = True
    detection_state['session_start'] = datetime.now()
    detection_state['alerts_count'] = 0
    
    socketio.emit('system_started', {
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)
    
    return jsonify({'status': 'success', 'message': 'System started'})


@app.route('/api/stop', methods=['POST'])
def stop_system():
    """Stop detection system"""
    detection_state['is_running'] = False
    
    socketio.emit('system_stopped', {
        'timestamp': datetime.now().isoformat(),
        'session_duration': (datetime.now() - detection_state['session_start']).total_seconds() if detection_state['session_start'] else 0
    }, broadcast=True)
    
    return jsonify({'status': 'success', 'message': 'System stopped'})


# ========== WEBSOCKET ROUTES ==========
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    detection_state['connections'].append(request.sid)
    
    emit('connected', {
        'status': 'connected',
        'timestamp': datetime.now().isoformat(),
        'metrics': detection_state['metrics'],
        'config': {
            'blur_enabled': detection_state['blur_enabled'],
            'gaze_enabled': detection_state['gaze_enabled'],
            'sensitivity': detection_state['sensitivity']
        }
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')
    if request.sid in detection_state['connections']:
        detection_state['connections'].remove(request.sid)


@socketio.on('process_frame')
def handle_frame(data):
    """Receive and process frame from client"""
    try:
        # Here you would process the frame with your detection system
        # For now, we'll just acknowledge receipt
        
        frame_data = data.get('frame')
        config = data.get('config', {})
        
        # Update config if provided
        if 'blurEnabled' in config:
            detection_state['blur_enabled'] = config['blurEnabled']
        if 'gazeEnabled' in config:
            detection_state['gaze_enabled'] = config['gazeEnabled']
        if 'sensitivity' in config:
            detection_state['sensitivity'] = config['sensitivity']
        
        emit('frame_processed', {
            'status': 'processed',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        emit('error', {
            'message': f'Frame processing error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })


@socketio.on('update_config')
def handle_config_update(data):
    """Update configuration from client"""
    try:
        if 'blur_enabled' in data:
            detection_state['blur_enabled'] = data['blur_enabled']
        
        if 'gaze_enabled' in data:
            detection_state['gaze_enabled'] = data['gaze_enabled']
        
        if 'sensitivity' in data:
            detection_state['sensitivity'] = int(data['sensitivity'])
        
        emit('config_updated', {
            'status': 'updated',
            'timestamp': datetime.now().isoformat(),
            'config': {
                'blur_enabled': detection_state['blur_enabled'],
                'gaze_enabled': detection_state['gaze_enabled'],
                'sensitivity': detection_state['sensitivity']
            }
        }, broadcast=True)
    
    except Exception as e:
        emit('error', {'message': str(e)})


# ========== HELPER FUNCTIONS ==========
def update_metrics(metrics_data):
    """Called from detection system to update metrics"""
    detection_state['metrics'].update(metrics_data)
    
    # Track alerts
    if metrics_data.get('alert_active'):
        detection_state['alerts_count'] += 1
        detection_state['last_alert'] = {
            'timestamp': datetime.now().isoformat(),
            'face_count': metrics_data.get('face_count', 0)
        }
    
    # Broadcast to all connected clients
    socketio.emit('metrics_updated', {
        'metrics': detection_state['metrics'],
        'last_alert': detection_state['last_alert'],
        'timestamp': datetime.now().isoformat()
    }, broadcast=True, skip_sid=None)


def emit_alert(face_count, threat_reason):
    """Emit alert to all connected clients"""
    detection_state['alerts_count'] += 1
    detection_state['last_alert'] = {
        'timestamp': datetime.now().isoformat(),
        'face_count': face_count,
        'reason': threat_reason
    }
    
    socketio.emit('threat_detected', {
        'face_count': face_count,
        'reason': threat_reason,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)


def get_system_info():
    """Get system information"""
    return {
        'is_running': detection_state['is_running'],
        'uptime': (datetime.now() - detection_state['session_start']).total_seconds() if detection_state['session_start'] else 0,
        'connected_clients': len(detection_state['connections']),
        'total_alerts': detection_state['alerts_count'],
        'metrics': detection_state['metrics'],
        'config': {
            'blur_enabled': detection_state['blur_enabled'],
            'gaze_enabled': detection_state['gaze_enabled'],
            'sensitivity': detection_state['sensitivity']
        }
    }


# ========== MAIN ==========
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌐 SHOULDER SURFING DETECTION - WEB APP SERVER")
    print("="*60)
    print("\n📍 Web App running at http://localhost:5000")
    print("📍 API available at http://localhost:5000/api/")
    print("📍 WebSocket server ready for connections\n")
    print("Visit http://localhost:5000 in your browser to get started.\n")
    
    detection_state['session_start'] = datetime.now()
    
    try:
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=5000, 
                    debug=True,
                    use_reloader=False,
                    allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Server shutting down...")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
