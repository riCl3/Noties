import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# API Endpoints
WHISPER_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
GEMMA_URL = "https://api-inference.huggingface.co/models/riCl2/gemma-3-270m-summarizer"
