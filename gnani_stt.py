"""
MediVoice AI - Gnani Speech-to-Text (STT) Module
Uses Gnani AI Prisma v3.0 REST API to transcribe audio into text.
"""

import os
import mimetypes
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Official Gnani Prisma v3.0 STT REST Endpoint
GNANI_STT_URL = "https://api.vachana.ai/stt/v3"


def transcribe_audio(
    audio_path: str,
    language: str = "ml-IN",
    format: str = "transcribe",
    preferred_language: str = None
) -> str:
    """
    Transcribes an audio file into text using the Gnani AI Speech-to-Text REST API.

    Parameters:
        audio_path (str): The file path to the audio file (supports WAV, MP3, OGG, FLAC, AAC, M4A).
        language (str): The language code for transcription.
                        Defaults to "ml-IN" (Malayalam).
                        Can also be "en-IN" (English), "indic-auto" (Auto-detect), etc.
        format (str): The transcript formatting style ("transcribe", "verbatim", "codemix").
                      Defaults to "transcribe" for normalized numbers and dates.
        preferred_language (str, optional): Language to bias/force decoding in multilingual speech.
                                            Defaults to the value of `language`.

    Returns:
        str: The transcribed text.

    Raises:
        ValueError: If GNANI_API_KEY is missing, audio path is invalid, or file is empty.
        FileNotFoundError: If the audio file does not exist on disk.
        TypeError: If the returned transcript is not a string.
        RuntimeError: If network fails, HTTP status is non-200, or the API response is invalid.
    """
    # 1. Retrieve the API key securely from environment variables
    api_key = os.getenv("GNANI_API_KEY")
    if not api_key or not api_key.strip() or api_key.strip() == "your_gnani_api_key_here":
        raise ValueError(
            "GNANI_API_KEY is missing or not configured. "
            "Please add your valid Gnani API key to the .env file."
        )

    # 2. Validate that the audio file exists and is not empty
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if not os.path.isfile(audio_path):
        raise ValueError(f"The path provided is not a file: {audio_path}")

    if os.path.getsize(audio_path) == 0:
        raise ValueError(f"The audio file is empty (0 bytes): {audio_path}")

    # Determine file MIME type (e.g., 'audio/wav', 'audio/mpeg')
    mime_type, _ = mimetypes.guess_type(audio_path)
    if mime_type is None:
        mime_type = "application/octet-stream"

    filename = os.path.basename(audio_path)

    # 3. Prepare headers
    # Gnani uses the X-API-Key-ID header for authentication
    headers = {
        "X-API-Key-ID": api_key.strip()
    }

    # 4. Prepare multipart/form-data payload parameters per Gnani REST API
    # Note: 'model' is not required for the REST endpoint and is omitted
    target_preferred_language = preferred_language if preferred_language is not None else language
    data = {
        "language_code": language,
        "preferred_language": target_preferred_language,
        "itn_native_numerals": "true",
        "format": format
    }

    # 5. Send multipart/form-data POST request
    try:
        with open(audio_path, "rb") as audio_file:
            files = {
                "audio_file": (filename, audio_file, mime_type)
            }
            response = requests.post(
                GNANI_STT_URL,
                headers=headers,
                data=data,
                files=files,
                timeout=60
            )

    except requests.exceptions.Timeout:
        raise RuntimeError("Request to Gnani STT API timed out. Please check your connection.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Failed to connect to Gnani STT API. Please check your network connection.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"An unexpected error occurred while calling Gnani STT: {e}")

    # 6. Parse and validate the JSON response
    try:
        response_json = response.json()
    except Exception:
        raise RuntimeError(
            f"Gnani STT returned a non-JSON response (HTTP {response.status_code})."
        )

    # 7. Check for HTTP errors (e.g., 401 Unauthorized, 422 Validation Error, 429 Rate Limit)
    if response.status_code != 200:
        if response.status_code == 401:
            raise RuntimeError(
                "Authentication failed (HTTP 401): Invalid or unauthorized Gnani API key. "
                "Please verify the GNANI_API_KEY in your .env file."
            )

        error_msg = None

        # Check for detail error structure (common in FastAPI 422 and 429 responses)
        if "detail" in response_json:
            detail = response_json["detail"]
            if isinstance(detail, dict) and "message" in detail:
                error_msg = f"{detail.get('error_code', 'ERROR')}: {detail['message']}"
            elif isinstance(detail, list):
                # Extract field-level validation messages (e.g., 422 Unprocessable Entity)
                items = []
                for item in detail:
                    if isinstance(item, dict):
                        field = item.get("loc", [""])[-1]
                        msg = item.get("msg", "")
                        items.append(f"{field}: {msg}" if field else msg)
                error_msg = "; ".join(items) if items else str(detail)
            else:
                error_msg = str(detail)

        # Check for standard error envelope {"success": false, "error": {...}}
        elif "error" in response_json:
            err = response_json["error"]
            if isinstance(err, dict):
                error_msg = f"{err.get('type', 'ERROR')}: {err.get('message', 'Unknown error')}"
            else:
                error_msg = str(err)

        if not error_msg:
            error_msg = str(response_json)

        raise RuntimeError(f"Gnani STT API error (HTTP {response.status_code}): {error_msg}")

    # 8. Extract and validate that the transcript is a string
    if "transcript" in response_json:
        transcript = response_json["transcript"]
        if not isinstance(transcript, str):
            raise TypeError(
                f"Invalid transcript format from Gnani STT: expected str, got {type(transcript).__name__}"
            )
        return transcript

    # If transcript key is absent, check if success is false or if there is an error message
    if not response_json.get("success", True):
        error_detail = response_json.get("error", "Unknown transcription error.")
        raise RuntimeError(f"Gnani STT transcription unsuccessful: {error_detail}")

    raise RuntimeError("Gnani STT response did not contain a 'transcript' field.")


if __name__ == "__main__":
    print("--- MediVoice AI: Gnani STT Module ---")
    api_key_status = "Configured" if os.getenv("GNANI_API_KEY") and os.getenv("GNANI_API_KEY") != "your_gnani_api_key_here" else "Not set"
    print(f"Status: API Key is {api_key_status}")
    print("Function 'transcribe_audio(audio_path, language=\"ml-IN\")' is ready to use.")
