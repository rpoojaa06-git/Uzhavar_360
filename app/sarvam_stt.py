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
import requests

from app.config import SARVAM_API_KEY, SARVAM_STT_MODEL

STT_URL = "https://api.sarvam.ai/speech-to-text"

SARVAM_STT_READY = bool(SARVAM_API_KEY)


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
    try:
        resp = requests.post(
            STT_URL,
            headers={"api-subscription-key": SARVAM_API_KEY},
            files={"file": ("voice.wav", audio_bytes, "audio/wav")},
            data={"model": SARVAM_STT_MODEL, "mode": "transcribe"},
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
    if not text:
        return None, ("Nothing heard — press Start and speak a little louder."
                      if lang == "English" else
                      "எதுவும் கேட்கவில்லை — Start அழுத்தி சற்று உரக்கப் பேசுங்கள்.")
    return text, None
