/**
 * MediVoice AI - Frontend Voice Recording & Transcription Client
 * Handles microphone capture with MediaRecorder, converts audio to 16-bit PCM WAV,
 * normalizes volume, and communicates with the Flask /transcribe API.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const micButton = document.getElementById("micButton");
    const statusText = document.getElementById("statusText");
    const hintText = document.getElementById("hintText");
    const languageSelect = document.getElementById("languageSelect");
    const transcriptText = document.getElementById("transcriptText");
    const transcriptPlaceholder = document.getElementById("transcriptPlaceholder");
    const transcriptBadge = document.getElementById("transcriptBadge");
    const responseText = document.getElementById("responseText");
    const responsePlaceholder = document.getElementById("responsePlaceholder");
    const responseBadge = document.getElementById("responseBadge");
    const responseActions = document.getElementById("responseActions");
    const speakButton = document.getElementById("speakButton");
    const speakButtonText = document.getElementById("speakButtonText");
    const speakIcon = document.getElementById("speakIcon");

    // Recording State Variables
    let isRecording = false;
    let mediaRecorder = null;
    let audioStream = null;
    let audioChunks = [];

    // TTS & Audio Playback State Variables
    let currentAudio = null;
    let currentAudioUrl = null;
    let isSynthesizing = false;

    // Helper: Update badge text when language dropdown changes
    if (languageSelect) {
        languageSelect.addEventListener("change", () => {
            const selectedText = languageSelect.options[languageSelect.selectedIndex].text;
            if (transcriptBadge) {
                transcriptBadge.textContent = selectedText;
            }
        });
    }

    // Helper: Set UI status message and style
    function setStatus(state, message, hint) {
        if (!statusText) return;
        statusText.className = "status-text " + state;
        statusText.textContent = message;
        if (hintText && hint) {
            hintText.textContent = hint;
        }
    }

    // Helper: Display transcript in the UI
    function showTranscript(text, langCode, isPlaceholder = false) {
        if (!transcriptText || !transcriptPlaceholder) return;
        transcriptPlaceholder.style.display = "none";
        transcriptText.style.display = "block";
        transcriptText.textContent = text;
        transcriptText.style.fontStyle = isPlaceholder ? "italic" : "normal";
        transcriptText.style.color = isPlaceholder ? "var(--text-muted)" : "var(--text-main)";

        if (transcriptBadge) {
            const label = langCode === "en-IN" ? "English (India)" : "Malayalam (മലയാളം)";
            transcriptBadge.textContent = label;
        }
    }

    // Helper: Stop active audio playback and revoke object URL
    function stopAudioPlayback() {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            currentAudio = null;
        }
        if (currentAudioUrl) {
            URL.revokeObjectURL(currentAudioUrl);
            currentAudioUrl = null;
        }
        resetSpeakButton();
    }

    // Helper: Reset speak button to default idle state
    function resetSpeakButton() {
        if (!speakButton || !speakButtonText || !speakIcon) return;
        speakButton.disabled = false;
        speakButton.classList.remove("loading", "playing");
        speakButtonText.textContent = "Listen to Response";
        speakIcon.textContent = "🔊";
        isSynthesizing = false;
    }

    // Helper: Display healthcare assistant response in the UI
    function showHealthcareResponse(response) {
        if (!responseText || !responsePlaceholder) return;
        if (!response || !response.trim()) {
            responsePlaceholder.style.display = "block";
            responseText.style.display = "none";
            responseText.textContent = "";
            if (responseBadge) {
                responseBadge.textContent = "Safety Guidance";
                responseBadge.className = "response-badge";
            }
            if (responseActions) {
                responseActions.style.display = "none";
            }
            stopAudioPlayback();
            return;
        }

        responsePlaceholder.style.display = "none";
        responseText.style.display = "block";
        responseText.textContent = response;

        if (responseBadge) {
            if (response.includes("🚨") || response.includes("അടിയന്തര") || response.toLowerCase().includes("urgent")) {
                responseBadge.textContent = "🚨 Emergency Warning";
                responseBadge.className = "response-badge emergency";
            } else {
                responseBadge.textContent = "Supportive Advice";
                responseBadge.className = "response-badge";
            }
        }

        // Show "Listen to Response" button only when a response is present
        if (responseActions) {
            responseActions.style.display = "flex";
            resetSpeakButton();
        }
    }

    // Listen to Response (TTS) Button Click Handler
    if (speakButton) {
        speakButton.addEventListener("click", async () => {
            // If already playing audio, clicking again stops playback
            if (currentAudio && !currentAudio.paused) {
                stopAudioPlayback();
                return;
            }

            // Prevent repeated clicks while a synthesis request is in progress
            if (isSynthesizing) return;

            const textToSpeak = responseText ? responseText.textContent.trim() : "";
            if (!textToSpeak) return;

            const selectedLanguage = languageSelect ? languageSelect.value : "ml-IN";

            // Stop previous audio before playing new audio
            stopAudioPlayback();

            try {
                isSynthesizing = true;
                speakButton.disabled = true;
                speakButton.classList.add("loading");
                speakButtonText.textContent = "Generating voice...";
                speakIcon.textContent = "⏳";

                const response = await fetch("/speak", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        text: textToSpeak,
                        language: selectedLanguage
                    })
                });

                if (!response.ok) {
                    let errMsg = "Speech synthesis failed";
                    try {
                        const errJson = await response.json();
                        if (errJson && errJson.error) {
                            errMsg = errJson.error;
                        }
                    } catch (_) {}
                    throw new Error(errMsg);
                }

                // Receive WAV audio blob from server
                const audioBlob = await response.blob();
                currentAudioUrl = URL.createObjectURL(audioBlob);
                currentAudio = new Audio(currentAudioUrl);

                speakButton.disabled = false;
                speakButton.classList.remove("loading");
                speakButton.classList.add("playing");
                speakButtonText.textContent = "Stop Listening";
                speakIcon.textContent = "⏹️";

                currentAudio.onended = () => {
                    stopAudioPlayback();
                };

                currentAudio.onerror = (audioErr) => {
                    console.error("Audio playback error:", audioErr);
                    stopAudioPlayback();
                    setStatus("error", "Playback error", "Could not play the synthesized audio.");
                };

                await currentAudio.play();

            } catch (err) {
                console.error("TTS synthesis error:", err);
                stopAudioPlayback();
                if (speakButtonText && speakIcon) {
                    speakButtonText.textContent = "Speech unavailable";
                    speakIcon.textContent = "⚠️";
                    setTimeout(() => {
                        resetSpeakButton();
                    }, 3000);
                }
            } finally {
                isSynthesizing = false;
            }
        });
    }

    // Microphone button click handler (toggle start/stop)
    if (micButton) {
        micButton.addEventListener("click", async () => {
            if (!isRecording) {
                await startRecording();
            } else {
                stopRecording();
            }
        });
    }

    /**
     * Starts recording audio from the user's microphone.
     */
    async function startRecording() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setStatus("error", "Microphone not supported", "Your browser does not support audio recording.");
            return;
        }

        try {
            audioChunks = [];
            audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Determine best supported MIME type
            let mimeType = "audio/webm;codecs=opus";
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";
            }

            const options = mimeType ? { mimeType } : {};
            mediaRecorder = new MediaRecorder(audioStream, options);

            // Collect audio chunks continuously as they are recorded
            mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            // When recording finishes, process and upload the collected audio
            mediaRecorder.onstop = async () => {
                // Safely stop microphone tracks AFTER MediaRecorder has finished flushing
                if (audioStream) {
                    audioStream.getTracks().forEach((track) => track.stop());
                    audioStream = null;
                }
                await processAndUploadAudio();
            };

            // Start recording with 200ms timeslice to ensure continuous data delivery
            mediaRecorder.start(200);
            isRecording = true;
            micButton.classList.add("recording");
            setStatus("recording", "🔴 Recording... Tap to stop", "Speak clearly in Malayalam or English");
            showHealthcareResponse(""); // Reset previous healthcare response on new recording

        } catch (error) {
            console.error("Microphone access error:", error);
            if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
                setStatus("error", "Microphone permission denied", "Please allow microphone access in your browser settings.");
            } else {
                setStatus("error", "Microphone error", error.message || "Could not access microphone.");
            }
        }
    }

    /**
     * Stops the ongoing recording.
     * Note: Tracks are released inside mediaRecorder.onstop to prevent premature audio cutoff.
     */
    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }

        isRecording = false;
        micButton.classList.remove("recording");
        setStatus("processing", "⏳ Transcribing with Gnani AI...", "Processing audio and transcribing speech...");
    }

    /**
     * Converts raw MediaRecorder chunks into a clean 16-bit PCM WAV at 16,000 Hz Mono,
     * logs audio metrics (size, duration, RMS, peak), normalizes volume, and uploads to Flask.
     */
    async function processAndUploadAudio() {
        if (audioChunks.length === 0) {
            setStatus("error", "No audio captured", "Please try speaking and recording again.");
            return;
        }

        try {
            // 1. Combine recorded chunks into a single Blob
            const rawBlob = new Blob(audioChunks, { type: mediaRecorder?.mimeType || "audio/webm" });
            console.log("--- BROWSER AUDIO RECORDING DIAGNOSTICS ---");
            console.log(`[1] MediaRecorder chunks: ${audioChunks.length}`);
            console.log(`[2] Raw recorded Blob: ${rawBlob.size} bytes (${rawBlob.type})`);

            // 2. Decode raw audio into PCM AudioBuffer via Web Audio API
            const arrayBuffer = await rawBlob.arrayBuffer();
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const decodedBuffer = await audioCtx.decodeAudioData(arrayBuffer);
            audioCtx.close().catch(() => {}); // Free audio context resources

            console.log(`[3] Decoded AudioBuffer: Duration = ${decodedBuffer.duration.toFixed(2)}s, SampleRate = ${decodedBuffer.sampleRate} Hz, Channels = ${decodedBuffer.numberOfChannels}`);

            // 3. Extract single channel (mono) PCM samples (channel 0)
            let monoSamples = extractMonoSamples(decodedBuffer);

            // Calculate raw audio metrics
            let rawSumSq = 0;
            let rawPeak = 0;
            let nonZeroCount = 0;
            for (let i = 0; i < monoSamples.length; i++) {
                const abs = Math.abs(monoSamples[i]);
                if (abs > 0.0001) nonZeroCount++;
                if (abs > rawPeak) rawPeak = abs;
                rawSumSq += monoSamples[i] * monoSamples[i];
            }
            const rawRms = Math.sqrt(rawSumSq / monoSamples.length);
            console.log(`[4] Raw PCM Stats: Non-zero samples = ${nonZeroCount}/${monoSamples.length} (${((nonZeroCount/monoSamples.length)*100).toFixed(1)}%), Peak = ${rawPeak.toFixed(4)}, RMS = ${rawRms.toFixed(5)}`);

            // 4. Resample to 16,000 Hz Mono (optimal for speech recognition)
            const targetSampleRate = 16000;
            const resampledSamples = resamplePCM(monoSamples, decodedBuffer.sampleRate, targetSampleRate);

            // 5. Check volume and apply volume normalization if speech is too quiet
            const normalizedSamples = normalizeVolume(resampledSamples);

            // Calculate normalized audio metrics
            let normSumSq = 0;
            let normPeak = 0;
            for (let i = 0; i < normalizedSamples.length; i++) {
                const abs = Math.abs(normalizedSamples[i]);
                if (abs > normPeak) normPeak = abs;
                normSumSq += normalizedSamples[i] * normalizedSamples[i];
            }
            const normRms = Math.sqrt(normSumSq / normalizedSamples.length);
            console.log(`[5] 16kHz WAV Prep: Samples = ${normalizedSamples.length}, Peak = ${normPeak.toFixed(4)}, RMS = ${normRms.toFixed(5)}`);

            // 6. Encode to standard 16-bit PCM WAV Blob
            const wavBlob = encodeWavBlob(normalizedSamples, targetSampleRate);
            console.log(`[6] Generated WAV Blob: ${wavBlob.size} bytes (${wavBlob.type})`);
            console.log("-------------------------------------------");

            // 7. Send WAV to Flask /transcribe endpoint
            const selectedLanguage = languageSelect ? languageSelect.value : "ml-IN";
            const formData = new FormData();
            formData.append("audio", wavBlob, "recording.wav");
            formData.append("language", selectedLanguage);
            formData.append("client_wav_size", wavBlob.size);

            const response = await fetch("/transcribe", {
                method: "POST",
                body: formData
            });

            const result = await response.json();
            console.log("[7] Flask /transcribe response:", result);

            if (result.success) {
                const transcript = (result.transcript || "").trim();
                const d = result.diagnostics || {};

                if (transcript) {
                    showTranscript(transcript, result.language, false);
                    showHealthcareResponse(result.response || "");
                    setStatus("success", "✅ Transcription complete", "Tap microphone to record again");
                } else {
                    const rmsInfo = d.rms_level !== undefined ? ` (RMS: ${d.rms_level}, Peak: ${d.peak_amplitude})` : "";
                    showTranscript(`(No clear speech detected${rmsInfo}. Please speak closer to your microphone and try again.)`, result.language, true);
                    showHealthcareResponse("");
                    setStatus("error", "No speech detected", "Please speak clearly and tap the microphone to try again");
                }
            } else {
                showHealthcareResponse("");
                setStatus("error", "Transcription failed", result.error || "Gnani STT was unable to transcribe.");
            }

        } catch (err) {
            console.error("Audio processing/upload error:", err);
            showHealthcareResponse("");
            setStatus("error", "Error processing audio", err.message || "Failed to process audio.");
        }
    }

    /**
     * Extracts mono PCM samples from an AudioBuffer.
     * Always uses Channel 0 (primary microphone) to avoid stereo phase cancellation.
     */
    function extractMonoSamples(audioBuffer) {
        return audioBuffer.getChannelData(0);
    }

    /**
     * Linear interpolation resampling from sourceRate to targetRate.
     * Avoids OfflineAudioContext duration/metadata bugs in Chromium.
     */
    function resamplePCM(samples, sourceRate, targetRate) {
        if (sourceRate === targetRate) {
            return samples;
        }

        const ratio = sourceRate / targetRate;
        const newLength = Math.round(samples.length / ratio);
        const result = new Float32Array(newLength);

        for (let i = 0; i < newLength; i++) {
            const pos = i * ratio;
            const index = Math.floor(pos);
            const frac = pos - index;
            const s1 = samples[index] || 0;
            const s2 = samples[index + 1] !== undefined ? samples[index + 1] : s1;
            result[i] = s1 + frac * (s2 - s1);
        }

        return result;
    }

    /**
     * Normalizes audio volume so quiet speech reaches optimal amplitude for STT recognition.
     */
    function normalizeVolume(samples) {
        let maxAmp = 0;
        for (let i = 0; i < samples.length; i++) {
            const abs = Math.abs(samples[i]);
            if (abs > maxAmp) {
                maxAmp = abs;
            }
        }

        // If audio has sound but is quiet (peak below 0.8), boost it to optimal 0.85 peak
        if (maxAmp > 0.001 && maxAmp < 0.8) {
            const gain = Math.min(50.0, 0.85 / maxAmp);
            const boosted = new Float32Array(samples.length);
            for (let i = 0; i < samples.length; i++) {
                boosted[i] = Math.max(-1, Math.min(1, samples[i] * gain));
            }
            return boosted;
        }

        return samples;
    }

    /**
     * Encodes single-channel Float32Array PCM samples into a valid 16-bit PCM WAV Blob.
     */
    function encodeWavBlob(samples, sampleRate) {
        const numChannels = 1;
        const bitDepth = 16;
        const bytesPerSample = bitDepth / 8;
        const blockAlign = numChannels * bytesPerSample;
        const dataSize = samples.length * bytesPerSample;
        const buffer = new ArrayBuffer(44 + dataSize);
        const view = new DataView(buffer);

        // RIFF chunk descriptor
        writeString(view, 0, "RIFF");
        view.setUint32(4, 36 + dataSize, true);
        writeString(view, 8, "WAVE");

        // fmt sub-chunk
        writeString(view, 12, "fmt ");
        view.setUint32(16, 16, true);                  // SubChunk1Size (16 for PCM)
        view.setUint16(20, 1, true);                   // AudioFormat (1 = PCM)
        view.setUint16(22, numChannels, true);         // NumChannels (1 = Mono)
        view.setUint32(24, sampleRate, true);          // SampleRate
        view.setUint32(28, sampleRate * blockAlign, true); // ByteRate
        view.setUint16(32, blockAlign, true);          // BlockAlign
        view.setUint16(34, bitDepth, true);            // BitsPerSample (16-bit)

        // data sub-chunk
        writeString(view, 36, "data");
        view.setUint32(40, dataSize, true);

        // Write 16-bit integer PCM samples
        let offset = 44;
        for (let i = 0; i < samples.length; i++, offset += 2) {
            const sample = Math.max(-1, Math.min(1, samples[i]));
            const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
            view.setInt16(offset, intSample, true);
        }

        return new Blob([view], { type: "audio/wav" });
    }

    function writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }
});
