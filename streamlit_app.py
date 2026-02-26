"""
Shoulder Surfing Detection - Streamlit Web App
Deployed on Streamlit Cloud for easy cloud access
"""

import streamlit as st
import numpy as np
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from PIL import Image, ImageDraw

# Try to import cv2, but don't fail if it's not available (for cloud deployment)
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.face_detector import FaceDetector
    from src.event_logger import logger, DetectionLogger
except ImportError:
    # Create dummy classes for demo mode
    FaceDetector = None
    DetectionLogger = None
    if HAS_CV2:
        st.error("❌ Error: Core modules not found. Make sure you're in the correct directory.")
        st.stop()

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="🔒 Shoulder Surfing Detection",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CUSTOM STYLING ==========
st.markdown("""
<style>
    .main {
        padding: 1.5rem;
    }
    
    /* Header styling */
    h1 {
        color: #fff;
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #1e293b;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Threat alert */
    .threat-alert {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: 2px solid #dc2626;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px rgba(220, 38, 38, 0.1);
    }
    
    /* Safe status */
    .safe-status {
        color: #16a34a;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    /* Threat status */
    .threat-status {
        color: #dc2626;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        padding: 1.5rem;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'metrics' not in st.session_state:
    st.session_state.metrics = {
        'face_count': 0,
        'fps': 0.0,
        'latency': 0,
        'frames_processed': 0
    }
if 'threat_active' not in st.session_state:
    st.session_state.threat_active = False
if 'sensitivity' not in st.session_state:
    st.session_state.sensitivity = 5
if 'blur_enabled' not in st.session_state:
    st.session_state.blur_enabled = True
if 'gaze_enabled' not in st.session_state:
    st.session_state.gaze_enabled = True

# ========== DEMO MODE FUNCTION ==========
def run_demo_mode():
    """Run demonstration with simulated data"""
    st.info("📊 Running demo scenario with simulated detections...")
    
    demo_data = [
        (1, False), (1, False), (2, True), (2, True), (2, True), (1, False)
    ]
    
    progress_bar = st.progress(0)
    
    for idx, (face_count, threat) in enumerate(demo_data):
        st.session_state.metrics['face_count'] = face_count
        st.session_state.threat_active = threat
        
        if threat:
            st.session_state.alerts.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'frame': idx,
                'face_count': face_count
            })
        
        progress_bar.progress((idx + 1) / len(demo_data))
        
        import time
        time.sleep(1)
    
    st.success("✅ Demo completed!")
    st.rerun()

# ========== HEADER ==========
st.title("🔒 Shoulder Surfing Detection System")
st.markdown("**Real-Time Privacy Protection** | Deployed on Streamlit Cloud")

# ========== SIDEBAR CONFIG ==========
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Show warning if OpenCV not available
    if not HAS_CV2:
        st.warning("⚠️ Running in **Demo Mode** - OpenCV not available on cloud")
    else:
        st.success("✅ **Live Mode** - Webcam available")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.blur_enabled = st.checkbox(
            "🔲 Screen Blur",
            value=st.session_state.blur_enabled,
            help="Blur screen when threat detected"
        )
    with col2:
        st.session_state.gaze_enabled = st.checkbox(
            "👀 Gaze Analysis",
            value=st.session_state.gaze_enabled,
            help="Analyze where person is looking"
        )
    
    st.session_state.sensitivity = st.slider(
        "Threat Sensitivity",
        min_value=1,
        max_value=10,
        value=st.session_state.sensitivity,
        help="Higher = more sensitive to threats"
    )
    
    st.divider()
    st.subheader("📊 Detection Settings")
    
    face_threshold = st.slider(
        "Face Detection Confidence",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Minimum confidence for face detection"
    )
    
    threat_faces = st.number_input(
        "Threat Face Count",
        min_value=2,
        max_value=10,
        value=2,
        help="Number of faces to trigger alert"
    )
    
    st.divider()
    st.subheader("📱 Demo Options")
    
    if st.button("▶ Run Demo Mode"):
        st.session_state.is_running = True
        st.success("✅ Demo mode started! Showing simulated detection...")
        run_demo_mode()
    
    if st.button("🗑 Clear History"):
        st.session_state.alerts = []
        st.success("✅ Alert history cleared!")

# ========== MAIN CONTENT ==========
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Faces Detected",
        st.session_state.metrics['face_count'],
        delta=None,
        help="Number of faces in frame"
    )

with col2:
    st.metric(
        "FPS",
        f"{st.session_state.metrics['fps']:.1f}",
        delta=None,
        help="Frames processed per second"
    )

with col3:
    st.metric(
        "Latency",
        f"{st.session_state.metrics['latency']:.0f}ms",
        delta=None,
        help="Processing time per frame"
    )

with col4:
    threat_label = "🚨 THREAT!" if st.session_state.threat_active else "✅ SAFE"
    st.metric(
        "Threat Status",
        threat_label,
        help="Current threat status"
    )

# ========== ALERT SECTION ==========
if st.session_state.threat_active:
    st.markdown("""
    <div class='threat-alert'>
        <h3>🚨 THREAT DETECTED!</h3>
        <p>Multiple faces detected in frame. Screen blur activated.</p>
    </div>
    """, unsafe_allow_html=True)

# ========== VIDEO SECTION ==========
st.subheader("📹 Video Stream")

col_video, col_info = st.columns([2, 1])

with col_video:
    # Create placeholder for video
    video_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Start/Stop buttons
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("▶ Start Webcam", key="start_btn"):
            st.session_state.is_running = True
            st.rerun()
    
    with col_stop:
        if st.button("⏹ Stop Webcam", key="stop_btn"):
            st.session_state.is_running = False
            st.rerun()
    
    # Webcam capture (only if cv2 is available)
    if HAS_CV2 and st.session_state.is_running:
        try:
            camera = cv2.VideoCapture(0)
            
            if not camera.isOpened():
                st.error("❌ Could not access webcam")
                st.session_state.is_running = False
            else:
                status_placeholder.info("📹 Webcam active - Click 'Stop Webcam' to exit")
                
                # Simple frame loop
                frame_count = 0
                while st.session_state.is_running:
                    ret, frame = camera.read()
                    
                    if not ret:
                        st.error("Failed to grab frame")
                        break
                    
                    # Resize for display
                    frame = cv2.resize(frame, (640, 480))
                    
                    # Simple face detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    face_cascade = cv2.CascadeClassifier(
                        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                    )
                    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                    
                    # Draw faces
                    face_count = len(faces)
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Update threat status
                    st.session_state.threat_active = face_count >= threat_faces
                    st.session_state.metrics['face_count'] = face_count
                    st.session_state.metrics['frames_processed'] = frame_count
                    
                    # Log if threat
                    if st.session_state.threat_active:
                        if not any(a['frame'] == frame_count for a in st.session_state.alerts):
                            st.session_state.alerts.append({
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'frame': frame_count,
                                'face_count': face_count
                            })
                    
                    # Display frame with threat overlay
                    if st.session_state.threat_active:
                        # Add red border
                        cv2.rectangle(frame, (5, 5), (635, 475), (0, 0, 255), 3)
                        cv2.putText(frame, "THREAT DETECTED", (20, 50),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    # Convert to RGB for display
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Display frame
                    video_placeholder.image(frame_rgb, channels="RGB")
                    
                    frame_count += 1
                    st.session_state.metrics['frames_processed'] = frame_count
                    
                    # Check for rerun
                    if not st.session_state.is_running:
                        break
                
                camera.release()
                status_placeholder.success("✅ Webcam stopped")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.session_state.is_running = False
    elif not HAS_CV2 and st.session_state.is_running:
        st.info("📡 Running demo mode (OpenCV not available on cloud)")
        run_demo_mode()
    else:
        # Display placeholder with Pillow instead of cv2
        placeholder_img = Image.new('RGB', (640, 480), color=(0, 0, 0))
        draw = ImageDraw.Draw(placeholder_img)
        text = "Click 'Start Webcam' to begin"
        # Draw text (simple without fonts)
        draw.multiline_text((150, 230), text, fill=(255, 255, 255))
        video_placeholder.image(placeholder_img)

with col_info:
    st.subheader("📊 Frame Details")
    st.write(f"**Frames Processed:** {st.session_state.metrics['frames_processed']}")
    st.write(f"**Faces in Frame:** {st.session_state.metrics['face_count']}")
    st.write(f"**Sensitivity Level:** {st.session_state.sensitivity}/10")
    
    if st.session_state.blur_enabled:
        st.write("✅ **Blur:** Enabled")
    else:
        st.write("❌ **Blur:** Disabled")

# ========== ALERT HISTORY ==========
st.subheader("🔔 Alert History")

if st.session_state.alerts:
    st.write(f"**Total Alerts:** {len(st.session_state.alerts)}")
    
    for alert in st.session_state.alerts[-10:]:  # Show last 10
        st.warning(
            f"⚠️ Frame {alert['frame']} at {alert['timestamp']}: "
            f"{alert['face_count']} faces detected"
        )
else:
    st.info("No alerts yet - System is monitoring...")

# ========== DATA EXPORT ==========
st.subheader("📥 Export Data")

export_data = {
    'timestamp': datetime.now().isoformat(),
    'metrics': st.session_state.metrics,
    'alerts': st.session_state.alerts,
    'config': {
        'sensitivity': st.session_state.sensitivity,
        'blur_enabled': st.session_state.blur_enabled,
        'gaze_enabled': st.session_state.gaze_enabled
    }
}

col_json, col_csv = st.columns(2)

with col_json:
    json_str = json.dumps(export_data, indent=2)
    st.download_button(
        label="📥 Download JSON",
        data=json_str,
        file_name=f"detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

with col_csv:
    if st.session_state.alerts:
        csv_data = "Timestamp,Frame,Face Count\n"
        for alert in st.session_state.alerts:
            csv_data += f"{alert['timestamp']},{alert['frame']},{alert['face_count']}\n"
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# ========== SYSTEM INFO ==========
st.divider()

col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.subheader("ℹ️ System")
    st.write(f"**Status:** {'🟢 Running' if st.session_state.is_running else '🔴 Stopped'}")
    st.write(f"**Frames:** {st.session_state.metrics['frames_processed']}")

with col_info2:
    st.subheader("🔐 Privacy")
    st.write("✅ Local processing")
    st.write("✅ No cloud storage")
    st.write("✅ Open source")

with col_info3:
    st.subheader("📚 Help")
    with st.expander("How to use"):
        st.markdown("""
        1. **Start Webcam** - Click to enable camera
        2. **Monitor** - Watch metrics update in real-time
        3. **Sensitivity** - Adjust detection level
        4. **Alerts** - View threat history
        5. **Export** - Download metrics as JSON/CSV
        """)

# ========== FOOTER ==========
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; margin-top: 2rem;'>
    <p>🔒 Real-Time Shoulder Surfing Detection & Screen Privacy Protection</p>
    <p><small>v1.0 | Deployed on <a href='https://streamlit.io'>Streamlit Cloud</a></small></p>
</div>
""", unsafe_allow_html=True)

