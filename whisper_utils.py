import os


def transcribe_audio(audio_path, client):
    """Transcribe audio using Gemini's audio understanding capabilities."""
    if not audio_path or not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Let exceptions from upload/generate propagate up to the caller (app.py),
    # which already has a try/except that shows the real error + traceback.
    # Swallowing it here (print + return None) is what was hiding the cause.
    uploaded_file = client.files.upload(file=audio_path)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
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
