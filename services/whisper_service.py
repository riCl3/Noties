import whisper
import os
import soundfile as sf
import numpy as np

class WhisperTranscriber:
    def __init__(self, model_size="base"):
        """
        Initialize Whisper model.
        model_size: tiny, base, small, medium, large
        """
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        print("Whisper model loaded!")

    def transcribe(self, audio_path):
        """
        Transcribe audio file to text.
        Returns the transcription text.
        """
        try:
            # Verify file exists
            if not os.path.exists(audio_path):
                print(f"Error: Audio file not found: {audio_path}")
                return None
                
            print(f"Transcribing {audio_path}...")
            
            # Load audio with soundfile (avoids ffmpeg dependency)
            audio_data, sample_rate = sf.read(audio_path)
            
            # Convert stereo to mono if needed
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)
            
            # Resample to 16kHz if needed (Whisper requires 16000)
            if sample_rate != 16000:
                print(f"Resampling from {sample_rate} to 16000 Hz")
                # Simple integer downsampling if possible (e.g. 48000 -> 16000)
                if sample_rate % 16000 == 0:
                    step = int(sample_rate / 16000)
                    audio_data = audio_data[::step]
                else:
                    # Basic linear interpolation for other rates
                    old_indices = np.arange(len(audio_data))
                    new_indices = np.linspace(0, len(audio_data) - 1, int(len(audio_data) * 16000 / sample_rate))
                    audio_data = np.interp(new_indices, old_indices, audio_data)
            
            # Whisper expects float32 normalized to [-1, 1]
            audio_data = audio_data.astype(np.float32)
            
            # Transcribe from numpy array
            result = self.model.transcribe(audio_data, fp16=False)
            text = result["text"].strip()
            print(f"Transcription: {text[:100]}...")
            
            # Clean up temp file after successful transcription
            try:
                os.remove(audio_path)
            except:
                pass
                
            return text
        except Exception as e:
            print(f"Transcription Error: {e}")
            import traceback
            traceback.print_exc()
            # Try to clean up on error too
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except:
                pass
            return None
