import os
from dotenv import load_dotenv
import litellm
import json

load_dotenv(override=True)

class LLMRouter:
    def __init__(self, model_name="arcee-ai/trinity-mini:free"):
        """
        Initialize LLM Router with flexible model support.
        
        Args:
            model_name: Model identifier for OpenRouter (e.g., "arcee-ai/trinity-mini:free", "google/gemini-1.5-flash")
        """
        self.model_name = model_name
        self.chat_history = []
        
        # Configure LiteLLM for OpenRouter
        litellm.set_verbose = False  # Disable verbose logging
        
        # Load API key from environment (stored as OPENAI_API_KEY for OpenRouter)
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file. Please add your OpenRouter API key.")

        # INFO: Print loaded key for debugging (masked)
        safe_key = f"{self.api_key[:10]}...{self.api_key[-4:]}" if len(self.api_key) > 10 else "INVALID"
        print(f"DEBUG: Loaded API Key: {safe_key}")
        
        # Ensure environment variable is set for LiteLLM internal usages
        os.environ["OPENAI_API_KEY"] = self.api_key
        
        self.api_base = "https://openrouter.ai/api/v1"
        
        # System prompt for meeting summarization
        self.system_prompt = """
        You are a real-time meeting assistant. 
        I will send you transcribed text chunks from a meeting in progress.
        For each chunk, you must:
        1. Note the new content from this chunk.
        2. Update a running summary of the ENTIRE meeting so far.
        
        Output your response in this JSON format ONLY:
        {
            "new_transcript": "The text from THIS chunk (repeat it).",
            "updated_summary": "The consolidated summary of the ENTIRE meeting so far."
        }
        """
        
        self.start_session()
    
    def start_session(self):
        """Initialize chat history with system prompt."""
        self.chat_history = [
            {"role": "system", "content": self.system_prompt},
            {"role": "assistant", "content": "Understood. I am ready to process the transcripts."}
        ]
    
    def process_transcript(self, transcript_text):
        """
        Send transcript to LLM for summarization.
        
        Args:
            transcript_text: Transcribed text from audio chunk
            
        Returns:
            dict: {"new_transcript": str, "updated_summary": str} or {"error": str}
        """
        if not transcript_text or not transcript_text.strip():
            return {"error": "Empty transcript"}
        
        try:
            # Add user message to history
            user_message = {
                "role": "user",
                "content": f"Here is the next transcript chunk:\n\n{transcript_text}"
            }
            self.chat_history.append(user_message)
            
            # Call LLM via litellm with OpenRouter configuration
            response = litellm.completion(
                model=f"openrouter/{self.model_name}",  # Prefix with openrouter/
                messages=self.chat_history,
                api_key=self.api_key,  # Explicitly pass the API key
                api_base=self.api_base,
                response_format={"type": "json_object"},
                temperature=0.3,
                # OpenRouter-specific headers
                extra_headers={
                    "HTTP-Referer": "https://github.com/noties-app",  # Optional: your app URL
                    "X-Title": "Noties - AI Meeting Assistant"  # Optional: your app name
                }
            )
            
            # Extract response text
            assistant_message = response.choices[0].message.content
            
            # Add assistant response to history
            self.chat_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Parse JSON response
            try:
                result = json.loads(assistant_message)
                return result
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                # Fallback: return raw text
                return {
                    "new_transcript": transcript_text,
                    "updated_summary": assistant_message
                }
        
        except Exception as e:
            print(f"LLM Router Error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def switch_model(self, new_model_name):
        """
        Switch to a different LLM model mid-session.
        
        Args:
            new_model_name: New model identifier
        """
        self.model_name = new_model_name
        print(f"Switched to model: {new_model_name}")
