from streamlit_mic_recorder import mic_recorder
import streamlit as st
from google import genai
from google.genai import types
import os
from datetime import datetime
import time

from whisper_utils import transcribe_audio
from audio_utils import play_audio_to_virtual_mic, text_to_speech, get_input_devices, start_recording, stop_recording_and_save
import db_utils

# Initialize Database
db_utils.init_db()

import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# --- Google Gemini API Setup ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("GOOGLE_API_KEY environment variable not set. Please check your .env file.")
    st.stop()
client = genai.Client(api_key=api_key)

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "paused" not in st.session_state:
    st.session_state.paused = False
if "last_audio_file" not in st.session_state:
    st.session_state.last_audio_file = ""
if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = ""
if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None
if "last_response" not in st.session_state:
    st.session_state.last_response = ""
if "new_response" not in st.session_state:
    st.session_state.new_response = False
if "new_mom" not in st.session_state:
    st.session_state.new_mom = False
if "mom_text" not in st.session_state:
    st.session_state.mom_text = ""

# --- Mode Prompts ---
role_contexts = {
    "🔁 Repeat": "You are a repeat bot. Repeat the user's message exactly, with no changes or commentary.",
    "✏️ Paraphrase": "You are a helpful assistant. Paraphrase the user's message clearly and crisply and don't go beyond 100 words.",
    "💡 Explain": "Answer the following clearly and directly. Do not rephrase or reflect on the user's question. Just answer it and don't go beyond 100 words."
}

# --- Generate Response ---
def stream_text(text):
    """Simulate a typing effect for Streamlit write_stream"""
    for chunk in text.split(" "):
        yield chunk + " "
        time.sleep(0.02)

def generate_response_with_history(user_input, role_context=None):
    try:
        # Build history as Content objects for the new SDK
        history = []
        for m in st.session_state.messages:
            history.append(types.Content(
                role=m["role"],
                parts=[types.Part.from_text(text=p) for p in m["parts"]]
            ))
        chat = client.chats.create(model="gemini-2.5-flash", history=history)
        full_prompt = (role_context + "\n\n" if role_context else "") + user_input
        
        max_retries = 3
        delay = 2
        for attempt in range(max_retries):
            try:
                response = chat.send_message(full_prompt)
                st.session_state.messages.append({"role": "user", "parts": [user_input]})
                st.session_state.messages.append({"role": "model", "parts": [response.text]})
                return response.text
            except Exception as e:
                err_str = str(e)
                if attempt < max_retries - 1 and ("503" in err_str or "429" in err_str or "UNAVAILABLE" in err_str):
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise e
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return None

# --- MoM Generator ---
def generate_minutes_of_meeting():
    if not st.session_state.messages:
        return "No conversation history to generate minutes."
    convo = ""
    for m in st.session_state.messages:
        role = m["role"].capitalize()
        text = "\n".join(m["parts"])
        convo += f"{role}: {text}\n"
    prompt = f"""You are a meeting assistant. Create professional minutes of the meeting (MoM) from the conversation below. Note that 'Meeting Transcript' indicates raw transcribed audio from the meeting. Use bullet points, group by topics, and highlight key decisions and action items.

Conversation:
{convo}
"""
    max_retries = 3
    delay = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            if attempt < max_retries - 1 and ("503" in err_str or "429" in err_str or "UNAVAILABLE" in err_str):
                time.sleep(delay)
                delay *= 2
            else:
                return f"Failed to generate MoM: {err_str}"

# --- Page Config ---
st.set_page_config(
    page_title="AI Meeting Intelligence System",
    page_icon="🎙️",
    layout="wide"
)

# --- Theme Toggle (Top Right) ---
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

col_spacer, col_toggle = st.columns([8, 2])
with col_toggle:
    is_dark_mode = st.toggle(
        "🌙 Dark Mode" if st.session_state.dark_mode else "☀️ Light Mode",
        key="dark_mode"
    )

if not is_dark_mode:
    theme_vars = """
    :root {
        --bg-base: #f8fafc;
        --bg-glow: radial-gradient(circle at 50% -20%, rgba(37, 99, 235, 0.15), transparent 70%);
        --bg-pattern: radial-gradient(rgba(15, 23, 42, 0.06) 1.5px, transparent 1.5px);
        --text: #0f172a;
        --text-muted: #64748b;
        --card-bg: rgba(255, 255, 255, 0.85);
        --card-blur: blur(12px);
        --border: rgba(226, 232, 240, 0.8);
        --border-hover: #cbd5e1;
        --accent: #2563eb;
        --user-chat: #eff6ff;
        --bot-chat: rgba(255, 255, 255, 0.9);
        --invert: 0;
    }
    """
else:
    theme_vars = """
    :root {
        --bg-base: #09090b;
        --bg-glow: radial-gradient(circle at 50% -20%, rgba(79, 70, 229, 0.2), transparent 70%);
        --bg-pattern: radial-gradient(rgba(250, 250, 250, 0.05) 1.5px, transparent 1.5px);
        --text: #fafafa;
        --text-muted: #a1a1aa;
        --card-bg: rgba(24, 24, 27, 0.75);
        --card-blur: blur(12px);
        --border: rgba(39, 39, 42, 0.8);
        --border-hover: #3f3f46;
        --accent: #4f46e5;
        --user-chat: #27272a;
        --bot-chat: rgba(24, 24, 27, 0.8);
        --invert: 1;
    }
    """

# ========================= CUSTOM CSS =========================
css_template = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    __THEME_VARS__

    /* Global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        color: var(--text) !important;
    }
    
    /* Force Widget Labels to correct color */
    [data-testid="stWidgetLabel"] p {
        color: var(--text) !important;
        font-weight: 500 !important;
    }

    /* Authentic Website Background */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: var(--bg-base) !important;
        background-image: var(--bg-glow), var(--bg-pattern) !important;
        background-size: 100% 100%, 24px 24px !important;
        background-position: 0 0, 0 0 !important;
        background-attachment: fixed !important;
    }

    .stApp {
        background-color: #09090b !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main container */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1000px !important;
    }

    /* Hero title */
    .hero-title {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
    }
    .hero-title h1 {
        font-size: 3rem;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    .hero-title p {
        color: var(--text-muted);
        font-size: 1.1rem;
        font-weight: 500;
        margin-top: 0;
        letter-spacing: 0.5px;
    }

    /* Cards */
    .glass-card, .response-card {
        background-color: var(--card-bg);
        backdrop-filter: var(--card-blur);
        -webkit-backdrop-filter: var(--card-blur);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.02);
    }
    .glass-card:hover, .response-card:hover {
        border-color: var(--border-hover);
    }

    .response-card .label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        margin-bottom: 1rem;
        border-bottom: 1px solid var(--border);
        padding-bottom: 0.5rem;
    }
    .response-card .text {
        color: var(--text);
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Section headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1.25rem;
    }
    .section-header .icon {
        width: 36px;
        height: 36px;
        background-color: var(--border);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        border: 1px solid var(--border-hover);
    }
    .section-header h3 {
        margin: 0;
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--text);
        letter-spacing: -0.025em;
    }

    /* Buttons */
    .stButton > button {
        background-color: var(--text) !important;
        color: var(--bg-base) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }
    .stButton > button:hover {
        background-color: var(--border) !important;
        color: var(--text) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Text area & Select box */
    .stTextArea textarea, .stSelectbox > div > div {
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        padding: 0.75rem !important;
        transition: border-color 0.2s ease !important;
    }
    .stTextArea textarea:focus, .stSelectbox > div > div:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }

    /* Chat messages */
    .chat-msg {
        padding: 1rem 1.25rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        font-size: 0.95rem;
        line-height: 1.6;
        animation: fadeIn 0.2s ease;
    }
    .chat-user {
        background-color: var(--user-chat);
        border-left: 4px solid var(--accent);
        margin-left: 2rem;
        color: var(--text);
    }
    .chat-bot {
        background-color: var(--bot-chat);
        border: 1px solid var(--border);
        margin-right: 2rem;
        color: var(--text);
    }
    .chat-role {
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .chat-role-user { color: var(--text-muted); }
    .chat-role-bot { color: var(--accent); }

    /* File uploader */
    .stFileUploader > div {
        border: 1px dashed var(--border-hover) !important;
        border-radius: 12px !important;
        background-color: var(--card-bg) !important;
        transition: all 0.2s ease !important;
    }
    .stFileUploader > div:hover {
        border-color: var(--text-muted) !important;
    }

    /* Divider */
    .purple-divider {
        height: 1px;
        background-color: var(--border);
        margin: 2rem 0;
    }

    /* Status badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        background-color: var(--card-bg);
        border: 1px solid var(--border);
        color: var(--text-muted);
    }
    .status-online {
        color: #10b981;
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Audio player */
    .stAudio {
        border-radius: 8px !important;
        overflow: hidden !important;
        filter: invert(var(--invert)) hue-rotate(180deg);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 6px;
        border: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px !important;
        color: var(--text-muted) !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--border) !important;
        color: var(--text) !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        color: var(--text) !important;
    }
    
    .audio-visualizer {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 4px;
        height: 40px;
        margin: 15px 0;
    }
    .bar {
        width: 6px;
        background-color: #ef4444;
        border-radius: 3px;
        animation: bounce 0.5s ease-in-out infinite alternate;
    }
    .bar:nth-child(1) { height: 16px; animation-delay: 0s; }
    .bar:nth-child(2) { height: 32px; animation-delay: 0.1s; }
    .bar:nth-child(3) { height: 40px; animation-delay: 0.2s; }
    .bar:nth-child(4) { height: 28px; animation-delay: 0.15s; }
    .bar:nth-child(5) { height: 20px; animation-delay: 0.05s; }
    @keyframes bounce {
        0% { transform: scaleY(0.4); opacity: 0.7; }
        100% { transform: scaleY(1); opacity: 1; }
    }
</style>
"""

st.markdown(css_template.replace("__THEME_VARS__", theme_vars), unsafe_allow_html=True)

# ========================= HERO HEADER =========================
st.markdown("""
<div class="hero-title">
    <h1>AIMIS</h1>
    <p>AI Meeting Intelligence System</p>
</div>
""", unsafe_allow_html=True)

# Status bar
col_status1, col_status2, col_status3 = st.columns([1, 1, 1])
with col_status1:
    st.markdown('<span class="status-badge status-online">● Gemini Connected</span>', unsafe_allow_html=True)
with col_status2:
    msg_count = len(st.session_state.messages) // 2
    st.markdown(f'<span class="status-badge status-online">💬 {msg_count} exchanges</span>', unsafe_allow_html=True)
with col_status3:
    st.markdown(f'<span class="status-badge status-online">🕐 {datetime.now().strftime("%I:%M %p")}</span>', unsafe_allow_html=True)

st.markdown('<div class="purple-divider"></div>', unsafe_allow_html=True)

# ========================= MAIN LAYOUT =========================
tab_transcribe, tab_chat, tab_history, tab_mom, tab_archive = st.tabs(["🎙️ Transcription", "💬 Chat", "📚 History", "📝 Minutes", "🗄️ Archive"])

# ========================= TAB: TRANSCRIPTION =========================
with tab_transcribe:
    st.markdown("""
    <div class="section-header">
        <div class="icon">🎙️</div>
        <h3>Meeting Transcription</h3>
    </div>
    """, unsafe_allow_html=True)

    col_live, col_upload = st.columns([1, 1], gap="large")
    
    with col_live:
        st.markdown("#### 🔴 Live Recording", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; font-size: 0.9rem;'>Select your meeting audio device and record live.</p>", unsafe_allow_html=True)
        
       input_devices = get_input_devices()

if (
    not input_devices
    or "Recording unavailable" in input_devices[0]
):

    st.info("🎙️ Live recording is not available on Streamlit Cloud.")

    btn1, btn2 = st.columns([1,1])

    with btn1:
        st.button("🔴 Start Recording", disabled=True, use_container_width=True)

    with btn2:
        st.button("⏹️ Stop & Transcribe", disabled=True, use_container_width=True)

else:

    selected_device = st.selectbox(
        "Audio Input Device",
        input_devices,
        label_visibility="collapsed"
    )

    device_id = int(selected_device.split("]")[0].replace("[", ""))

    btn1, btn2 = st.columns([1,1])

    with btn1:
        if not st.session_state.is_recording:
            if st.button("🔴 Start Recording", use_container_width=True):
                if start_recording(device_index=device_id):
                    st.session_state.is_recording = True
                    st.session_state.last_transcript = ""
                    st.rerun()
        else:
            st.button("Recording...", disabled=True, use_container_width=True)
    device_id = int(selected_device.split("]")[0].replace("[", ""))

    btn1, btn2 = st.columns([1,1])

    with btn1:
        if not st.session_state.is_recording:
            if st.button("🔴 Start Recording", use_container_width=True):
                if start_recording(device_index=device_id):
                    st.session_state.is_recording = True
                    st.session_state.last_transcript = ""
                    st.rerun()
        else:
            st.button("Recording...", disabled=True, use_container_width=True)
            with btn2:
                if st.session_state.is_recording:
                    if st.button("⏹️ Stop & Transcribe", use_container_width=True):
                        with st.spinner("🎧 Transcribing entire meeting..."):
                            temp_file = stop_recording_and_save("meeting_record.wav")
                            st.session_state.is_recording = False
                            if temp_file:
                                transcript = transcribe_audio(temp_file, client)
                                if transcript:
                                    st.toast("✅ Meeting successfully recorded and transcribed!")
                                    st.session_state.last_transcript = transcript
                                    st.session_state.messages.append({
                                        "role": "user",
                                        "parts": [f"Meeting Transcript:\n{transcript}"]
                                    })
                                else:
                                    st.toast("❌ Failed to transcribe the meeting.", icon="⚠️")
                            st.rerun()
                else:
                    st.button("⏹️ Stop & Transcribe", disabled=True, use_container_width=True)
                    
        if st.session_state.is_recording:
            st.markdown("""
            <div class="audio-visualizer">
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
            </div>
            <div style="text-align:center; color:#ef4444; font-weight:bold; animation: pulse 2s infinite;">Recording Active...</div>
            """, unsafe_allow_html=True)

    with col_upload:
        st.markdown("#### 📁 File Upload", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; font-size: 0.9rem;'>Upload an existing audio file.</p>", unsafe_allow_html=True)
        audio_upload = st.file_uploader(
            "Drop your audio file here",
            type=["wav", "mp3", "m4a", "flac", "ogg"],
            label_visibility="collapsed"
        )
        if st.button("✨ Transcribe File", use_container_width=True):
            if audio_upload:
                ext = os.path.splitext(audio_upload.name)[1] or ".wav"
                upload_path = f"uploaded_audio{ext}"
                with open(upload_path, "wb") as f:
                    f.write(audio_upload.read())
                with st.spinner("🎧 Transcribing uploaded audio..."):
                    transcript = transcribe_audio(upload_path, client)
                    if transcript:
                        st.toast("✅ File successfully transcribed!")
                        st.session_state.last_transcript = transcript
                        st.session_state.messages.append({
                            "role": "user",
                            "parts": [f"Meeting Transcript:\n{transcript}"]
                        })
                    else:
                        st.toast("❌ Could not transcribe the audio.", icon="⚠️")
            else:
                st.toast("ℹ️ Please upload an audio file first.")
                
    if st.session_state.last_transcript:
        st.markdown("""
        <div class="response-card" style="margin-top: 2rem;">
            <div class="label">📝 Transcription Result</div>
            <div class="text">
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.last_transcript)
        st.markdown("</div></div>", unsafe_allow_html=True)

# ========================= TAB: CHAT =========================
with tab_chat:
    left_col, right_col = st.columns([3, 2], gap="large")

    with left_col:
        st.markdown("""
        <div class="section-header">
            <div class="icon">💬</div>
            <h3>Compose Your Message</h3>
        </div>
        """, unsafe_allow_html=True)

        mode = st.selectbox("Select Mode", list(role_contexts.keys()), label_visibility="collapsed")
        role = role_contexts.get(mode)

        # Mode description
        mode_descriptions = {
            "🔁 Repeat": "Echo your message back exactly as spoken",
            "✏️ Paraphrase": "Rephrase your message clearly and concisely",
            "💡 Explain": "Provide a direct, clear answer to your question"
        }
        st.caption(f"**Mode:** {mode_descriptions.get(mode, '')}")

        user_prompt = st.text_area(
            "message_input",
            placeholder="Type your message, question, or meeting topic here...",
            height=140,
            label_visibility="collapsed"
        )

        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            generate_clicked = st.button("🚀 Generate Response", use_container_width=True)
        with btn_col2:
            if st.button("🔊 Play to Virtual Mic", use_container_width=True):
                filename = st.session_state.last_audio_file
                if filename and os.path.exists(filename):
                    if play_audio_to_virtual_mic(filename, "CABLE Input"):
                        st.toast("✅ Playing through virtual mic!")
                    else:
                        st.toast("⚠️ Could not find VB-CABLE. Check your audio devices.")
                else:
                    st.toast("ℹ️ Generate a response first to play audio.")

    with right_col:
        st.markdown("""
        <div class="section-header">
            <div class="icon">🤖</div>
            <h3>AI Response</h3>
        </div>
        """, unsafe_allow_html=True)

        if generate_clicked and user_prompt.strip():
            with st.spinner("✨ Generating response..."):
                response = generate_response_with_history(user_input=user_prompt.strip(), role_context=role)
                if response:
                    st.session_state.last_response = response
                    st.session_state.new_response = True

                    # Generate TTS audio
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    filename = f"response_{timestamp}.mp3"
                    audio_file, audio_bytes = text_to_speech(response, filename)
                    if audio_file:
                        st.session_state.last_audio_file = audio_file
                    if audio_bytes:
                        st.session_state.last_audio_bytes = audio_bytes
        elif generate_clicked:
            st.warning("Please enter a message first.")

        # Display last response
        if st.session_state.last_response:
            clean_mode = mode.split(" ", 1)[-1] if " " in mode else mode
            st.markdown(f"""
            <div class="response-card">
                <div class="label">✦ {clean_mode} Response</div>
                <div class="text">
            """, unsafe_allow_html=True)
            
            # Streaming effect for the text
            if st.session_state.new_response:
                st.write_stream(stream_text(st.session_state.last_response))
                st.session_state.new_response = False
            else:
                st.markdown(st.session_state.last_response)
            
            st.markdown("</div></div>", unsafe_allow_html=True)

            # Audio player
            if st.session_state.last_audio_bytes:
                st.markdown("**🔊 Listen:**")
                st.audio(st.session_state.last_audio_bytes, format="audio/mp3")
        else:
            st.markdown("""
            <div class="response-card" style="text-align: center; padding: 3rem 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎙️</div>
                <div class="text" style="color: #64748B;">Your AI response will appear here.<br>Select a mode and type your message to get started.</div>
            </div>
            """, unsafe_allow_html=True)

# ========================= TAB: HISTORY =========================
with tab_history:
    st.markdown("""
    <div class="section-header">
        <div class="icon">📚</div>
        <h3>Conversation History</h3>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.messages:
        if st.button("🗑️ Clear History", use_container_width=False):
            st.session_state.messages = []
            st.session_state.last_response = ""
            st.session_state.last_audio_file = ""
            st.session_state.last_audio_bytes = None
            st.rerun()

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown("""
                <div class="chat-msg chat-user">
                    <div class="chat-role chat-role-user">🧑 You</div>
                """, unsafe_allow_html=True)
                st.markdown(msg['parts'][0])
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="chat-msg chat-bot">
                    <div class="chat-role chat-role-bot">🤖 AIMIS</div>
                """, unsafe_allow_html=True)
                st.markdown(msg['parts'][0])
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="response-card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💭</div>
            <div class="text" style="color: #64748B;">No messages yet. Start a conversation in the Chat tab!</div>
        </div>
        """, unsafe_allow_html=True)

# ========================= TAB: MINUTES =========================
with tab_mom:
    st.markdown("""
    <div class="section-header">
        <div class="icon">📝</div>
        <h3>Minutes of the Meeting</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card">
        <p style="color: #94A3B8;">
            Generate a professional summary of your conversation with key decisions,
            action items, and discussion points organized by topic.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📋 Generate Meeting Minutes", use_container_width=True):
        if st.session_state.messages:
            with st.spinner("📝 Generating meeting minutes..."):
                mom = generate_minutes_of_meeting()
                st.session_state.mom_text = mom
                st.session_state.new_mom = True
        else:
            st.toast("ℹ️ Have a conversation first, then generate minutes!")
            
    if st.session_state.mom_text:
        st.markdown(f"""
        <div class="response-card">
            <div class="label">📋 Meeting Minutes — {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
        """, unsafe_allow_html=True)
        if st.session_state.new_mom:
            st.write_stream(stream_text(st.session_state.mom_text))
            st.session_state.new_mom = False
        else:
            st.markdown(st.session_state.mom_text)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Current Meeting to Archive", use_container_width=True):
            title = f"Meeting - {datetime.now().strftime('%b %d, %Y')}"
            if st.session_state.messages:
                try:
                    title = st.session_state.messages[0]['parts'][0][:40] + "..."
                except:
                    pass
            with st.spinner("💾 Saving to database..."):
                db_utils.save_meeting(
                    title=title,
                    transcript=st.session_state.last_transcript,
                    mom=st.session_state.mom_text,
                    chat_messages=st.session_state.messages
                )
                st.toast("✅ Meeting saved to Archive!")
                
# ========================= TAB: ARCHIVE =========================
with tab_archive:
    st.markdown("""
    <div class="section-header">
        <div class="icon">🗄️</div>
        <h3>Meeting Archive</h3>
    </div>
    """, unsafe_allow_html=True)
    
    meetings = db_utils.get_all_meetings()
    if not meetings:
        st.info("No saved meetings found in the archive.")
    else:
        for m in meetings:
            with st.expander(f"📁 {m['title']}  •  {m['date']}"):
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("Load Data", key=f"load_{m['id']}"):
                        st.session_state[f"show_details_{m['id']}"] = True
                        
                if st.session_state.get(f"show_details_{m['id']}", False):
                    details = db_utils.get_meeting(m['id'])
                    if details:
                        if details['transcript']:
                            st.markdown("#### 📝 Transcript")
                            st.markdown(f'<div class="response-card"><div class="text">{details["transcript"]}</div></div>', unsafe_allow_html=True)
                            
                        if details['mom']:
                            st.markdown("#### 📋 Minutes of the Meeting")
                            st.markdown(f'<div class="response-card"><div class="text">{details["mom"]}</div></div>', unsafe_allow_html=True)
                            
                        if details['chats']:
                            st.markdown("#### 💬 Chat History")
                            for chat in details['chats']:
                                if chat["role"] == "user":
                                    st.markdown(f'<div class="chat-msg chat-user"><div class="chat-role chat-role-user">🧑 You</div>{chat["content"]}</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="chat-msg chat-bot"><div class="chat-role chat-role-bot">🤖 AIMIS</div>{chat["content"]}</div>', unsafe_allow_html=True)

# ========================= FOOTER =========================
st.markdown('<div class="purple-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 0.5rem; color: #475569; font-size: 0.8rem;">
    AIMIS &nbsp;·&nbsp; AI Meeting Intelligence System &nbsp;·&nbsp; Powered by Google Gemini
</div>
""", unsafe_allow_html=True)
