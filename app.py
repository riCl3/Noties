# app.py (clean main entry)
import os
import types
import torch
import warnings
import streamlit as st

# === Compatibility Fixes ===
if hasattr(torch, 'classes') and not hasattr(torch.classes, '__path__'):
    torch.classes.__path__ = types.SimpleNamespace(_path=[])
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
warnings.filterwarnings("ignore", category=UserWarning, module="gradio.components.dropdown")

# === Streamlit Setup ===
st.set_page_config(
    page_title="Noties - AI Meeting Summarizer",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === Load External CSS ===
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === Import Core Logic ===
from core import initialize_transcriber
from ui_layout import render_ui

# === Initialize State ===
if 'transcriber' not in st.session_state:
    st.session_state.transcriber = None
if 'audio_recorder' not in st.session_state:
    st.session_state.audio_recorder = None

# === Start UI ===
if __name__ == "__main__":
    render_ui(initialize_transcriber)
