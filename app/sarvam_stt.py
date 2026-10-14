"""
Sarvam AI Speech-to-Text (optional, browser-independent voice input)
================================================================================
Transcribes microphone recordings SERVER-SIDE via Sarvam's saaras model.
Unlike the browser's Web Speech API (Chrome-only, silently fails in Edge or
without Google's speech servers), this works in every modern browser because
the browser only needs MediaRecorder + getUserMedia — universal APIs.

API (verified against the live service):
  POST https://api.sarvam.ai/speech-to-text
  header  api-subscription-key: <key>
  multipart: file=<audio/wav>, model=saaras:v3, mode=transcribe
  response: {"request_id": ..., "transcript": "...", "language_code": "en-IN"}
Constraints: sync API accepts up to 30 s of audio; WAV/MP3/AAC/FLAC/OGG.
"""
import io
import re
import wave

import requests

from app.config import SARVAM_API_KEY, SARVAM_STT_MODEL

STT_URL = "https://api.sarvam.ai/speech-to-text"

SARVAM_STT_READY = bool(SARVAM_API_KEY)

# The app only supports English and Tamil. Telling Sarvam the language up front
# stops its auto-detect from guessing Hindi (e.g. "भूज।") on noise or silence.
LANG_CODES = {"English": "en-IN", "Tamil": "ta-IN"}

# Audio gate: recordings that are too short or silent are never sent to the
# STT model (it hallucinates words like "okay" on silence).
MIN_SECONDS = 0.6
MIN_PEAK = 0.04          # 99th-percentile amplitude, 0..1 scale

# Anything that is not Latin / Tamil / digits / punctuation is rejected.
_ALLOWED = re.compile(r"[A-Za-z\u0B80-\u0BFF0-9\s.,?!:;'\"()\-/%&@#+₹]")
_FILLERS = {"ok", "okay", "hmm", "hm", "mm", "mmm", "uh", "um", "ah", "oh",
            "thank you", "thanks", "you", "bye"}


def _audio_is_silent(audio_bytes: bytes) -> bool:
    """True when the WAV is too short or too quiet to contain speech.
    Returns False if the audio cannot be inspected (let the STT decide)."""
    try:
        import numpy as np
        with wave.open(io.BytesIO(audio_bytes), "rb") as w:
            rate, width, frames = w.getframerate(), w.getsampwidth(), w.getnframes()
            raw = w.readframes(frames)
        if width != 2 or not rate:
            return False
        if frames / float(rate) < MIN_SECONDS:
            return True
        samples = np.frombuffer(raw, dtype="<i2").astype("float32") / 32768.0
        if samples.size == 0:
            return True
        return float(np.percentile(np.abs(samples), 99)) < MIN_PEAK
    except Exception:
        return False


def _transcript_ok(text: str) -> bool:
    if not any(ch.isalnum() for ch in text):
        return False
    if any(not _ALLOWED.match(ch) for ch in text):
        return False                      # Hindi / other scripts
    return text.strip(" .!?,").lower() not in _FILLERS


def sarvam_speech_to_text(audio_bytes: bytes, lang: str = "English"):
    """Transcribe recorded audio via Sarvam STT.

    Returns ``(text, error)`` — exactly one of the two is non-empty, so the UI
    can always show the farmer a clear, actionable message on failure.
    """
    if not SARVAM_API_KEY:
        return None, ("Voice input needs SARVAM_API_KEY in .env" if lang == "English"
                      else "குரல் உள்ளீட்டுக்கு .env இல் SARVAM_API_KEY தேவை")
    if not audio_bytes:
        return None, ("Empty recording — please try again." if lang == "English"
                      else "பதிவு காலியாக உள்ளது — மீண்டும் முயற்சிக்கவும்.")
    if _audio_is_silent(audio_bytes):
        return None, ("Nothing heard — press Start and speak a little louder."
                      if lang == "English" else
                      "எதுவும் கேட்கவில்லை — Start அழுத்தி சற்று உரக்கப் பேசுங்கள்.")
    try:
        resp = requests.post(
            STT_URL,
            headers={"api-subscription-key": SARVAM_API_KEY},
            files={"file": ("voice.wav", audio_bytes, "audio/wav")},
            data={"model": SARVAM_STT_MODEL, "mode": "transcribe",
                  "language_code": LANG_CODES.get(lang, "en-IN")},
            timeout=90,
        )
    except requests.RequestException:
        return None, ("Voice service unreachable — check the internet connection."
                      if lang == "English" else
                      "குரல் சேவையை அணுக முடியவில்லை — இணைய இணைப்பை சரிபார்க்கவும்.")
    if resp.status_code == 403:
        return None, ("Voice service rejected the API key (403)." if lang == "English"
                      else "குரல் சேவை API விசையை நிராகரித்தது (403).")
    if resp.status_code == 422:
        return None, ("Recording could not be processed (over 30 s or unsupported format) — ask a shorter question."
                      if lang == "English" else
                      "பதிவை செயலாக்க முடியவில்லை (30 வினாடிகளுக்கு மேல்) — சிறிய கேள்வி கேளுங்கள்.")
    if resp.status_code == 429:
        return None, ("Voice service is busy — try again in a moment." if lang == "English"
                      else "குரல் சேவை பரபரப்பாக உள்ளது — சற்று கழித்து முயற்சிக்கவும்.")
    try:
        resp.raise_for_status()
        text = (resp.json().get("transcript") or "").strip()
    except (requests.HTTPError, ValueError):
        return None, ("Voice service returned an unexpected response." if lang == "English"
                      else "குரல் சேவை எதிர்பாராத பதிலை அனுப்பியது.")
    if not text or not _transcript_ok(text):
        return None, ("Nothing heard — press Start and speak a little louder."
                      if lang == "English" else
                      "எதுவும் கேட்கவில்லை — Start அழுத்தி சற்று உரக்கப் பேசுங்கள்.")
    return text, None
