#!/usr/bin/env python3
"""
Shoulder Surfing Detection System - Main Entry Point

Usage:
    python run.py [--debug] [--duration SECONDS] [--gui]
    
Examples:
    python run.py                    # Run in CLI mode
    python run.py --debug            # Run with debug output
    python run.py --duration 60      # Run for 60 seconds
    python run.py --gui              # Run with GUI
"""

import argparse
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import ShoulderSurfingDetectionSystem
from src.event_logger import logger
from config.settings import LOG_LEVEL


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Real-Time Shoulder Surfing Detection and Screen Privacy Protection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run.py                    Run in normal mode
  python run.py --debug            Enable debug logging
  python run.py --duration 60      Run for 60 seconds
  python run.py --gui              Launch with GUI interface
  python run.py --export report.json  Export logs to file
  python run.py --demo             Run in demo mode (no webcam)
        '''
    )


def run_demo_mode():
    """Run a demo without actual webcam"""
    import numpy as np
    import cv2
    from src.face_detector import FaceDetector
    from src.event_logger import logger
    
    logger.logger.info("\n=== DEMO MODE ===")
    logger.logger.info("Generating simulated detection data...\n")
    
    # Create test image with synthetic detected faces
    width, height = 640, 480
    
    # Simulate detections
    simulated_detections = [
        {'timestamp': 0, 'face_count': 1, 'alert': False},
        {'timestamp': 1, 'face_count': 1, 'alert': False},
        {'timestamp': 2, 'face_count': 2, 'alert': True},  # Alert!
        {'timestamp': 3, 'face_count': 2, 'alert': True},
        {'timestamp': 4, 'face_count': 2, 'alert': True},
        {'timestamp': 5, 'face_count': 1, 'alert': False},
        {'timestamp': 6, 'face_count': 1, 'alert': False},
    ]
    
    print("\n" + "="*50)
    print("SHOULDER SURFING DETECTION - DEMO MODE")
    print("="*50)
    print("\nSimulating detection scenario...")
    print("-" * 50)
    
    for detection in simulated_detections:
        status = "🚨 THREAT DETECTED!" if detection['alert'] else "✅ SAFE"
        print(f"[T={detection['timestamp']}s] Faces: {detection['face_count']} | {status}")
        
        if detection['alert']:
            logger.log_detection('alert', {
                'face_count': detection['face_count'],
                'timestamp': detection['timestamp']
            })
        
        import time
        time.sleep(1)
    
    print("-" * 50)
    summary = logger.get_detection_summary()
    print(f"\nSession Summary:")
    print(f"  Total Detections: {summary['total_detections']}")
    print(f"  Total Alerts: {summary['total_alerts']}")
    print(f"  Duration: {summary['session_duration']}")
    
    export_path = logger.export_logs('demo_report.json')
    print(f"\n✅ Demo completed! Logs exported to: {export_path}")
    print("="*50)


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Real-Time Shoulder Surfing Detection and Screen Privacy Protection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run.py                    Run in normal mode
  python run.py --debug            Enable debug logging
  python run.py --duration 60      Run for 60 seconds
  python run.py --gui              Launch with GUI interface
  python run.py --export report.json  Export logs to file
  python run.py --demo             Run in demo mode (no webcam)
  python run.py --web              Launch web app server
        '''
    )
    
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode with verbose output')
    
    parser.add_argument('--duration', type=float, default=None,
                       help='Run for specified duration in seconds')
    
    parser.add_argument('--gui', action='store_true',
                       help='Launch with graphical user interface')
    
    parser.add_argument('--web', action='store_true',
                       help='Launch web app server (http://localhost:5000)')
    
    parser.add_argument('--export', type=str, default=None,
                       help='Export logs to specified file')
    
    parser.add_argument('--headless', action='store_true',
                       help='Run without screen overlay (testing mode)')
    
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera ID to use (default: 0)')
    
    parser.add_argument('--log-level', type=str, default=LOG_LEVEL,
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    
    parser.add_argument('--demo', action='store_true',
                       help='Run in demo mode without webcam (for testing)')
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set logging level
    logger.logger.setLevel(args.log_level)
    
    logger.logger.info("=" * 60)
    logger.logger.info("Shoulder Surfing Detection System")
    logger.logger.info("=" * 60)
    
    if args.debug:
        logger.logger.info("DEBUG MODE ENABLED")
    
    if args.web:
        logger.logger.info("LAUNCHING WEB APP SERVER...")
        logger.logger.info("Opening web app on http://localhost:5000")
        try:
            import web_server
            # The web_server.py script will handle the server startup
        except ImportError as e:
            logger.logger.error(f"Failed to import web_server: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.logger.info("\nWeb server stopped by user")
            sys.exit(0)
        return
    
    if args.demo:
        logger.logger.info("DEMO MODE - Running without webcam")
        run_demo_mode()
        return
    
    try:
        # Create detection system
        system = ShoulderSurfingDetectionSystem(debug=args.debug)
        
        if args.gui:
            logger.logger.info("Launching GUI interface...")
            from src.gui import launch_gui
            launch_gui(system)
        elif args.headless:
            logger.logger.info("Running in headless mode (no screen overlay)")
            system.run(duration=args.duration)
        else:
            logger.logger.info("Starting detection system...")
            logger.logger.info(f"Press Ctrl+C to stop")
            system.run(duration=args.duration)
        
        # Export logs if requested
        if args.export:
            sys.path.insert(0, str(Path(__file__).parent))
            export_path = system.export_report(args.export)
            logger.logger.info(f"Logs exported to: {export_path}")
        
        # Print final metrics
        metrics = system.get_metrics()
        logger.logger.info("\n" + "=" * 60)
        logger.logger.info("Session Summary:")
        logger.logger.info(f"  Frames Processed: {metrics['frame_count']}")
        logger.logger.info(f"  Average FPS: {metrics['performance']['fps']:.2f}")
        logger.logger.info(f"  Avg Processing Time: {metrics['performance']['avg_frame_time_ms']:.2f}ms")
        logger.logger.info(f"  Detections: {metrics['detection_summary']['total_detections']}")
        logger.logger.info(f"  Alerts: {metrics['detection_summary']['total_alerts']}")
        logger.logger.info("=" * 60)
    
    except KeyboardInterrupt:
        logger.logger.info("\nSystem interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
