# core.py
import os
import time
import whisper
import numpy as np
from pathlib import Path
from datetime import datetime
from pydub import AudioSegment
import google.generativeai as genai
import sounddevice as sd
import soundfile as sf
import streamlit as st


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
Please analyze and summarize the following audio transcript. The audio file is: \"{audio_filename}\"

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


class SystemAudioRecorder:
    def __init__(self, transcriber):
        self.transcriber = transcriber
        self.recording = False
        self.audio_data = []

    def get_audio_devices(self):
        try:
            devices = sd.query_devices()
            return ["Default"] + [f"{i}: {d['name'][:37] + '...' if len(d['name']) > 40 else d['name']}"
                                   for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        except Exception as e:
            st.error(f"Error getting audio devices: {e}")
            return ["Default"]

    def parse_device_selection(self, device_selection):
        if not device_selection or device_selection == "Default":
            return None
        try:
            return int(device_selection.split(":")[0])
        except:
            return None

    def record_system_audio(self, duration_minutes, device_selection=None):
        try:
            duration_seconds = duration_minutes * 60
            sample_rate = 44100
            device_id = self.parse_device_selection(device_selection)
            progress_bar = st.progress(0)
            status_text = st.empty()

            configs = [
                {"channels": 2, "device": device_id},
                {"channels": 1, "device": device_id},
                {"channels": 2, "device": None},
                {"channels": 1, "device": None},
            ]

            successful_config = next((cfg for cfg in configs if self._try_config(cfg, sample_rate)), None)
            if not successful_config:
                raise Exception("No suitable audio configuration found")

            status_text.text("Recording audio...")
            progress_bar.progress(30)
            audio_data = sd.rec(int(duration_seconds * sample_rate), samplerate=sample_rate,
                                channels=successful_config["channels"], device=successful_config["device"],
                                dtype=np.float32)

            for i in range(duration_seconds):
                progress_bar.progress(30 + int(50 * (i / duration_seconds)))
                status_text.text(f"Recording... {i + 1}/{duration_seconds} seconds")
                time.sleep(1)

            sd.wait()

            filename = f"meeting_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            sf.write(filename, audio_data, sample_rate)
            if not os.path.exists(filename) or os.path.getsize(filename) < 1000:
                raise Exception("Audio file not created properly")

            progress_bar.progress(100)
            status_text.text("Recording completed!")
            return filename

        except Exception as e:
            st.error(f"Recording error: {e}")
            return None

    def _try_config(self, config, sample_rate):
        try:
            sd.rec(int(1 * sample_rate), samplerate=sample_rate,
                   channels=config["channels"], device=config["device"], dtype=np.float32)
            sd.wait()
            return True
        except:
            return False


def initialize_transcriber(api_key):
    try:
        if not api_key.strip():
            return "❌ Please enter your Gemini API key"
        st.session_state.transcriber = AudioTranscriber(api_key.strip())
        st.session_state.audio_recorder = SystemAudioRecorder(st.session_state.transcriber)
        return "✅ Transcriber and audio recorder initialized!"
    except Exception as e:
        return f"❌ Initialization error: {str(e)}"
