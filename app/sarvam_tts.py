"""
Sarvam AI Text-to-Speech (optional, natural Indian-language voice)
================================================================================
Uses Sarvam's bulbul TTS via REST:
    POST https://api.sarvam.ai/text-to-speech
    header: api-subscription-key: <SARVAM_API_KEY>
    body: { text[], language_code (BCP-47), speaker, model, ... }
    -> { audios: [ base64 wav, ... ] }

Enable it by adding to .env:
    SARVAM_API_KEY=your_key_here
    SARVAM_TTS_SPEAKER=shubh        # optional, shubh is the default voice

If SARVAM_API_KEY is missing or the call fails, callers automatically fall
back to the browser's built-in Web Speech synthesis.
"""
from __future__ import annotations

import base64
import json

import streamlit as st
import streamlit.components.v1 as components

from .config import SARVAM_API_KEY, SARVAM_TTS_MODEL, SARVAM_TTS_SPEAKER

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"


@st.cache_data(show_spinner=False)
def _sarvam_speak_cached(text: str, language_code: str, speaker: str, model: str) -> bytes | None:
    """Call Sarvam bulbul TTS; returns WAV bytes or None on any failure."""
    if not SARVAM_API_KEY or not text:
        return None
    try:
        import urllib.request

        payload = json.dumps({
            "text": text[:2500],             # string (bulbul:v3 limit; 'inputs' is for lists)
            "language_code": language_code,   # BCP-47: en-IN / ta-IN
            "speaker": speaker,
            "model": model,
            "speech_sample_rate": 22050,
            "output_audio_codec": "wav",
        }).encode("utf-8")
        req = urllib.request.Request(
            SARVAM_TTS_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "api-subscription-key": SARVAM_API_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        audios = data.get("audios") or []
        if not audios:
            return None
        return base64.b64decode(audios[0])
    except Exception:
        return None


def render_sarvam_audio(text: str, lang: str, auto_play: bool = False, key: str = "sarvam") -> bool:
    """
    Render a Sarvam (Shubh voice) audio player for the text — the ONE voice
    helper used by every speech point in the app (splash, onboarding prompts,
    completion, chat answers). Returns True when the Sarvam player was
    rendered, False when the caller should fall back to browser speech.
    """
    if not SARVAM_API_KEY:
        return False
    language_code = "ta-IN" if lang == "Tamil" else "en-IN"
    speaker = SARVAM_TTS_SPEAKER
    wav = _sarvam_speak_cached(text, language_code, speaker, SARVAM_TTS_MODEL)
    if not wav:
        return False

    b64 = base64.b64encode(wav).decode("ascii")
    autoplay = "true" if auto_play else "false"
    audio_id = f"sarvamAudio_{abs(hash(key)) % 100000}"
    components.html(
        f"""
        <audio id="{audio_id}" src="data:audio/wav;base64,{b64}" preload="auto"></audio>
        <div style="display:inline-flex; gap:8px; align-items:center;">
            <button onclick="var a=document.getElementById('{audio_id}'); a.currentTime=0; a.play();"
                    style="padding:8px 16px; border-radius:999px; border:1.5px solid #bbf7d0; background:#f0fdf4; color:#166534; font-weight:700; cursor:pointer;">🔊 Listen</button>
            <button onclick="var a=document.getElementById('{audio_id}'); a.pause();"
                    style="padding:8px 16px; border-radius:999px; border:1.5px solid #bbf7d0; background:#f0fdf4; color:#166534; font-weight:700; cursor:pointer;">⏸ Pause</button>
            <button onclick="var a=document.getElementById('{audio_id}'); a.pause(); a.currentTime=0;"
                    style="padding:8px 16px; border-radius:999px; border:1.5px solid #bbf7d0; background:#f0fdf4; color:#166534; font-weight:700; cursor:pointer;">⏹ Stop</button>
            <span style="font-size:0.8rem; color:#15803d; font-weight:600;">Sarvam · {speaker}</span>
        </div>
        <script>
        {f"setTimeout(function(){{var a=document.getElementById('{audio_id}'); a.play().catch(function(){{}});}}, 300);" if auto_play else ""}
        </script>
        """,
        height=60,
    )
    return True


def speak_text(text: str, lang: str, key: str, autoplay: bool = True) -> None:
    """
    Speak `text` with Sarvam (Shubh) when configured; fall back to the
    browser's Web Speech player otherwise. `key` must be unique per speech
    point so Streamlit doesn't collide the players.
    """
    from streamlit_app import render_audio_player  # local import: avoids cycle at module load
    try:
        spoken = render_sarvam_audio(text[:2500], lang, auto_play=autoplay, key=key)
    except Exception:
        spoken = False
    if not spoken:
        render_audio_player(text[:600], lang, auto_play=autoplay, player_id=key)
