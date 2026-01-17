import customtkinter as ctk
import threading
import time
import queue
from services.audio_service import AudioRecorder
from services.whisper_service import WhisperTranscriber
from services.llm_router import LLMRouter

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class NotiesApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Noties - Realtime AI Meeting Assistant")
        self.geometry("1100x700")

        # Services
        self.audio_recorder = AudioRecorder(chunk_duration=15)
        self.transcriber = WhisperTranscriber(model_size="base")
        # Using OpenRouter with free Nvidia model
        self.llm = LLMRouter(model_name="nvidia/nemotron-nano-9b-v2:free")
        
        # State
        self.is_running = False
        self.process_thread = None

        self._init_ui()

    def _init_ui(self):
        # Configure Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar (Left Panel) ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#1e1e1e") # Darker Sidebar
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1) # Spacer push to bottom

        # Logo / Title
        self.logo_label = ctk.CTkLabel(self.sidebar, text="NOTIES AI", 
                                     font=ctk.CTkFont(family="Roboto", size=24, weight="bold"),
                                     text_color="white")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10), sticky="w")
        
        ctk.CTkLabel(self.sidebar, text="Meeting Assistant", 
                     font=ctk.CTkFont(family="Roboto", size=12),
                     text_color="#888888").grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Audio Input Section
        ctk.CTkLabel(self.sidebar, text="AUDIO SOURCE", 
                     font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                     text_color="#666666").grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.devices = self.audio_recorder.get_input_devices()
        default_device = self.devices[0] if self.devices else "Default"
        self.device_var = ctk.StringVar(value=default_device)
        self.device_menu = ctk.CTkOptionMenu(self.sidebar, variable=self.device_var, values=self.devices, 
                                           command=lambda x: self._restart_monitoring(),
                                           width=200, fg_color="#333333", button_color="#444444",
                                           text_color="white", dropdown_fg_color="#333333")
        self.device_menu.grid(row=3, column=0, padx=20, pady=0)

        # Audio Meter Section
        ctk.CTkLabel(self.sidebar, text="INPUT LEVEL", 
                     font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                     text_color="#666666").grid(row=4, column=0, padx=20, pady=(20, 5), sticky="w")
        
        # Meter Container
        meter_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        meter_frame.grid(row=5, column=0, padx=20, sticky="ew")
        
        self.level_bar = ctk.CTkProgressBar(meter_frame, height=8, corner_radius=4, 
                                          progress_color="#3B8ED0", fg_color="#333333")
        self.level_bar.pack(fill="x", pady=(0, 5))
        self.level_bar.set(0)
        
        self.level_value = ctk.CTkLabel(meter_frame, text="0%", text_color="gray", 
                                      font=("Roboto", 10), anchor="e")
        self.level_value.pack(side="right")

        # Control Section
        self.start_btn = ctk.CTkButton(self.sidebar, text="START RECORDING", 
                                     command=self.toggle_recording, 
                                     font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
                                     height=40, corner_radius=20,
                                     fg_color="#10B981", hover_color="#059669")
        self.start_btn.grid(row=6, column=0, padx=20, pady=(40, 10), sticky="ew")

        # Status Badge
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="#333333", corner_radius=8)
        self.status_frame.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color="gray", font=("Arial", 16))
        self.status_dot.pack(side="left", padx=(10, 5), pady=5)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", text_color="#aaaaaa", font=("Roboto", 12))
        self.status_label.pack(side="left", pady=5)


        # --- Main Content (Split View) ---
        self.content = ctk.CTkFrame(self, fg_color="#121212") # Very Dark Background
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1) # Transcript
        self.content.grid_columnconfigure(1, weight=1) # Summary
        self.content.grid_rowconfigure(0, weight=1)

        # 1. Transcript Card
        self.transcript_card = self._create_card(self.content, "Live Transcript", "📝", 0)
        self.transcript_box = ctk.CTkTextbox(self.transcript_card, width=400, fg_color="#1E1E1E", 
                                           text_color="#E5E7EB", font=("Roboto", 14),
                                           corner_radius=8)
        self.transcript_box.pack(expand=True, fill="both", padx=15, pady=15)

        # 2. Summary Card
        self.summary_card = self._create_card(self.content, "AI Summary", "🧠", 1)
        self.summary_box = ctk.CTkTextbox(self.summary_card, width=400, fg_color="#1E1E1E", 
                                        text_color="#E5E7EB", font=("Roboto", 14),
                                        corner_radius=8)
        self.summary_box.pack(expand=True, fill="both", padx=15, pady=15)
        
        # Initial Text
        self.transcript_box.insert("end", "Waiting for audio...\n")
        self.transcript_box.configure(state="disabled")
        
        self.summary_box.insert("end", "Summary will appear here...\n")
        self.summary_box.configure(state="disabled")

        # Start Monitoring Stream (Levels only)
        # Default to first available device
        self._restart_monitoring()

        # Start Processing Thread
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True) # Daemon!
        self.process_thread.start()
        
        # Start level monitoring timer
        self._update_level_meter()

    def _create_card(self, parent, title, icon, col):
        """Helper to create consistent card layout"""
        card = ctk.CTkFrame(parent, fg_color="#262626", corner_radius=15)
        card.grid(row=0, column=col, sticky="nsew", padx=15, pady=15)
        
        # Header
        header = ctk.CTkFrame(card, fg_color="transparent", height=40)
        header.pack(fill="x", padx=15, pady=(15, 0))
        
        ctk.CTkLabel(header, text=icon, font=("Arial", 20)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(header, text=title.upper(), font=("Roboto", 12, "bold"), 
                     text_color="#AAAAAA").pack(side="left")
        
        return card

    def _restart_monitoring(self):
        """Restarts audio stream with current device selection."""
        device = self.device_var.get()
        self.audio_recorder.start_stream(device)

    def toggle_recording(self):
        if not self.is_running:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_running = True
        self.start_btn.configure(text="STOP RECORDING", fg_color="#EF4444", hover_color="#DC2626") # Red
        self.update_status("Recording...", "active")
        
        # Enable capturing (stream is already running)
        self.audio_recorder.start_recording()
        
    def stop_recording(self):
        self.is_running = False
        self.start_btn.configure(text="START RECORDING", fg_color="#10B981", hover_color="#059669") # Green
        self.update_status("Stopped (Monitoring)", "idle")
        
        # Disable capturing (monitoring continues)
        self.audio_recorder.stop_recording()

    def _update_level_meter(self):
        """Poll audio level and update meter (runs on UI thread)."""
        # This method now runs continuously after _init_ui
        if self.audio_recorder.is_stream_active(): # Check if stream is active
            level = self.audio_recorder.get_audio_level()
            self._update_audio_level(level)
        # Schedule next update in 100ms regardless of recording state
        self.after(100, self._update_level_meter)

    def _process_loop(self):
        # Keep thread alive to process queue
        while True:
            # Get chunk (timeout allows checking if we should exit)
            try:
                item = self.audio_recorder.get_next_chunk()
            except:
                continue
            
            if not item:
                continue
            
            # Handle errors
            if isinstance(item, dict) and "error" in item:
                self.update_status(f"Error: {item['error']}", "error")
                self.stop_recording()
                break
                    
            audio_path = item
            if audio_path:
                self.update_status(f"Transcribing...", "active")
                
                # 2. Transcribe with Whisper
                try:
                    # Method is transcribe() and returns string
                    text = self.transcriber.transcribe(audio_path)
                    
                    if not text:
                        text = ""
                    else:
                        text = text.strip()
                    
                    print(f"RAW Transcription: [{text}]") # DEBUG
                    
                    # Simple hallucination filter
                    is_hallucination = (
                        len(text) < 5 or 
                        "1.5%" in text or 
                        "2.5%" in text or 
                        "1-2-3-4" in text or
                        text.count(text.split()[0]) > 4 
                    )
                    
                    if is_hallucination:
                        print(f"Skipping hallucination: {text[:50]}...")
                        self.update_status("Skipping silence...", "active")
                        continue
                        
                    # Safe Update Transcript
                    self.after(0, lambda t=text: self._safe_append_transcript(t))
                        
                    self.update_status(f"Summarizing...", "active")
                    
                    # 3. Summarize with LLM
                    result = self.llm.process_transcript(text)
                    
                    # Always show transcript, even if summary fails
                    if result and "error" not in result:
                        summary = result.get("updated_summary", "")
                        if summary:
                             # Safe Update Summary
                             self.after(0, lambda s=summary: self._safe_update_summary(s))
                        
                        self.update_status("Recording...", "active")
                except Exception as e:
                    print(f"Processing Error: {e}")
                    self.update_status(f"Error: {str(e)[:30]}...", "error")

    def _safe_append_transcript(self, text):
        self.transcript_box.configure(state="normal")
        self.transcript_box.insert("end", text + "\n\n")
        self.transcript_box.configure(state="disabled")
        self.transcript_box.see("end")

    def _safe_update_summary(self, summary):
        self.summary_box.configure(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("end", summary)
        self.summary_box.configure(state="disabled")
        
    def update_status(self, text, state="normal"):
        """Update status label and dot color."""
        color = "#aaaaaa" # Default Gray
        dot_color = "gray"
        
        if state == "active":
            color = "#10B981" # Green
            dot_color = "#10B981"
        elif state == "error":
            color = "#EF4444" # Red
            dot_color = "#EF4444"
            
        # Use after to be thread safe
        def _update():
            self.status_label.configure(text=text, text_color=color)
            self.status_dot.configure(text_color=dot_color)
            if state == "active":
                self.level_bar.configure(progress_color="#10B981") # Green bar when recording
            else:
                self.level_bar.configure(progress_color="#3B8ED0") # Blue bar when monitoring
                
        self.after(0, _update)

    def _update_audio_level(self, level):
        """Update the audio level meter."""
        self.level_bar.set(level / 100.0)  # 0.0 to 1.0
        self.level_value.configure(text=f"{level}%")
        
        # Change color based on level
        if level > 80:
            self.level_bar.configure(progress_color="#EF4444") # Red clip
        elif self.is_running:
             self.level_bar.configure(progress_color="#10B981") # Green record
        else:
             self.level_bar.configure(progress_color="#3B8ED0") # Blue monitor
