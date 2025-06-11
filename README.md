
# 🎧 Noties — AI Meeting Summarizer

**Noties** is a sleek, AI-powered meeting note-taker built with **Streamlit** that transcribes and summarizes your meetings and recordings with minimal effort. It uses **OpenAI's Whisper** for transcription and **Google's Gemini** for generating concise, intelligent summaries — all processed locally for privacy.

![Noties Demo](assets/noties-demo.gif) <!-- Replace with your actual screenshot or gif -->

---

## 🚀 Live Demo

👉 *Coming soon on Streamlit Cloud*  
*(Deploy it easily via [Streamlit Cloud](https://streamlit.io/cloud))*

---

## 📌 Features

- 🎙️ **Smart Transcription**: Accurate speech-to-text via Whisper.
- 🧠 **AI-Powered Summarization**: Powered by Gemini (`gemini-1.5-flash`).
- 🔊 **Audio Input Options**:
  - Upload audio (MP3, WAV, FLAC, M4A, OGG)
  - Record live audio from mic/system (via `meeting_recorder.py`)
- 📝 **Custom Summaries**:
  - ✔️ Comprehensive
  - 📌 Bullet Points
  - ⚡ Brief
- 🧾 **Editable, Downloadable Notes**.
- 🔐 **Fully Local Processing**: Your data stays with you.

---

## 🛠️ Tech Stack

| Layer        | Technology                                               |
|--------------|-----------------------------------------------------------|
| Frontend     | [Streamlit](https://streamlit.io)                         |
| Backend      | Python, Whisper, Gemini API                               |
| Audio Utils  | Pydub, SoundDevice, SoundFile                             |
| ML Models    | OpenAI Whisper, Gemini `gemini-1.5-flash`                 |
| Deployment   | Streamlit Cloud / Localhost                               |

---

## 🧠 How It Works

1. **Upload or record** an audio file.
2. The file is **converted to WAV** (if needed) using `pydub`.
3. Transcription is handled by **Whisper**.
4. A **prompted summary** is generated using Gemini.
5. Final output includes editable **transcript + summary**.

---

## 📁 Project Structure

```

Noties/
├── app.py                      # Streamlit frontend
├── meeting_recorder.py         # (Optional) record system audio
├── .env                        # API key (user-provided)
├── requirements.txt            # Python dependencies
└── README.md                   # This file

````

Rest Files get Created automatically when you run the code. Remember, you need to Create Virtual Environment (.venv) to run the Code.

---

## 📦 Installation & Local Setup

> Get Noties running locally in just a few steps:

### 1. Clone the Repository

```bash
git clone https://github.com/riCl3/Noties.git
cd Noties
````

### 2. Create a Virtual Environment

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

<details>
<summary>📦 Optional: If <code>requirements.txt</code> is missing</summary>

```bash
pip install streamlit torch pydub python-dotenv google-generativeai openai-whisper sounddevice soundfile numpy selenium
```

</details>

### 4. Add Your Gemini API Key

Create a `.env` file in the root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Run the App

```bash
streamlit run app.py
```

---

## 💻 Optional: System Audio Recorder

If you want to record system-level audio (e.g., meetings):

1. Make sure **FFmpeg** is installed and added to your PATH.
2. Run the recorder:

```bash
python meeting_recorder.py
```

This will save a `.wav` file for transcription.

---

## ☁️ Deployment on Streamlit Cloud

Deploy Noties in a few clicks:

1. Push code to GitHub.
2. Go to [Streamlit Cloud](https://streamlit.io/cloud).
3. Create a **New App**, select the repo and branch.
4. Set `GEMINI_API_KEY` in **Secrets**.
5. Click **Deploy** 🎉

---

## 💡 Future Improvements

* 🌐 Multi-language transcription
* 🧑‍💻 Speaker diarization support
* 🔍 Searchable transcript timeline
* 📱 Responsive mobile layout
* 📊 Meeting insights dashboard

---

## 🤝 Contributing

We welcome contributions!

```bash
# Fork and clone the repo
git checkout -b feature/YourFeature
git commit -m "Add YourFeature"
git push origin feature/YourFeature
# Open a Pull Request
```

---

## 📜 License

This project is licensed under the MIT License — see `LICENSE` for details.

---

## 🙌 Acknowledgements

* [OpenAI Whisper](https://github.com/openai/whisper)
* [Gemini (Google AI)](https://ai.google.dev)
* [Streamlit](https://streamlit.io)
* [Soumya Das](https://github.com/riCl3) — for ideation, implementation, and design

---

> Made with ❤️ by **Soumya** @ NIT Allahabad
> Let's build smarter meetings, together.

```
