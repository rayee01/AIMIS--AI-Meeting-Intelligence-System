# AI Meeting Bot - Full VSCode Version

## Features
- Streamlit app for prompt-to-speech, transcription, and virtual mic output.
- Uses Google Gemini, gTTS, Whisper, sounddevice.

## Setup

```bash
pip install -r requirements.txt
export GOOGLE_API_KEY=your_google_api_key
streamlit run app.py
```

For virtual mic playback, ensure you have a virtual mic driver like VB-CABLE (Windows) or BlackHole (Mac).