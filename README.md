# Noties - Real-time AI Meeting Assistant

**Noties** is a powerful, locally-running desktop application that acts as your personal AI meeting secretary. It listens to your system audio (Zoom, Teams, Meet, YouTube), transcribes it in real-time using OpenAI's Whisper model, and generates live summaries using advanced LLMs via OpenRouter.

![UI Screenshot](https://via.placeholder.com/800x500?text=Noties+AI+Interface)
*(Replace with actual screenshot)*

## ✨ Features

- **🎙️ System Audio Capture**: Capable of recording "What you hear" (System Audio/Speakers) on Windows using WASAPI Loopback. No virtual cables required!
- **📝 Real-time Transcription**: Uses a local instance of **OpenAI Whisper** to generate accurate transcripts completely offline (privacy-focused).
- **🧠 Live AI Summaries**: Intelligently summarizes the conversation as it happens using **OpenRouter** (flexible model support, e.g., Nvidia Nemotron, Gemini, GPT-4).
- **🎨 Modern Dark UI**: Built with `customtkinter` for a sleek, professional, and responsive user experience.
- **⚡ Robust Architecture**:
  - Thread-safe background processing.
  - Automatic audio resampling (48kHz → 16kHz) for high-accuracy transcription.
  - Continuous audio level monitoring.

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- Windows (for WASAPI Loopback support) / Mac / Linux

### Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/riCl3/Noties.git
   cd Noties
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   *Note: If you don't have PyTorch installed, you might need to install it specifically for your CUDA version from [pytorch.org](https://pytorch.org).*

3. **Configure Environment**:
   - Create a `.env` file in the root directory.
   - Add your OpenRouter API Key:

     ```env
     OPENAI_API_KEY="sk-or-v1-your-key-here"
     ```

## 🛠️ Usage

1. **Run the Application**:

   ```bash
   python main.py
   ```

2. **Select Audio Source**:
   - In the sidebar, select your device.
   - **For Meetings/System Audio**: Select the device labeled **`[SYSTEM AUDIO] Speakers...`**.
   - **For Microphone**: Select your microphone device.

3. **Check Levels**:
   - Play some audio or speak. The **Input Level** bar should move.
   - If it doesn't move, try a different device.

4. **Start Recording**:
   - Click **START RECORDING**.
   - The app will begin transcribing and summarizing in real-time.

## 🔧 Troubleshooting

- **"User not found" (401 Error)**: Check your `.env` file. Ensure there are **no spaces** around the `=` sign (e.g., `KEY="value"`, not `KEY = "value"`).
- **Garbage Transcription?**: If you see text like `1.5%` or repeated characters, it usually means silence or static. The app automatically filters this, but ensure you are selecting the correct active audio device.
- **Audio Meter not moving**: You might have selected a device that isn't playing sound. For system audio, ensure you pick the `[SYSTEM AUDIO]` option corresponding to your active speakers.

## 📦 Tech Stack

- **UI**: CustomTkinter
- **Audio**: SoundDevice, SoundFile, Numpy
- **AI/ML**: OpenAI Whisper (Local), LiteLLM (OpenRouter Interface)

## License

MIT License
