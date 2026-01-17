from .config import GEMMA_URL
from .api_client import APIClient

class SummarizerService:
    @staticmethod
    def summarize(transcript, audio_filename, summary_type="comprehensive"):
        """Summarize transcript using Gemma-3 model."""
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
            "options": {"wait_for_model": True}
        }
        
        result = APIClient.post(GEMMA_URL, json=payload)
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get('generated_text', "").strip()
        return "No summary generated."
