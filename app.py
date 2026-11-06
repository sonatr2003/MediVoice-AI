"""
MediVoice AI - Multilingual Healthcare Voice Assistant
Main Flask Application File
"""

import os
import tempfile
import uuid
import wave
import struct
import math
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
from gnani_stt import transcribe_audio
from healthcare_advisor import get_healthcare_response
from gnani_tts import synthesize_speech

# Load environment variables from .env file (if present)
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

# Secret key for session security (loaded safely from environment or fallback for dev)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-fallback-key-replace-in-production")


@app.route("/")
def home():
    """
    Renders the MediVoice AI homepage.
    """
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    """
    Handles audio uploaded from the browser microphone, passes it to
    Gnani Prisma STT, and returns the transcribed text.
    """
    if "audio" not in request.files and "audio_file" not in request.files:
        return jsonify({"success": False, "error": "No audio file provided in request."}), 400

    audio_file = request.files.get("audio") or request.files.get("audio_file")

    if not audio_file or audio_file.filename == "":
        return jsonify({"success": False, "error": "Empty audio file received."}), 400

    # Retrieve selected language from request form (defaults to Malayalam 'ml-IN')
    language = request.form.get("language", "ml-IN")

    # Preserve original file extension or default to .wav
    _, ext = os.path.splitext(audio_file.filename)
    if not ext:
        ext = ".wav"

    temp_dir = tempfile.gettempdir()
    temp_filename = f"medivoice_{uuid.uuid4().hex}{ext}"
    temp_path = os.path.join(temp_dir, temp_filename)

    try:
        audio_file.save(temp_path)
        file_size = os.path.getsize(temp_path)
        client_wav_size = request.form.get("client_wav_size")

        # Diagnostics dictionary
        diag = {
            "file_size": file_size,
            "filename": audio_file.filename,
            "language": language,
            "client_wav_size": int(client_wav_size) if client_wav_size and client_wav_size.isdigit() else None,
            "is_identical": (int(client_wav_size) == file_size) if client_wav_size and client_wav_size.isdigit() else True
        }

        # Analyze audio properties if it's a WAV file
        if ext.lower() == ".wav":
            try:
                with wave.open(temp_path, "rb") as wf:
                    diag["channels"] = wf.getnchannels()
                    diag["sample_width"] = wf.getsampwidth()
                    diag["framerate"] = wf.getframerate()
                    diag["n_frames"] = wf.getnframes()
                    diag["duration_seconds"] = round(diag["n_frames"] / diag["framerate"], 2) if diag["framerate"] > 0 else 0

                    raw_frames = wf.readframes(diag["n_frames"])
                    if diag["sample_width"] == 2 and diag["n_frames"] > 0:
                        samples = struct.unpack(f"<{diag['n_frames'] * diag['channels']}h", raw_frames)
                        diag["total_samples"] = len(samples)
                        diag["non_zero_samples"] = sum(1 for s in samples if s != 0)
                        diag["zero_samples"] = diag["total_samples"] - diag["non_zero_samples"]
                        diag["peak_amplitude"] = max(abs(s) for s in samples) if samples else 0
                        
                        # Calculate RMS (Root Mean Square) energy
                        sum_sq = sum(s * s for s in samples)
                        rms = math.sqrt(sum_sq / len(samples)) if samples else 0.0
                        diag["rms_level"] = round(rms, 2)
                        diag["rms_dbfs"] = round(20 * math.log10(rms / 32768), 2) if rms > 0 else -100.0
                        diag["is_audible"] = bool(diag["peak_amplitude"] > 300 and rms > 50)
            except Exception as wave_err:
                diag["wav_parse_error"] = str(wave_err)

        # Print structured diagnostic log to console
        print("\n" + "=" * 60)
        print("[MediVoice AI] AUDIO UPLOAD DIAGNOSTICS")
        print("=" * 60)
        print(f"File Name:        {diag['filename']} ({diag['file_size']} bytes)")
        if diag.get("client_wav_size"):
            match_status = "IDENTICAL" if diag["is_identical"] else "MISMATCH!"
            print(f"Integrity Check:  Client: {diag['client_wav_size']} B | Server: {diag['file_size']} B ({match_status})")
        if "duration_seconds" in diag:
            print(f"Format:           WAV (Channels: {diag.get('channels')}, Rate: {diag.get('framerate')} Hz, Width: {diag.get('sample_width')*8}-bit)")
            print(f"Duration:         {diag['duration_seconds']} seconds ({diag.get('n_frames')} frames)")
            print(f"Samples:          Total: {diag.get('total_samples')} | Non-Zero: {diag.get('non_zero_samples')} | Zero: {diag.get('zero_samples')}")
            print(f"Peak Amplitude:   {diag.get('peak_amplitude')} / 32767 ({round((diag.get('peak_amplitude',0)/32767)*100, 1)}%)")
            print(f"RMS Energy Level: {diag.get('rms_level')} ({diag.get('rms_dbfs')} dBFS)")
            aud_str = "YES (Audible speech present)" if diag.get("is_audible") else "NO (Signal is silent or near-zero)"
            print(f"Audible Speech:   {aud_str}")
        print(f"Language:         {language}")
        print("=" * 60)

        # Call existing transcribe_audio function from gnani_stt.py
        transcript = transcribe_audio(temp_path, language=language)

        # Print result safely to console without Windows cp1252 UnicodeEncodeError
        try:
            print(f"[MediVoice AI] Transcription result: '{transcript}'\n")
        except UnicodeEncodeError:
            print(f"[MediVoice AI] Transcription successful: ({len(transcript)} characters)\n")

        # Generate safe healthcare guidance from the transcript
        healthcare_response = ""
        try:
            if transcript and transcript.strip():
                healthcare_response = get_healthcare_response(transcript, language=language)
        except Exception as advisor_err:
            print(f"[MediVoice AI] Healthcare Advisor Error: {advisor_err}")
            healthcare_response = (
                "ക്ഷമിക്കണം, ആരോഗ്യ നിർദ്ദേശങ്ങൾ ലഭ്യമാക്കുന്നതിൽ തടസ്സം നേരിട്ടു. ദയവായി ഡോക്ടറുടെ സേവനം തേടുക."
                if str(language).startswith("ml")
                else "Sorry, could not process healthcare guidance at this moment. Please consult a qualified doctor."
            )

        return jsonify({
            "success": True,
            "transcript": transcript,
            "response": healthcare_response,
            "language": language,
            "diagnostics": diag
        })

    except ValueError as ve:
        # Handles validation issues (e.g., missing API key or empty audio)
        return jsonify({"success": False, "error": str(ve), "diagnostics": diag if "diag" in locals() else None}), 400

    except Exception as e:
        # Handles API and network errors safely without leaking sensitive information
        return jsonify({"success": False, "error": str(e), "diagnostics": diag if "diag" in locals() else None}), 500

    finally:
        # Always clean up temporary audio files from disk
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@app.route("/speak", methods=["POST"])
def speak():
    """
    Synthesizes speech from text using Gnani Timbre v3.0 Text-to-Speech API.
    Expects JSON with 'text' and 'language' ('ml-IN' or 'en-IN').
    Returns binary WAV audio with Content-Type: audio/wav.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "error": "Invalid JSON request payload."}), 400

    text = data.get("text")
    if not text or not str(text).strip():
        return jsonify({"success": False, "error": "Text cannot be empty."}), 400

    language = data.get("language", "ml-IN")
    if language not in ("ml-IN", "en-IN"):
        return jsonify({
            "success": False,
            "error": f"Unsupported language '{language}'. Only 'ml-IN' and 'en-IN' are allowed."
        }), 400

    try:
        audio_bytes = synthesize_speech(text=str(text).strip(), language=language)
        return Response(audio_bytes, mimetype="audio/wav")
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Running the app locally in debug mode
    # debug=True allows hot-reloading when code changes and gives detailed error traces in the browser
    print("Starting MediVoice AI application...")
    print("Open your browser and navigate to: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
