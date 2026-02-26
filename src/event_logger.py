"""
Event logging and analytics for shoulder surfing detection
"""
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import threading

from config.settings import (
    LOG_DIR, LOG_FILE, LOG_LEVEL, LOG_ENABLE_FILE, 
    LOG_ENABLE_CONSOLE, LOG_MAX_FILE_SIZE, RETENTION_DAYS
)


class DetectionLogger:
    """Logs detection events with timestamps and metrics"""
    
    def __init__(self, name: str = "ShoulderSurfing"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVEL)
        self.events_log: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
        # Ensure log directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Setup formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if LOG_ENABLE_CONSOLE:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if LOG_ENABLE_FILE:
            log_file = LOG_DIR / "system.log"
            file_handler = logging.FileHandler(log_file, mode='a')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_detection(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log a detection event with timestamp
        
        Args:
            event_type: Type of event (detected, alert, blur_on, blur_off)
            data: Event data including confidence, face count, etc.
        """
        with self.lock:
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'data': data
            }
            self.events_log.append(event)
            
            # Log to file
            self._write_event_to_file(event)
            
            # Console output
            if event_type == 'alert':
                self.logger.warning(f"ALERT: {event_type} - {data}")
            elif event_type == 'detected':
                self.logger.info(f"Detection: {data}")
            else:
                self.logger.debug(f"{event_type}: {data}")
    
    def _write_event_to_file(self, event: Dict[str, Any]) -> None:
        """Write event to JSON log file"""
        event_file = LOG_DIR / "detection_events.jsonl"
        try:
            with open(event_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
            
            # Check file size and rotate if necessary
            if event_file.stat().st_size > LOG_MAX_FILE_SIZE:
                self._rotate_log_file(event_file)
        except Exception as e:
            self.logger.error(f"Failed to write event log: {e}")
    
    def _rotate_log_file(self, log_file: Path) -> None:
        """Rotate log file when it exceeds max size"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = log_file.parent / f"detection_events_{timestamp}.jsonl"
        try:
            log_file.rename(backup_file)
            self.logger.info(f"Log file rotated: {backup_file}")
        except Exception as e:
            self.logger.error(f"Failed to rotate log file: {e}")
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """Get summary of all detections in current session"""
        with self.lock:
            total_detections = len([e for e in self.events_log if e['event_type'] == 'detected'])
            total_alerts = len([e for e in self.events_log if e['event_type'] == 'alert'])
            
            return {
                'total_detections': total_detections,
                'total_alerts': total_alerts,
                'session_duration': self._get_session_duration(),
                'false_positives': len([e for e in self.events_log if e['event_type'] == 'false_positive'])
            }
    
    def _get_session_duration(self) -> str:
        """Calculate session duration"""
        if not self.events_log:
            return "0s"
        
        start_time = datetime.fromisoformat(self.events_log[0]['timestamp'])
        end_time = datetime.fromisoformat(self.events_log[-1]['timestamp'])
        duration = (end_time - start_time).total_seconds()
        
        mins, secs = divmod(int(duration), 60)
        hours, mins = divmod(mins, 60)
        
        if hours > 0:
            return f"{hours}h {mins}m {secs}s"
        elif mins > 0:
            return f"{mins}m {secs}s"
        else:
            return f"{secs}s"
    
    def export_logs(self, filename: str = None) -> Path:
        """Export logs to file"""
        if filename is None:
            filename = f"detection_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_path = LOG_DIR / filename
        
        with self.lock:
            with open(export_path, 'w') as f:
                json.dump(self.events_log, f, indent=2)
        
        self.logger.info(f"Logs exported to {export_path}")
        return export_path
    
    def cleanup_old_logs(self) -> None:
        """Remove logs older than retention period"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        
        for log_file in LOG_DIR.glob("detection_events_*.jsonl"):
            try:
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    log_file.unlink()
                    self.logger.info(f"Deleted old log: {log_file}")
            except Exception as e:
                self.logger.error(f"Failed to delete log file {log_file}: {e}")


# Global logger instance
logger = DetectionLogger()
