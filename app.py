# app.py
import os
import torch
import types

# Patch torch.classes to avoid Streamlit __path__ scan error
if hasattr(torch, 'classes') and not hasattr(torch.classes, '__path__'):
    torch.classes.__path__ = types.SimpleNamespace(_path=[])

# Disable Streamlit file watcher
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

import time
import whisper
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment
import streamlit as st
import google.generativeai as genai
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import platform
import warnings
import tempfile

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


# === AUDIO TRANSCRIBER CLASS ===
class AudioTranscriber:
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        with st.spinner("Loading Whisper model..."):
            self.whisper_model = whisper.load_model("base")

    def validate_audio_file(self, audio_path):
        if not os.path.exists(audio_path):
            raise Exception(f"Audio not found: {audio_path}")
        return True

    def convert_to_wav(self, audio_path):
        ext = Path(audio_path).suffix.lower()
        if ext == '.wav':
            return audio_path
        output_path = str(Path(audio_path).with_suffix('.wav'))
        audio = AudioSegment.from_file(audio_path)
        audio.export(output_path, format="wav")
        return output_path

    def transcribe_audio(self, audio_path):
        result = self.whisper_model.transcribe(audio_path)
        return result["text"]

    def summarize_transcript(self, transcript, audio_filename, summary_type="comprehensive"):
        prompts = {
            "comprehensive": f"""
Please analyze and summarize the following audio transcript. The audio file is: "{audio_filename}"

Create a comprehensive summary that includes:
1. Main Topic
2. Key Points
3. Notable Quotes
4. Action Items
5. Decisions Made
6. Next Steps

TRANSCRIPT:
{transcript}
""",
            "bullet_points": f"""
Summarize this audio transcript in bullet points format:
- Main topics discussed
- Key decisions made
- Action items
- Important points

TRANSCRIPT:
{transcript}
""",
            "brief": f"""
Provide a brief summary of this meeting transcript:

TRANSCRIPT:
{transcript}
"""
        }
        prompt = prompts.get(summary_type, prompts["comprehensive"])
        response = self.model.generate_content(prompt)
        return response.text

    def process_audio(self, audio_path, summary_type="comprehensive", cleanup_converted=True):
        converted_path = None
        try:
            self.validate_audio_file(audio_path)
            converted_path = self.convert_to_wav(audio_path)
            transcript = self.transcribe_audio(converted_path)
            summary = self.summarize_transcript(transcript, Path(audio_path).name, summary_type)
            if cleanup_converted and converted_path != audio_path:
                os.remove(converted_path)
            return {
                'filename': Path(audio_path).name,
                'original_path': audio_path,
                'transcript': transcript,
                'summary': summary,
                'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            raise e


# === SYSTEM AUDIO RECORDER CLASS ===
class SystemAudioRecorder:
    def __init__(self, transcriber):
        self.transcriber = transcriber
        self.recording = False
        self.audio_data = []

    def get_audio_devices(self):
        """Get list of available audio input devices"""
        try:
            devices = sd.query_devices()
            input_devices = ["Default"]

            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    device_name = device['name']
                    if len(device_name) > 40:
                        device_name = device_name[:37] + "..."
                    device_entry = f"{i}: {device_name}"
                    input_devices.append(device_entry)

            return input_devices
        except Exception as e:
            st.error(f"Error getting audio devices: {e}")
            return ["Default"]

    def parse_device_selection(self, device_selection):
        """Parse device selection and return device ID"""
        if not device_selection or device_selection == "Default":
            return None
        try:
            device_id = int(device_selection.split(":")[0])
            return device_id
        except (ValueError, IndexError):
            return None

    def record_system_audio(self, duration_minutes, device_selection=None):
        """Record system audio directly"""
        try:
            duration_seconds = duration_minutes * 60
            sample_rate = 44100
            device_id = self.parse_device_selection(device_selection)

            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Starting audio recording...")
            progress_bar.progress(10)

            recording_configs = [
                {"channels": 2, "device": device_id},
                {"channels": 1, "device": device_id},
                {"channels": 2, "device": None},
                {"channels": 1, "device": None},
            ]

            successful_config = None

            for config in recording_configs:
                try:
                    status_text.text(f"Testing {config['channels']} channel(s)...")
                    test_duration = 1
                    test_audio = sd.rec(
                        int(test_duration * sample_rate),
                        samplerate=sample_rate,
                        channels=config["channels"],
                        device=config["device"],
                        dtype=np.float32
                    )
                    sd.wait()
                    successful_config = config
                    break
                except Exception:
                    continue

            if not successful_config:
                raise Exception("No suitable audio configuration found")

            status_text.text("Recording audio...")
            progress_bar.progress(30)

            audio_data = sd.rec(
                int(duration_seconds * sample_rate),
                samplerate=sample_rate,
                channels=successful_config["channels"],
                device=successful_config["device"],
                dtype=np.float32
            )

            # Progress updates during recording
            for i in range(duration_seconds):
                progress = 30 + (50 * (i / duration_seconds))
                progress_bar.progress(int(progress))
                status_text.text(f"Recording... {i + 1}/{duration_seconds} seconds")
                time.sleep(1)

            sd.wait()

            status_text.text("Saving audio file...")
            progress_bar.progress(80)

            filename = f"meeting_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            sf.write(filename, audio_data, sample_rate)

            if not os.path.exists(filename) or os.path.getsize(filename) < 1000:
                raise Exception("Audio file was not created properly or is too small")

            progress_bar.progress(100)
            status_text.text("Recording completed!")
            return filename

        except Exception as e:
            st.error(f"Recording error: {e}")
            return None


# Initialize session state
if 'transcriber' not in st.session_state:
    st.session_state.transcriber = None
if 'audio_recorder' not in st.session_state:
    st.session_state.audio_recorder = None


def initialize_transcriber(api_key):
    """Initialize the transcriber and audio recorder"""
    try:
        if not api_key or not api_key.strip():
            return "❌ Please enter your Gemini API key"
        st.session_state.transcriber = AudioTranscriber(api_key.strip())
        st.session_state.audio_recorder = SystemAudioRecorder(st.session_state.transcriber)
        return "✅ Transcriber and audio recorder initialized!"
    except Exception as e:
        return f"❌ Initialization error: {str(e)}"


def main():
    # Header
    # Header
    st.markdown("""
        <div class="app-header">
            <div class="app-title">🎧 Noties</div>
            <div class="app-subtitle">Minimal AI Meeting Summarizer: Transcribe & Summarize Effortlessly</div>
            <div style="margin-top: 1.5rem; font-size: 0.9rem; opacity: 0.8;">
                <div style="margin-bottom: 0.5rem;">Developed by Soumya, NIT Allahabad</div>
                <div>
                    <a href="https://coff.ee/ricl.2" target="_blank" style="color: #fbbf24; text-decoration: none; font-weight: 500;">
                        ☕ Buy me a coffee
                    </a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # API Configuration (Front and Center)
    st.markdown("""
    <div class="api-config-card">
        <div class="config-title">
            <span class="card-icon">🔐</span>
            API Configuration
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col1:
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="Enter your Gemini API key here...",
            help="Get your free API key from Google AI Studio: https://ai.google.dev/"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some space
        if st.button("🔄 Initialize", key="init_btn", use_container_width=True):
            with st.spinner("Initializing..."):
                result = initialize_transcriber(api_key)
                if "✅" in result:
                    st.success(result)
                else:
                    st.error(result)

    # Show initialization status
    if st.session_state.transcriber is not None:
        st.success("✅ Ready to process audio!")
    else:
        st.warning("⚠️ Please enter your API key and initialize first")

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

        if st.session_state.transcriber is None:
            st.warning("⚠️ Please initialize the transcriber first")
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

                            # Process the audio
                            results = st.session_state.transcriber.process_audio(
                                audio_path=tmp_path,
                                summary_type=summary_type,
                                cleanup_converted=cleanup
                            )

                            # Clean up temp file
                            os.unlink(tmp_path)

                            # Display results
                            st.markdown(f"""
                            <div class="status-success">
                                ✅ Processed: {results['filename']} at {results['processed_at']}
                            </div>
                            """, unsafe_allow_html=True)

                            col1, col2 = st.columns(2)

                            with col1:
                                st.subheader("📝 Transcript")
                                st.text_area("", results['transcript'], height=400, key="transcript_upload",
                                             label_visibility="collapsed")

                            with col2:
                                st.subheader("📊 Summary")
                                st.text_area("", results['summary'], height=400, key="summary_upload",
                                             label_visibility="collapsed")

                            # Download buttons
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    "📄 Download Transcript",
                                    results['transcript'],
                                    file_name=f"transcript_{results['filename']}.txt",
                                    mime="text/plain"
                                )

                            with col2:
                                st.download_button(
                                    "📊 Download Summary",
                                    results['summary'],
                                    file_name=f"summary_{results['filename']}.txt",
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

        if st.session_state.transcriber is None:
            st.warning("⚠️ Please initialize the transcriber first")
        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                duration = st.slider("Duration (minutes)", min_value=1, max_value=60, value=5)

            with col2:
                recording_method = st.selectbox(
                    "Recording Mode",
                    ["System Audio (Recommended)", "FFmpeg Fallback"]
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
                                results = st.session_state.transcriber.process_audio(
                                    audio_path=audio_file,
                                    summary_type="comprehensive",
                                    cleanup_converted=False
                                )

                            st.markdown(f"""
                            <div class="status-success">
                                ✅ Recording processed: {results['filename']}
                            </div>
                            """, unsafe_allow_html=True)

                            col1, col2 = st.columns(2)

                            with col1:
                                st.subheader("📝 Transcript")
                                st.text_area("", results['transcript'], height=400, key="transcript_record",
                                             label_visibility="collapsed")

                            with col2:
                                st.subheader("📊 Summary")
                                st.text_area("", results['summary'], height=400, key="summary_record",
                                             label_visibility="collapsed")

                            # Download buttons
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.download_button(
                                    "📄 Download Transcript",
                                    results['transcript'],
                                    file_name=f"transcript_{results['filename']}.txt",
                                    mime="text/plain"
                                )

                            with col2:
                                st.download_button(
                                    "📊 Download Summary",
                                    results['summary'],
                                    file_name=f"summary_{results['filename']}.txt",
                                    mime="text/plain"
                                )

                            with col3:
                                with open(audio_file, "rb") as file:
                                    st.download_button(
                                        "🎵 Download Audio",
                                        file.read(),
                                        file_name=results['filename'],
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
                    <li><strong>Smart Transcription:</strong> Uses OpenAI Whisper for accurate speech-to-text</li>
                    <li><strong>AI Summarization:</strong> Powered by Google Gemini for intelligent summaries</li>
                    <li><strong>Direct Recording:</strong> Capture system audio without browser automation</li>
                    <li><strong>Multiple Formats:</strong> Supports MP3, WAV, M4A, OGG, and FLAC files</li>
                    <li><strong>Privacy First:</strong> All processing happens locally on your machine</li>
                </ul>

                <h4 style="margin-top: 2rem;">🛠️ How to Use</h4>
                <ol style="font-size: 1.1rem; line-height: 1.8;">
                    <li><strong>Setup:</strong> Enter your Gemini API key and click Initialize</li>
                    <li><strong>Upload:</strong> Use the "Upload Audio" tab to process existing audio files</li>
                    <li><strong>Record:</strong> Use the "Record Meeting" tab to capture live audio</li>
                    <li><strong>Download:</strong> Save transcripts, summaries, and audio files</li>
                </ol>

                <h4 style="margin-top: 2rem;">🔑 API Key Setup</h4>
                <p style="font-size: 1.1rem; line-height: 1.8;">
                    Get your free Gemini API key from 
                    <a href="https://ai.google.dev/" target="_blank" style="color: #667eea; text-decoration: none; font-weight: 600;">
                        Google AI Studio
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
                <h3 style="color: #f59e0b; margin: 0;">🔒</h3>
                <h4 style="margin: 0.5rem 0;">Private</h4>
                <p style="margin: 0; color: #94a3b8;">Local processing</p>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()