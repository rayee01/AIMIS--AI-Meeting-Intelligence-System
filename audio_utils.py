import os
import io
import streamlit as st
from gtts import gTTS
import numpy as np

# Optional imports
try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    import soundfile as sf
except Exception:
    sf = None

try:
    import soundcard as sc
except Exception:
    sc = None


def text_to_speech(text, filename="output.mp3"):
    """Convert text to speech."""
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(filename)

        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)

        return filename, audio_bytes

    except Exception as e:
        st.error(f"Text-to-speech failed: {e}")
        return None, None


def play_audio_to_virtual_mic(audio_filepath, virtual_mic_name):
    """Disabled on Streamlit Cloud."""
    st.warning("Virtual microphone playback is not supported on Streamlit Cloud.")
    return False


def get_input_devices():
    """Return dummy device list."""
    return ["Recording unavailable on Streamlit Cloud"]


def start_recording(device_index=None, samplerate=16000, channels=1):
    """Disabled on Streamlit Cloud."""
    st.warning("Recording is not supported on Streamlit Cloud.")
    return False


def stop_recording_and_save(filename="live_meeting.wav", samplerate=16000):
    """Disabled on Streamlit Cloud."""
    st.warning("Recording is not supported on Streamlit Cloud.")
    return None
