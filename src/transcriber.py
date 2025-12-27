from .config import WHISPER_URL
from .api_client import APIClient

class TranscriberService:
    @staticmethod
    def transcribe(audio_path):
        """Transcribe audio file using HF Whisper API."""
        with open(audio_path, "rb") as f:
            data = f.read()
            
        result = APIClient.post(WHISPER_URL, data=data)
        return result.get("text", "")
