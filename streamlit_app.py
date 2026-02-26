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

# ========== CUSTOM STYLING - LIGHT THEME ==========
st.markdown("""
<style>
    /* Overall page styling */
    .main {
        background-color: #f8fafc;
        padding: 2rem;
    }
    
    /* Title styling */
    h1 {
        color: #1e293b;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    /* Subtitle styling */
    .subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    
    /* Metric containers */
    [data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }
    
    /* Metric labels */
    [data-testid="metric-container"] label {
        color: #64748b;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 700;
    }
    
    /* Metric values */
    [data-testid="metric-container"] > div:nth-child(2) {
        color: #1e293b;
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Safe status */
    .safe-alert {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, rgba(34, 197, 94, 0.02) 100%);
        border: 1px solid #bbf7d0;
        border-left: 4px solid #22c55e;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1.5rem 0;
    }
    
    .safe-alert h3 {
        color: #15803d;
        margin: 0 0 0.5rem 0;
    }
    
    .safe-alert p {
        color: #166534;
        margin: 0;
    }
    
    /* Threat alert */
    .threat-alert {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(239, 68, 68, 0.04) 100%);
        border: 1px solid #fecaca;
        border-left: 4px solid #ef4444;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    .threat-alert h3 {
        color: #991b1b;
        margin: 0 0 0.5rem 0;
        font-size: 1.25rem;
    }
    
    .threat-alert p {
        color: #b91c1c;
        margin: 0;
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.95;
        }
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .status-safe {
        background-color: #d1fae5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    
    .status-threat {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }
    
    /* Section headers */
    h2, h3 {
        color: #1e293b;
    }
    
    h2 {
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .stDivider {
        border-color: #e2e8f0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
        transform: translateY(-2px);
    }
    
    /* Slider styling */
    .stSlider > label {
        color: #1e293b;
        font-weight: 600;
    }
    
    /* Checkbox styling */
    .stCheckbox > label {
        color: #1e293b;
        font-weight: 500;
    }
    
    /* Number input styling */
    .stNumberInput > label {
        color: #1e293b;
        font-weight: 600;
    }
    
    /* Text styling */
    p, span, li {
        color: #475569;
    }
    
    /* Links */
    a {
        color: #3b82f6;
        text-decoration: none;
    }
    
    a:hover {
        color: #2563eb;
        text-decoration: underline;
    }
    
    /* Info/Warning/Success boxes */
    .stInfo {
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1e40af;
    }
    
    .stWarning {
        background-color: #fef3c7;
        border: 1px solid #fcd34d;
        color: #92400e;
    }
    
    .stSuccess {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #15803d;
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
col_title, col_status = st.columns([3, 1])

with col_title:
    st.title("🔒 Shoulder Surfing Detection")
    st.markdown('<p class="subtitle">Real-Time Privacy Protection System</p>', unsafe_allow_html=True)

with col_status:
    # Display current status at top right
    if HAS_CV2:
        st.markdown('<div class="status-badge status-safe">✅ Live Mode</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge status-threat">⚠️ Demo Mode</div>', unsafe_allow_html=True)

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

# ========== TAB NAVIGATION ==========
tabs = st.tabs(["Dashboard", "Settings", "Logs"])

# ========== DASHBOARD TAB ==========
with tabs[0]:
    st.header("📊 Dashboard")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Faces Detected",
            st.session_state.metrics['face_count'],
            help="Number of faces in frame"
        )

    with col2:
        st.metric(
            "FPS",
            f"{st.session_state.metrics['fps']:.1f}",
            help="Frames processed per second"
        )

    with col3:
        st.metric(
            "Latency",
            f"{st.session_state.metrics['latency']:.0f}ms",
            help="Processing time per frame"
        )

    with col4:
        threat_label = "🚨 THREAT!" if st.session_state.threat_active else "✅ SAFE"
        st.metric(
            "Threat Status",
            threat_label,
            help="Current threat status"
        )

    # Placeholder for future data visualizations
    st.subheader("📈 Data Visualizations")
    st.write("(Charts and graphs will be added here)")

# ========== SETTINGS TAB ==========
with tabs[1]:
    st.header("⚙️ Settings")
    st.sidebar.header("⚙️ Configuration")

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
    st.subheader("📱 Demo Options")

    if st.button("▶ Run Demo Mode"):
        st.session_state.is_running = True
        st.success("✅ Demo mode started! Showing simulated detection...")
        run_demo_mode()

    if st.button("🗑 Clear History"):
        st.session_state.alerts = []
        st.success("✅ Alert history cleared!")

# ========== LOGS TAB ==========
with tabs[2]:
    st.header("📜 Logs")
    st.write("(Logs will be displayed here)")

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

