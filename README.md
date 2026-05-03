# 🚀 RAPIDS  
### Real-time AI Platform for Intelligent Discussions & Meeting Summaries

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-red)
![AI Powered](https://img.shields.io/badge/AI-Powered-purple)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 Overview

RAPIDS is a real-time AI meeting assistant that listens to conversations, transcribes speech, generates intelligent responses, and speaks back during live meetings.

It also creates structured Minutes of Meeting (MoM) and stores session archives, making it useful for meeting automation, documentation, and productivity.

---

## ✨ Features

- 🎤 Speech-to-text using Whisper  
- 🤖 AI responses using Google Gemini  
- 📝 Automatic MoM (Minutes of Meeting) generation  
- 🗂️ Session archiving  
- 🔊 Text-to-speech using gTTS  
- 🎧 Virtual microphone integration for live meetings (Zoom, Teams, etc.)  
- ⚡ Simple Streamlit interface  

---

## 🛠️ Tech Stack

- Frontend: Streamlit  
- Speech Recognition: Whisper  
- LLM: Google Gemini  
- Text-to-Speech: gTTS  
- Audio Routing: VB-CABLE / BlackHole  

---

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/your-username/rapids.git

# Navigate to project folder
cd rapids

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

---

## 🎧 Virtual Microphone Setup

- Install a virtual audio driver:
  - Windows: VB-CABLE  
  - Mac: BlackHole  

- Set the virtual cable as your microphone in Zoom/Teams  
- Route app audio output to the virtual cable  

---

## 📂 Project Structure

```
rapids/
│── app.py
│── requirements.txt
│── modules/
│── archive/
│── README.md
│── LICENSE
```

---

## 📸 Use Cases

- Meeting assistant  
- Automatic documentation & MoM  
- AI participant in online meetings  
- Discussion tracking & review  

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙌 Contribution

Contributions are welcome! Feel free to fork and submit a pull request.

---

## ⭐ Acknowledgements

- OpenAI Whisper  
- Google Gemini  
- Streamlit  
- gTTS  
