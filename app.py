# app.py
import os
import time
import whisper
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment
import gradio as gr
import google.generativeai as genai
from meeting_recorder import record_and_process_meeting

# === AUDIO TRANSCRIBER CLASS ===
class AudioTranscriber:
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        print("Whisper model loaded!")

    def validate_audio_file(self, audio_path):
        if not os.path.exists(audio_path):
            raise Exception(f"Audio not found: {audio_path}")
        return True

    def convert_to_wav(self, audio_path, progress_callback=None):
        ext = Path(audio_path).suffix.lower()
        if ext == '.wav':
            return audio_path
        output_path = str(Path(audio_path).with_suffix('.wav'))
        audio = AudioSegment.from_file(audio_path)
        audio.export(output_path, format="wav")
        return output_path

    def transcribe_audio(self, audio_path, progress_callback=None):
        result = self.whisper_model.transcribe(audio_path)
        return result["text"]

    def summarize_transcript(self, transcript, audio_filename, summary_type="comprehensive", progress_callback=None):
        prompts = {
            "comprehensive": f"""
Please analyze and summarize the following audio transcript. The audio file is: "{audio_filename}"

Create a comprehensive summary that includes:
1. Main Topic
2. Key Points
3. Notable Quotes
4. Takeaways
5. Structure

TRANSCRIPT:
{transcript}
""",
            "bullet_points": f"""
Summarize this audio transcript in bullet points:

TRANSCRIPT:
{transcript}
""",
            "brief": f"""
Briefly summarize the transcript below:

TRANSCRIPT:
{transcript}
"""
        }
        prompt = prompts.get(summary_type, prompts["comprehensive"])
        response = self.model.generate_content(prompt)
        return response.text

    def process_audio(self, audio_path, summary_type="comprehensive", cleanup_converted=True, progress_callback=None):
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

transcriber = None

def initialize_transcriber(api_key=None):
    global transcriber
    try:
        if not api_key:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or not api_key.strip():
            return "❌ Please enter your Gemini API key"
        transcriber = AudioTranscriber(api_key.strip())
        return "✅ Transcriber initialized!"
    except Exception as e:
        return f"❌ Initialization error: {str(e)}"

def process_audio_file(audio_file, summary_type, cleanup_converted, progress=gr.Progress()):
    global transcriber
    if not transcriber:
        return "❌ Initialize transcriber first", "", "", ""
    if not audio_file:
        return "❌ Upload an audio file", "", "", ""

    def update_progress(msg):
        progress(0.1, desc=msg)

    audio_path = audio_file.name if hasattr(audio_file, 'name') else str(audio_file)
    try:
        results = transcriber.process_audio(audio_path=audio_path, summary_type=summary_type, cleanup_converted=cleanup_converted, progress_callback=update_progress)
        status = f"✅ Processed: {results['filename']} at {results['processed_at']}"
        return status, results['transcript'], results['summary'], f"{results['summary']}"
    except Exception as e:
        return f"❌ Error: {str(e)}", "", "", ""

# === GUI ===
def create_gui():
    css = ".gradio-container { font-family: 'Arial', sans-serif; }"
    with gr.Blocks(css=css, title="AI Meeting Summarizer") as interface:
        gr.Markdown("## 🎧 AI Meeting Audio Transcriber & Summarizer")

        with gr.Tab("🔧 Setup"):
            api_key_input = gr.Textbox(label="Gemini API Key", type="password")
            init_button = gr.Button("Initialize")
            init_status = gr.Textbox(label="Status")
            init_button.click(fn=initialize_transcriber, inputs=[api_key_input], outputs=[init_status])

        with gr.Tab("🎵 Upload Audio"):
            audio_file = gr.File(label="Upload Audio File")
            summary_type = gr.Dropdown(choices=["comprehensive", "bullet_points", "brief"], value="comprehensive")
            cleanup = gr.Checkbox(label="Clean up temp WAV", value=True)
            process_button = gr.Button("🚀 Process Audio")
            status_out = gr.Textbox(label="Status")
            transcript_out = gr.Textbox(label="Transcript", lines=15)
            summary_out = gr.Textbox(label="Summary", lines=15)
            report_out = gr.Textbox(label="Full Report", lines=20)
            process_button.click(fn=process_audio_file, inputs=[audio_file, summary_type, cleanup],
                                 outputs=[status_out, transcript_out, summary_out, report_out])

        with gr.Tab("🎥 Record Meeting"):
            meeting_link_input = gr.Textbox(label="Meeting Link (Google Meet)")
            duration_input = gr.Slider(label="Recording Duration (mins)", minimum=1, maximum=120, step=1, value=5)
            record_button = gr.Button("🎥 Join & Record Meeting")
            recording_status = gr.Textbox(label="Recording Status")
            transcript_box = gr.Textbox(label="Transcript", lines=10)
            summary_box = gr.Textbox(label="Summary", lines=10)
            record_button.click(fn=record_and_process_meeting,
                                inputs=[meeting_link_input, duration_input],
                                outputs=[recording_status, transcript_box, summary_box])

    return interface

if __name__ == "__main__":
    interface = create_gui()
    interface.launch(server_name="127.0.0.1", server_port=7860)
