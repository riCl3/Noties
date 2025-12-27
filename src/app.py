# app.py
import os

import streamlit as st
import time
import tempfile
import warnings 
import streamlit as st
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Import services (local imports since app.py is now in src/)
from transcriber import TranscriberService
from summarizer import SummarizerService
from recorder import SystemAudioRecorder
from audio_utils import AudioUtils

# Disable Streamlit file watcher
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="gradio.components.dropdown")

# Page configuration
st.set_page_config(
    page_title="Noties - AI Meeting Summarizer",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern dark styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main app background */
    .stApp {
        background-color: #0f172a !important;
    }

    /* Main container styling */
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }

    /* Header styling */
    .app-header {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        color: white;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }

    .app-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(45deg, #fff, #e0e7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .app-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 300;
    }

    /* API Configuration Card */
    .api-config-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        border: 1px solid #475569;
    }

    .config-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Card styling */
    .feature-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        border: 1px solid #475569;
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
        border-color: #667eea;
    }

    .card-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .card-icon {
        font-size: 1.8rem;
    }

    /* Status styling */
    .status-success {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 500;
    }

    .status-error {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 500;
    }

    .status-info {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 500;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    /* Input styling */
    .stTextInput > div > div > input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid #475569 !important;
        border-radius: 12px !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }

    /* Select box styling */
    .stSelectbox > div > div {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid #475569 !important;
        border-radius: 12px !important;
    }

    /* Text area styling */
    .stTextArea textarea {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid #475569 !important;
        border-radius: 12px !important;
    }

    .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }

    /* File uploader styling */
    .stFileUploader > div {
        border-radius: 12px;
        border: 2px dashed #475569;
        background: #1e293b;
        color: #f8fafc;
    }

    .stFileUploader label {
        color: #f8fafc !important;
    }

    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 6px;
    }

    /* Metrics styling */
    .metric-container {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        border: 1px solid #475569;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        background: #1e293b;
        color: #94a3b8;
        font-weight: 500;
        border: 1px solid #475569;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: #667eea;
    }

    /* Checkbox styling */
    .stCheckbox > label {
        color: #f8fafc !important;
    }

    /* Slider styling */
    .stSlider > label {
        color: #f8fafc !important;
    }

    /* Success/Warning/Error messages */
    .stSuccess {
        background-color: #065f46 !important;
        color: #ecfdf5 !important;
        border: 1px solid #10b981 !important;
    }

    .stWarning {
        background-color: #92400e !important;
        color: #fef3c7 !important;
        border: 1px solid #f59e0b !important;
    }

    .stError {
        background-color: #7f1d1d !important;
        color: #fecaca !important;
        border: 1px solid #ef4444 !important;
    }

    /* Labels */
    .stSelectbox > label, .stTextInput > label, .stTextArea > label, .stFileUploader > label {
        color: #f8fafc !important;
        font-weight: 500 !important;
    }

    /* Download button styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }

    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(5, 150, 105, 0.3);
    }

    /* Make sure all text is visible */
    .stMarkdown, .stText, p, div, span, label {
        color: #f8fafc !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'audio_recorder' not in st.session_state:
    st.session_state.audio_recorder = None


def initialize_app():
    """Initialize the audio recorder and check API token"""
    try:
        if not os.getenv("HF_TOKEN"):
             return "❌ Error: HF_TOKEN not found in environment."
        
        st.session_state.audio_recorder = SystemAudioRecorder()
        st.session_state.initialized = True
        return "✅ Cloud AI Services initialized!"
    except Exception as e:
        return f"❌ Initialization error: {str(e)}"


def main():
    # Header
    st.markdown("""
        <div class="app-header">
            <div class="app-title">🎧 Noties</div>
            <div class="app-subtitle">Minimal AI Meeting Summarizer: Transcribe & Summarize Effortlessly</div>
            <div style="margin-top: 1.5rem; font-size: 0.9rem; opacity: 0.8;">
                <div style="margin-bottom: 0.5rem;">Developed by Soumya, NIT Allahabad</div>
                <div>
                     Using <b>riCl2/gemma-3-270m-summarizer</b>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


    col1, col2 = st.columns([3, 1])

    with col1:
        st.info("Ensure HF_TOKEN is set in your .env file or deployment secrets.")

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some space
        if st.button("🔄 Initialize", key="init_btn", use_container_width=True):
            with st.spinner("Initializing..."):
                result = initialize_app()
                if "✅" in result:
                    st.success(result)
                else:
                    st.error(result)

    # Show initialization status
    if st.session_state.initialized:
        st.success("✅ Ready to process audio!")
    else:
        st.warning("⚠️ Please initialize first")

    st.markdown("<br>", unsafe_allow_html=True)

    # Main content
    tab1, tab2, tab3 = st.tabs(["📁 Upload Audio", "🎙️ Record Meeting", "ℹ️ About"])

    with tab1:
        st.markdown("""
        <div class="feature-card">
            <div class="card-title">
                <span class="card-icon">📁</span>
                Upload and Summarize Audio File
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.initialized:
            st.warning("⚠️ Please initialize first")
        else:
            col1, col2 = st.columns([2, 1])

            with col1:
                uploaded_file = st.file_uploader(
                    "Choose Audio File",
                    type=['mp3', 'wav', 'm4a', 'ogg', 'flac'],
                    help="Upload your audio file to transcribe and summarize"
                )

            with col2:
                summary_type = st.selectbox(
                    "Summary Style",
                    ["comprehensive", "bullet_points", "brief"],
                    help="Choose the type of summary you prefer"
                )

                cleanup = st.checkbox("Delete temp files", value=True)

            if uploaded_file is not None:
                if st.button("🚀 Process Audio", key="process_btn"):
                    with st.spinner("Processing audio file..."):
                        try:
                            # Save uploaded file temporarily
                            with tempfile.NamedTemporaryFile(delete=False,
                                                             suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_path = tmp_file.name

                            # 1. Validate (just check existence)
                            AudioUtils.validate_file(tmp_path)
                            
                            # 2. Transcribe (Directly send original file to API)
                            st.write("Transcribing...")
                            transcript = TranscriberService.transcribe(tmp_path)
                            
                            # 3. Summarize
                            st.write("Summarizing...")
                            summary = SummarizerService.summarize(transcript, uploaded_file.name, summary_type)

                            # Clean up
                            if cleanup:
                                os.unlink(tmp_path)

                            # Display results
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            st.markdown(f"""
                            <div class="status-success">
                                ✅ Processed: {uploaded_file.name} at {timestamp}
                            </div>
                            """, unsafe_allow_html=True)

                            col1, col2 = st.columns(2)

                            with col1:
                                st.subheader("📝 Transcript")
                                st.text_area("", transcript, height=400, key="transcript_upload",
                                             label_visibility="collapsed")

                            with col2:
                                st.subheader("📊 Summary")
                                st.text_area("", summary, height=400, key="summary_upload",
                                             label_visibility="collapsed")

                            # Download buttons
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    "📄 Download Transcript",
                                    transcript,
                                    file_name=f"transcript_{uploaded_file.name}.txt",
                                    mime="text/plain"
                                )

                            with col2:
                                st.download_button(
                                    "📊 Download Summary",
                                    summary,
                                    file_name=f"summary_{uploaded_file.name}.txt",
                                    mime="text/plain"
                                )

                        except Exception as e:
                            st.markdown(f"""
                            <div class="status-error">
                                ❌ Error: {str(e)}
                            </div>
                            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("""
        <div class="feature-card">
            <div class="card-title">
                <span class="card-icon">🎙️</span>
                Record System Audio and Generate Summary
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.initialized:
            st.warning("⚠️ Please initialize first")
        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                duration = st.slider("Duration (minutes)", min_value=1, max_value=60, value=5)

            with col2:
                # For future use if we add ffmpeg back
                recording_method = st.selectbox(
                    "Recording Mode",
                    ["System Audio (Recommended)"]
                )

            with col3:
                if st.button("🔄 Refresh Devices"):
                    st.rerun()

                # Get audio devices
                if st.session_state.audio_recorder:
                    devices = st.session_state.audio_recorder.get_audio_devices()
                    selected_device = st.selectbox("Audio Device", devices)
                else:
                    selected_device = "Default"

            if st.button("🎙️ Start Recording", key="record_btn"):
                if st.session_state.audio_recorder:
                    try:
                        st.markdown("""
                        <div class="status-info">
                            🎙️ Starting recording... Please ensure your meeting audio is playing!
                        </div>
                        """, unsafe_allow_html=True)

                        # Record audio
                        audio_file = st.session_state.audio_recorder.record_system_audio(
                            duration_minutes=duration,
                            device_selection=selected_device
                        )

                        if audio_file:
                            st.success("✅ Recording completed! Processing...")

                            # Process the recorded audio
                            with st.spinner("Transcribing and summarizing..."):
                                # 2. Transcribe
                                transcript = TranscriberService.transcribe(audio_file)
                                
                                # 3. Summarize
                                summary = SummarizerService.summarize(transcript, audio_file, "comprehensive")


                            st.markdown(f"""
                            <div class="status-success">
                                ✅ Recording processed: {audio_file}
                            </div>
                            """, unsafe_allow_html=True)

                            col1, col2 = st.columns(2)

                            with col1:
                                st.subheader("📝 Transcript")
                                st.text_area("", transcript, height=400, key="transcript_record",
                                             label_visibility="collapsed")

                            with col2:
                                st.subheader("📊 Summary")
                                st.text_area("", summary, height=400, key="summary_record",
                                             label_visibility="collapsed")

                            # Download buttons
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.download_button(
                                    "📄 Download Transcript",
                                    transcript,
                                    file_name=f"transcript_{audio_file}.txt",
                                    mime="text/plain"
                                )
                            with col2: 
                                st.download_button(
                                    "📊 Download Summary",
                                    summary,
                                    file_name=f"summary_{audio_file}.txt",
                                    mime="text/plain"
                                )

                            with col3:
                                with open(audio_file, "rb") as file:
                                    st.download_button(
                                        "🎵 Download Audio",
                                        file.read(),
                                        file_name=audio_file,
                                        mime="audio/wav"
                                    )
                        else:
                            st.error("❌ Recording failed. Please check your audio settings.")

                    except Exception as e:
                        st.error(f"❌ Recording error: {str(e)}")
                else:
                    st.error("❌ Audio recorder not initialized")

    with tab3:
        st.markdown("""
        <div class="feature-card">
            <div class="card-title">
                <span class="card-icon">ℹ️</span>
                About Noties
            </div>
            <div style="margin-top: 1.5rem;">
                <h4>🎯 Features</h4>
                <ul style="font-size: 1.1rem; line-height: 1.8;">
                    <li><strong>Smart Transcription:</strong> Uses OpenAI Whisper (Large-v3) via HF API</li>
                    <li><strong>AI Summarization:</strong> Powered by Gemma-3-270m via HF API</li>
                    <li><strong>Direct Recording:</strong> Capture system audio directly</li>
                    <li><strong>Cloud Powered:</strong> No heavy local models downloads required</li>
                    <li><strong>Privacy First:</strong> Secure API transmission</li>
                </ul>

                <h4 style="margin-top: 2rem;">🛠️ How to Use</h4>
                <ol style="font-size: 1.1rem; line-height: 1.8;">
                    <li><strong>Setup:</strong> Ensure HF_TOKEN is in .env and click Initialize</li>
                    <li><strong>Upload:</strong> Use the "Upload Audio" tab to process existing audio files</li>
                    <li><strong>Record:</strong> Use the "Record Meeting" tab to capture live audio</li>
                    <li><strong>Download:</strong> Save transcripts, summaries, and audio files</li>
                </ol>

                <h4 style="margin-top: 2rem;">🔑 API Key Setup</h4>
                <p style="font-size: 1.1rem; line-height: 1.8;">
                    Get your free User Access Token from 
                    <a href="https://huggingface.co/settings/tokens" target="_blank" style="color: #667eea; text-decoration: none; font-weight: 600;">
                        Hugging Face Settings
                    </a>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Statistics/Metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class="metric-container">
                <h3 style="color: #667eea; margin: 0;">🎯</h3>
                <h4 style="margin: 0.5rem 0;">Accurate</h4>
                <p style="margin: 0; color: #94a3b8;">Whisper-powered transcription</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-container">
                <h3 style="color: #10b981; margin: 0;">⚡</h3>
                <h4 style="margin: 0.5rem 0;">Fast</h4>
                <p style="margin: 0; color: #94a3b8;">Quick AI summarization</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="metric-container">
                <h3 style="color: #f59e0b; margin: 0;">☁️</h3>
                <h4 style="margin: 0.5rem 0;">Lightweight</h4>
                <p style="margin: 0; color: #94a3b8;">Cloud Inference API</p>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()