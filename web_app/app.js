// ========================================
// SHOULDER SURFING DETECTION - WEB APP
// Frontend JavaScript Logic
// ========================================

class ShoulderSurfingDetectionApp {
    constructor() {
        // State
        this.isRunning = false;
        this.isCameraActive = false;
        this.stream = null;
        this.socket = null;
        this.alerts = [];
        this.logs = [];
        
        // Configuration
        this.config = {
            blurEnabled: true,
            gazeEnabled: true,
            sensitivity: 5,
            alertVolume: 0.5
        };
        
        // Metrics
        this.metrics = {
            faceCount: 0,
            fps: 0,
            latency: 0,
            threatActive: false
        };
        
        // Canvas and context
        this.canvas = document.getElementById('video-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.init();
    }
    
    // ========== INITIALIZATION ==========
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.log('🎬 Application initialized');
    }
    
    setupEventListeners() {
        // Video controls
        document.getElementById('start-webcam-btn').addEventListener('click', () => this.startWebcam());
        document.getElementById('stop-webcam-btn').addEventListener('click', () => this.stopWebcam());
        
        // Settings
        document.getElementById('blur-toggle').addEventListener('change', (e) => {
            this.config.blurEnabled = e.target.checked;
            this.updateSettings();
        });
        
        document.getElementById('gaze-toggle').addEventListener('change', (e) => {
            this.config.gazeEnabled = e.target.checked;
            this.updateSettings();
        });
        
        document.getElementById('sensitivity-slider').addEventListener('change', (e) => {
            this.config.sensitivity = parseInt(e.target.value);
            document.getElementById('sensitivity-value').textContent = e.target.value;
            this.updateSettings();
        });
        
        document.getElementById('alert-volume').addEventListener('change', (e) => {
            this.config.alertVolume = parseInt(e.target.value) / 100;
            document.getElementById('alert-volume-value').textContent = e.target.value + '%';
        });
        
        // Buttons
        document.getElementById('export-btn').addEventListener('click', () => this.exportMetrics());
        document.getElementById('clear-history-btn').addEventListener('click', () => this.clearHistory());
        document.getElementById('clear-logs-btn').addEventListener('click', () => this.clearLogs());
    }
    
    // ========== WEBSOCKET CONNECTION ==========
    connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            this.socket = io(window.location.origin, {
                transports: ['websocket', 'polling']
            });
            
            // Connection events
            this.socket.on('connect', () => {
                this.updateConnectionStatus(true);
                this.log('✅ Connected to server');
            });
            
            this.socket.on('disconnect', () => {
                this.updateConnectionStatus(false);
                this.log('❌ Disconnected from server');
            });
            
            // Metrics update
            this.socket.on('metrics_updated', (data) => {
                this.updateMetrics(data);
            });
            
            // Config update confirmation
            this.socket.on('config_updated', (data) => {
                this.log('⚙️ Settings updated on server');
            });
            
            // Error handling
            this.socket.on('error', (error) => {
                console.error('WebSocket error:', error);
                this.log('⚠️ WebSocket error: ' + error);
            });
            
        } catch (error) {
            console.error('Failed to connect:', error);
            this.log('❌ Failed to connect to server');
        }
    }
    
    // ========== WEBCAM MANAGEMENT ==========
    async startWebcam() {
        try {
            this.log('📹 Starting webcam...');
            
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: false
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            
            // Create video element to capture frames
            const video = document.createElement('video');
            video.srcObject = this.stream;
            video.play();
            
            // Start frame capture
            this.isCameraActive = true;
            this.isRunning = true;
            this.updateCameraStatus(true);
            this.updateSystemStatus(true);
            
            // Update button states
            document.getElementById('start-webcam-btn').disabled = true;
            document.getElementById('stop-webcam-btn').disabled = false;
            
            // Hide no-camera message
            document.getElementById('no-camera').style.display = 'none';
            
            this.log('✅ Webcam started successfully');
            
            // Start capture loop
            this.captureFrame(video);
            
        } catch (error) {
            console.error('Webcam error:', error);
            this.log('❌ Webcam error: ' + error.message);
            alert('Unable to access webcam. Make sure you have given permission.');
        }
    }
    
    async stopWebcam() {
        try {
            this.isCameraActive = false;
            this.isRunning = false;
            this.updateCameraStatus(false);
            this.updateSystemStatus(false);
            
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
                this.stream = null;
            }
            
            // Update button states
            document.getElementById('start-webcam-btn').disabled = false;
            document.getElementById('stop-webcam-btn').disabled = true;
            
            // Show no-camera message
            document.getElementById('no-camera').style.display = 'flex';
            
            // Clear canvas
            this.ctx.fillStyle = '#000';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.log('⏹ Webcam stopped');
            
        } catch (error) {
            console.error('Error stopping webcam:', error);
            this.log('❌ Error stopping webcam: ' + error.message);
        }
    }
    
    captureFrame(video) {
        if (!this.isCameraActive) return;
        
        try {
            // Only draw if video is ready
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                this.ctx.drawImage(video, 0, 0, this.canvas.width, this.canvas.height);
                
                // Get frame data
                const frameData = this.canvas.toDataURL('image/jpeg', 0.8);
                
                // Send to server for processing
                if (this.socket && this.socket.connected) {
                    this.socket.emit('process_frame', {
                        frame: frameData,
                        config: this.config
                    });
                }
                
                // Draw detection overlays if threat
                if (this.metrics.threatActive) {
                    this.drawThreatOverlay();
                }
            }
        } catch (error) {
            console.error('Error capturing frame:', error);
        }
        
        // Continue loop
        requestAnimationFrame(() => this.captureFrame(video));
    }
    
    drawThreatOverlay() {
        this.ctx.strokeStyle = '#dc2626';
        this.ctx.lineWidth = 3;
        this.ctx.shadowColor = '#dc2626';
        this.ctx.shadowBlur = 10;
        
        // Draw border
        this.ctx.strokeRect(5, 5, this.canvas.width - 10, this.canvas.height - 10);
        
        // Draw warning text
        this.ctx.fillStyle = '#dc2626';
        this.ctx.font = 'bold 20px Arial';
        this.ctx.fillText('🚨 THREAT DETECTED', 20, 40);
        
        this.ctx.shadowColor = 'transparent';
    }
    
    // ========== METRICS MANAGEMENT ==========
    updateMetrics(data) {
        if (data.metrics) {
            this.metrics.faceCount = data.metrics.face_count || 0;
            this.metrics.fps = (data.metrics.fps || 0).toFixed(1);
            this.metrics.latency = data.metrics.latency || 0;
            this.metrics.threatActive = data.metrics.alert_active || false;
        }
        
        // Update UI
        this.updateMetricsUI();
        
        // Handle threat
        if (this.metrics.threatActive) {
            this.showAlert(data);
        } else {
            this.hideAlert();
        }
    }
    
    updateMetricsUI() {
        document.getElementById('faces-count').textContent = this.metrics.faceCount;
        document.getElementById('fps-value').textContent = this.metrics.fps;
        document.getElementById('latency-value').textContent = this.metrics.latency + 'ms';
        
        const threatStatus = document.getElementById('threat-status');
        if (this.metrics.threatActive) {
            threatStatus.textContent = '🚨 Threat!';
            threatStatus.style.color = '#dc2626';
        } else {
            threatStatus.textContent = '✅ Safe';
            threatStatus.style.color = '#16a34a';
        }
    }
    
    // ========== ALERT MANAGEMENT ==========
    showAlert(data) {
        const alertSection = document.getElementById('alert-section');
        const message = document.getElementById('alert-message');
        
        const alertMsg = `${this.metrics.faceCount} faces detected in frame`;
        message.textContent = alertMsg;
        alertSection.style.display = 'block';
        
        // Add to history
        this.addAlert({
            timestamp: new Date().toLocaleTimeString(),
            message: alertMsg,
            faceCount: this.metrics.faceCount
        });
        
        // Play alert sound
        this.playAlertSound();
        
        // Log
        this.log(`🚨 ALERT: ${alertMsg}`);
    }
    
    hideAlert() {
        document.getElementById('alert-section').style.display = 'none';
    }
    
    playAlertSound() {
        // Create simple beep using Web Audio API
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(this.config.alertVolume, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    }
    
    addAlert(alert) {
        this.alerts.unshift(alert);
        this.updateHistoryUI();
    }
    
    clearHistory() {
        this.alerts = [];
        this.updateHistoryUI();
        this.log('🗑 Alert history cleared');
    }
    
    updateHistoryUI() {
        const historyList = document.getElementById('history-list');
        
        if (this.alerts.length === 0) {
            historyList.innerHTML = '<p class="empty-message">No alerts yet</p>';
            return;
        }
        
        const html = this.alerts.slice(0, 20).map(alert => `
            <div class="history-item alert">
                <strong>${alert.timestamp}</strong> - ${alert.message}
            </div>
        `).join('');
        
        historyList.innerHTML = html;
    }
    
    // ========== LOGGING ==========
    log(message) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = `[${timestamp}] ${message}`;
        
        this.logs.unshift(logEntry);
        this.updateLogsUI();
    }
    
    clearLogs() {
        this.logs = [];
        this.updateLogsUI();
    }
    
    updateLogsUI() {
        const logsList = document.getElementById('logs-list');
        
        if (this.logs.length === 0) {
            logsList.innerHTML = '<p class="empty-message">No logs</p>';
            return;
        }
        
        const html = this.logs.slice(0, 50).map(log => `
            <div class="log-entry">${log}</div>
        `).join('');
        
        logsList.innerHTML = html;
    }
    
    // ========== STATUS UPDATES ==========
    updateConnectionStatus(connected) {
        const status = document.getElementById('connection-status');
        if (connected) {
            status.textContent = '🟢 Connected';
            status.className = 'status-value connected';
        } else {
            status.textContent = '🔴 Disconnected';
            status.className = 'status-value disconnected';
        }
    }
    
    updateSystemStatus(running) {
        const status = document.getElementById('system-status');
        if (running) {
            status.textContent = '▶ Running';
            status.className = 'status-value running';
        } else {
            status.textContent = '⏹ Stopped';
            status.className = 'status-value stopped';
        }
    }
    
    updateCameraStatus(active) {
        const status = document.getElementById('camera-status');
        if (active) {
            status.textContent = '📹 On';
            status.className = 'status-value on';
        } else {
            status.textContent = '📹 Off';
            status.className = 'status-value off';
        }
    }
    
    // ========== SETTINGS ==========
    updateSettings() {
        if (this.socket && this.socket.connected) {
            this.socket.emit('update_config', {
                blur_enabled: this.config.blurEnabled,
                gaze_enabled: this.config.gazeEnabled,
                sensitivity: this.config.sensitivity
            });
        }
    }
    
    // ========== EXPORT ==========
    exportMetrics() {
        const exportData = {
            timestamp: new Date().toISOString(),
            metrics: this.metrics,
            config: this.config,
            alertHistory: this.alerts,
            logs: this.logs.slice(0, 100)
        };
        
        // Convert to JSON
        const jsonString = JSON.stringify(exportData, null, 2);
        
        // Create blob and download
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `detection-report-${Date.now()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        this.log('📥 Exported metrics to: ' + link.download);
    }
}

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ShoulderSurfingDetectionApp();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.app && window.app.isCameraActive) {
        window.app.stopWebcam();
    }
});
