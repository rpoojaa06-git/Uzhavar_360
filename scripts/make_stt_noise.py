"""Generate real STT-noise dataset rows by round-tripping seed questions
through the actual production voice path: Sarvam bulbul:v3 TTS -> wav ->
Sarvam saaras:v3 STT. The raw transcript (no cleanup) becomes the question,
with the ORIGINAL intent as the label — this is the real acoustic/
transcription distribution the router will face.

Requires SARVAM_API_KEY in .env. Writes data/router_eval/stt_roundtrips.jsonl
"""

import base64
import json
import os
import sys
import wave

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
TTS_URL = "https://api.sarvam.ai/text-to-speech"
STT_URL = "https://api.sarvam.ai/speech-to-text"

SEEDS = [
    # (question, intent, language, tts_lang_code)
    ("What is the market price of tomato today", "demo", "en", "en-IN"),
    ("where do I rent a tractor for two days", "demo", "en", "en-IN"),
    ("Am I eligible for the PM-KISAN instalment", "scheme", "en", "en-IN"),
    ("how do I apply for the old age pension for farmers", "scheme", "en", "en-IN"),
    ("how do I control stem borer in paddy", "agri", "en", "en-IN"),
    ("when is the right time to transplant tomato seedlings", "agri", "en", "en-IN"),
    ("தற்போதைய சந்தை விலை என்ன", "demo", "ta", "ta-IN"),
    ("உரம் கையிருப்பு எவ்வளவு உள்ளது", "demo", "ta", "ta-IN"),
    ("ஓய்வூதியத் தொகை எவ்வளவு", "scheme", "ta", "ta-IN"),
    ("பயிர் காப்பீட்டிற்கு விண்ணப்பிக்க என்ன தகுதி தேவை", "scheme", "ta", "ta-IN"),
    ("நெல்லின் இலை மஞ்சளாக மாறுகிறது, என்ன செய்வது", "agri", "ta", "ta-IN"),
    ("களைக்கட்டுப்பாடு என்ன வழி", "agri", "ta", "ta-IN"),
]


def tts_to_wav(text: str, lang: str) -> bytes:
    r = requests.post(
        TTS_URL,
        headers={"api-subscription-key": SARVAM_API_KEY,
                 "Content-Type": "application/json"},
        json={
            "text": text,
            "target_language_code": lang,
            "speaker": "shubh",
            "model": "bulbul:v3",
            "speech_sample_rate": 16000,
            "encode_as_wav": True,
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    audios = data.get("audios") or []
    if not audios:
        raise RuntimeError(f"no audio in TTS response: {data}")
    return base64.b64decode(audios[0])


def stt(wav_bytes: bytes) -> str:
    files = {"file": ("q.wav", wav_bytes, "audio/wav")}
    r = requests.post(
        STT_URL,
        headers={"api-subscription-key": SARVAM_API_KEY},
        files=files,
        data={"model": "saaras:v3", "mode": "transcribe"},
        timeout=90,
    )
    r.raise_for_status()
    return (r.json().get("transcript") or "").strip()


def main():
    if not SARVAM_API_KEY:
        sys.exit("SARVAM_API_KEY missing in .env")
    out = os.path.join(os.path.dirname(HERE), "data", "router_eval", "stt_roundtrips.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rows = []
    with open(out, "w", encoding="utf-8") as f:
        for q, intent, lang, tts_lang in SEEDS:
            try:
                wav = tts_to_wav(q, tts_lang)
                transcript = stt(wav)
                rows.append({"question": transcript, "language": lang,
                             "intent": intent, "source": "stt",
                             "tier1_demo_card": None, "hardness": "stt_noise"})
                print(f"OK  [{intent}] {transcript}")
                f.write(json.dumps(rows[-1], ensure_ascii=False) + "\n")
                f.flush()
            except Exception as e:
                print(f"ERR {q[:30]} -> {type(e).__name__}: {e}")
            # Politeness toward the rate-limited sync endpoints
            import time; time.sleep(1.0)
    print(f"wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
