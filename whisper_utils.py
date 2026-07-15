import os
import time

def transcribe_audio(audio_path, client):
    """Transcribe audio using Gemini's audio understanding capabilities."""
    if not audio_path or not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    uploaded_file = client.files.upload(file=audio_path)

    max_retries = 3
    delay = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=[
                    uploaded_file,
                    "Transcribe this audio file. Distinguish between different speakers. "
                    "Format the transcript professionally: start a new paragraph (with double "
                    "line breaks) for each speaker change, and make the speaker labels bold "
                    "(e.g., **Speaker 1:**). Return only the formatted transcription text."
                ]
            )
            if not response.text:
                raise ValueError(
                    "Gemini returned an empty transcript. This usually means the audio "
                    "was silent, too short, in an unsupported format, or was blocked by "
                    "a safety filter."
                )
            return response.text
        except Exception as e:
            err_str = str(e)
            if attempt < max_retries - 1 and ("503" in err_str or "429" in err_str or "UNAVAILABLE" in err_str):
                time.sleep(delay)
                delay *= 2
            else:
                raise e
