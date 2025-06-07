# meeting_recorder.py
import subprocess, os, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import whisper
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

OUTPUT_AUDIO = "last_meeting_recording.wav"
OUTPUT_SUMMARY = "last_meeting_summary.txt"

# === Minimal Transcriber Class ===
class AudioTranscriber:
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        print("Whisper loaded.")

    def process_audio(self, audio_path):
        print("Transcribing...")
        transcript = self.whisper_model.transcribe(audio_path)["text"]
        print("Summarizing...")
        prompt = f"""Summarize the following meeting transcript:\n\n{transcript}"""
        summary = self.model.generate_content(prompt).text
        return {"transcript": transcript, "summary": summary}

# === Global instance ===
transcriber = None

def initialize_transcriber():
    global transcriber
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("Gemini API key not found in environment or .env file.")
    transcriber = AudioTranscriber(api_key.strip())

# === Browser + Meeting Logic ===
def setup_driver():
    options = Options()
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(service=Service(), options=options)

def join_meeting(driver, url):
    driver.get(url)
    time.sleep(10)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Join now')]"))
        )
        print("Please click 'Join now' manually.")
        time.sleep(10)
    except:
        pass

# === Audio Recording ===
def record_audio(duration_seconds):
    devices = [
        "Stereo Mix (Realtek(R) Audio)",
        "Microphone Array (Realtek(R) Audio)"
    ]
    for device in devices:
        print(f"🔄 Trying device: {device}")
        cmd = [
            "ffmpeg", "-y",
            "-f", "dshow",
            "-i", f"audio={device}",
            "-t", str(duration_seconds),
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            OUTPUT_AUDIO
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(OUTPUT_AUDIO) and os.path.getsize(OUTPUT_AUDIO) > 10000:
            print(f"✅ Recording succeeded with: {device}")
            return OUTPUT_AUDIO
        else:
            print(f"❌ Failed with: {device}")
            print(result.stderr)


# === Entry Point from GUI ===
def record_and_process_meeting(meeting_url: str, duration_minutes: int):
    try:
        initialize_transcriber()
        driver = setup_driver()
        join_meeting(driver, meeting_url)
        duration_seconds = duration_minutes * 60
        audio_file = record_audio(duration_seconds)
        driver.quit()

        if not audio_file:
            return "❌ Recording failed.", "", ""

        results = transcriber.process_audio(audio_file)
        with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
            f.write(results["summary"])
        return "✅ Meeting processed successfully!", results["transcript"], results["summary"]

    except Exception as e:
        return f"❌ Error: {e}", "", ""

def record_audio(duration_seconds):
    devices = [
        "Stereo Mix (Realtek(R) Audio)",
        "Microphone Array (Realtek(R) Audio)"
    ]
    print("🎙️ Available devices to try:", devices)

    for device in devices:
        print(f"🔄 Trying device: {device}")
        cmd = [
            "ffmpeg", "-y",
            "-f", "dshow",
            "-i", f"audio={device}",
            "-t", str(duration_seconds),
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            OUTPUT_AUDIO
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(OUTPUT_AUDIO):
            print(f"✅ Recording succeeded with: {device}")
            return OUTPUT_AUDIO
        else:
            print(f"❌ Failed with: {device}")
            print(result.stderr)

    print("❌ All audio devices failed. Please check device settings or permissions.")
    return None
