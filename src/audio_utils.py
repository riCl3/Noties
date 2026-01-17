import os
from pathlib import Path

class AudioUtils:
    @staticmethod
    def validate_file(audio_path):
        if not os.path.exists(audio_path):
            raise Exception(f"Audio file not found: {audio_path}")
        return True
