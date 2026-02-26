"""
PyQt5-based screen overlay for blur effect
"""
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt5.QtCore import QThread
import threading
from typing import Optional, Tuple
from datetime import datetime

from config.settings import BLUR_INTENSITY, BLUR_OVERLAY_OPACITY, BLUR_TRANSITION_SPEED
from src.utils import ImageProcessor, TimeCounter


class ScreenBlurOverlay(QWidget):
    """
    PyQt5 overlay widget for blurring the screen
    """
    
    blur_toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_active = False
        self.blur_intensity = BLUR_INTENSITY
        self.opacity = BLUR_OVERLAY_OPACITY
        self.transition_speed = BLUR_TRANSITION_SPEED
        self.current_opacity = 0.0
        self.target_opacity = 0.0
        self.blur_pixmap = None
        self.blur_effect_enabled = True
        
        # Setup window properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setCursor(Qt.ArrowCursor)
        
        # Timer for smooth transitions
        self.transition_timer = QTimer()
        self.transition_timer.timeout.connect(self._update_opacity)
        self.transition_interval = 16  # ~60 FPS
        
        # Initialize full screen
        self.setGeometry(0, 0, 1920, 1080)
    
    def enable_full_screen(self) -> None:
        """Make overlay cover entire screen"""
        screen = QApplication.primaryScreen()
        if screen:
            rect = screen.geometry()
            self.setGeometry(rect)
    
    def activate_blur(self) -> None:
        """Activate blur overlay"""
        if not self.is_active:
            self.is_active = True
            self.target_opacity = self.opacity
            self.transition_timer.start(self.transition_interval)
            self.show()
            self.raise_()
            self.activateWindow()
            self.blur_toggled.emit(True)
    
    def deactivate_blur(self) -> None:
        """Deactivate blur overlay with smooth transition"""
        if self.is_active:
            self.is_active = False
            self.target_opacity = 0.0
            self.transition_timer.start(self.transition_interval)
            self.blur_toggled.emit(False)
    
    def _update_opacity(self) -> None:
        """Update opacity for smooth transitions"""
        if abs(self.current_opacity - self.target_opacity) < 0.01:
            self.current_opacity = self.target_opacity
            self.transition_timer.stop()
            
            if self.current_opacity == 0.0:
                self.hide()
        else:
            # Move towards target opacity
            step = (self.target_opacity - self.current_opacity) * 0.1
            self.current_opacity += step
        
        self.update()
    
    def set_blur_intensity(self, intensity: int) -> None:
        """Set blur kernel size (must be odd)"""
        if intensity % 2 == 0:
            intensity += 1
        self.blur_intensity = intensity
    
    def set_opacity(self, opacity: float) -> None:
        """Set overlay opacity (0-1)"""
        self.opacity = max(0.0, min(1.0, opacity))
    
    def capture_screen(self) -> np.ndarray:
        """
        Capture current screen content
        """
        screen = QApplication.primaryScreen()
        if screen:
            screenshot = screen.grabWindow(0)
            # Convert QPixmap to numpy array
            image = screenshot.toImage()
            width = image.width()
            height = image.height()
            ptr = image.bits()
            ptr.setsize(image.byteCount())
            arr = np.array(ptr).reshape(height, width, 4)
            # Convert RGBA to BGR
            return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        return None
    
    def apply_blur(self, should_blur: bool, blur_type: str = "gaussian") -> None:
        """
        Apply blur to screen
        
        Args:
            should_blur: Whether to apply blur
            blur_type: Type of blur ('gaussian', 'pixelate', 'solid')
        """
        if should_blur and self.blur_effect_enabled:
            try:
                # Capture screen
                screenshot = QApplication.primaryScreen().grabWindow(0)
                
                # Convert to OpenCV format
                image = screenshot.toImage()
                width = image.width()
                height = image.height()
                ptr = image.bits()
                ptr.setsize(image.byteCount())
                arr = np.array(ptr).reshape(height, width, 4)
                
                # Convert RGBA to BGR
                bgr_image = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
                
                # Apply blur effect
                if blur_type == "gaussian":
                    blurred = ImageProcessor.blur_image(bgr_image, self.blur_intensity)
                elif blur_type == "pixelate":
                    blurred = ImageProcessor.pixelate_image(bgr_image, 20)
                else:
                    # Solid color overlay
                    blurred = np.zeros_like(bgr_image)
                
                # Convert back to Qt format
                blurred_rgb = cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB)
                h, w, ch = blurred_rgb.shape
                bytes_per_line = 3 * w
                qt_image = QImage(blurred_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.blur_pixmap = QPixmap.fromImage(qt_image)
                
            except Exception as e:
                print(f"Error applying blur: {e}")
    
    def paintEvent(self, event) -> None:
        """Paint overlay"""
        if self.current_opacity <= 0:
            return
        
        painter = QPainter(self)
        painter.setOpacity(self.current_opacity)
        
        if self.blur_pixmap:
            painter.drawPixmap(0, 0, self.blur_pixmap)
        else:
            # Fallback to solid color
            painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        painter.end()
    
    def mousePressEvent(self, event):
        """Block mouse clicks from passing through"""
        if self.is_active:
            event.accept()
    
    def keyPressEvent(self, event):
        """Handle keyboard input"""
        if event.key() == Qt.Key_Escape:
            self.deactivate_blur()


class ScreenBlurManager:
    """
    Manage screen blur overlay without using separate window
    Uses direct frame overlay approach
    """
    
    def __init__(self):
        self.is_blurred = False
        self.blur_intensity = BLUR_INTENSITY
        self.overlay_window = None
        self.lock = threading.Lock()
    
    def enable_blur(self) -> None:
        """Enable screen blur"""
        with self.lock:
            if not self.is_blurred:
                self.is_blurred = True
                if self.overlay_window:
                    self.overlay_window.activate_blur()
    
    def disable_blur(self) -> None:
        """Disable screen blur"""
        with self.lock:
            if self.is_blurred:
                self.is_blurred = False
                if self.overlay_window:
                    self.overlay_window.deactivate_blur()
    
    def toggle_blur(self) -> None:
        """Toggle blur state"""
        if self.is_blurred:
            self.disable_blur()
        else:
            self.enable_blur()
    
    def set_blur_intensity(self, intensity: int) -> None:
        """Set blur intensity"""
        self.blur_intensity = intensity
        if self.overlay_window:
            self.overlay_window.set_blur_intensity(intensity)
    
    def initialize_overlay(self, app: Optional[QApplication] = None) -> ScreenBlurOverlay:
        """Initialize overlay window"""
        if app is None:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
        
        self.overlay_window = ScreenBlurOverlay()
        self.overlay_window.enable_full_screen()
        
        # Hide initially
        self.overlay_window.hide()
        
        return self.overlay_window
    
    def get_status(self) -> bool:
        """Get current blur status"""
        return self.is_blurred
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.overlay_window:
            self.overlay_window.close()
