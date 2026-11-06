"""
MediVoice AI - Gnani Text-to-Speech (TTS) Module
Uses Gnani AI Timbre v3.0 REST API to synthesize speech from text.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

# Official Gnani Timbre v3.0 TTS REST Endpoint
GNANI_TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"

# Supported language codes for speech synthesis
SUPPORTED_LANGUAGES = {"ml-IN", "en-IN"}


def synthesize_speech(
    text: str,
    language: str = "ml-IN",
    voice: str = "Chetana",
    model: str = "timbre-v3.0"
) -> bytes:
    """
    Synthesizes text into spoken WAV audio using the Gnani AI Timbre v3.0 REST API.

    Parameters:
        text (str): The text to be converted to speech.
        language (str): Language code ("ml-IN" for Malayalam, "en-IN" for English).
        voice (str): Voice name (default: "Chetana").
        model (str): Model name (default: "timbre-v3.0").

    Returns:
        bytes: Raw WAV audio bytes.

    Raises:
        ValueError: If input text is empty, language is unsupported, or GNANI_API_KEY is missing.
        RuntimeError: If the API request fails, times out, or returns a non-200 status.
    """
    # 1. Validate text input
    if not text or not str(text).strip():
        raise ValueError("Text for speech synthesis cannot be empty.")

    cleaned_text = str(text).strip()

    # 2. Validate language code
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}'. "
            f"Supported languages are: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
        )

    # 3. Retrieve the API key securely from environment variables
    api_key = os.getenv("GNANI_API_KEY")
    if not api_key or not api_key.strip() or api_key.strip() == "your_gnani_api_key_here":
        raise ValueError(
            "GNANI_API_KEY is missing or not configured. "
            "Please add your Gnani API key to the .env file."
        )

    # 4. Prepare headers and payload as per official Gnani Timbre v3.0 specs
    headers = {
        "Content-Type": "application/json",
        "X-API-Key-ID": api_key.strip()
    }

    payload = {
        "text": cleaned_text,
        "model": model,
        "voice": voice,
        "language": language,
        "audio_config": {
            "sample_rate": 24000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav"
        }
    }

    # 5. Send POST request with timeout and error handling
    try:
        response = requests.post(
            GNANI_TTS_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Gnani TTS API request timed out after 30 seconds.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Failed to connect to Gnani TTS API. Please check your network connection.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error while communicating with Gnani TTS API: {e}")

    # 6. Validate HTTP response status
    if response.status_code != 200:
        error_detail = ""
        try:
            error_json = response.json()
            error_detail = f": {error_json.get('message') or error_json.get('error') or error_json}"
        except Exception:
            if response.text:
                error_detail = f": {response.text[:200]}"
        raise RuntimeError(f"Gnani TTS API error (HTTP {response.status_code}){error_detail}")

    # 7. Validate audio bytes returned
    if not response.content:
        raise RuntimeError("Gnani TTS API returned empty audio content.")

    return response.content
