# frontend/app.py - Streamlit frontend for SOAP Note App
import streamlit as st
import requests
import time
import json
from audio_recorder_streamlit import audio_recorder
from streamlit_autorefresh import st_autorefresh
import io
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="🩺 SOAP Note App",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Backend URL
BACKEND_URL = "http://127.0.0.1:8002"

# Custom CSS for better UI
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}

.patient-msg {
    background: linear-gradient(135deg, #ffeef8 0%, #f8e8ff 100%);
    color: #2d2d2d;
    padding: 15px;
    border-radius: 15px;
    margin: 10px 0;
    border-left: 5px solid #9C27B0;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.doctor-msg {
    background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%);
    color: #2d2d2d;
    padding: 15px;
    border-radius: 15px;
    margin: 10px 0;
    border-left: 5px solid #2196F3;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.status-active {
    background: #4CAF50;
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: bold;
    display: inline-block;
}

.status-inactive {
    background: #757575;
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: bold;
    display: inline-block;
}

.soap-section {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    border-left: 4px solid #007bff;
}

.conversation-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 10px;
    background: #fafafa;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'listening_mode' not in st.session_state:
    st.session_state.listening_mode = False
if 'soap_note' not in st.session_state:
    st.session_state.soap_note = None

# Helper functions
def call_backend(endpoint, method="GET", data=None, files=None):
    """Call backend API"""
    try:
        url = f"{BACKEND_URL}/{endpoint}"
        if method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Backend error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def start_session():
    """Start a new conversation session"""
    result = call_backend("session/start", "POST", {})
    if result and result.get('success'):
        st.session_state.session_id = result['data']['session_id']
        st.session_state.conversation = []
        st.session_state.listening_mode = True
        st.session_state.soap_note = None
        return True
    return False

def stop_session():
    """Stop current session"""
    if st.session_state.session_id:
        result = call_backend("session/stop", "POST", {"session_id": st.session_state.session_id})
        if result and result.get('success'):
            st.session_state.listening_mode = False
            return True
    return False

def process_audio(audio_bytes):
    """Process audio and add to conversation"""
    if not st.session_state.session_id:
        return False
    
    files = {"audio": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
    result = call_backend(f"voice/process?session_id={st.session_state.session_id}", "POST", files=files)
    
    if result and result.get('success'):
        # Refresh conversation
        get_conversation()
        return True
    return False

def get_conversation():
    """Get current conversation from backend"""
    if not st.session_state.session_id:
        return
    
    result = call_backend(f"session/{st.session_state.session_id}/conversation")
    if result and result.get('success'):
        st.session_state.conversation = result['data']['messages']

def generate_soap_note(patient_name="Unknown Patient"):
    """Generate SOAP note from conversation"""
    if not st.session_state.session_id:
        return False
    
    result = call_backend("soap/generate", "POST", {
        "session_id": st.session_state.session_id,
        "patient_name": patient_name
    })
    
    if result and result.get('success'):
        st.session_state.soap_note = result['data']
        return True
    return False

# Main UI
st.markdown("""
<div class="main-header">
    <h1>🩺 SOAP Note App</h1>
    <p>Real-time Patient-Doctor Conversation Analysis</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh for real-time updates
if st.session_state.listening_mode:
    st_autorefresh(interval=3000, key="conversation_refresh")

# Main layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎤 Voice Recording Control")
    
    # Session status
    if st.session_state.listening_mode:
        st.markdown('<div class="status-active">🔴 LIVE RECORDING</div>', unsafe_allow_html=True)
        st.info(f"Session ID: {st.session_state.session_id}")
    else:
        st.markdown('<div class="status-inactive">⚫ STOPPED</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Control buttons
    if not st.session_state.listening_mode:
        if st.button("🎤 Start Listen Mode", type="primary", use_container_width=True):
            if start_session():
                st.success("✅ Recording started!")
                st.rerun()
            else:
                st.error("❌ Failed to start session")
    else:
        if st.button("🛑 Stop Listen Mode", type="secondary", use_container_width=True):
            if stop_session():
                st.success("✅ Recording stopped!")
                st.rerun()
            else:
                st.error("❌ Failed to stop session")
    
    # Voice recorder (only when listening)
    if st.session_state.listening_mode:
        st.markdown("### 🎙️ Record Voice")
        st.info("👨‍⚕️ Doctor and 🤒 Patient can both speak - the system will identify who is talking!")
        
        audio_bytes = audio_recorder(
            text="🎤 Click to Record",
            recording_color="#e74c3c",
            neutral_color="#4CAF50",
            icon_name="microphone",
            icon_size="2x",
            key=f"voice_recorder_{len(st.session_state.conversation)}"
        )
        
        if audio_bytes:
            with st.spinner("🎧 Processing voice..."):
                if process_audio(audio_bytes):
                    st.success("✅ Voice processed!")
                    st.rerun()
                else:
                    st.error("❌ Failed to process voice")
    
    # Manual refresh button
    if st.session_state.session_id:
        if st.button("🔄 Refresh Conversation", use_container_width=True):
            get_conversation()
            st.rerun()

with col2:
    st.subheader("💬 Live Conversation")
    
    if st.session_state.conversation:
        # Display conversation in scrollable container
        st.markdown('<div class="conversation-container">', unsafe_allow_html=True)
        
        for msg in st.session_state.conversation:
            speaker_emoji = "👨‍⚕️" if msg["speaker"] == "Doctor" else "🤒"
            timestamp = msg.get("timestamp", "")
            confidence = msg.get("confidence", 0)
            
            if msg["speaker"] == "Doctor":
                st.markdown(f"""
                <div class="doctor-msg">
                    <strong style="color: #1976D2;">{speaker_emoji} Doctor [{timestamp}]</strong>
                    <span style="float: right; font-size: 0.8em; color: #666;">Confidence: {confidence:.1%}</span><br>
                    {msg['text']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="patient-msg">
                    <strong style="color: #7B1FA2;">{speaker_emoji} Patient [{timestamp}]</strong>
                    <span style="float: right; font-size: 0.8em; color: #666;">Confidence: {confidence:.1%}</span><br>
                    {msg['text']}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show conversation stats
        total_messages = len(st.session_state.conversation)
        doctor_messages = len([m for m in st.session_state.conversation if m["speaker"] == "Doctor"])
        patient_messages = len([m for m in st.session_state.conversation if m["speaker"] == "Patient"])
        
        st.markdown(f"""
        **📊 Conversation Stats:**
        - Total Messages: {total_messages}
        - Doctor: {doctor_messages} | Patient: {patient_messages}
        """)
        
    else:
        st.info("🎤 Start recording to see live conversation here!")

# SOAP Note Generation Section
st.markdown("---")
st.subheader("📋 SOAP Note Generation")

if st.session_state.conversation:
    col3, col4 = st.columns([1, 2])
    
    with col3:
        patient_name = st.text_input("Patient Name:", value="Unknown Patient")
        
        if st.button("📋 Generate SOAP Note", type="primary", use_container_width=True):
            with st.spinner("🤖 Analyzing conversation and generating SOAP note..."):
                if generate_soap_note(patient_name):
                    st.success("✅ SOAP note generated!")
                else:
                    st.error("❌ Failed to generate SOAP note")
    
    with col4:
        if st.session_state.soap_note:
            soap = st.session_state.soap_note
            
            st.markdown(f"""
            <div class="soap-section">
                <h4>📋 SOAP Note - {soap.get('patient_name', 'Unknown')}</h4>
                <p><strong>Date:</strong> {soap.get('date', 'N/A')} | <strong>Generated:</strong> {soap.get('generated_at', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # SOAP sections
            sections = [
                ("S - Subjective", soap.get('subjective', ''), "#e3f2fd"),
                ("O - Objective", soap.get('objective', ''), "#f3e5f5"),
                ("A - Assessment", soap.get('assessment', ''), "#e8f5e8"),
                ("P - Plan", soap.get('plan', ''), "#fff3e0")
            ]
            
            for title, content, color in sections:
                st.markdown(f"""
                <div style="background: {color}; padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <h5 style="margin: 0 0 10px 0; color: #333;">{title}</h5>
                    <p style="margin: 0; color: #555;">{content}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Download option
            soap_text = f"""
SOAP NOTE
Patient: {soap.get('patient_name', 'Unknown')}
Date: {soap.get('date', 'N/A')}

S - SUBJECTIVE:
{soap.get('subjective', '')}

O - OBJECTIVE:
{soap.get('objective', '')}

A - ASSESSMENT:
{soap.get('assessment', '')}

P - PLAN:
{soap.get('plan', '')}

Generated: {soap.get('generated_at', 'N/A')}
Confidence: {soap.get('confidence_score', 0):.1%}
            """
            
            st.download_button(
                label="📄 Download SOAP Note",
                data=soap_text,
                file_name=f"soap_note_{soap.get('patient_name', 'patient').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

else:
    st.info("📝 Record a conversation first to generate SOAP notes!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🩺 SOAP Note App - Real-time Medical Conversation Analysis</p>
    <p>Built with Streamlit + FastAPI + Groq AI</p>
</div>
""", unsafe_allow_html=True)
