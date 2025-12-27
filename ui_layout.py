# ui_layout.py
import streamlit as st
import tempfile
import os


def render_ui(initialize_transcriber):
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

    # Initialize automatically
    if 'transcriber' not in st.session_state or st.session_state.transcriber is None:
        result = initialize_transcriber()
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)

    if st.session_state.transcriber is not None:
        st.success("✅ Ready to process audio!")
    else:
        st.warning("⚠️ Models are still loading or an error occurred. Please wait or refresh.")

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📁 Upload Audio", "🎙️ Record Meeting", "ℹ️ About"])

    render_upload_tab(tab1)
    render_record_tab(tab2)
    render_about_tab(tab3)


def render_upload_tab(tab):
    with tab:
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
            return

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

        if uploaded_file and st.button("🚀 Process Audio", key="process_btn"):
            with st.spinner("Processing audio file..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False,
                                                     suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name

                    results = st.session_state.transcriber.process_audio(
                        audio_path=tmp_path,
                        summary_type=summary_type,
                        cleanup_converted=cleanup
                    )

                    os.unlink(tmp_path)

                    st.markdown(f"""
                        <div class="status-success">
                            ✅ Processed: {results['filename']} at {results['processed_at']}
                        </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📝 Transcript")
                        st.text_area("", results['transcript'], height=400, key="transcript_upload")
                    with col2:
                        st.subheader("📊 Summary")
                        st.text_area("", results['summary'], height=400, key="summary_upload")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button("📄 Download Transcript", results['transcript'],
                                           file_name=f"transcript_{results['filename']}.txt")
                    with col2:
                        st.download_button("📊 Download Summary", results['summary'],
                                           file_name=f"summary_{results['filename']}.txt")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


def render_record_tab(tab):
    with tab:
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
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            duration = st.slider("Duration (minutes)", 1, 60, 5)
        with col2:
            recording_method = st.selectbox("Recording Mode", ["System Audio (Recommended)", "FFmpeg Fallback"])
        with col3:
            if st.button("🔄 Refresh Devices"):
                st.rerun()

            if st.session_state.audio_recorder:
                devices = st.session_state.audio_recorder.get_audio_devices()
                selected_device = st.selectbox("Audio Device", devices)
            else:
                selected_device = "Default"

        if st.button("🎙️ Start Recording", key="record_btn"):
            try:
                audio_file = st.session_state.audio_recorder.record_system_audio(
                    duration_minutes=duration,
                    device_selection=selected_device
                )
                if audio_file:
                    st.success("✅ Recording completed! Processing...")
                    with st.spinner("Transcribing and summarizing..."):
                        results = st.session_state.transcriber.process_audio(
                            audio_path=audio_file,
                            summary_type="comprehensive",
                            cleanup_converted=False
                        )

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📝 Transcript")
                        st.text_area("", results['transcript'], height=400, key="transcript_record")
                    with col2:
                        st.subheader("📊 Summary")
                        st.text_area("", results['summary'], height=400, key="summary_record")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button("📄 Download Transcript", results['transcript'],
                                           file_name=f"transcript_{results['filename']}.txt")
                    with col2:
                        st.download_button("📊 Download Summary", results['summary'],
                                           file_name=f"summary_{results['filename']}.txt")
                    with col3:
                        with open(audio_file, "rb") as file:
                            st.download_button("🎵 Download Audio", file.read(),
                                               file_name=results['filename'], mime="audio/wav")
                else:
                    st.error("❌ Recording failed. Please check your audio settings.")
            except Exception as e:
                st.error(f"❌ Recording error: {str(e)}")


def render_about_tab(tab):
    with tab:
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
                    <li><strong>AI Summarization:</strong> Powered by your fine-tuned Gemma model for intelligent summaries</li>
                    <li><strong>Direct Recording:</strong> Capture system audio without browser automation</li>
                    <li><strong>Multiple Formats:</strong> Supports MP3, WAV, M4A, OGG, and FLAC files</li>
                    <li><strong>Cloud API Powered:</strong> Fast processing using Hugging Face Inference API</li>
                </ul>

                <h4 style="margin-top: 2rem;">🛠️ How to Use</h4>
                <ol style="font-size: 1.1rem; line-height: 1.8;">
                    <li><strong>Wait for models to load:</strong> The app will initialize automatically.</li>
                    <li><strong>Upload:</strong> Use the "Upload Audio" tab to process existing audio files</li>
                    <li><strong>Record:</strong> Use the "Record Meeting" tab to capture live audio</li>
                    <li><strong>Download:</strong> Save transcripts, summaries, and audio files</li>
                </ol>
            </div>
        </div>
        """, unsafe_allow_html=True)