"""
Graphical User Interface for Shoulder Surfing Detection System
"""
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QCheckBox, QComboBox, QTextEdit, QApplication,
    QTabWidget, QProgressBar, QSpinBox, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap, QImage
import cv2
import numpy as np
from typing import Optional

from src.main import ShoulderSurfingDetectionSystem
from src.event_logger import logger


class DetectionThread(QThread):
    """Background thread for detection processing"""
    frame_ready = pyqtSignal(dict)
    
    def __init__(self, system: ShoulderSurfingDetectionSystem):
        super().__init__()
        self.system = system
        self.is_running = True
    
    def run(self):
        """Run detection loop"""
        while self.is_running and self.system.is_running:
            result = self.system.process_frame()
            if result.get('success'):
                self.frame_ready.emit(result)
    
    def stop(self):
        """Stop detection thread"""
        self.is_running = False
        self.wait()


class ShoulderSurfingGUI(QMainWindow):
    """Main GUI window for the detection system"""
    
    def __init__(self, system: ShoulderSurfingDetectionSystem):
        super().__init__()
        self.system = system
        self.detection_thread = None
        self.is_monitoring = False
        
        self.setWindowTitle("Shoulder Surfing Detection System")
        self.setGeometry(100, 100, 1200, 800)
        
        self._setup_ui()
        
        # Update timer for metrics
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_metrics)
        self.update_timer.start(1000)  # Update every second
    
    def _setup_ui(self):
        """Setup user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Detection Tab
        self.tabs.addTab(self._create_detection_tab(), "Detection")
        
        # Settings Tab
        self.tabs.addTab(self._create_settings_tab(), "Settings")
        
        # Logs Tab
        self.tabs.addTab(self._create_logs_tab(), "Logs")
        
        # Metrics Tab
        self.tabs.addTab(self._create_metrics_tab(), "Metrics")
        
        main_layout.addWidget(self.tabs)
        central_widget.setLayout(main_layout)
    
    def _create_detection_tab(self) -> QWidget:
        """Create detection tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Real-Time Detection")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Status indicators
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        self.face_count_label = QLabel("Faces: 0")
        status_layout.addWidget(self.face_count_label)
        
        self.alert_label = QLabel("Alert: OFF")
        self.alert_label.setStyleSheet("color: green;")
        status_layout.addWidget(self.alert_label)
        
        self.fps_label = QLabel("FPS: 0.0")
        status_layout.addWidget(self.fps_label)
        
        layout.addLayout(status_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Detection")
        self.start_button.clicked.connect(self._start_detection)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Detection")
        self.stop_button.clicked.connect(self._stop_detection)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self._toggle_pause)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)
        
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        layout.addWidget(QLabel("Activity:"))
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        return tab
    
    def _create_settings_tab(self) -> QWidget:
        """Create settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Detection settings
        detection_group = QGroupBox("Detection Settings")
        detection_form = QFormLayout()
        
        self.min_faces_spin = QSpinBox()
        self.min_faces_spin.setMinimum(1)
        self.min_faces_spin.setMaximum(10)
        self.min_faces_spin.setValue(self.system.min_faces_for_alert)
        self.min_faces_spin.valueChanged.connect(
            lambda v: setattr(self.system, 'min_faces_for_alert', v)
        )
        detection_form.addRow("Min Faces for Alert:", self.min_faces_spin)
        
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setMinimum(0)
        self.confidence_slider.setMaximum(100)
        self.confidence_slider.setValue(50)
        detection_form.addRow("Confidence Threshold:", self.confidence_slider)
        
        detection_group.setLayout(detection_form)
        layout.addWidget(detection_group)
        
        # Blur settings
        blur_group = QGroupBox("Blur Settings")
        blur_form = QFormLayout()
        
        self.blur_checkbox = QCheckBox("Enable Screen Blur")
        self.blur_checkbox.setChecked(self.system.blur_enabled)
        self.blur_checkbox.stateChanged.connect(
            lambda state: setattr(self.system, 'blur_enabled', state == Qt.Checked)
        )
        blur_form.addRow("", self.blur_checkbox)
        
        self.gaze_checkbox = QCheckBox("Enable Gaze Estimation")
        self.gaze_checkbox.setChecked(self.system.gaze_enabled)
        self.gaze_checkbox.stateChanged.connect(
            lambda state: setattr(self.system, 'gaze_enabled', state == Qt.Checked)
        )
        blur_form.addRow("", self.gaze_checkbox)
        
        self.blur_intensity_slider = QSlider(Qt.Horizontal)
        self.blur_intensity_slider.setMinimum(5)
        self.blur_intensity_slider.setMaximum(50)
        self.blur_intensity_slider.setValue(25)
        self.blur_intensity_slider.valueChanged.connect(
            lambda v: self.system.screen_blur_manager.set_blur_intensity(v)
        )
        blur_form.addRow("Blur Intensity:", self.blur_intensity_slider)
        
        blur_group.setLayout(blur_form)
        layout.addWidget(blur_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        return tab
    
    def _create_logs_tab(self) -> QWidget:
        """Create logs tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(QLabel("Detection Logs:"))
        layout.addWidget(self.logs_text)
        
        button_layout = QHBoxLayout()
        
        export_button = QPushButton("Export Logs")
        export_button.clicked.connect(self._export_logs)
        button_layout.addWidget(export_button)
        
        clear_button = QPushButton("Clear Logs")
        clear_button.clicked.connect(self.logs_text.clear)
        button_layout.addWidget(clear_button)
        
        layout.addLayout(button_layout)
        tab.setLayout(layout)
        
        return tab
    
    def _create_metrics_tab(self) -> QWidget:
        """Create metrics tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Metrics display
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        layout.addWidget(QLabel("Performance Metrics:"))
        layout.addWidget(self.metrics_text)
        
        tab.setLayout(layout)
        
        return tab
    
    def _start_detection(self):
        """Start detection system"""
        if self.system.start():
            self.is_monitoring = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.pause_button.setEnabled(True)
            self.status_label.setText("Status: Running")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Start detection thread
            if self.detection_thread is None:
                self.detection_thread = DetectionThread(self.system)
                self.detection_thread.frame_ready.connect(self._on_frame_ready)
            self.detection_thread.start()
    
    def _stop_detection(self):
        """Stop detection system"""
        self.is_monitoring = False
        self.system.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        if self.detection_thread:
            self.detection_thread.stop()
    
    def _toggle_pause(self):
        """Toggle pause state"""
        if self.system.is_paused:
            self.system.resume()
            self.pause_button.setText("Pause")
        else:
            self.system.pause()
            self.pause_button.setText("Resume")
    
    def _on_frame_ready(self, result: dict):
        """Handle new frame"""
        if result.get('success'):
            self.face_count_label.setText(f"Faces: {result['face_count']}")
            
            if result['alert_state']:
                self.alert_label.setText("Alert: ON")
                self.alert_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.alert_label.setText("Alert: OFF")
                self.alert_label.setStyleSheet("color: green;")
    
    def _update_metrics(self):
        """Update metrics display"""
        if self.system.is_running:
            metrics = self.system.get_metrics()
            
            # Update FPS
            fps = metrics['performance']['fps']
            self.fps_label.setText(f"FPS: {fps:.1f}")
            
            # Update progress bar
            progress = min(100, int(fps * 10))
            self.progress_bar.setValue(progress)
            
            # Update metrics text
            text = f"""
Performance Metrics:
  Average FPS: {fps:.2f}
  Avg Frame Time: {metrics['performance']['avg_frame_time_ms']:.2f}ms
  Avg Detection Time: {metrics['performance']['avg_detection_time_ms']:.2f}ms
  Frames Processed: {metrics['frame_count']}

Detection Summary:
  Total Detections: {metrics['detection_summary']['total_detections']}
  Total Alerts: {metrics['detection_summary']['total_alerts']}
  Session Duration: {metrics['detection_summary']['session_duration']}
  False Positives: {metrics['detection_summary']['false_positives']}

Blur Status:
  Screen Blur Active: {metrics['blur_active']}
            """
            self.metrics_text.setText(text)
    
    def _export_logs(self):
        """Export logs to file"""
        path = self.system.export_report()
        logger.logger.info(f"Logs exported to: {path}")
        self.logs_text.append(f"Logs exported to: {path}")
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.system.is_running:
            self.system.stop()
        if self.detection_thread:
            self.detection_thread.stop()
        self.update_timer.stop()
        event.accept()


def launch_gui(system: Optional[ShoulderSurfingDetectionSystem] = None):
    """Launch the GUI application"""
    if system is None:
        system = ShoulderSurfingDetectionSystem()
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = ShoulderSurfingGUI(system)
    window.show()
    
    sys.exit(app.exec_())
