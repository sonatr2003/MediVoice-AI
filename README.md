# MediVoice AI 🩺

A multilingual healthcare voice assistant supporting Malayalam and English. Users can speak through a microphone, receive general health guidance, and listen to responses.

## Features

- Speech-to-text transcription in Malayalam and English.
- Multilingual healthcare responses.
- Text-to-speech using AI-generated audio.
- Rule-based emergency keyword warnings.
- Handles empty or unclear audio with retry guidance.
- Simple web interface.

## How It Works

1. The user speaks in Malayalam or English.
2. Gnani Prisma STT converts speech into text.
3. A rule-based healthcare advisor generates a general response.
4. The response appears on the web interface.
5. The user can click **Listen to Response** to hear it using Gnani Timbre TTS.

## Technologies Used

- Python
- Flask
- HTML, CSS and JavaScript
- Requests
- python-dotenv
- Gnani Prisma Speech-to-Text API
- Gnani Timbre Text-to-Speech API

## Project Structure

```text
MediVoice_AI/
├── app.py
├── gnani_stt.py
├── gnani_tts.py
├── healthcare_advisor.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## Setup and Installation

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd MediVoice_AI
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Install dependencies

For Windows PowerShell:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Add your Gnani API credentials to `.env`.

**Never upload your `.env` file or expose your API keys publicly.**

### 5. Run the application

```powershell
.\venv\Scripts\python.exe app.py
```

Open your browser:

```text
http://127.0.0.1:5000
```

## Medical Disclaimer

MediVoice AI is an educational project, not a medical diagnosis or treatment system.

Healthcare responses use rule-based keyword matching. Emergency keyword detection is limited and cannot identify every medical emergency.

Do not rely on this application for medical decisions. For serious or emergency symptoms, seek immediate professional medical help.

## Project Status

Working prototype. Core speech transcription, general response generation, emergency keyword warnings, and speech playback have been manually tested in Malayalam and English.