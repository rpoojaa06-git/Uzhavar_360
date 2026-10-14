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
import threading
from concurrent.futures import ThreadPoolExecutor

import streamlit.components.v1 as components

from .config import SARVAM_API_KEY, SARVAM_TTS_MODEL, SARVAM_TTS_SPEAKER

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"


def _fetch_wav(text: str, language_code: str, speaker: str, model: str) -> bytes | None:
    """Call Sarvam bulbul TTS; returns WAV bytes or None on any failure."""
    if not SARVAM_API_KEY or not text:
        return None
    try:
        import urllib.request
        import urllib.error

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
    except urllib.error.HTTPError as e:
        if e.code == 402:
            print("[Sarvam TTS] No credits available for today (HTTP 402).")
        return None
    except Exception as e:
        print(f"[Sarvam TTS] Request error: {e}")
        return None


# One shared cache of in-flight/finished requests. Prefetching and rendering use the
# same entry, so a clip that was prefetched in the background plays instantly and
# the same text is never requested twice.
_POOL = ThreadPoolExecutor(max_workers=3)
_FUTURES: dict = {}
_LOCK = threading.Lock()
_MAX_CACHED = 300


def _wav_future(text: str, language_code: str, speaker: str, model: str):
    k = (text[:2500], language_code, speaker, model)
    with _LOCK:
        f = _FUTURES.get(k)
        if f is None or (f.done() and f.result() is None):   # never keep failures
            f = _POOL.submit(_fetch_wav, *k)
            _FUTURES[k] = f
            while len(_FUTURES) > _MAX_CACHED:
                _FUTURES.pop(next(iter(_FUTURES)))
    return f


def _sarvam_speak_cached(text: str, language_code: str, speaker: str, model: str) -> bytes | None:
    try:
        return _wav_future(text, language_code, speaker, model).result(timeout=45)
    except Exception:
        return None


def prefetch_speech(text: str, lang: str) -> None:
    """Start generating the clip in the background (non-blocking)."""
    if not SARVAM_API_KEY or not text:
        return
    _wav_future(text, "ta-IN" if lang == "Tamil" else "en-IN", SARVAM_TTS_SPEAKER, SARVAM_TTS_MODEL)


def render_sarvam_audio(text: str, lang: str, auto_play: bool = False, key: str = "sarvam",
                        show_controls: bool = True, retry_on_interaction: bool = False) -> bool:
    """
    Render a Sarvam audio player for the text — the ONE voice
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
        if show_controls:
            msg = ("⚠️ வாய்ஸ் கிரெடிட் முடிந்துவிட்டது (Voice credits exhausted for today)"
                   if lang == "Tamil" else
                   "⚠️ Voice credits exhausted for today")
            components.html(f"""
            <style>
              body {{ margin: 0; padding: 4px 0; background: transparent;
                     font-family: 'Plus Jakarta Sans', -apple-system, 'Segoe UI', sans-serif; }}
              .notice {{ display: inline-flex; align-items: center; gap: 6px; padding: 7px 16px;
                         background: #fef2f2; border: 1px solid #fecaca; border-radius: 999px;
                         color: #991b1b; font-size: 0.84rem; font-weight: 700; }}
            </style>
            <div class="notice"><span>{msg}</span></div>
            """, height=44)
            return True
        return False

    b64 = base64.b64encode(wav).decode("ascii")
    audio_id = f"sarvamAudio_{abs(hash(key)) % 100000}"
    # Autoplay. If the browser blocks it (no tap yet on a freshly opened link) and
    # retry_on_interaction is set, play on the farmer's first tap/key press instead,
    # using an Audio object owned by the parent page so a Streamlit rerun cannot cut it off.
    retry_js = (
        "var d=window.parent.document, fired=false;"
        "var go=function(){if(fired)return;fired=true;"
        "['pointerdown','keydown','touchstart'].forEach(function(e){d.removeEventListener(e,go,true);});"
        "try{var pa=new window.parent.Audio(a.src);pa.play().catch(function(){});}catch(x){}};"
        "['pointerdown','keydown','touchstart'].forEach(function(e){d.addEventListener(e,go,true);});"
        if retry_on_interaction else ""
    )
    autoplay_js = (
        f"setTimeout(function(){{var a=document.getElementById('{audio_id}'); "
        f"var p=a.play(); if(p&&p.catch){{p.catch(function(){{try{{{retry_js}}}catch(x){{}}}});}}}}, 300);"
        if auto_play else ""
    )
    if lang == "Tamil":
        listen, pause, resume, stop = "🔊 கேள்", "⏸ இடைநிறுத்து", "▶ தொடர்", "⏹ நிறுத்து"
    else:
        listen, pause, resume, stop = "🔊 Listen", "⏸ Pause", "▶ Resume", "⏹ Stop"
    components.html(
        f"""
        <style>
          body {{ margin: 0; padding: 4px 0; background: transparent;
                 font-family: 'Plus Jakarta Sans', -apple-system, 'Segoe UI', sans-serif; }}
          .bar {{ display: inline-flex; gap: 8px; align-items: center; }}
          .btn {{ padding: 8px 18px; border-radius: 999px; border: 1px solid #bbf7d0;
                  background: #f0fdf4; color: #166534; font-weight: 700; font-size: 0.88rem;
                  cursor: pointer; transition: all .18s ease; }}
          .btn:hover {{ background: #166534; color: #fff; border-color: #166534; }}
        </style>
        <audio id="{audio_id}" src="data:audio/wav;base64,{b64}" preload="auto"></audio>
        <div class="bar" style="{'' if show_controls else 'display:none'}">
            <button class="btn" id="bL_{audio_id}">{listen}</button>
            <button class="btn" id="bP_{audio_id}" style="display:none">{pause}</button>
            <button class="btn" id="bR_{audio_id}" style="display:none">{resume}</button>
            <button class="btn" id="bS_{audio_id}" style="display:none">{stop}</button>
        </div>
        <script>
        (function() {{
            var a = document.getElementById('{audio_id}');
            var bL = document.getElementById('bL_{audio_id}'), bP = document.getElementById('bP_{audio_id}'),
                bR = document.getElementById('bR_{audio_id}'), bS = document.getElementById('bS_{audio_id}');
            // idle -> [Listen]   playing -> [Listen][Pause][Stop]   paused -> [Listen][Resume][Stop]
            function ui(state) {{
                bP.style.display = state === 'playing' ? '' : 'none';
                bR.style.display = state === 'paused' ? '' : 'none';
                bS.style.display = state === 'idle' ? 'none' : '';
            }}
            bL.onclick = function() {{ a.currentTime = 0; a.play(); }};
            bP.onclick = function() {{ a.pause(); ui('paused'); }};
            bR.onclick = function() {{ a.play(); }};
            bS.onclick = function() {{ a.pause(); a.currentTime = 0; ui('idle'); }};
            a.addEventListener('play', function() {{ ui('playing'); }});
            a.addEventListener('ended', function() {{ ui('idle'); }});
        }})();
        </script>
        <script>{autoplay_js}</script>
        """,
        height=52 if show_controls else 1,   # height=1 iframes are hidden by the app CSS
    )
    return True


def render_sarvam_sequence(items, key: str = "seq", auto_play: bool = True) -> bool:
    """Play several clips back to back (e.g. English then Tamil) in one small player
    with Listen / Stop. items = [(text, "English"|"Tamil"), ...].
    Returns False when Sarvam is unavailable so the caller can fall back."""
    if not SARVAM_API_KEY or not items:
        return False
    clips = []
    for text, lang in items:
        wav = _sarvam_speak_cached(text, "ta-IN" if lang == "Tamil" else "en-IN",
                                   SARVAM_TTS_SPEAKER, SARVAM_TTS_MODEL)
        if not wav:
            return False
        clips.append(base64.b64encode(wav).decode("ascii"))
    uid = f"seq_{abs(hash(key)) % 100000}"
    audios = "".join(
        f'<audio id="{uid}_{i}" src="data:audio/wav;base64,{b}" preload="auto"></audio>'
        for i, b in enumerate(clips)
    )
    components.html(
        f"""
        <style>
          body {{ margin: 0; padding: 4px 0; background: transparent;
                 font-family: 'Plus Jakarta Sans', -apple-system, 'Segoe UI', sans-serif; text-align: center; }}
          .btn {{ padding: 8px 20px; border-radius: 999px; border: 1px solid #bbf7d0;
                  background: #f0fdf4; color: #166534; font-weight: 700; font-size: 0.92rem;
                  cursor: pointer; margin: 0 4px; transition: all .18s ease; }}
          .btn:hover {{ background: #166534; color: #fff; border-color: #166534; }}
        </style>
        {audios}
        <button class="btn" id="{uid}_L">🔊 Listen · கேள்</button>
        <button class="btn" id="{uid}_S" style="display:none">⏹ Stop · நிறுத்து</button>
        <script>
        (function() {{
            var n = {len(clips)}, els = [], run = 0;
            for (var i = 0; i < n; i++) els.push(document.getElementById('{uid}_' + i));
            var bL = document.getElementById('{uid}_L'), bS = document.getElementById('{uid}_S');
            function ui(playing) {{ bS.style.display = playing ? '' : 'none'; }}
            function stop() {{ run++; els.forEach(function(a) {{ a.pause(); a.currentTime = 0; }}); ui(false); }}
            function playAll() {{
                stop(); var me = run, i = 0; ui(true);
                function next() {{
                    if (me !== run) return;
                    if (i >= n) {{ ui(false); return; }}
                    var a = els[i++]; a.onended = next;
                    var p = a.play(); if (p && p.catch) p.catch(function() {{ ui(false); }});
                }}
                next();
            }}
            bL.onclick = playAll; bS.onclick = stop;
            {"setTimeout(playAll, 300);" if auto_play else ""}
        }})();
        </script>
        """,
        height=52,
    )
    return True



