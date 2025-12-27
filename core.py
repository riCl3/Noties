# core.py
import os
import time
import requests
import numpy as np
from pathlib import Path
from datetime import datetime
from pydub import AudioSegment
import sounddevice as sd
import soundfile as sf
import streamlit as st

class AudioTranscriber:
    def __init__(self):
        with st.spinner("Connecting to AI Cloud Services..."):
            # Configuration for the Hugging Face Inference API
            self.hf_token = os.getenv("HF_TOKEN")
            self.headers = {"Authorization": f"Bearer {self.hf_token}"}
            
            # API Endpoints
            # Whisper for transcription (Speech-to-Text)
            self.whisper_url = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
            
            # Your fine-tuned Gemma-3 model for summarization
            # Replace with [Your-HF-Username]/[Your-Model-Name]
            self.gemma_url = "https://api-inference.huggingface.co/models/[Your-HF-Username]/[Your-Model-Name]"

    def validate_audio_file(self, audio_path):
        if not os.path.exists(audio_path):
            raise Exception(f"Audio file not found: {audio_path}")
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
        """Sends audio binary to Hugging Face Whisper API for transcription."""
        with open(audio_path, "rb") as f:
            data = f.read()
        
        # Calling the Serverless Inference API for Whisper
        response = requests.post(self.whisper_url, headers=self.headers, data=data)
        
        if response.status_code == 200:
            return response.json().get("text", "Transcription failed or returned empty.")
        else:
            raise Exception(f"Whisper API Error: {response.status_code} - {response.text}")

    def summarize_transcript(self, transcript, audio_filename, summary_type="comprehensive"):
        """Sends transcript to your merged Gemma-3 model for AI summarization."""
        instructions = {
            "comprehensive": f"Analyze the following meeting transcript and provide a comprehensive summary. The audio file is: \"{audio_filename}\"\n\nThe summary should include:\n1. Main Topic\n2. Key Points\n3. Action Items\n4. Decisions Made",
            "bullet_points": "Summarize this audio transcript in clear bullet points, focusing on key decisions and action items.",
            "brief": "Provide a brief, one-paragraph summary of this meeting transcript."
        }

        instruction = instructions.get(summary_type, instructions["comprehensive"])
        
        # Gemma-3 chat format
        prompt = f"<bos><start_of_turn>user\n{instruction}\n\n{transcript}<end_of_turn>\n<start_of_turn>model\n"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.7,
                "return_full_text": False
            },
            "options": {
                "wait_for_model": True # Ensures the model loads if it was inactive
            }
        }

        # Calling the Serverless Inference API for your Gemma model
        response = requests.post(self.gemma_url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                # The API often returns the full text or just the generation depending on endpoint config.
                # Usually return_full_text=False handles it, but let's be safe.
                return result[0].get('generated_text', "No summary returned.").strip()
            return "Unexpected response format from summarizer API."
        else:
            raise Exception(f"Gemma API Error: {response.status_code} - {response.text}")

    def process_audio(self, audio_path, summary_type="comprehensive", cleanup_converted=True):
        converted_path = None
        try:
            self.validate_audio_file(audio_path)
            converted_path = self.convert_to_wav(audio_path)
            
            # Step 1: Transcribe via Cloud API
            transcript = self.transcribe_audio(converted_path)
            
            # Step 2: Summarize via Cloud API
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
                raise Exception("Audio file was not recorded successfully.")

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

def initialize_transcriber():
    try:
        # Check for the required token in .env
        if not os.getenv("HF_TOKEN"):
            return "❌ Error: HF_TOKEN not found. Please add it to your .env file."
            
        if 'transcriber' not in st.session_state or st.session_state.transcriber is None:
            st.session_state.transcriber = AudioTranscriber()
            st.session_state.audio_recorder = SystemAudioRecorder(st.session_state.transcriber)
        return "✅ AI Cloud Services initialized!"
    except Exception as e:
        return f"❌ Initialization error: {str(e)}"