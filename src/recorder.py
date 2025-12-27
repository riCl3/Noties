import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import streamlit as st
from datetime import datetime
import os

class SystemAudioRecorder:
    def __init__(self):
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
