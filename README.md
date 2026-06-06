# AI Meeting Bot - Full VSCode Version

## Features
- Streamlit app for prompt-to-speech, transcription, and virtual mic output.
- Uses Google Gemini, gTTS, Whisper, sounddevice.

## Setup

1. Rename `.env.example` to `.env` and add your Google Gemini API key:
   `GOOGLE_API_KEY=your_actual_key_here`

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run app.py
```

For virtual mic playback, ensure you have a virtual mic driver like VB-CABLE (Windows) or BlackHole (Mac).