"""
Uzhavar AI — Voice-First Intelligent Agricultural Guide
================================================================================
Features:
  1. Language Selection Splash with Auto Voice Guidance (English & Tamil)
  2. Voice & Interactive Onboarding (Name, Age, Gender, Farmer Category, Documents)
  3. Persistent Offline Profile Storage (SQLite & JSON in data/)
  4. Grounded Agricultural RAG Guidance (Focused purely on agronomy & farming)
  5. Always-Visible Top Navigation with Instant Voice/Text & Language Toggles
  6. Modern, Fluid Glassmorphism UI with Micro-Animations & Polished Effects
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import time
from app.profile_store import save_farmer_profile

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Uzhavar AI — உழவர் AI",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# MODERN DESIGN SYSTEM & MICRO-ANIMATIONS (CSS)
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+Tamil:wght@400;500;600;700&display=swap');

:root {
    --primary: #1e7e34;
    --primary-dark: #145a27;
    --primary-light: #e8f5e9;
    --primary-hover: #155724;
    --accent: #f59e0b;
    --accent-light: #fef3c7;
    --surface-glass: rgba(255, 255, 255, 0.92);
    --surface-card: #ffffff;
    --border-soft: #c8e6c9;
    --border-glass: rgba(46, 125, 50, 0.16);
    --text-main: #1c2b1e;
    --text-muted: #4a5d4e;
    --shadow-soft: 0 10px 25px -5px rgba(24, 75, 34, 0.08), 0 8px 10px -6px rgba(24, 75, 34, 0.04);
    --shadow-hover: 0 14px 28px -4px rgba(24, 75, 34, 0.14), 0 10px 10px -5px rgba(24, 75, 34, 0.06);
}

/* Global Font & Smooth Scrolling */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Noto Sans Tamil', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-main);
    background-color: #f7faf7;
}

/* Keyframe Animations */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(18px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-14px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes floatMascot {
    0% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-8px) rotate(2deg); }
    100% { transform: translateY(0px) rotate(0deg); }
}

@keyframes pulseGlow {
    0% {
        box-shadow: 0 0 0 0 rgba(46, 125, 50, 0.4);
    }
    70% {
        box-shadow: 0 0 0 14px rgba(46, 125, 50, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(46, 125, 50, 0);
    }
}

/* Splash Screen Hero */
.splash-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 68vh;
    text-align: center;
    animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1);
    padding: 20px;
}

.splash-mascot {
    font-size: 5rem;
    margin-bottom: 0.5rem;
    display: inline-block;
    animation: floatMascot 4s ease-in-out infinite;
    filter: drop-shadow(0 8px 12px rgba(46, 125, 50, 0.2));
}

.splash-title {
    font-size: 3.2rem;
    font-weight: 800;
    color: var(--primary-dark);
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}

.splash-tamil-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--primary);
    margin-bottom: 0.5rem;
}

.splash-sub {
    font-size: 1.05rem;
    color: var(--text-muted);
    max-width: 580px;
    margin-bottom: 2rem;
    line-height: 1.5;
}

.splash-lang-pill {
    background: var(--surface-glass);
    border: 1.5px solid var(--border-soft);
    padding: 12px 28px;
    border-radius: 999px;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--primary-dark);
    box-shadow: var(--shadow-soft);
    margin-bottom: 2.2rem;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    backdrop-filter: blur(8px);
}

/* Modern Sticky-style Top Bar */
.topbar-wrapper {
    background: var(--surface-glass);
    border: 1px solid var(--border-glass);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 12px 24px;
    margin-bottom: 18px;
    box-shadow: var(--shadow-soft);
    animation: fadeInDown 0.5s ease-out;
}

.topbar-brand {
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--primary-dark);
    display: flex;
    align-items: center;
    gap: 8px;
}

.topbar-sub {
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 500;
}

/* Onboarding Card */
.ob-card {
    background: var(--surface-card);
    border: 1.5px solid var(--border-soft);
    border-radius: 24px;
    padding: 36px 44px;
    max-width: 680px;
    margin: 0 auto;
    box-shadow: var(--shadow-soft);
    text-align: center;
    animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}

.ob-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 5px;
    background: linear-gradient(90deg, var(--primary), #81c784, var(--accent));
}

.ob-step-indicator {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--primary);
    background: var(--primary-light);
    padding: 4px 14px;
    border-radius: 999px;
    margin-bottom: 14px;
}

.ob-question {
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--primary-dark);
    line-height: 1.45;
    margin-bottom: 22px;
}

/* Styled Info Box */
.styled-info-box {
    background: #f1f8e9;
    border-left: 4px solid var(--primary);
    padding: 14px 18px;
    border-radius: 10px;
    font-size: 0.92rem;
    color: var(--primary-dark);
    text-align: left;
    margin: 16px 0;
    line-height: 1.5;
}

/* Progress Bar Container */
.stProgress > div > div > div > div {
    background-color: var(--primary);
    border-radius: 999px;
}

/* Buttons Styling */
div.stButton > button {
    border-radius: 12px;
    font-weight: 600;
    padding: 10px 20px;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    border: 1px solid rgba(46, 125, 50, 0.25);
}

div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(46, 125, 50, 0.18);
    border-color: var(--primary);
}

/* Suggested Question Pills */
.suggested-section-title {
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
}

/* Chat bubble styling */
[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    animation: fadeInUp 0.4s ease-out;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# RAG ENGINE LAZY LOADER
# ============================================================
@st.cache_resource(show_spinner=False)
def get_rag_engine():
    try:
        from app.rag import RAG
        return RAG()
    except Exception as e:
        st.error(f"⚠️ RAG Engine initialization note: {e}")
        return None

# ============================================================
# MULTILINGUAL SCRIPT & CONVERSATION CONTENT
# ============================================================
SCRIPT = {
    "welcome_voice_en": "Welcome to Uzhavar AI. Please select your language — English or Tamil.",
    "welcome_voice_ta": "உழவர் AI-க்கு வரவேற்கிறோம். தயவுசெய்து உங்கள் மொழியை தேர்ந்தெடுங்கள் — ஆங்கிலம் அல்லது தமிழ்.",
    "intro": {
        "English": (
            "Welcome to Uzhavar AI — your personal farming guide for Tamil Nadu. "
            "I will ask you a few quick questions to personalize your experience. "
            "You can speak your answers or type them using the text box. "
            "You can switch between voice and text at any time using the buttons at the top of the screen."
        ),
        "Tamil": (
            "உழவர் AI-க்கு வரவேற்கிறோம். இது தமிழ்நாடு விவசாயிகளுக்கான உங்கள் தனிப்பட்ட வழிகாட்டி. "
            "உங்கள் அனுபவத்தை தனிப்பயனாக்க சில எளிய கேள்விகள் கேட்கிறேன். "
            "நீங்கள் பேசியோ அல்லது தட்டச்சு செய்தோ பதில் சொல்லலாம். "
            "குரல் மற்றும் உரைக்கு இடையே திரையின் மேலே உள்ள பொத்தான்களை பயன்படுத்தி எப்போது வேண்டுமானாலும் மாறலாம்."
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
        "English": "What is your gender? Please select one of the options below.",
        "Tamil": "உங்கள் பாலினம் என்ன? கீழே உள்ள விருப்பங்களில் ஒன்றை தேர்ந்தெடுக்கவும்.",
    },
    "ask_farmer_type": {
        "English": "Are you an existing farmer, or are you planning to start farming now?",
        "Tamil": "நீங்கள் தற்போது ஒரு விவசாயியா, அல்லது புதிதாக விவசாயம் தொடங்குகிறீர்களா?",
    },
    "ask_docs_existing": {
        "English": (
            "To maintain accurate farm records in Tamil Nadu, farmers typically have: "
            "Patta, Chitta or Adangal, Aadhaar card, and a Farmer ID card. "
            "Do you currently have these land and identity documents?"
        ),
        "Tamil": (
            "தமிழ்நாட்டில் விவசாய ஆவணங்களை பராமரிக்க, விவசாயிகளுக்கு பட்டா, சிட்டா அல்லது அடங்கல், "
            "ஆதார் அட்டை மற்றும் உழவர் அடையாள அட்டை தேவை. "
            "இந்த ஆவணங்கள் உங்களிடம் உள்ளனவா?"
        ),
    },
    "ask_docs_new": {
        "English": (
            "To begin farming in Tamil Nadu, key initial documents include: "
            "Aadhaar card, Ration card, and proof of land or lease agreement. "
            "Do you currently have these ready?"
        ),
        "Tamil": (
            "தமிழ்நாட்டில் விவசாயம் தொடங்க, ஆதார் அட்டை, ரேஷன் அட்டை, "
            "மற்றும் நில உரிமை அல்லது குத்தகை ஆவணங்கள் தேவை. "
            "இவை உங்களிடம் தயாராக உள்ளனவா?"
        ),
    },
    "completion": {
        "English": (
            "Thank you {name}! Your profile details have been securely recorded. "
            "Let us begin your farming journey. You can ask me anything about crops, soil health, "
            "machinery, irrigation, or pest management."
        ),
        "Tamil": (
            "நன்றி {name}! உங்கள் விவரங்கள் பாதுகாப்பாக பதிவு செய்யப்பட்டுள்ளன. "
            "இப்போது உங்கள் விவசாய வழிகாட்டலை தொடங்குவோம். பயிர்கள், மண் வளம், "
            "இயந்திரங்கள், பாசனம் அல்லது பூச்சி மேலாண்மை பற்றி என்னிடத்தில் கேளுங்கள்."
        ),
    },
}

LABELS = {
    "English": {
        "begin": "▶ Begin Guidance",
        "next": "Next →",
        "male": "👨 Male",
        "female": "👩 Female",
        "other": "⚧ Other",
        "existing_farmer": "🧑‍🌾 I am an Existing Farmer",
        "new_farmer": "🌱 I am Starting Fresh",
        "has_docs": "✅ Yes, I have them ready",
        "no_docs": "📋 No / Arranging them",
        "use_answer": "✓ Confirm Answer",
        "type_label": "Or type your answer below:",
        "type_placeholder": "Type here...",
        "confirm": "Confirm →",
        "chat_placeholder": "Ask any farming question (e.g., 'How to control fall armyworm in maize?')...",
        "voice_hint": "🎤 Tap mic → speak → confirm",
        "mode_voice": "🎤 Voice Mode",
        "mode_text": "💬 Text Mode",
        "lang_toggle": "🌐 Language",
        "suggested": "💡 Suggested Farming Questions",
        "reset": "🗑️ Reset Conversation",
        "sources_label": "📚 Verified Agricultural Knowledge Sources",
        "spinner": "🔍 Consulting verified agricultural guides & ICAR manuals...",
        "q1": "🌱 How do I start farming?",
        "q2": "🌾 What crop should I grow?",
        "q3": "🚜 What machinery do I need?",
        "q4": "💧 How to install drip irrigation?",
        "q5": "🐛 How to control pests & weeds?",
        "q6": "🧪 How to test soil health?",
        "q1_full": "How do I start farming? What are the key first steps?",
        "q2_full": "What crop should I grow? Help me choose the right crop for my region.",
        "q3_full": "What farm machinery do I need and how do I use it effectively?",
        "q4_full": "How can I install drip irrigation? How much water does it save?",
        "q5_full": "What are the best methods to control pests and weeds in my farm?",
        "q6_full": "How do I conduct soil testing and prepare my land before sowing?",
        "step_label": "Farmer Profile Setup",
        "tap_mic": "Tap mic to speak",
        "listening": "Listening...",
        "got_it": "Captured! Tap Confirm to proceed.",
        "try_again": "Could not catch that. Tap mic to retry.",
        "no_support": "Voice input not supported in this browser. Please type.",
        "age_label": "Your age in years:",
    },
    "Tamil": {
        "begin": "▶ வழிகாட்டலை தொடங்கு",
        "next": "அடுத்து →",
        "male": "👨 ஆண்",
        "female": "👩 பெண்",
        "other": "⚧ பிற",
        "existing_farmer": "🧑‍🌾 நான் தற்போது விவசாயி",
        "new_farmer": "🌱 புதிதாக தொடங்குகிறேன்",
        "has_docs": "✅ ஆம், தயார் நிலையில் உள்ளன",
        "no_docs": "📋 இல்லை / ஏற்பாடு செய்கிறேன்",
        "use_answer": "✓ பதிலை உறுதிப்படுத்து",
        "type_label": "அல்லது கீழே தட்டச்சு செய்யவும்:",
        "type_placeholder": "இங்கே எழுதவும்...",
        "confirm": "உறுதிப்படுத்து →",
        "chat_placeholder": "விவசாய கேள்வியை கேளுங்கள் (எ.கா: 'மக்காச்சோளத்தில் படைப்புழு கட்டுப்பாடு எப்படி?')...",
        "voice_hint": "🎤 மைக் தட்டவும் → பேசவும் → உறுதிப்படுத்தவும்",
        "mode_voice": "🎤 குரல் பயன்முறை",
        "mode_text": "💬 உரை பயன்முறை",
        "lang_toggle": "🌐 மொழி",
        "suggested": "💡 பரிந்துரைக்கப்பட்ட விவசாய கேள்விகள்",
        "reset": "🗑️ உரையாடலை மீட்டமை",
        "sources_label": "📚 சரிபார்க்கப்பட்ட விவசாய குறிப்புகள் & புத்தகங்கள்",
        "spinner": "🔍 விவசாய வழிகாட்டிகள் & ICAR குறிப்புகளை ஆய்வு செய்கிறேன்...",
        "q1": "🌱 விவசாயம் எப்படி தொடங்குவது?",
        "q2": "🌾 என்ன பயிர் விளைவிக்கலாம்?",
        "q3": "🚜 என்ன இயந்திரங்கள் தேவை?",
        "q4": "💧 சொட்டு நீர் பாசனம் அமைப்பது எப்படி?",
        "q5": "🐛 பூச்சி & களை கட்டுப்பாடு எப்படி?",
        "q6": "🧪 மண் பரிசோதனை செய்வது எப்படி?",
        "q1_full": "விவசாயம் எப்படி தொடங்குவது? நிலத்தில் செய்ய வேண்டிய முதல் படிகள் என்ன?",
        "q2_full": "என்ன பயிர் விளைவிக்கலாம்? என் நிலத்திற்கு உகந்த பயிரை பரிந்துரைக்கவும்.",
        "q3_full": "என்ன விவசாய இயந்திரங்கள் தேவை மற்றும் அவற்றை எவ்வாறு பயன்படுத்துவது?",
        "q4_full": "சொட்டு நீர் பாசனம் எப்படி அமைப்பது? எவ்வளவு தண்ணீர் மிச்சமாகும்?",
        "q5_full": "என் பண்ணையில் பூச்சி மற்றும் களைகளை கட்டுப்படுத்த சிறந்த வழிகள் என்ன?",
        "q6_full": "விதைப்பதற்கு முன் மண் பரிசோதனை செய்வது எப்படி? நிலத்தை எப்படி பண்படுத்துவது?",
        "step_label": "உழவர் விவர பதிவு",
        "tap_mic": "பேச மைக்கை தட்டவும்",
        "listening": "கேட்கிறேன்...",
        "got_it": "பதிவானது! தொடர உறுதிப்படுத்தவும்.",
        "try_again": "மீண்டும் முயற்சிக்க மைக்கை தட்டவும்.",
        "no_support": "இந்த உலாவியில் குரல் ஆதரிக்கப்படவில்லை. கீழே தட்டச்சு செய்யவும்.",
        "age_label": "உங்கள் வயது:",
    },
}

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
_INITIAL_STATE = {
    "language": None,
    "onboarding_step": "intro",
    "farmer_info": {},
    "voice_mode": True,
    "messages": [],
    "completion_spoken": False,
    "last_tts_key": None,
}
for key, default in _INITIAL_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================
# TEXT-TO-SPEECH (TTS) VIA WEB SPEECH API
# ============================================================
def trigger_tts(text: str, lang: str, key: str):
    """Speaks text using browser SpeechSynthesis, executed only once per unique key."""
    if st.session_state.last_tts_key == key:
        return
    st.session_state.last_tts_key = key
    lang_code = "ta-IN" if lang == "Tamil" else "en-IN"
    escaped_text = json.dumps(text)

    components.html(f"""
    <script>
    (function() {{
        var synth = window.speechSynthesis;
        synth.cancel();
        function speakNow() {{
            var utt = new SpeechSynthesisUtterance({escaped_text});
            utt.lang = '{lang_code}';
            utt.rate = 0.90;
            utt.pitch = 1.02;
            var voices = synth.getVoices();
            var matched = voices.find(v => v.lang === '{lang_code}')
                       || voices.find(v => v.lang.startsWith('{lang_code[:2]}'));
            if (matched) utt.voice = matched;
            synth.speak(utt);
        }}
        synth.getVoices().length ? speakNow() : synth.addEventListener('voiceschanged', speakNow, {{once: true}});
    }})();
    </script>
    """, height=0, key=f"__tts_{key}")

# ============================================================
# VOICE CAPTURE WIDGET (STT)
# ============================================================
def voice_capture_widget(step_key: str, lang: str) -> str | None:
    params = st.query_params
    if params.get("vstep") == step_key and params.get("vresult"):
        result = params["vresult"]
        st.query_params.clear()
        return result

    L = LABELS[lang]
    lang_code = "ta-IN" if lang == "Tamil" else "en-IN"

    components.html(f"""
    <style>
    .voice-wrapper {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    .mic-btn {{
        width: 72px;
        height: 72px;
        border-radius: 50%;
        border: none;
        cursor: pointer;
        font-size: 2rem;
        color: #ffffff;
        background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%);
        box-shadow: 0 6px 18px rgba(46, 125, 50, 0.35);
        transition: all 0.25s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .mic-btn:hover {{
        transform: scale(1.06);
        box-shadow: 0 8px 24px rgba(46, 125, 50, 0.45);
    }}
    .mic-btn.recording {{
        background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%);
        animation: pulseGlow 1.2s infinite;
    }}
    @keyframes pulseGlow {{
        0% {{ box-shadow: 0 0 0 0 rgba(211, 47, 47, 0.5); }}
        70% {{ box-shadow: 0 0 0 16px rgba(211, 47, 47, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(211, 47, 47, 0); }}
    }}
    .transcript-box {{
        min-height: 40px;
        min-width: 260px;
        max-width: 90%;
        background: #f1f8e9;
        border: 1.5px solid #c8e6c9;
        border-radius: 12px;
        padding: 10px 16px;
        text-align: center;
        color: #1b5e20;
        font-size: 1rem;
        font-weight: 500;
        word-break: break-word;
    }}
    .status-text {{
        font-size: 0.85rem;
        color: #4a5d4e;
        font-weight: 500;
    }}
    .submit-voice-btn {{
        display: none;
        padding: 8px 24px;
        background: #1b5e20;
        color: #ffffff;
        border: none;
        border-radius: 20px;
        cursor: pointer;
        font-size: 0.95rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(27, 94, 32, 0.25);
        transition: transform 0.2s ease;
    }}
    .submit-voice-btn:hover {{
        transform: translateY(-2px);
    }}
    </style>
    <div class="voice-wrapper">
        <button class="mic-btn" id="micBtn" onclick="toggleRecord()">🎤</button>
        <div class="status-text" id="statusText">{L["tap_mic"]}</div>
        <div class="transcript-box" id="transcriptBox"></div>
        <button class="submit-voice-btn" id="submitBtn" onclick="sendTranscript()">{L["use_answer"]}</button>
    </div>
    <script>
    var recognition = null, capturedText = '', isListening = false;
    function toggleRecord() {{
        isListening ? recognition.stop() : startListening();
    }}
    function startListening() {{
        var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {{
            document.getElementById('statusText').innerText = "{L["no_support"]}";
            return;
        }}
        recognition = new SR();
        recognition.lang = '{lang_code}';
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;
        isListening = true;
        capturedText = '';

        var btn = document.getElementById('micBtn');
        btn.classList.add('recording');
        btn.innerText = '⏹';
        document.getElementById('statusText').innerText = '{L["listening"]}';
        document.getElementById('transcriptBox').innerText = '';
        document.getElementById('submitBtn').style.display = 'none';

        recognition.onresult = function(e) {{
            var interim = '';
            for (var i = e.resultIndex; i < e.results.length; i++) {{
                if (e.results[i].isFinal) {{
                    capturedText += e.results[i][0].transcript;
                }} else {{
                    interim += e.results[i][0].transcript;
                }}
            }}
            document.getElementById('transcriptBox').innerText = capturedText || interim;
        }};

        recognition.onend = function() {{
            isListening = false;
            btn.classList.remove('recording');
            btn.innerText = '🎤';
            document.getElementById('statusText').innerText = capturedText ? '{L["got_it"]}' : '{L["try_again"]}';
            if (capturedText) {{
                document.getElementById('submitBtn').style.display = 'inline-block';
            }}
        }};

        recognition.onerror = function(e) {{
            isListening = false;
            btn.classList.remove('recording');
            btn.innerText = '🎤';
            document.getElementById('statusText').innerText = '{L["try_again"]}';
        }};

        recognition.start();
    }}

    function sendTranscript() {{
        if (!capturedText) return;
        var loc = new URL(window.parent.location.href);
        loc.searchParams.set('vstep', '{step_key}');
        loc.searchParams.set('vresult', capturedText);
        window.parent.location.href = loc.toString();
    }}
    </script>
    """, height=180, key=f"__stt_{step_key}_{int(time.time()*100)%1000}")
    return None

# ============================================================
# PERSISTENT TOP NAVIGATION BAR
# ============================================================
def render_topbar():
    lang = st.session_state.language
    L = LABELS[lang]

    st.markdown('<div class="topbar-wrapper">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([4, 3, 3])

    with c1:
        st.markdown(
            '<div class="topbar-brand">🌾 Uzhavar AI &nbsp;<span style="color:#2e7d32; font-weight:600;">உழவர் AI</span></div>'
            '<div class="topbar-sub">Digital Farming Guide & Agronomic Assistant · Tamil Nadu</div>',
            unsafe_allow_html=True
        )

    with c2:
        st.caption(f"**{L['lang_toggle']}**")
        la, lb = st.columns(2)
        with la:
            st.button(
                "🇬🇧 English",
                key="top_btn_en",
                use_container_width=True,
                type="primary" if lang == "English" else "secondary",
                on_click=set_app_language, args=("English",)
            )
        with lb:
            st.button(
                "🇮🇳 தமிழ்",
                key="top_btn_ta",
                use_container_width=True,
                type="primary" if lang == "Tamil" else "secondary",
                on_click=set_app_language, args=("Tamil",)
            )

    with c3:
        st.caption(f"**{L['mode_voice']} / {L['mode_text']}**")
        va, vb = st.columns(2)
        with va:
            st.button(
                L["mode_voice"],
                key="top_btn_voice",
                use_container_width=True,
                type="primary" if st.session_state.voice_mode else "secondary",
                on_click=set_voice_mode, args=(True,)
            )
        with vb:
            st.button(
                L["mode_text"],
                key="top_btn_text",
                use_container_width=True,
                type="primary" if not st.session_state.voice_mode else "secondary",
                on_click=set_voice_mode, args=(False,)
            )

    st.markdown('</div>', unsafe_allow_html=True)

def set_app_language(lang_val: str):
    st.session_state.language = lang_val
    st.session_state.last_tts_key = None

def set_voice_mode(is_voice: bool):
    st.session_state.voice_mode = is_voice

# ============================================================
# ONBOARDING FLOW & PERSISTENT STORAGE
# ============================================================
STEP_ORDER = ["intro", "name", "age", "gender", "farmer_type", "docs"]
STEP_COUNT = len(STEP_ORDER)

def render_step_progress(step: str):
    idx = STEP_ORDER.index(step) if step in STEP_ORDER else STEP_COUNT
    L = LABELS[st.session_state.language]
    st.progress(idx / STEP_COUNT, text=f"{L['step_label']} — Step {idx} of {STEP_COUNT}")

def render_dual_input(step_key: str, lang: str) -> str | None:
    L = LABELS[lang]
    result = None

    if st.session_state.voice_mode:
        v_col, t_col = st.columns([1, 1], gap="large")
        with v_col:
            result = voice_capture_widget(step_key, lang)
        with t_col:
            st.markdown(f"<div style='font-size:0.88rem; font-weight:600; color:#2e7d32; margin-bottom:6px;'>{L['type_label']}</div>", unsafe_allow_html=True)
            with st.form(f"form_{step_key}"):
                val = st.text_input("", placeholder=L["type_placeholder"], label_visibility="collapsed", key=f"inp_{step_key}")
                if st.form_submit_button(L["confirm"], use_container_width=True) and val.strip():
                    result = val.strip()
    else:
        with st.form(f"form_text_{step_key}"):
            val = st.text_input(L["type_label"], placeholder=L["type_placeholder"], key=f"inp_t_{step_key}")
            if st.form_submit_button(L["next"], use_container_width=True) and val.strip():
                result = val.strip()

    return result

def complete_onboarding():
    """Saves farmer profile persistently to SQLite & JSON, then transitions to main chat."""
    info = st.session_state.farmer_info
    info["language"] = st.session_state.language
    save_farmer_profile(info)

    st.session_state.onboarding_step = "done"
    st.session_state.last_tts_key = None
    st.session_state.completion_spoken = False
    st.session_state.messages = []
    st.rerun()

# ============================================================
# VIEW 1: LANGUAGE SELECTION SPLASH
# ============================================================
def view_language_splash():
    components.html("""
    <script>
    (function() {
        var s = window.speechSynthesis;
        s.cancel();
        function playPrompt() {
            var en = new SpeechSynthesisUtterance("Welcome to Uzhavar AI. Please select your language — English or Tamil.");
            en.lang = 'en-IN'; en.rate = 0.88;
            var ta = new SpeechSynthesisUtterance("உழவர் AI-க்கு வரவேற்கிறோம். தயவுசெய்து உங்கள் மொழியை தேர்ந்தெடுங்கள் — ஆங்கிலம் அல்லது தமிழ்.");
            ta.lang = 'ta-IN'; ta.rate = 0.88;
            en.onend = function() { s.speak(ta); };
            s.speak(en);
        }
        s.getVoices().length ? playPrompt() : s.addEventListener('voiceschanged', playPrompt, {once:true});
    })();
    </script>
    """, height=0, key="splash_audio_init")

    st.markdown("""
    <div class="splash-container">
        <div class="splash-mascot">🌾</div>
        <div class="splash-title">Uzhavar AI</div>
        <div class="splash-tamil-title">உழவர் AI — தமிழ்நாட்டின் டிஜிட்டல் உழவன் வழிகாட்டி</div>
        <div class="splash-sub">
            Your conversational digital companion for crops, land preparation, machinery, and smart agricultural practices.
        </div>
        <div class="splash-lang-pill">
            🔊 Please Choose Your Language &nbsp;•&nbsp; மொழியை தேர்வு செய்யவும்
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, btn_en_col, _, btn_ta_col, _ = st.columns([2, 3, 1, 3, 2])
    with btn_en_col:
        if st.button("🇬🇧 &nbsp; English", use_container_width=True, key="splash_btn_en", type="primary"):
            st.session_state.language = "English"
            st.session_state.onboarding_step = "intro"
            st.session_state.last_tts_key = None
            st.rerun()

    with btn_ta_col:
        if st.button("🇮🇳 &nbsp; தமிழ் (Tamil)", use_container_width=True, key="splash_btn_ta", type="primary"):
            st.session_state.language = "Tamil"
            st.session_state.onboarding_step = "intro"
            st.session_state.last_tts_key = None
            st.rerun()

# ============================================================
# VIEW 2: VOICE ONBOARDING
# ============================================================
def view_onboarding():
    lang = st.session_state.language
    L = LABELS[lang]
    step = st.session_state.onboarding_step
    info = st.session_state.farmer_info

    render_topbar()
    render_step_progress(step)
    st.markdown("")

    # 1. INTRO
    if step == "intro":
        trigger_tts(SCRIPT["intro"][lang], lang, "intro")
        _, center, _ = st.columns([1, 4, 1])
        with center:
            st.markdown(f"""
            <div class="ob-card">
                <div style="font-size: 3.5rem; margin-bottom: 10px;">🌾</div>
                <div class="ob-question">
                    {"Welcome to Uzhavar AI — your personal farming guide for Tamil Nadu." if lang == "English"
                     else "உழவர் AI-க்கு வரவேற்கிறோம் — தமிழ்நாட்டு விவசாயிகளுக்கான உங்கள் தனிப்பட்ட வழிகாட்டி."}
                </div>
                <p style="color: #4a5d4e; font-size: 1rem; line-height: 1.6;">
                    {"I will ask a few quick questions to personalize your farming advice. You can speak your answers or type them. You can switch between voice and text anytime using the top bar." if lang == "English"
                     else "உங்கள் விவசாய சூழலுக்கு ஏற்ப வழிகாட்ட சில எளிய கேள்விகள் கேட்கிறேன். நீங்கள் பேசியோ தட்டச்சு செய்தோ பதிலளிக்கலாம். மேல்பட்டியில் இருந்து எப்போது வேண்டுமானாலும் முறையை மாற்றலாம்."}
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            _, btn_c, _ = st.columns([2, 3, 2])
            with btn_c:
                if st.button(L["begin"], use_container_width=True, key="ob_start_btn", type="primary"):
                    st.session_state.onboarding_step = "name"
                    st.session_state.last_tts_key = None
                    st.rerun()

    # 2. NAME
    elif step == "name":
        question = SCRIPT["ask_name"][lang]
        trigger_tts(question, lang, "ob_name")
        _, center, _ = st.columns([1, 4, 1])
        with center:
            st.markdown(f"""
            <div class="ob-card">
                <div class="ob-step-indicator">Step 1 of 5</div>
                <div class="ob-question">👤 &nbsp; {question}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            captured = render_dual_input("ob_name", lang)
            if captured:
                info["name"] = captured.strip().title()
                st.session_state.onboarding_step = "age"
                st.session_state.last_tts_key = None
                st.rerun()

    # 3. AGE
    elif step == "age":
        question = SCRIPT["ask_age"][lang]
        trigger_tts(question, lang, "ob_age")
        _, center, _ = st.columns([1, 4, 1])
        with center:
            st.markdown(f"""
            <div class="ob-card">
                <div class="ob-step-indicator">Step 2 of 5</div>
                <div class="ob-question">🎂 &nbsp; {question}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")

            if st.session_state.voice_mode:
                v_col, t_col = st.columns([1, 1], gap="large")
                with v_col:
                    age_spoken = voice_capture_widget("ob_age", lang)
                    if age_spoken:
                        extracted = "".join(filter(str.isdigit, age_spoken))
                        if extracted:
                            info["age"] = extracted
                            st.session_state.onboarding_step = "gender"
                            st.session_state.last_tts_key = None
                            st.rerun()
                with t_col:
                    with st.form("form_age"):
                        age_num = st.number_input(L["age_label"], min_value=15, max_value=100, value=35, step=1)
                        if st.form_submit_button(L["confirm"], use_container_width=True):
                            info["age"] = str(age_num)
                            st.session_state.onboarding_step = "gender"
                            st.session_state.last_tts_key = None
                            st.rerun()
            else:
                with st.form("form_age_text"):
                    age_num = st.number_input(L["age_label"], min_value=15, max_value=100, value=35, step=1)
                    if st.form_submit_button(L["next"], use_container_width=True):
                        info["age"] = str(age_num)
                        st.session_state.onboarding_step = "gender"
                        st.session_state.last_tts_key = None
                        st.rerun()

    # 4. GENDER
    elif step == "gender":
        question = SCRIPT["ask_gender"][lang]
        trigger_tts(question, lang, "ob_gender")
        _, center, _ = st.columns([1, 4, 1])
        with center:
            st.markdown(f"""
            <div class="ob-card">
                <div class="ob-step-indicator">Step 3 of 5</div>
                <div class="ob-question">🧑 &nbsp; {question}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            g1, g2, g3 = st.columns(3)
            with g1:
                if st.button(L["male"], use_container_width=True, key="gen_male"):
                    info["gender"] = "Male"
                    st.session_state.onboarding_step = "farmer_type"
                    st.session_state.last_tts_key = None
                    st.rerun()
            with g2:
                if st.button(L["female"], use_container_width=True, key="gen_female"):
                    info["gender"] = "Female"
                    st.session_state.onboarding_step = "farmer_type"
                    st.session_state.last_tts_key = None
                    st.rerun()
            with g3:
                if st.button(L["other"], use_container_width=True, key="gen_other"):
                    info["gender"] = "Other"
                    st.session_state.onboarding_step = "farmer_type"
                    st.session_state.last_tts_key = None
                    st.rerun()

    # 5. FARMER TYPE
    elif step == "farmer_type":
        question = SCRIPT["ask_farmer_type"][lang]
        trigger_tts(question, lang, "ob_ftype")
        _, center, _ = st.columns([1, 4, 1])
        with center:
            st.markdown(f"""
            <div class="ob-card">
                <div class="ob-step-indicator">Step 4 of 5</div>
                <div class="ob-question">🌱 &nbsp; {question}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                if st.button(L["existing_farmer"], use_container_width=True, key="ft_existing", type="primary"):
                    info["farmer_type"] = "existing"
                    st.session_state.onboarding_step = "docs"
                    st.session_state.last_tts_key = None
                    st.rerun()
            with f_col2:
                if st.button(L["new_farmer"], use_container_width=True, key="ft_new", type="secondary"):
                    info["farmer_type"] = "new"
                    st.session_state.onboarding_step = "docs"
                    st.session_state.last_tts_key = None
                    st.rerun()

    # 6. DOCUMENTS
    elif step == "docs":
        is_existing = (info.get("farmer_type") == "existing")
        q_key = "ask_docs_existing" if is_existing else "ask_docs_new"
        question = SCRIPT[q_key][lang]
        trigger_tts(question, lang, f"ob_docs_{info.get('farmer_type')}")

        _, center, _ = st.columns([1, 4, 1])
        with center:
            st.markdown(f"""
            <div class="ob-card">
                <div class="ob-step-indicator">Step 5 of 5</div>
                <div class="ob-question">📄 &nbsp; {question}</div>
            </div>
            """, unsafe_allow_html=True)

            if lang == "English":
                doc_summary = (
                    "**Key Agricultural Documents for TN Farmers:**<br>"
                    "• Patta / Chitta / Adangal (Land Ownership & Cultivation Record)<br>"
                    "• Aadhaar Card & Farmer ID / PPB Book<br>"
                    "• Active Bank Passbook linked with Aadhaar"
                    if is_existing else
                    "**Initial Documents for New Farmers:**<br>"
                    "• Aadhaar Card & Ration Card<br>"
                    "• Land Title (Patta) or Registered Lease Deed<br>"
                    "• Bank Account Details"
                )
            else:
                doc_summary = (
                    "**தமிழ்நாடு விவசாயிகளுக்கான முக்கிய ஆவணங்கள்:**<br>"
                    "• பட்டா / சிட்டா / அடங்கல் (நில உரிமை மற்றும் சாகுபடி சான்று)<br>"
                    "• ஆதார் அட்டை மற்றும் உழவர் அடையாள அட்டை<br>"
                    "• ஆதாருடன் இணைக்கப்பட்ட வங்கி கணக்கு புத்தகம்"
                    if is_existing else
                    "**புதிய விவசாயிகளுக்கான தொடக்க ஆவணங்கள்:**<br>"
                    "• ஆதார் அட்டை மற்றும் குடும்ப அட்டை<br>"
                    "• நில உரிமை ஆவணம் (பட்டா) அல்லது குத்தகை ஒப்பந்தம்<br>"
                    "• வங்கி கணக்கு விவரங்கள்"
                )

            st.markdown(f'<div class="styled-info-box">{doc_summary}</div>', unsafe_allow_html=True)

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                if st.button(L["has_docs"], use_container_width=True, key="doc_yes", type="primary"):
                    info["has_docs"] = True
                    complete_onboarding()
            with d_col2:
                if st.button(L["no_docs"], use_container_width=True, key="doc_no", type="secondary"):
                    info["has_docs"] = False
                    complete_onboarding()

# ============================================================
# VIEW 3: MAIN AGRICULTURAL CHAT INTERFACE
# ============================================================
def view_main_chat():
    lang = st.session_state.language
    L = LABELS[lang]
    info = st.session_state.farmer_info
    farmer_name = info.get("name", "Farmer")

    # Initial completion speech
    if not st.session_state.completion_spoken:
        spoken_text = SCRIPT["completion"][lang].format(name=farmer_name)
        trigger_tts(spoken_text, lang, "completion_chat")
        st.session_state.completion_spoken = True

    # Initial Assistant Greeting
    if not st.session_state.messages:
        is_existing = (info.get("farmer_type") == "existing")
        has_docs = info.get("has_docs", True)

        if lang == "English":
            greeting = f"Vanakkam **{farmer_name}**! 🙏 I am **Uzhavar AI**, your digital agronomic companion.\n\n"
            if is_existing:
                greeting += "As an active farmer, I am here to help you with crop health, drip irrigation, machinery selection, fertilizer calculation, and pest control techniques."
            else:
                greeting += "Since you are starting your farming journey, I will guide you step-by-step through land preparation, soil testing, seed selection, and first-season crop management."
            if not has_docs:
                greeting += "\n\n💡 *Tip: Having your Patta and Chitta updated will help smooth your agricultural operations in Tamil Nadu.*"
            greeting += "\n\n**How can I assist you in your field today?**"
        else:
            greeting = f"வணக்கம் **{farmer_name}**! 🙏 நான் **உழவர் AI**, உங்கள் தனிப்பட்ட விவசாய வழிகாட்டி.\n\n"
            if is_existing:
                greeting += "அனுபவமிக்க விவசாயியாக, பயிர் பாதுகாப்பு, சொட்டு நீர் பாசனம், பண்ணை இயந்திரங்கள் மற்றும் பூச்சி மேலாண்மையில் உங்களுக்கு உதவுகிறேன்."
            else:
                greeting += "நீங்கள் விவசாயத்தை புதிதாக தொடங்குவதால், நிலம் பண்படுத்துதல், மண் பரிசோதனை, விதை தேர்வு மற்றும் சாகுபடி முறைகளை படிப்படியாக வழிகாட்டுகிறேன்."
            if not has_docs:
                greeting += "\n\n💡 *குறிப்பு: உங்கள் பட்டா மற்றும் சிட்டா ஆவணங்களை புதுப்பித்து வைத்திருப்பது நல்லது.*"
            greeting += "\n\n**இன்று உங்கள் பண்ணைக்கு என்ன உதவி தேவை?**"

        st.session_state.messages = [{
            "role": "assistant",
            "content": greeting,
            "sources": []
        }]

    # Top Navigation Bar
    render_topbar()

    # Suggested Farming Questions Section
    st.markdown(f'<div class="suggested-section-title">{L["suggested"]}</div>', unsafe_allow_html=True)
    q_row1 = st.columns(3)
    q_row2 = st.columns(3)
    chosen_prompt = None

    q_items = [
        ("q1", "q1_full"), ("q2", "q2_full"), ("q3", "q3_full"),
        ("q4", "q4_full"), ("q5", "q5_full"), ("q6", "q6_full")
    ]
    for idx, (short_k, full_k) in enumerate(q_items):
        target_col = (q_row1 if idx < 3 else q_row2)[idx % 3]
        with target_col:
            if st.button(L[short_k], use_container_width=True, key=f"sq_{idx}"):
                chosen_prompt = L[full_k]

    st.markdown("<hr style='margin: 18px 0; border: none; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)

    # Chat History Display
    for msg in st.session_state.messages:
        role = msg["role"]
        avatar = "👨‍🌾" if role == "user" else "🌾"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander(f"{L['sources_label']} ({len(msg['sources'])})"):
                    for src in msg["sources"]:
                        st.markdown(f"• **{src['source']}** (Page {src['page']}) — *Relevance: {src['score']}*")

    # Voice Input Panel (Active only in Voice Mode)
    voice_query = None
    if st.session_state.voice_mode:
        url_params = st.query_params
        if url_params.get("vstep") == "chat" and url_params.get("vresult"):
            voice_query = url_params["vresult"]
            st.query_params.clear()
        else:
            with st.expander("🎤 " + ("Speak your agricultural question" if lang == "English" else "உங்கள் கேள்வியை பேசவும்"), expanded=True):
                voice_query = voice_capture_widget("chat", lang)

    # Text Input Bar (Always Available)
    typed_query = st.chat_input(L["chat_placeholder"])

    # Resolve Query Priority
    active_query = voice_query or typed_query or chosen_prompt

    if active_query:
        # Append user query to conversation
        st.session_state.messages.append({"role": "user", "content": active_query})
        with st.chat_message("user", avatar="👨‍🌾"):
            st.markdown(active_query)

        # Context profile dictionary
        profile_dict = {
            "name": info.get("name"),
            "age": info.get("age"),
            "gender": info.get("gender"),
            "farmer_type": info.get("farmer_type"),
            "has_docs": info.get("has_docs"),
            "language": lang,
            "farming_stage": "Planning",
        }

        chat_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]

        # Generate Grounded Guidance
        with st.chat_message("assistant", avatar="🌾"):
            with st.spinner(L["spinner"]):
                rag = get_rag_engine()
                if rag:
                    answer_text, contexts, _, _ = rag.answer(
                        question=active_query,
                        profile=profile_dict,
                        history=chat_history,
                        return_details=True
                    )
                else:
                    answer_text = (
                        "Uzhavar AI engine is initializing. Please verify document index configuration."
                        if lang == "English" else
                        "உழவர் AI தயாராகிறது. ஆவண குறியீட்டு அமைப்பை சரிபார்க்கவும்."
                    )
                    contexts = []

                st.markdown(answer_text)

                # Voice output if Voice Mode is active
                if st.session_state.voice_mode:
                    trigger_tts(answer_text[:350], lang, f"ans_{int(time.time())}")

                # Citations
                if contexts:
                    with st.expander(f"{L['sources_label']} ({len(contexts)})"):
                        for c in contexts:
                            st.markdown(
                                f"• **{c['source']}** (Page {c['page']}) — "
                                f"*{round(c.get('rerank_score', c.get('score', 0.0)), 4)}*"
                            )

                sources_stored = [
                    {
                        "source": c["source"],
                        "page": c["page"],
                        "score": round(c.get("rerank_score", c.get("score", 0.0)), 4)
                    }
                    for c in contexts
                ]

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer_text,
                    "sources": sources_stored
                })

    # Minimal Sidebar with Reset and System Status
    with st.sidebar:
        st.markdown("### 🌾 Uzhavar AI")
        if st.button(L["reset"], use_container_width=True):
            st.session_state.messages = []
            st.session_state.completion_spoken = False
            st.rerun()

        st.divider()
        with st.expander("📚 Knowledge Base"):
            st.caption(
                "• Crop production.pdf\n"
                "• drip_irrigation.pdf\n"
                "• Farm Machinery.pdf\n"
                "• ICAR Kharif Agro-Advisories 2025\n"
                "• Principles and Practices of Weed Management"
            )
            st.write("**Vector Store:** 1,353 chunks · Qdrant")
            st.write("**Model:** Gemini 2.5 Flash")

# ============================================================
# APPLICATION ROUTING
# ============================================================
if st.session_state.language is None:
    view_language_splash()
elif st.session_state.onboarding_step != "done":
    view_onboarding()
else:
    view_main_chat()
