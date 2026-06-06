import os
import io
import queue
import threading
import numpy as np
import streamlit as st
from gtts import gTTS
import sounddevice as sd
import soundfile as sf


def text_to_speech(text, filename="output.mp3"):
    """Convert text to speech and return the audio bytes + saved file path."""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        # Save to file
        tts.save(filename)
        # Also return bytes for Streamlit audio player
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return filename, audio_bytes
    except Exception as e:
        st.error(f"Text-to-speech failed: {e}")
        return None, None

def play_audio_to_virtual_mic(audio_filepath, virtual_mic_name):
    """Play an audio file to a virtual microphone device."""
    try:
        if not os.path.exists(audio_filepath):
            st.error(f"Audio file not found: {audio_filepath}")
            return False
        data, fs = sf.read(audio_filepath, dtype='float32')
        devices = sd.query_devices()
        output_device_id = next(
            (i for i, d in enumerate(devices)
             if virtual_mic_name.lower() in d['name'].lower() and d['max_output_channels'] > 0),
            -1
        )
        if output_device_id != -1:
            sd.play(data, fs, device=output_device_id)
            sd.wait()
            return True
        else:
            st.warning(f"Virtual mic '{virtual_mic_name}' not found. Available devices:")
            for i, d in enumerate(devices):
                if d['max_output_channels'] > 0:
                    st.text(f"  [{i}] {d['name']}")
            return False
    except Exception as e:
        st.error(f"Playback error: {e}")
        return False

# Global variables for recording
recording_flag = False
recording_threads = []
mic_queue = queue.Queue()
spk_queue = queue.Queue()

import soundcard as sc

def get_input_devices():
    """Return a list of available input devices."""
    return ["[0] Default (Mic + System Audio)"]

import ctypes
import sys

def _record_device(device, queue_obj, samplerate):
    if sys.platform == 'win32':
        ctypes.windll.ole32.CoInitialize(None)
    try:
        with device.recorder(samplerate=samplerate) as rec:
            while recording_flag:
                # Use a small numframes to check recording_flag frequently
                data = rec.record(numframes=1024)
                queue_obj.put(data)
    except Exception as e:
        print(f"Error recording from {device.name}: {e}")
    finally:
        if sys.platform == 'win32':
            ctypes.windll.ole32.CoUninitialize()

def start_recording(device_index=None, samplerate=16000, channels=1):
    """Start continuous background audio recording for both mic and speakers."""
    global recording_flag, recording_threads, mic_queue, spk_queue
    
    if sys.platform == 'win32':
        ctypes.windll.ole32.CoInitialize(None)
        
    recording_flag = True
    
    # Clear queues
    with mic_queue.mutex:
        mic_queue.queue.clear()
    with spk_queue.mutex:
        spk_queue.queue.clear()
        
    try:
        mic = sc.default_microphone()
        spk = sc.get_microphone(sc.default_speaker().id, include_loopback=True)
        
        t_mic = threading.Thread(target=_record_device, args=(mic, mic_queue, samplerate))
        t_spk = threading.Thread(target=_record_device, args=(spk, spk_queue, samplerate))
        
        recording_threads = [t_mic, t_spk]
        t_mic.start()
        t_spk.start()
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        st.error(f"Failed to start recording: {e}")
        recording_flag = False
        return False

def stop_recording_and_save(filename="live_meeting.wav", samplerate=16000):
    """Stop recording, collect all chunks from both mic and speakers, mix them, and save to a WAV file."""
    global recording_flag, recording_threads, mic_queue, spk_queue
    recording_flag = False
    
    # Wait for threads to finish
    for t in recording_threads:
        t.join(timeout=2.0)
    recording_threads = []
    
    mic_chunks = []
    while not mic_queue.empty():
        mic_chunks.append(mic_queue.get())
        
    spk_chunks = []
    while not spk_queue.empty():
        spk_chunks.append(spk_queue.get())
        
    mic_data = np.concatenate(mic_chunks, axis=0) if mic_chunks else np.array([])
    spk_data = np.concatenate(spk_chunks, axis=0) if spk_chunks else np.array([])
    
    # Mix them. We need to match lengths.
    max_len = max(len(mic_data), len(spk_data))
    
    if max_len == 0:
        return None
        
    def pad_and_mono(arr, target_len):
        if len(arr) == 0:
            return np.zeros(target_len, dtype=np.float32)
        if len(arr.shape) > 1:
            arr = np.mean(arr, axis=1) # mix to mono
        if len(arr) < target_len:
            arr = np.pad(arr, (0, target_len - len(arr)), 'constant')
        elif len(arr) > target_len:
            arr = arr[:target_len]
        return arr

    mic_mono = pad_and_mono(mic_data, max_len)
    spk_mono = pad_and_mono(spk_data, max_len)
    
    # Add them together (mix)
    mixed = mic_mono + spk_mono
    
    # Prevent clipping
    max_val = np.max(np.abs(mixed))
    if max_val > 1.0:
        mixed = mixed / max_val
        
    try:
        sf.write(filename, mixed, samplerate)
        return filename
    except Exception as e:
        st.error(f"Failed to save recording: {e}")
        return None