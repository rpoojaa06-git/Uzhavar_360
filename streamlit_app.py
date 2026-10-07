"""
Uzhavar AI — Voice-First Intelligent Farmer Journey & Scheme Discovery Platform
================================================================================
Flow:
  1. Language Selection splash  →  2. Voice Onboarding (name/age/gender/farmer-type/docs)
  →  3. Main Chat (voice + text, with always-visible language & mode toggles)
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import time

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Uzhavar AI — உழவர் AI",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
:root {
    --green-dark: #1b5e20;
    --green-primary: #2e7d32;
    --green-light: #e8f5e9;
    --green-border: #c8e6c9;
    --orange: #f57f17;
}

/* ---- Language selection splash ---- */
.splash-wrap {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-height: 70vh; text-align: center;
}
.splash-icon { font-size: 5rem; margin-bottom: 0.6rem; }
.splash-title { font-size: 3rem; font-weight: 900; color: var(--green-dark); }
.splash-sub   { font-size: 1.2rem; color: #558b2f; margin-bottom: 0.4rem; }
.splash-tagline { font-size: 0.95rem; color: #666; margin-bottom: 2rem; }
.lang-prompt {
    font-size: 1.15rem; font-weight: 700; color: var(--green-primary);
    background: var(--green-light); border: 1px solid var(--green-border);
    border-radius: 12px; padding: 12px 24px; margin-bottom: 1.8rem;
    display: inline-block;
}

/* ---- Top bar ---- */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    background: var(--green-light); border-bottom: 2px solid var(--green-border);
    padding: 10px 20px; border-radius: 10px; margin-bottom: 14px;
}
.topbar-title { font-size: 1.4rem; font-weight: 800; color: var(--green-dark); }
.topbar-note  { font-size: 0.75rem; color: #558b2f; margin-top: 2px; }

/* ---- Onboarding card ---- */
.ob-card {
    background: #fff; border: 2px solid var(--green-border);
    border-radius: 16px; padding: 32px 40px; max-width: 680px;
    margin: 0 auto; box-shadow: 0 4px 16px rgba(46,125,50,0.10);
    text-align: center;
}
.ob-question {
    font-size: 1.35rem; font-weight: 700; color: var(--green-dark);
    margin-bottom: 24px; line-height: 1.5;
}
.ob-step-label {
    font-size: 0.8rem; color: #888; margin-bottom: 8px; letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ---- Voice widget ---- */
.mic-outer {
    display: flex; flex-direction: column; align-items: center;
    gap: 10px; padding: 10px 0;
}
.voice-status {
    font-size: 0.88rem; color: #555; min-height: 20px;
}
.voice-transcript {
    background: var(--green-light); border: 1px solid var(--green-border);
    border-radius: 10px; padding: 10px 16px; min-width: 260px;
    min-height: 38px; font-size: 1rem; color: var(--green-dark);
    text-align: center; word-break: break-word;
}

/* ---- Scheme card ---- */
.scheme-card {
    background: #fff; border: 2px solid var(--green-primary);
    border-radius: 12px; padding: 18px; margin: 14px 0;
    box-shadow: 0 4px 12px rgba(46,125,50,0.12);
}
.scheme-badge {
    background: var(--green-light); color: var(--green-dark); font-weight: 700;
    padding: 4px 12px; border-radius: 20px; font-size: 0.82rem;
    display: inline-block; margin-bottom: 8px; border: 1px solid #81c784;
}
.scheme-title { color: var(--green-dark); font-size: 1.2rem; font-weight: 700; margin-bottom: 4px; }
.scheme-tamil { color: #558b2f; font-size: 0.92rem; font-weight: 500; margin-bottom: 8px; }
.match-pill {
    background: #ffecb3; color: #e65100; font-weight: 700;
    padding: 3px 10px; border-radius: 12px; font-size: 0.82rem; float: right;
}
.reason-item { color: var(--green-primary); font-weight: 500; margin: 3px 0; font-size: 0.88rem; }
.disclaimer-box {
    font-size: 0.76rem; color: #616161; background: #fafafa;
    border-left: 3px solid #ffa000; padding: 8px 12px; margin-top: 10px; border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# IMPORTS
# ============================================================
try:
    from app.schemes import evaluate_scheme_eligibility
except ImportError:
    import sys
    sys.path.append(".")
    from app.schemes import evaluate_scheme_eligibility


@st.cache_resource(show_spinner=False)
def get_rag_engine():
    try:
        from app.rag import RAG
        return RAG()
    except Exception as e:
        st.error(f"⚠️ RAG Engine error: {e}")
        return None


# ============================================================
# MULTILINGUAL SCRIPT
# ============================================================
SCRIPT = {
    "welcome_voice_en": (
        "Welcome to Uzhavar AI. Please select your language — English or Tamil."
    ),
    "welcome_voice_ta": (
        "உழவர் AI-க்கு வரவேற்கிறோம். தயவுசெய்து உங்கள் மொழியை தேர்ந்தெடுங்கள் — ஆங்கிலம் அல்லது தமிழ்."
    ),
    "intro": {
        "English": (
            "Welcome to Uzhavar AI — your personal farming guide for Tamil Nadu. "
            "I will ask you a few quick questions to personalise your experience. "
            "You can speak your answers or type them using the text box. "
            "You can switch between voice and text at any time using the buttons at the top of the screen. "
            "You can also change the language anytime from the top bar."
        ),
        "Tamil": (
            "உழவர் AI-க்கு வரவேற்கிறோம். இது தமிழ்நாடு விவசாயிகளுக்கான உங்கள் தனிப்பட்ட வழிகாட்டி. "
            "உங்கள் அனுபவத்தை தனிப்பயனாக்க சில கேள்விகள் கேட்கிறேன். "
            "நீங்கள் பேசியோ அல்லது தட்டச்சு செய்தோ பதில் சொல்லலாம். "
            "திரையின் மேல்பகுதியில் உள்ள பொத்தான்களை பயன்படுத்தி குரல் மற்றும் உரைக்கு இடையே எப்போதும் மாறலாம். "
            "மொழியையும் மேல்பட்டியில் மாற்றலாம்."
        ),
    },
    "ask_name": {
        "English": "First, what is your name?",
        "Tamil": "முதலில், உங்கள் பெயர் என்ன?",
    },
    "ask_age": {
        "English": "How old are you?",
        "Tamil": "உங்கள் வயது என்ன?",
    },
    "ask_gender": {
        "English": "What is your gender? Please tap one of the options below.",
        "Tamil": "நீங்கள் ஆண் ஆவீர்களா, பெண் ஆவீர்களா? கீழே உள்ள விருப்பத்தை தேர்ந்தெடுங்கள்.",
    },
    "ask_farmer_type": {
        "English": "Are you an existing farmer, or are you planning to start farming?",
        "Tamil": "நீங்கள் தற்போது ஒரு விவசாயி ஆவீர்களா, அல்லது விவசாயம் தொடங்க திட்டமிடுகிறீர்களா?",
    },
    "ask_docs_existing": {
        "English": (
            "Great! To access government schemes, farmers in Tamil Nadu typically need: "
            "Patta, Chitta or Adangal, Aadhaar card, and a Farmer ID or PPB card. "
            "Do you currently have these documents?"
        ),
        "Tamil": (
            "நல்லது! தமிழ்நாட்டில் அரசு திட்டங்களை பெற, விவசாயிகளுக்கு பட்டா, சிட்டா அல்லது அடங்கல், "
            "ஆதார் அட்டை, மற்றும் விவசாயி அடையாள அட்டை தேவை. "
            "இந்த ஆவணங்கள் உங்களிடம் இருக்கின்றனவா?"
        ),
    },
    "ask_docs_new": {
        "English": (
            "To register as a farmer in Tamil Nadu, you will need: "
            "Aadhaar card, Ration card, and land ownership proof such as Patta. "
            "Do you currently have these documents ready?"
        ),
        "Tamil": (
            "தமிழ்நாட்டில் விவசாயியாக பதிவு செய்ய, ஆதார் அட்டை, ரேஷன் அட்டை, "
            "மற்றும் பட்டா போன்ற நில உரிமை ஆவணங்கள் தேவை. "
            "இந்த ஆவணங்கள் உங்களிடம் தயாராக இருக்கின்றனவா?"
        ),
    },
    "completion": {
        "English": (
            "Thank you {name}! I have noted your details. Let us begin your farming journey. "
            "You can ask me anything about crops, machinery, irrigation, or government schemes. "
            "To switch between voice and text, use the buttons at the top of the screen anytime."
        ),
        "Tamil": (
            "நன்றி {name}! உங்கள் விவரங்களை நான் குறித்துக்கொண்டேன். "
            "இப்போது உங்கள் விவசாய பயணத்தை தொடங்குவோம். "
            "பயிர்கள், இயந்திரங்கள், பாசனம், அல்லது அரசு திட்டங்கள் பற்றி எதுவும் கேளுங்கள். "
            "மேலே உள்ள பொத்தான்களை பயன்படுத்தி குரல் மற்றும் உரைக்கு இடையே மாறலாம்."
        ),
    },
}

LABELS = {
    "English": {
        "begin": "▶  Begin",
        "next": "Next  →",
        "male": "👨  Male",
        "female": "👩  Female",
        "other": "⚧  Other / Prefer not to say",
        "existing_farmer": "🧑‍🌾  I am an existing farmer",
        "new_farmer": "🌱  I am starting fresh",
        "has_docs": "✅  Yes, I have them",
        "no_docs": "📋  No / I'll arrange them",
        "use_answer": "✓  Use this answer",
        "type_label": "Or type your answer:",
        "type_placeholder": "Type here…",
        "confirm": "Confirm  →",
        "chat_placeholder": "Ask any farming or scheme question…",
        "voice_hint": "🎤  Tap mic → speak → confirm",
        "mode_voice": "🎤  Voice",
        "mode_text": "💬  Text",
        "lang_toggle": "🌐  Language",
        "suggested": "💡  Suggested Questions:",
        "reset": "🗑️  Reset Conversation",
        "sources_label": "📚  Verified Sources",
        "spinner": "🔍  Consulting verified agricultural guides…",
        "q1": "🌱  How do I start farming?",
        "q2": "🌾  What crop should I grow?",
        "q3": "🚜  What machinery do I need?",
        "q4": "💧  How to install drip irrigation?",
        "q5": "🐛  How to control pests & weeds?",
        "q6": "🏛️  What government subsidies are available?",
        "q1_full": "How do I start farming? What are the key first steps?",
        "q2_full": "What crop should I grow? Help me choose the right crop.",
        "q3_full": "What farm machinery do I need and how do I use it?",
        "q4_full": "How can I install drip irrigation? How much water does it save?",
        "q5_full": "What are the best methods to control pests and weeds in my farm?",
        "q6_full": "Am I eligible for a drip irrigation or machinery subsidy from the government?",
        "step_label": "Setting up your profile",
        "tap_mic": "Tap the mic to speak",
        "listening": "Listening…",
        "got_it": "Got it! Tap ✓ to confirm.",
        "try_again": "Tap mic to try again.",
        "no_support": "Voice not supported in this browser. Please type below.",
        "age_label": "Your age:",
    },
    "Tamil": {
        "begin": "▶  தொடங்குவோம்",
        "next": "அடுத்து  →",
        "male": "👨  ஆண்",
        "female": "👩  பெண்",
        "other": "⚧  வேறு / சொல்ல விரும்பவில்லை",
        "existing_farmer": "🧑‍🌾  நான் தற்போது விவசாயி",
        "new_farmer": "🌱  நான் புதிதாக தொடங்குகிறேன்",
        "has_docs": "✅  ஆம், என்னிடம் இருக்கின்றன",
        "no_docs": "📋  இல்லை / ஏற்பாடு செய்கிறேன்",
        "use_answer": "✓  இந்த பதிலை பயன்படுத்து",
        "type_label": "அல்லது தட்டச்சு செய்யுங்கள்:",
        "type_placeholder": "இங்கே தட்டச்சு செய்யுங்கள்…",
        "confirm": "உறுதிப்படுத்து  →",
        "chat_placeholder": "உங்கள் விவசாய அல்லது திட்ட கேள்வியை கேளுங்கள்…",
        "voice_hint": "🎤  மைக்கை தட்டவும் → பேசவும் → உறுதிப்படுத்தவும்",
        "mode_voice": "🎤  குரல்",
        "mode_text": "💬  உரை",
        "lang_toggle": "🌐  மொழி",
        "suggested": "💡  பரிந்துரைக்கப்பட்ட கேள்விகள்:",
        "reset": "🗑️  உரையாடலை மீட்டமை",
        "sources_label": "📚  சரிபார்க்கப்பட்ட ஆதாரங்கள்",
        "spinner": "🔍  விவசாய வழிகாட்டிகளை ஆய்வு செய்கிறேன்…",
        "q1": "🌱  விவசாயம் எப்படி தொடங்குவது?",
        "q2": "🌾  என்ன பயிர் விளைவிக்க வேண்டும்?",
        "q3": "🚜  என்ன இயந்திரங்கள் தேவை?",
        "q4": "💧  சொட்டு நீர் பாசனம் எப்படி அமைப்பது?",
        "q5": "🐛  பூச்சி மற்றும் களை கட்டுப்பாடு?",
        "q6": "🏛️  என்ன அரசு மானியங்கள் கிடைக்கும்?",
        "q1_full": "விவசாயம் எப்படி தொடங்குவது? முக்கிய படிகள் என்ன?",
        "q2_full": "என்ன பயிர் விளைவிக்க வேண்டும்? சரியான பயிரை தேர்ந்தெடுக்க உதவுங்கள்.",
        "q3_full": "என்ன விவசாய இயந்திரங்கள் தேவை மற்றும் எப்படி பயன்படுத்துவது?",
        "q4_full": "சொட்டு நீர் பாசனம் எப்படி அமைப்பது? எவ்வளவு தண்ணீர் மிச்சமாகும்?",
        "q5_full": "என் பண்ணையில் பூச்சி மற்றும் களையை கட்டுப்படுத்த சிறந்த வழிகள் என்ன?",
        "q6_full": "சொட்டுநீர் பாசனம் அல்லது இயந்திர மானியத்திற்கு நான் தகுதியானவரா?",
        "step_label": "உங்கள் விவரங்களை அமைக்கிறோம்",
        "tap_mic": "பேச மைக்கை தட்டவும்",
        "listening": "கேட்கிறேன்…",
        "got_it": "புரிந்தது! ✓ தட்டி உறுதிப்படுத்துங்கள்.",
        "try_again": "மீண்டும் முயற்சிக்க மைக்கை தட்டவும்.",
        "no_support": "இந்த உலாவியில் குரல் ஆதரிக்கப்படவில்லை. கீழே தட்டச்சு செய்யுங்கள்.",
        "age_label": "உங்கள் வயது:",
    },
}

# ============================================================
# SESSION STATE DEFAULTS
# ============================================================
_DEFAULTS = {
    "language": None,               # None → language not selected
    "onboarding_step": "intro",     # intro / name / age / gender / farmer_type / docs / done
    "farmer_info": {},              # collected profile dict
    "voice_mode": True,             # True = voice, False = text
    "messages": [],                 # chat history
    "completion_spoken": False,     # avoid replaying completion TTS
    "last_tts_key": None,           # guard: only speak once per step
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ============================================================
# UTILITY — TTS via Web Speech API
# ============================================================
def _speak(text: str, lang: str, key: str):
    """Injects a JS TTS utterance, keyed so it only fires once per unique key."""
    if st.session_state.last_tts_key == key:
        return
    st.session_state.last_tts_key = key
    lang_code = "ta-IN" if lang == "Tamil" else "en-IN"
    escaped = json.dumps(text)
    components.html(f"""
    <script>
    (function() {{
        var s = window.speechSynthesis;
        s.cancel();
        function go() {{
            var u = new SpeechSynthesisUtterance({escaped});
            u.lang = '{lang_code}'; u.rate = 0.88; u.pitch = 1.05;
            var vv = s.getVoices();
            var pref = vv.find(v => v.lang === '{lang_code}')
                     || vv.find(v => v.lang.startsWith('{lang_code[:2]}'));
            if (pref) u.voice = pref;
            s.speak(u);
        }}
        s.getVoices().length ? go() : s.addEventListener('voiceschanged', go, {{once:true}});
    }})();
    </script>
    """, height=0, key=f"__tts_{key}")


# ============================================================
# UTILITY — Voice capture widget (STT via Web Speech API)
# Returns recognized string if confirmed via query param, else None.
# ============================================================
def _voice_capture(step_key: str, lang: str) -> str | None:
    params = st.query_params
    if params.get("vstep") == step_key and params.get("vresult"):
        result = params["vresult"]
        st.query_params.clear()
        return result

    L = LABELS[lang]
    lang_code = "ta-IN" if lang == "Tamil" else "en-IN"

    components.html(f"""
    <style>
    .mic-wrap {{ display:flex; flex-direction:column; align-items:center; gap:8px; font-family:sans-serif; }}
    .mic-btn {{
        width:70px; height:70px; border-radius:50%; border:none; cursor:pointer;
        font-size:1.9rem; color:#fff; background:#2e7d32;
        box-shadow:0 4px 12px rgba(46,125,50,.35); transition:.2s;
    }}
    .mic-btn.rec {{ background:#c62828; animation:pulse 1s infinite; }}
    @keyframes pulse {{
        0%  {{ box-shadow:0 0 0 0 rgba(198,40,40,.45); }}
        70% {{ box-shadow:0 0 0 14px rgba(198,40,40,0); }}
        100%{{ box-shadow:0 0 0 0 rgba(198,40,40,0); }}
    }}
    .trs  {{ min-height:36px; min-width:240px; background:#e8f5e9; border:1px solid #c8e6c9;
             border-radius:8px; padding:8px 14px; text-align:center; color:#1b5e20;
             font-size:0.98rem; word-break:break-word; }}
    .st   {{ font-size:.82rem; color:#555; min-height:18px; }}
    .use-btn {{
        display:none; padding:7px 22px; background:#2e7d32; color:#fff;
        border:none; border-radius:18px; cursor:pointer; font-size:.92rem;
        margin-top:2px;
    }}
    </style>
    <div class="mic-wrap">
        <button class="mic-btn" id="mb" onclick="toggle()">🎤</button>
        <div class="st" id="st">{L["tap_mic"]}</div>
        <div class="trs" id="trs"></div>
        <button class="use-btn" id="ub" onclick="submit()">{L["use_answer"]}</button>
    </div>
    <script>
    var recog = null, final = '', going = false;
    function toggle() {{ going ? recog.stop() : start(); }}
    function start() {{
        var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {{ document.getElementById('st').innerText = "{L["no_support"]}"; return; }}
        recog = new SR();
        recog.lang = '{lang_code}'; recog.interimResults = true; recog.maxAlternatives = 1;
        going = true; final = '';
        document.getElementById('mb').classList.add('rec');
        document.getElementById('mb').innerText = '⏹';
        document.getElementById('st').innerText  = '{L["listening"]}';
        document.getElementById('trs').innerText = '';
        document.getElementById('ub').style.display = 'none';
        recog.onresult = function(e) {{
            var int = '';
            for (var i=e.resultIndex; i<e.results.length; i++) {{
                e.results[i].isFinal ? (final += e.results[i][0].transcript)
                                     : (int   += e.results[i][0].transcript);
            }}
            document.getElementById('trs').innerText = final || int;
        }};
        recog.onend = function() {{
            going = false;
            document.getElementById('mb').classList.remove('rec');
            document.getElementById('mb').innerText = '🎤';
            document.getElementById('st').innerText = final ? '{L["got_it"]}' : '{L["try_again"]}';
            if (final) document.getElementById('ub').style.display = 'inline-block';
        }};
        recog.onerror = function(e) {{
            going = false;
            document.getElementById('mb').classList.remove('rec');
            document.getElementById('mb').innerText = '🎤';
            document.getElementById('st').innerText = 'Error: ' + e.error + '. {L["try_again"]}';
        }};
        recog.start();
    }}
    function submit() {{
        if (!final) return;
        var url = new URL(window.parent.location.href);
        url.searchParams.set('vstep', '{step_key}');
        url.searchParams.set('vresult', final);
        window.parent.location.href = url.toString();
    }}
    </script>
    """, height=175, key=f"__stt_{step_key}_{int(time.time()*100)%1000}")
    return None


# ============================================================
# TOP BAR  (always visible once language chosen)
# ============================================================
def _topbar():
    lang = st.session_state.language
    L = LABELS[lang]

    c1, c2, c3 = st.columns([4, 3, 3])
    with c1:
        st.markdown(
            "<div style='font-size:1.35rem;font-weight:900;color:#1b5e20;'>"
            "🌾 Uzhavar AI — உழவர் AI</div>"
            "<div style='font-size:0.72rem;color:#558b2f;'>"
            "Intelligent Farmer Journey & Scheme Discovery</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(f"<b>{L['lang_toggle']}</b>", unsafe_allow_html=True)
        ea, ta = st.columns(2)
        with ea:
            st.button(
                "EN 🇬🇧",
                key="tb_en",
                use_container_width=True,
                type="primary" if lang == "English" else "secondary",
                on_click=_switch_lang, args=("English",),
            )
        with ta:
            st.button(
                "தமிழ் 🇮🇳",
                key="tb_ta",
                use_container_width=True,
                type="primary" if lang == "Tamil" else "secondary",
                on_click=_switch_lang, args=("Tamil",),
            )
    with c3:
        st.markdown(f"<b>{L['mode_voice']} / {L['mode_text']}</b>", unsafe_allow_html=True)
        va, ta2 = st.columns(2)
        with va:
            st.button(
                L["mode_voice"],
                key="tb_voice",
                use_container_width=True,
                type="primary" if st.session_state.voice_mode else "secondary",
                on_click=_set_mode, args=(True,),
            )
        with ta2:
            st.button(
                L["mode_text"],
                key="tb_text",
                use_container_width=True,
                type="primary" if not st.session_state.voice_mode else "secondary",
                on_click=_set_mode, args=(False,),
            )
    st.divider()


def _switch_lang(new_lang):
    st.session_state.language = new_lang
    st.session_state.last_tts_key = None


def _set_mode(voice: bool):
    st.session_state.voice_mode = voice


# ============================================================
# ONBOARDING HELPERS
# ============================================================
STEP_ORDER = ["intro", "name", "age", "gender", "farmer_type", "docs"]
STEP_TOTAL = len(STEP_ORDER)


def _step_progress(step):
    idx = STEP_ORDER.index(step) if step in STEP_ORDER else STEP_TOTAL
    L = LABELS[st.session_state.language]
    st.progress(idx / STEP_TOTAL, text=f"{L['step_label']} — {idx}/{STEP_TOTAL}")


def _ob_input_row(step_key: str, lang: str):
    """Voice widget on left + text fallback on right. Returns confirmed text or None."""
    L = LABELS[lang]
    result = None

    if st.session_state.voice_mode:
        vc, tc = st.columns([1, 1], gap="large")
        with vc:
            result = _voice_capture(step_key, lang)
        with tc:
            st.markdown(f"<div style='font-size:.88rem;color:#555;margin-bottom:4px;'>{L['type_label']}</div>",
                        unsafe_allow_html=True)
            with st.form(f"txt_{step_key}"):
                val = st.text_input("", placeholder=L["type_placeholder"],
                                    label_visibility="collapsed", key=f"tf_{step_key}")
                if st.form_submit_button(L["confirm"]) and val.strip():
                    result = val.strip()
    else:
        with st.form(f"txt_{step_key}"):
            val = st.text_input(L["type_label"], placeholder=L["type_placeholder"],
                                key=f"tf_{step_key}")
            if st.form_submit_button(L["next"]) and val.strip():
                result = val.strip()

    return result


# ============================================================
# PAGE 1 — LANGUAGE SELECTION SPLASH
# ============================================================
def page_language_select():
    # Auto-play bilingual welcome voice on first load
    components.html("""
    <script>
    (function() {
        var s = window.speechSynthesis;
        s.cancel();
        function go() {
            var en = new SpeechSynthesisUtterance(
                "Welcome to Uzhavar AI. Please select your language — English or Tamil.");
            en.lang = 'en-IN'; en.rate = 0.88;
            var ta = new SpeechSynthesisUtterance(
                "உழவர் AI-க்கு வரவேற்கிறோம். தயவுசெய்து உங்கள் மொழியை தேர்ந்தெடுங்கள்.");
            ta.lang = 'ta-IN'; ta.rate = 0.88;
            en.onend = function() { s.speak(ta); };
            s.speak(en);
        }
        s.getVoices().length ? go() : s.addEventListener('voiceschanged', go, {once:true});
    })();
    </script>
    """, height=0, key="splash_tts")

    st.markdown("""
    <div class="splash-wrap">
        <div class="splash-icon">🌾</div>
        <div class="splash-title">Uzhavar AI</div>
        <div class="splash-sub">உழவர் AI</div>
        <div class="splash-tagline">Intelligent Farmer Journey & Scheme Discovery — Tamil Nadu</div>
        <div class="lang-prompt">
            🔊 Please select your language &nbsp;/&nbsp; உங்கள் மொழியை தேர்வு செய்யுங்கள்
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, cl, cg, cr, _ = st.columns([2, 3, 1, 3, 2])
    with cl:
        if st.button("🇬🇧  English", use_container_width=True, key="sel_en"):
            st.session_state.language = "English"
            st.session_state.onboarding_step = "intro"
            st.session_state.last_tts_key = None
            st.rerun()
    with cr:
        if st.button("🇮🇳  தமிழ் (Tamil)", use_container_width=True, key="sel_ta"):
            st.session_state.language = "Tamil"
            st.session_state.onboarding_step = "intro"
            st.session_state.last_tts_key = None
            st.rerun()


# ============================================================
# PAGE 2 — VOICE ONBOARDING
# ============================================================
def page_onboarding():
    lang = st.session_state.language
    L = LABELS[lang]
    step = st.session_state.onboarding_step
    fi = st.session_state.farmer_info

    _topbar()
    _step_progress(step)
    st.markdown("")

    # ---- INTRO ----
    if step == "intro":
        _speak(SCRIPT["intro"][lang], lang, "intro")
        _, cc, _ = st.columns([1, 4, 1])
        with cc:
            st.markdown(f"""
            <div class="ob-card">
                <div style='font-size:3rem;'>🌾</div>
                <div class="ob-question">
                    {"Welcome to Uzhavar AI — your personal farming guide for Tamil Nadu."
                     if lang=="English" else
                     "உழவர் AI-க்கு வரவேற்கிறோம் — தமிழ்நாட்டு விவசாயிகளுக்கான உங்கள் வழிகாட்டி."}
                </div>
                <p style='color:#555; font-size:.95rem;'>
                    {"I'll ask a few quick questions to personalize your experience. "
                     "You can speak or type your answers. "
                     "Switch between voice & text anytime from the top bar."
                     if lang=="English" else
                     "உங்கள் அனுபவத்தை தனிப்பயனாக்க சில கேள்விகள் கேட்கிறேன். "
                     "பேசியோ தட்டச்சு செய்தோ பதில் சொல்லலாம். "
                     "குரல் மற்றும் உரைக்கு இடையே மேல்பட்டியிலிருந்து மாறலாம்."}
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            _, bc, _ = st.columns([2, 3, 2])
            with bc:
                if st.button(L["begin"], use_container_width=True, key="begin_btn"):
                    st.session_state.onboarding_step = "name"
                    st.session_state.last_tts_key = None
                    st.rerun()

    # ---- NAME ----
    elif step == "name":
        q = SCRIPT["ask_name"][lang]
        _speak(q, lang, "ob_name")
        _, cc, _ = st.columns([1, 4, 1])
        with cc:
            st.markdown(f"""
            <div class="ob-card">
                <div class="ob-step-label">Step 1 / {STEP_TOTAL}</div>
                <div class="ob-question">👤 {q}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            result = _ob_input_row("ob_name", lang)
            if result:
                fi["name"] = result.strip().title()
                st.session_state.onboarding_step = "age"
                st.session_state.last_tts_key = None
                st.rerun()

    # ---- AGE ----
    elif step == "age":
        q = SCRIPT["ask_age"][lang]
        _speak(q, lang, "ob_age")
        _, cc, _ = st.columns([1, 4, 1])
        with cc:
            st.markdown(f"""
            <div class="ob-card">
                <div class="ob-step-label">Step 2 / {STEP_TOTAL}</div>
                <div class="ob-question">🎂 {q}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")

            if st.session_state.voice_mode:
                vc, tc = st.columns([1, 1], gap="large")
                with vc:
                    age_voice = _voice_capture("ob_age", lang)
                    if age_voice:
                        digits = "".join(filter(str.isdigit, age_voice))
                        if digits:
                            fi["age"] = digits
                            st.session_state.onboarding_step = "gender"
                            st.session_state.last_tts_key = None
                            st.rerun()
                with tc:
                    with st.form("age_form"):
                        age_val = st.number_input(L["age_label"], min_value=15,
                                                  max_value=100, value=35, step=1,
                                                  key="age_num")
                        if st.form_submit_button(L["confirm"]):
                            fi["age"] = str(age_val)
                            st.session_state.onboarding_step = "gender"
                            st.session_state.last_tts_key = None
                            st.rerun()
            else:
                with st.form("age_form_t"):
                    age_val = st.number_input(L["age_label"], min_value=15,
                                              max_value=100, value=35, step=1, key="age_num_t")
                    if st.form_submit_button(L["next"]):
                        fi["age"] = str(age_val)
                        st.session_state.onboarding_step = "gender"
                        st.session_state.last_tts_key = None
                        st.rerun()

    # ---- GENDER ----
    elif step == "gender":
        q = SCRIPT["ask_gender"][lang]
        _speak(q, lang, "ob_gender")
        _, cc, _ = st.columns([1, 4, 1])
        with cc:
            st.markdown(f"""
            <div class="ob-card">
                <div class="ob-step-label">Step 3 / {STEP_TOTAL}</div>
                <div class="ob-question">🧑 {q}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            g1, g2, g3 = st.columns(3)
            for label, val, col in [
                (L["male"], "Male", g1),
                (L["female"], "Female", g2),
                (L["other"], "Other", g3),
            ]:
                with col:
                    if st.button(label, use_container_width=True, key=f"gen_{val}"):
                        fi["gender"] = val
                        st.session_state.onboarding_step = "farmer_type"
                        st.session_state.last_tts_key = None
                        st.rerun()

    # ---- FARMER TYPE ----
    elif step == "farmer_type":
        q = SCRIPT["ask_farmer_type"][lang]
        _speak(q, lang, "ob_ftype")
        _, cc, _ = st.columns([1, 4, 1])
        with cc:
            st.markdown(f"""
            <div class="ob-card">
                <div class="ob-step-label">Step 4 / {STEP_TOTAL}</div>
                <div class="ob-question">🌱 {q}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            fa, fb = st.columns(2)
            with fa:
                if st.button(L["existing_farmer"], use_container_width=True, key="ft_ex"):
                    fi["farmer_type"] = "existing"
                    st.session_state.onboarding_step = "docs"
                    st.session_state.last_tts_key = None
                    st.rerun()
            with fb:
                if st.button(L["new_farmer"], use_container_width=True, key="ft_new"):
                    fi["farmer_type"] = "new"
                    st.session_state.onboarding_step = "docs"
                    st.session_state.last_tts_key = None
                    st.rerun()

    # ---- DOCS ----
    elif step == "docs":
        ftype = fi.get("farmer_type", "new")
        q_key = "ask_docs_existing" if ftype == "existing" else "ask_docs_new"
        q = SCRIPT[q_key][lang]
        _speak(q, lang, f"ob_docs_{ftype}")
        _, cc, _ = st.columns([1, 4, 1])
        with cc:
            st.markdown(f"""
            <div class="ob-card">
                <div class="ob-step-label">Step 5 / {STEP_TOTAL}</div>
                <div class="ob-question">📄 {q}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")

            # Show required doc list as info box
            if lang == "English":
                docs_md = (
                    "**Required documents (TN farmers):**\n"
                    "Patta / Chitta / Adangal &nbsp;·&nbsp; Aadhaar &nbsp;·&nbsp; "
                    "Farmer ID / PPB Card &nbsp;·&nbsp; Bank passbook"
                    if ftype == "existing" else
                    "**Documents to register as a farmer:**\n"
                    "Aadhaar &nbsp;·&nbsp; Ration card &nbsp;·&nbsp; Land proof (Patta) &nbsp;·&nbsp; Bank account"
                )
            else:
                docs_md = (
                    "**தேவையான ஆவணங்கள்:**\n"
                    "பட்டா / சிட்டா / அடங்கல் &nbsp;·&nbsp; ஆதார் &nbsp;·&nbsp; "
                    "விவசாயி அடையாள அட்டை &nbsp;·&nbsp; வங்கி கணக்கு"
                    if ftype == "existing" else
                    "**விவசாயியாக பதிவு செய்ய:**\n"
                    "ஆதார் &nbsp;·&nbsp; ரேஷன் அட்டை &nbsp;·&nbsp; நில உரிமை சான்று (பட்டா) &nbsp;·&nbsp; வங்கி கணக்கு"
                )
            st.info(docs_md)

            da, db = st.columns(2)
            with da:
                if st.button(L["has_docs"], use_container_width=True, key="doc_yes"):
                    fi["has_docs"] = True
                    _go_done()
            with db:
                if st.button(L["no_docs"], use_container_width=True, key="doc_no"):
                    fi["has_docs"] = False
                    _go_done()


def _go_done():
    st.session_state.onboarding_step = "done"
    st.session_state.last_tts_key = None
    st.session_state.completion_spoken = False
    st.session_state.messages = []   # fresh — greeting will be built in main chat
    st.rerun()


# ============================================================
# PAGE 3 — MAIN CHAT
# ============================================================
def page_main_chat():
    lang = st.session_state.language
    L = LABELS[lang]
    fi = st.session_state.farmer_info
    name = fi.get("name", "")

    # Play completion voice exactly once
    if not st.session_state.completion_spoken:
        text = SCRIPT["completion"][lang].format(name=name)
        _speak(text, lang, "completion")
        st.session_state.completion_spoken = True

    # Personalized greeting (runs once when messages is empty)
    if not st.session_state.messages:
        ftype = fi.get("farmer_type", "new")
        has_docs = fi.get("has_docs", True)
        if lang == "English":
            g = (
                f"Vanakkam {name}! 🙏 I'm **Uzhavar AI**, your personal farming companion.\n\n"
            )
            g += (
                "As an experienced farmer, I can help you with crop management, pest control, "
                "irrigation, machinery, and government schemes."
                if ftype == "existing" else
                "Since you're starting fresh, I'll guide you step by step — "
                "from land preparation and crop selection to government support for new farmers."
            )
            if ftype == "existing" and not has_docs:
                g += "\n\nI can also guide you on which documents to gather for government scheme applications."
            g += "\n\n**How can I help you today?**"
        else:
            g = (
                f"வணக்கம் {name}! 🙏 நான் **உழவர் AI**, உங்கள் தனிப்பட்ட விவசாய வழிகாட்டி.\n\n"
            )
            g += (
                "அனுபவமிக்க விவசாயியாக, பயிர் மேலாண்மை, பூச்சி கட்டுப்பாடு, பாசனம், "
                "இயந்திரங்கள் மற்றும் அரசு திட்டங்களில் உதவுகிறேன்."
                if ftype == "existing" else
                "விவசாயத்தை புதிதாக தொடங்குவதால், நில தேர்வு, பயிர் தேர்வு மற்றும் "
                "புதிய விவசாயிகளுக்கான அரசு ஆதரவு வரை படிப்படியாக வழிகாட்டுகிறேன்."
            )
            g += "\n\n**இன்று நான் உங்களுக்கு எப்படி உதவலாம்?**"

        st.session_state.messages = [{"role": "assistant", "content": g,
                                      "sources": [], "schemes": []}]

    # --- TOP BAR ---
    _topbar()

    # --- SUGGESTED QUESTIONS ---
    st.markdown(f"##### {L['suggested']}")
    qa = st.columns(3)
    qb = st.columns(3)
    chosen_prompt = None
    qs = [("q1", "q1_full"), ("q2", "q2_full"), ("q3", "q3_full"),
          ("q4", "q4_full"), ("q5", "q5_full"), ("q6", "q6_full")]
    for i, (short, full) in enumerate(qs):
        col = (qa if i < 3 else qb)[i % 3]
        with col:
            if st.button(L[short], use_container_width=True, key=f"qq_{i}"):
                chosen_prompt = L[full]

    # --- CHAT HISTORY ---
    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message(role, avatar="👨‍🌾" if role == "user" else "🌾"):
            st.markdown(msg["content"])
            if msg.get("schemes"):
                _render_schemes(msg["schemes"])
            if msg.get("sources"):
                with st.expander(f"{L['sources_label']} ({len(msg['sources'])})"):
                    for s in msg["sources"]:
                        st.markdown(f"• **{s['source']}** (Page {s['page']}) — *{s['score']}*")

    # --- VOICE INPUT (if voice mode on, show capture widget above chat input) ---
    voice_query = None
    if st.session_state.voice_mode:
        params = st.query_params
        if params.get("vstep") == "chat" and params.get("vresult"):
            voice_query = params["vresult"]
            st.query_params.clear()
        else:
            with st.expander("🎤 Speak your question", expanded=True):
                voice_query = _voice_capture("chat", lang)

    # --- TEXT CHAT INPUT (always visible) ---
    typed_query = st.chat_input(L["chat_placeholder"])

    # Resolve final query
    user_query = voice_query or typed_query or chosen_prompt

    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user", avatar="👨‍🌾"):
            st.markdown(user_query)

        profile_dict = {
            "name": fi.get("name"),
            "age": fi.get("age"),
            "gender": fi.get("gender"),
            "farmer_type": fi.get("farmer_type"),
            "has_docs": fi.get("has_docs"),
            "language": lang,
            "farming_stage": "Planning",
        }
        chat_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]

        with st.chat_message("assistant", avatar="🌾"):
            with st.spinner(L["spinner"]):
                rag = get_rag_engine()
                if rag:
                    answer, contexts, matched_schemes, _stage = rag.answer(
                        question=user_query,
                        profile=profile_dict,
                        history=chat_history,
                        return_details=True,
                    )
                else:
                    answer = ("Uzhavar AI engine is initializing. "
                              "Please check Qdrant / Gemini configuration."
                              if lang == "English" else
                              "உழவர் AI தயாராகுகிறது. Qdrant / Gemini அமைப்பை சரிபார்க்கவும்.")
                    contexts = []
                    matched_schemes = evaluate_scheme_eligibility(user_query, profile_dict)

                st.markdown(answer)

                # TTS of answer if voice mode
                if st.session_state.voice_mode:
                    _speak(answer[:400], lang, f"ans_{int(time.time())}")

                if matched_schemes:
                    _render_schemes(matched_schemes)

                if contexts:
                    with st.expander(f"{L['sources_label']} ({len(contexts)})"):
                        for c in contexts:
                            st.markdown(
                                f"• **{c['source']}** (Page {c['page']}) — "
                                f"*{round(c.get('rerank_score', c.get('score', 0.0)), 4)}*"
                            )

                sources_stored = [
                    {"source": c["source"], "page": c["page"],
                     "score": round(c.get("rerank_score", c.get("score", 0.0)), 4)}
                    for c in contexts
                ]
                st.session_state.messages.append({
                    "role": "assistant", "content": answer,
                    "sources": sources_stored, "schemes": matched_schemes,
                })

    # Sidebar — minimal, just reset
    with st.sidebar:
        st.markdown("### ℹ️ Info")
        if st.button(L["reset"], use_container_width=True):
            st.session_state.messages = []
            st.session_state.completion_spoken = False
            st.rerun()
        st.divider()
        with st.expander("📚 Knowledge Base"):
            st.caption(
                "• Crop production.pdf\n• drip_irrigation.pdf\n"
                "• Farm Machinery.pdf\n• ICAR Kharif Agro-Advisories 2025\n"
                "• Weed Management Guide"
            )
            st.write("**Vector DB:** 1,353 chunks · BAAI/bge-m3")


def _render_schemes(schemes):
    for sch in schemes:
        st.markdown(f"""
        <div class="scheme-card">
            <span class="match-pill">🎯 {sch['potential_match']}% match</span>
            <span class="scheme-badge">🏛️ {sch['category']} Scheme</span>
            <div class="scheme-title">{sch['name']}</div>
            <div class="scheme-tamil">{sch.get('tamil_name','')}</div>
            <p style="font-size:.9rem;color:#424242;margin-bottom:8px;">{sch['description']}</p>
            <p style="font-size:.88rem;font-weight:600;color:#1b5e20;">
                <b>Subsidy:</b> {sch['subsidy_details']}</p>
            <div style="margin-top:8px;"><b>Why this may match:</b>
                {"".join(f"<div class='reason-item'>✓ {r}</div>" for r in sch['reasons'])}
            </div>
            <div class="disclaimer-box">⚠️ <b>Note:</b> {sch['disclaimer']}</div>
        </div>
        """, unsafe_allow_html=True)
        cb, _ = st.columns([2, 3])
        with cb:
            if st.button("🔗 Continue to Uzhavar",
                         key=f"uzhavar_{sch['scheme_id']}_{id(sch)}"):
                st.success(
                    f"✅ Uzhavar Portal → `{sch['official_url']}`\n\n"
                    "*(Prototype: links to official Uzhavar app in production)*"
                )


# ============================================================
# ROUTING
# ============================================================
if st.session_state.language is None:
    page_language_select()
elif st.session_state.onboarding_step != "done":
    page_onboarding()
else:
    page_main_chat()
