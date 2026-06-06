import os

def transcribe_audio(audio_path, client):
    """Transcribe audio using Gemini's audio understanding capabilities."""
    if not audio_path or not os.path.exists(audio_path):
        return None
    try:
        # Upload the audio file to Gemini
        uploaded_file = client.files.upload(file=audio_path)

        # Ask Gemini to transcribe
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                uploaded_file,
                "Transcribe this audio file. Distinguish between different speakers. Format the transcript professionally: start a new paragraph (with double line breaks) for each speaker change, and make the speaker labels bold (e.g., **Speaker 1:**). Return only the formatted transcription text."
            ]
        )
        return response.text
    except Exception as e:
        print(f"Transcription error: {e}")
        return None