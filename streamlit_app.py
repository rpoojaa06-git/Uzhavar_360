"""
Uzhavar AI — Voice-First Intelligent Agricultural Guide
================================================================================
Highlighted, High-Contrast UI & Accessible Farmer Experience:
  1. Language Selection with Automatic Bilingual Voice Audio
  2. Guided Onboarding with Large High-Contrast Step Cards
  3. Persistent Farmer Profile Storage in SQLite & JSON (silent, zero clutter)
  4. High-Contrast Message Containers (User & Assistant cards never merge with background)
  5. Dedicated Live Voice Hub with Audio Visualizer & Clear Transcript Pill
  6. Listen Aloud (TTS) capability for all agricultural responses
  7. Categorized Quick Action Agricultural Questions
  8. Persistent Top Navigation with Instant Voice/Text & Language Toggles
"""

import streamlit as st
import streamlit.components.v1 as components

try:
    from streamlit_mic_recorder import speech_to_text
    MIC_STT_AVAILABLE = True
except Exception:  # optional dependency — app degrades to typed input
    speech_to_text = None
    MIC_STT_AVAILABLE = False

import re
import json
import time
import html
from app.profile_store import save_farmer_profile

try:
    from app.sarvam_tts import render_sarvam_audio
    SARVAM_TTS = True
except Exception:
    render_sarvam_audio = None
    SARVAM_TTS = False

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
# HIGH-CONTRAST DESIGN SYSTEM & MICRO-ANIMATIONS (CSS)
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+Tamil:wght@400;500;600;700;800&display=swap');

:root {
    --bg-page: #f1f5f1;
    --primary-dark: #134e23;
    --primary-main: #1b7332;
    --primary-light: #e8f5e9;
    --user-card-bg: #eaf8ed;
    --user-card-border: #72cf87;
    --ai-card-bg: #ffffff;
    --ai-card-border: #1b7332;
    --accent-gold: #f59e0b;
    --accent-gold-bg: #fffbeb;
    --text-dark: #0f172a;
    --text-muted: #334155;
    --shadow-card: 0 10px 25px -5px rgba(19, 78, 35, 0.10), 0 8px 10px -6px rgba(19, 78, 35, 0.05);
    --shadow-float: 0 16px 36px -6px rgba(19, 78, 35, 0.16);
}

/* App Canvas */
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', 'Noto Sans Tamil', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-dark);
    background-color: var(--bg-page) !important;
}

/* Hide 1px audio TTS iframes completely */
iframe[height="1"], [data-testid="stIFrame"]:has(iframe[height="1"]) {
    display: none !important;
    position: absolute !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
}

/* Animations */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(16px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulseMic {
    0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.55); }
    70% { box-shadow: 0 0 0 18px rgba(220, 38, 38, 0); }
    100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
}

@keyframes gentleFloat {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-7px); }
    100% { transform: translateY(0px); }
}

/* Top Navigation Bar */
.topbar-container {
    background: #ffffff;
    border: 2px solid #c8e6c9;
    border-radius: 18px;
    padding: 14px 24px;
    margin-bottom: 20px;
    box-shadow: var(--shadow-card);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.topbar-brand {
    font-size: 1.55rem;
    font-weight: 800;
    color: var(--primary-dark);
    display: flex;
    align-items: center;
    gap: 8px;
    letter-spacing: -0.01em;
}

.topbar-sub {
    font-size: 0.82rem;
    color: #2e7d32;
    font-weight: 600;
}

/* ========================================================
   HIGH-CONTRAST CHAT CONTAINERS (NEVER MERGE WITH BG)
   ======================================================== */

/* User Message Highlight Box */
.user-msg-bubble {
    background: var(--user-card-bg);
    border: 2.5px solid var(--user-card-border);
    border-left: 8px solid var(--primary-main);
    border-radius: 18px;
    padding: 18px 22px;
    margin: 16px 0 20px 0;
    box-shadow: 0 6px 18px rgba(27, 115, 50, 0.12);
    animation: fadeInUp 0.35s ease-out;
}

.user-msg-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    border-bottom: 1.5px solid rgba(46, 125, 50, 0.2);
    padding-bottom: 6px;
}

.user-badge {
    background: #1b7332;
    color: #ffffff;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    letter-spacing: 0.3px;
}

.user-text-content {
    font-size: 1.15rem;
    font-weight: 600;
    color: #0d3818;
    line-height: 1.55;
    word-break: break-word;
}

/* Assistant (AI) Message Highlight Box */
.ai-msg-bubble {
    background: var(--ai-card-bg);
    border: 2.5px solid var(--ai-card-border);
    border-left: 8px solid #0f441c;
    border-radius: 20px;
    padding: 24px 26px;
    margin: 16px 0 26px 0;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.10);
    animation: fadeInUp 0.4s ease-out;
}

.ai-msg-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
    border-bottom: 1.5px solid #e2e8f0;
    padding-bottom: 10px;
}

.ai-badge {
    background: #0f441c;
    color: #ffffff;
    font-size: 0.84rem;
    font-weight: 700;
    padding: 5px 14px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.verified-pill {
    background: #dcfce7;
    color: #14532d;
    border: 1px solid #86efac;
    font-size: 0.76rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.ai-text-content {
    font-size: 1.05rem;
    font-weight: 450;
    color: #1e293b;
    line-height: 1.7;
    word-break: break-word;
}

.ai-text-content h1, .ai-text-content h2, .ai-text-content h3 {
    color: #134e23;
    font-weight: 700;
    margin-top: 14px;
    margin-bottom: 6px;
}

.ai-text-content ul, .ai-text-content ol {
    padding-left: 20px;
    margin: 10px 0;
}

.ai-text-content li {
    margin-bottom: 6px;
}

/* Dedicated Live Voice Console */
.voice-console-card {
    background: #ffffff;
    border: 2.5px solid #2e7d32;
    border-radius: 20px;
    padding: 20px 24px;
    margin: 18px 0;
    box-shadow: var(--shadow-card);
    text-align: center;
}

.voice-console-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #134e23;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-bottom: 6px;
}

.voice-console-sub {
    font-size: 0.85rem;
    color: #475569;
    margin-bottom: 14px;
}

/* Onboarding Highlight Card */
.ob-hero-card {
    background: #ffffff;
    border: 2.5px solid #a7f3d0;
    border-radius: 26px;
    padding: 38px 46px;
    max-width: 720px;
    margin: 20px auto;
    box-shadow: var(--shadow-float);
    text-align: center;
    position: relative;
    overflow: hidden;
}

.ob-hero-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 6px;
    background: linear-gradient(90deg, #1b7332, #10b981, #f59e0b);
}

.ob-step-chip {
    background: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 5px 16px;
    border-radius: 999px;
    display: inline-block;
    margin-bottom: 16px;
}

.ob-question-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: #0f391b;
    line-height: 1.4;
    margin-bottom: 22px;
}

.ob-doc-alert {
    background: #f0fdf4;
    border: 2px solid #86efac;
    border-radius: 14px;
    padding: 16px 20px;
    text-align: left;
    margin: 18px 0;
    color: #14532d;
    font-size: 0.95rem;
    line-height: 1.55;
}

/* Suggested Question Chips */
.topic-grid-title {
    font-size: 0.92rem;
    font-weight: 800;
    color: #134e23;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin: 14px 0 8px 0;
    display: flex;
    align-items: center;
    gap: 6px;
}

div.stButton > button {
    border-radius: 14px !important;
    font-weight: 700 !important;
    padding: 12px 20px !important;
    font-size: 0.98rem !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1.5px solid #a7f3d0 !important;
    background-color: #ffffff !important;
    color: #134e23 !important;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.04) !important;
}

div.stButton > button:hover {
    transform: translateY(-2px) !important;
    border-color: #1b7332 !important;
    box-shadow: 0 8px 20px rgba(27, 115, 50, 0.20) !important;
    background-color: #f0fdf4 !important;
    color: #0f391b !important;
}

div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1b7332 0%, #134e23 100%) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(19, 78, 35, 0.28) !important;
}

div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #228c3d 0%, #175d2b 100%) !important;
    color: #ffffff !important;
}

/* Chat Input Bar Highlight */
[data-testid="stChatInput"] {
    border-radius: 18px !important;
    border: 2px solid #1b7332 !important;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08) !important;
    background: #ffffff !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #0f441c !important;
    box-shadow: 0 0 0 4px rgba(27, 115, 50, 0.2) !important;
}

/* Source Expander */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03) !important;
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
    "welcome_voice_en": "Welcome to Uzhavar AI. Please choose your language — English or Tamil.",
    "welcome_voice_ta": "உழவர் AI-க்கு வரவேற்கிறோம். தயவுசெய்து உங்கள் மொழியை தேர்ந்தெடுங்கள் — ஆங்கிலம் அல்லது தமிழ்.",
    "intro": {
        "English": (
            "Welcome to Uzhavar AI — your personal farming guide for Tamil Nadu. "
            "I will ask you a few quick questions to personalize your experience. "
            "You can speak your answers or type them. "
            "You can switch between voice and text anytime using the top bar."
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
        "begin": "▶ Begin Consultation",
        "next": "Next Step →",
        "male": "👨 Male",
        "female": "👩 Female",
        "other": "⚧ Other",
        "existing_farmer": "🧑‍🌾 I am an Existing Farmer",
        "new_farmer": "🌱 I am Starting Fresh",
        "has_docs": "✅ Yes, I have them ready",
        "no_docs": "📋 No / Arranging them",
        "use_answer": "✓ Send Spoken Question",
        "type_label": "Or type your answer below:",
        "type_placeholder": "Type here...",
        "confirm": "Confirm Answer →",
        "chat_placeholder": "Ask any farming question (e.g., 'What machinery is required for 2 acres paddy?')...",
        "voice_hint": "🎤 Tap mic → speak in English or Tamil → Send",
        "mode_voice": "🎤 Voice Mode",
        "mode_text": "💬 Text Mode",
        "lang_toggle": "Language",
        "suggested": "💡 Recommended Farming Questions",
        "reset": "🔄 New Conversation",
        "sources_label": "📚 Verified Agricultural Sources (ICAR & TNAU)",
        "spinner": "🔍 Consulting verified agricultural guides & ICAR manuals...",
        "listen_btn": "🔊 Read Aloud",
        "q1": "🌱 How do I start farming?",
        "q2": "🌾 What crop should I grow?",
        "q3": "🚜 What machinery do I need?",
        "q4": "💧 How to install drip irrigation?",
        "q5": "🐛 How to control pests & weeds?",
        "q6": "🧪 How to test soil health?",
        "q1_full": "How do I start farming? What are the key first steps for land and crop?",
        "q2_full": "What crop should I grow? Help me choose the right crop based on season and soil.",
        "q3_full": "What farm machinery do I need and how do I use it effectively?",
        "q4_full": "How can I install drip irrigation? How much water does it save?",
        "q5_full": "What are the best methods to control pests and weeds in my farm?",
        "q6_full": "How do I conduct soil testing and prepare my land before sowing?",
        "step_label": "Farmer Profile Setup",
        "tap_mic": "Tap mic to speak",
        "listening": "Listening... Speak clearly in Tamil or English",
        "got_it": "Speech captured! Click Send below.",
        "try_again": "Could not hear clearly. Tap mic to retry.",
        "no_support": "Voice input not supported in this browser. Please type.",
        "age_label": "Your age in years:",
        "your_question": "Your Question:",
        "ai_guidance": "Uzhavar AI Guidance",
        "demo_links_card": "Uzhavar Demo App",
        "demo_links_hint": "Open this page of the demo app for the sample data",
        "demo_links_footer": "🌐 Browse the full demo app",
    },
    "Tamil": {
        "begin": "▶ வழிகாட்டலை தொடங்கு",
        "next": "அடுத்த படி →",
        "male": "👨 ஆண்",
        "female": "👩 பெண்",
        "other": "⚧ பிற",
        "existing_farmer": "🧑‍🌾 நான் தற்போது விவசாயி",
        "new_farmer": "🌱 புதிதாக தொடங்குகிறேன்",
        "has_docs": "✅ ஆம், தயார் நிலையில் உள்ளன",
        "no_docs": "📋 இல்லை / ஏற்பாடு செய்கிறேன்",
        "use_answer": "✓ பேசிய கேள்வியை அனுப்பு",
        "type_label": "அல்லது கீழே தட்டச்சு செய்யவும்:",
        "type_placeholder": "இங்கே எழுதவும்...",
        "confirm": "பதிலை உறுதிப்படுத்து →",
        "chat_placeholder": "விவசாய கேள்வியை கேளுங்கள் (எ.கா: '2 ஏக்கர் நெல்லுக்கு என்ன இயந்திரங்கள் தேவை?')...",
        "voice_hint": "🎤 மைக் தட்டவும் → தமிழில் பேசவும் → அனுப்பு",
        "mode_voice": "🎤 குரல் பயன்முறை",
        "mode_text": "💬 உரை பயன்முறை",
        "lang_toggle": "மொழி",
        "suggested": "💡 பரிந்துரைக்கப்பட்ட விவசாய கேள்விகள்",
        "reset": "🔄 புதிய உரையாடல்",
        "sources_label": "📚 சரிபார்க்கப்பட்ட விவசாய குறிப்புகள் & நூல்கள்",
        "spinner": "🔍 விவசாய வழிகாட்டிகள் & ICAR குறிப்புகளை ஆய்வு செய்கிறேன்...",
        "listen_btn": "🔊 வாசித்து கேள்",
        "q1": "🌱 விவசாயம் எப்படி தொடங்குவது?",
        "q2": "🌾 என்ன பயிர் விளைவிக்கலாம்?",
        "q3": "🚜 என்ன இயந்திரங்கள் தேவை?",
        "q4": "💧 சொட்டு நீர் பாசனம் அமைப்பது எப்படி?",
        "q5": "🐛 பூச்சி & களை கட்டுப்பாடு எப்படி?",
        "q6": "🧪 மண் பரிசோதனை செய்வது எப்படி?",
        "q1_full": "விவசாயம் எப்படி தொடங்குவது? நிலத்தில் செய்ய வேண்டிய முதல் முக்கிய படிகள் என்ன?",
        "q2_full": "என்ன பயிர் விளைவிக்கலாம்? பருவம் மற்றும் மண்ணுக்கு ஏற்ற பயிரை பரிந்துரைக்கவும்.",
        "q3_full": "என்ன விவசாய இயந்திரங்கள் தேவை மற்றும் அவற்றை எவ்வாறு சிக்கனமாக பயன்படுத்துவது?",
        "q4_full": "சொட்டு நீர் பாசனம் எப்படி அமைப்பது? எவ்வளவு தண்ணீர் மிச்சமாகும்?",
        "q5_full": "என் பண்ணையில் பூச்சி மற்றும் களைகளை கட்டுப்படுத்த சிறந்த முறைகள் என்ன?",
        "q6_full": "விதைப்பதற்கு முன் மண் பரிசோதனை செய்வது எப்படி? நிலத்தை எப்படி பண்படுத்துவது?",
        "step_label": "உழவர் விவர பதிவு",
        "tap_mic": "பேச மைக்கை தட்டவும்",
        "listening": "கேட்கிறேன்... தமிழில் தெளிவாக பேசுங்கள்",
        "got_it": "குரல் பதிவானது! கீழே அனுப்பு பொத்தானை அழுத்தவும்.",
        "try_again": "தெளிவாக கேட்கவில்லை. மீண்டும் மைக்கை தட்டி பேசவும்.",
        "no_support": "இந்த உலாவியில் குரல் ஆதரிக்கப்படவில்லை. கீழே தட்டச்சு செய்யவும்.",
        "age_label": "உங்கள் வயது:",
        "your_question": "உங்கள் கேள்வி:",
        "ai_guidance": "உழவர் AI வழிகாட்டல்",
        "demo_links_card": "உழவர் மாதிரி செயலி",
        "demo_links_hint": "மாதிரி தரவுக்கு செயலியின் இந்த பக்கத்தை திறக்கவும்",
        "demo_links_footer": "🌐 முழு மாதிரி செயலியையும் பார்க்க",
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
    "tts_auto_play_idx": None,
}
for key, default in _INITIAL_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================
# TEXT-TO-SPEECH (TTS) CLEANER & WEB SPEECH ENGINE
# ============================================================
def clean_for_speech(text: str) -> str:
    """Make text natural to SPEAK: drops emojis/symbols/markdown, keeps sentence
    punctuation (. , ? ! : ;) so the voice pauses correctly, converts the rest.
    (Fixes: TTS previously read out emojis, bullets, markdown and stray symbols.)"""
    if not text:
        return ""
    # 1. Markdown links -> their label
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 2. Code blocks and inline code out
    t = re.sub(r'```.*?```', ' ', t, flags=re.DOTALL)
    t = re.sub(r'`[^`]*`', ' ', t)
    # 3. Emojis, pictographs, dingbats and misc symbols out (before other strips;
    #    ranges cover emoji + variation selectors + ZWJ + skin tones)
    t = re.sub(
        r'[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF'
        r'\U0001F1E6-\U0001F1FF\U0000FE00-\U0000FE0F\U00002190-\U000021FF'
        r'\U00002700-\U000027BF\U0001F900-\U0001F9FF\U000025A0-\U000025FF'
        r'\U00002100-\U0000214F\U00003030\U0000303D\U00003297\U00003299\U0000200D]',
        ' ', t)
    # 4. Headings/list/quote/HR markers -> spoken separators
    t = re.sub(r'^#{1,6}\s*', '', t, flags=re.MULTILINE)
    t = re.sub(r'^\s*[-+*]\s+', '', t, flags=re.MULTILINE)   # bullets
    t = re.sub(r'^\s*>\s?', '', t, flags=re.MULTILINE)       # blockquotes
    t = re.sub(r'^\s*-{3,}\s*$', ' ', t, flags=re.MULTILINE)  # horizontal rules
    t = re.sub(r'\n?\*\*\*?\n?', ' ', t)                     # leftover bold rules
    # 5. Bold/italic markers and backticks
    t = t.replace('**', ' ').replace('*', ' ').replace('_', ' ')
    t = t.replace('`', ' ').replace('~', ' ')
    # 6. HTML tags out
    t = re.sub(r'<[^>]+>', ' ', t)
    # 7. Symbols TTS must not read aloud -> drop or verbalize
    t = t.replace('&', ' and ')
    t = re.sub(r'https?://\S+', ' ', t)                      # never read URLs
    t = re.sub(r'(?<=\w)/(?=\w)', ' per ', t)                # ml/hectare -> ml per hectare
    t = re.sub(r'(?<=\d)%', ' percent', t)
    t = re.sub(r'[#`|•◦▪►✓✔☑→←↔■□{}<>\\/=+^~]', ' ', t)
    t = re.sub(r'\bRs\.?\s?', 'rupees ', t)
    t = re.sub(r'₹', 'rupees ', t)
    # 8. Keep ONLY natural speech punctuation; drop brackets/quotes/dashes etc.
    t = re.sub(r'[^\w\s.,?!:;\'\u0b80-\u0bff]', ' ', t)
    # 9. Tidy spacing around sentence marks (but keep decimals like 0.1 intact)
    t = re.sub(r'\s+([.,?!:;])', r'\1', t)
    t = re.sub(r'([.,?!:;])(?=[A-Za-z\u0b80-\u0bff])', r'\1 ', t)
    # 10. Collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def trigger_tts(text: str, lang: str, key: str):
    """Speaks an onboarding/splash prompt: Sarvam (Shubh) first, browser
    voice as fallback. Spoken once per unique key."""
    if st.session_state.last_tts_key == key:
        return
    st.session_state.last_tts_key = key
    clean_text = clean_for_speech(text)
    if not clean_text:
        return
    if SARVAM_TTS:
        try:
            spoken = render_sarvam_audio(clean_text[:2500], lang, auto_play=True, key=key)
        except Exception:
            spoken = False
        if spoken:
            return
    # Fallback: browser speech synthesis (autoplay blocked until first click
    # in some browsers — the language button click provides that gesture).
    lang_code = "ta-IN" if lang == "Tamil" else "en-IN"
    escaped_text = json.dumps(clean_text)
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
    """, height=1)

def render_audio_player(text: str, lang: str, auto_play: bool = False, player_id: str = "player"):
    """Interactive Audio Control Bar with Play, Pause, Resume, and Stop controls."""
    clean_text = clean_for_speech(text)
    escaped_text = json.dumps(clean_text)
    lang_code = "ta-IN" if lang == "Tamil" else "en-IN"

    play_label = "🔊 மீண்டும் கேள் (Play)" if lang == "Tamil" else "🔊 Listen"
    pause_label = "⏸️ இடைநிறுத்து (Pause)" if lang == "Tamil" else "⏸️ Pause"
    resume_label = "▶️ தொடர் (Resume)" if lang == "Tamil" else "▶️ Resume"
    stop_label = "⏹️ நிறுத்து (Stop)" if lang == "Tamil" else "⏹️ Stop"
    idle_label = "🔊 ஆடியோ கட்டுப்பாடு" if lang == "Tamil" else "🔊 Voice Player"
    auto_start_js = "true" if auto_play else "false"

    player_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
    body {{
        margin: 0;
        padding: 4px 0;
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: transparent;
    }}
    .player-wrap {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #ffffff;
        border: 2px solid #86efac;
        padding: 6px 14px;
        border-radius: 999px;
        box-shadow: 0 2px 8px rgba(27, 115, 50, 0.08);
    }}
    .p-btn {{
        background: #f0fdf4;
        border: 1.5px solid #bbf7d0;
        color: #166534;
        font-size: 0.88rem;
        font-weight: 700;
        padding: 6px 13px;
        border-radius: 999px;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        transition: all 0.18s ease;
    }}
    .p-btn:hover {{
        background: #166534;
        color: #ffffff;
        border-color: #166534;
        transform: translateY(-1px);
    }}
    .p-status {{
        font-size: 0.82rem;
        font-weight: 700;
        color: #15803d;
        margin-left: 6px;
        min-width: 110px;
    }}
    </style>
    </head>
    <body>
    <div class="player-wrap">
        <button class="p-btn" onclick="startSpeech()">{play_label}</button>
        <button class="p-btn" onclick="pauseSpeech()">{pause_label}</button>
        <button class="p-btn" onclick="resumeSpeech()">{resume_label}</button>
        <button class="p-btn" onclick="stopSpeech()">{stop_label}</button>
        <span class="p-status" id="pStatus">{idle_label}</span>
    </div>
    <script>
    var synth = window.speechSynthesis;
    var utt = null;
    var speechText = {escaped_text};
    var speechLang = '{lang_code}';

    function buildUtterance() {{
        var u = new SpeechSynthesisUtterance(speechText);
        u.lang = speechLang;
        u.rate = 0.90;
        u.pitch = 1.02;
        var voices = synth.getVoices();
        var matched = voices.find(v => v.lang === speechLang)
                   || voices.find(v => v.lang.startsWith(speechLang.substring(0, 2)));
        if (matched) u.voice = matched;
        u.onstart = function() {{
            document.getElementById('pStatus').innerText = '🔊 Speaking...';
        }};
        u.onend = function() {{
            document.getElementById('pStatus').innerText = '✓ Finished';
        }};
        u.onerror = function() {{
            document.getElementById('pStatus').innerText = '⏹ Stopped';
        }};
        return u;
    }}

    function startSpeech() {{
        synth.cancel();
        utt = buildUtterance();
        synth.speak(utt);
    }}

    function pauseSpeech() {{
        if (synth.speaking && !synth.paused) {{
            synth.pause();
            document.getElementById('pStatus').innerText = '⏸️ Paused';
        }}
    }}

    function resumeSpeech() {{
        if (synth.paused) {{
            synth.resume();
            document.getElementById('pStatus').innerText = '🔊 Speaking...';
        }}
    }}

    function stopSpeech() {{
        synth.cancel();
        document.getElementById('pStatus').innerText = '⏹️ Stopped';
    }}

    if ({auto_start_js}) {{
        function autoRun() {{
            startSpeech();
        }}
        synth.getVoices().length ? autoRun() : synth.addEventListener('voiceschanged', autoRun, {{once: true}});
    }}
    </script>
    </body>
    </html>
    """
    components.html(player_html, height=54)

# ============================================================
# PROMINENT LIVE VOICE CAPTURE WIDGET (STT)
# ============================================================
def voice_capture_widget(step_key: str, lang: str) -> str | None:
    """One-shot speech capture for onboarding steps (returns the transcript)."""
    L = LABELS[lang]
    if not MIC_STT_AVAILABLE:
        st.caption("🎙️ " + L["no_support"])
        return None
    lang_code = "ta-IN" if lang == "Tamil" else "en-IN"
    text = speech_to_text(
        language=lang_code,
        start_prompt=L["tap_mic"],
        stop_prompt="⏹ Stop",
        use_container_width=True,
        just_once=True,
        key=f"stt_{step_key}",
    )
    return (text or "").strip() or None


def voice_console_auto(lang: str) -> None:
    """Voice console with an EXPLICIT Stop & Send button (no auto-stop).

    Behavior:
      - the mic starts when the console mounts (after each answer re-render)
        and records CONTINUOUSLY — the farmer decides when they are finished;
      - a live transcript panel grows as they speak (visible in the console);
      - chrome auto-caps a recognition session (~60s): the console silently
        restarts and APPENDS to the transcript, so recording effectively runs
        until the farmer presses the button;
      - ⏹ Stop & Send → stops the mic, injects the full transcript into
        st.chat_input and submits it → the AI answers;
      - ⏸ Pause (stop recording WITHOUT sending) / 🎙 Resume — independent.
    The transcript flows in through st.chat_input; returns nothing.
    """
    L = LABELS[lang]
    if not MIC_STT_AVAILABLE:
        st.caption("🎙️ " + L["no_support"])
        return

    paused = st.session_state.get("voice_paused", False)
    lang_code = "ta-IN" if lang == "Tamil" else "en-IN"
    mic_label = ("🎤 Recording… press Stop when done"
                 if lang == "English" else "🎤 பதிவு செய்யும்… முடிந்ததும் Stop அழுத்தவும்")

    def _toggle_pause():
        st.session_state.voice_paused = not st.session_state.get("voice_paused", False)

    pc1, pc2 = st.columns([3, 1])
    with pc1:
        st.markdown(
            f'<div class="voice-status-text" style="font-weight:700;color:#166534;font-size:0.95rem;padding:6px 0;">{mic_label if not paused else "⏸ Voice paused — press Resume to record again"}</div>',
            unsafe_allow_html=True,
        )
    with pc2:
        st.button("⏸ Pause" if not paused else "🎙 Resume", key="vp_chat",
                  use_container_width=True, on_click=_toggle_pause)

    if paused:
        return

    components.html(
        f"""
    <style>
    .vconsole {{ border:2.5px solid #86efac; border-radius:16px; padding:10px 14px; background:#ffffff; font-family:'Plus Jakarta Sans',sans-serif; }}
    .vtrans {{ min-height:46px; background:#fffbeb; border:2px solid #f59e0b; border-radius:12px; padding:8px 14px; color:#78350f; font-size:1.05rem; font-weight:600; margin:8px 0; word-break:break-word; }}
    .vstop {{ width:100%; padding:12px 0; border:none; border-radius:12px; cursor:pointer; font-size:1.1rem; font-weight:800; color:#ffffff; background:linear-gradient(135deg,#1b7332 0%,#15803d 100%); box-shadow:0 4px 14px rgba(27,115,50,0.28); }}
    .vhint {{ font-size:0.8rem; color:#475569; text-align:center; margin-top:6px; }}
    </style>
    <div class="vconsole">
        <div class="vtrans" id="vTranscript">…</div>
        <button class="vstop" id="vStopBtn">⏹ Stop &amp; Send</button>
        <div class="vhint">{"Speak freely — recording continues until you press Stop. Long pauses won't cut you off (recording auto-continues every ~60 s)." if lang == "English" else "தயங்காமல் பேசுங்கள் — Stop அழுத்தும் வரை பதிவு தொடரும்."}</div>
    </div>
    <script>
    (function() {{
        var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {{
            document.querySelector('.vhint').innerText = {json.dumps(L["no_support"])};
            document.getElementById('vStopBtn').disabled = true;
            return;
        }}
        var rec = null, manualStop = false, restartTimer = null;
        var transcript = '';
        var transEl = document.getElementById('vTranscript');

        function paint() {{
            transEl.innerText = transcript || '…';
            try {{
                var s = window.parent.document.querySelector('.voice-status-text');
                if (s) s.innerText = '🎤 Recording… ' + transcript.trim().split(/\\s+/).filter(Boolean).length + ' words — press Stop when done';
            }} catch (e) {{}}
        }}

        function start() {{
            try {{
                rec = new SR();
                rec.lang = '{lang_code}';
                rec.interimResults = true;
                rec.maxAlternatives = 1;
                rec.continuous = true;
                rec.onaudiostart = function() {{ paint(); }};
                rec.onresult = function(e) {{
                    // rebuild transcript from all finalized results
                    transcript = '';
                    for (var i = 0; i < e.results.length; i++) {{
                        if (e.results[i].isFinal) transcript += e.results[i][0].transcript;
                    }}
                    var last = e.results[e.results.length-1];
                    if (last && !last.isFinal) paint((transcript + ' ' + last[0].transcript));
                    else paint();
                }};
                rec.onerror = function(e) {{
                    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {{
                        try {{ var s = window.parent.document.querySelector('.voice-status-text'); if (s) s.innerText = '🎤 Mic blocked — allow microphone access'; }} catch (err) {{}}
                    }}
                }};
                rec.onend = function() {{
                    if (manualStop) return;
                    // Chrome caps sessions (~60 s): restart and keep recording.
                    restartTimer = setTimeout(start, 300);
                }};
                rec.start();
            }} catch (e) {{ restartTimer = setTimeout(start, 600); }}
        }}

        function sendAndStop() {{
            manualStop = true;
            clearTimeout(restartTimer);
            try {{ rec.stop(); }} catch (e) {{}}
            var t = (transcript || '').trim();
            try {{
                var s = window.parent.document.querySelector('.voice-status-text');
                if (s) s.innerText = '⏳ Transcribed — generating the answer…';
            }} catch (e) {{}}
            if (!t) {{
                transEl.innerText = {json.dumps(L["try_again"])};
                manualStop = false;
                setTimeout(start, 500);
                return;
            }}
            try {{
                var ta = window.parent.document.querySelector('textarea[aria-label]');
                if (!ta) ta = window.parent.document.querySelector('[data-testid="stChatInput"] textarea');
                if (!ta) return;
                var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, 'value').set;
                setter.call(ta, t);
                ta.dispatchEvent(new window.parent.Event('input', {{ bubbles: true }}));
                setTimeout(function() {{
                    var root = ta.closest('[data-testid="stChatInput"]') || window.parent.document;
                    var btn = root.querySelector('button[aria-label="Send"], button[data-testid="stChatInputSendButton"]');
                    if (!btn) {{
                        var btns = window.parent.document.querySelectorAll('button');
                        for (var i = btns.length - 1; i >= 0; i--) {{
                            if (btns[i].offsetParent && !btns[i].disabled && btns[i].querySelector('svg')) {{ btn = btns[i]; break; }}
                        }}
                    }}
                    if (btn) btn.click(); else {{ ta.focus(); ta.dispatchEvent(new window.parent.KeyboardEvent('keydown', {{key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true}})); }}
                }}, 80);
            }} catch (err) {{
                transEl.innerText = 'Send failed — tap ⏹ again';
                manualStop = false;
                setTimeout(start, 800);
            }}
        }}

        document.getElementById('vStopBtn').onclick = sendAndStop;
        start();
    }})();
    """,
        height=170,
    )
    return None


def _legacy_voice_widget_disabled(step_key: str, lang: str) -> str | None:
    """Superseded by voice_capture_widget above (kept for reference, never called):
    the old iframe mic + ?vresult= query-param round-trip reloaded the whole page
    on every spoken turn. Safe to delete once the integration is merged."""
    params = st.query_params
    if params.get("vstep") == step_key and params.get("vresult"):
        result = params["vresult"]
        st.query_params.clear()
        return result

    L = LABELS[lang]
    lang_code = "ta-IN" if lang == "Tamil" else "en-IN"

    components.html(f"""
    <style>
    .voice-hub {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: #ffffff;
        padding: 16px 20px;
        border-radius: 18px;
        border: 2px solid #86efac;
        box-shadow: 0 4px 14px rgba(27, 115, 50, 0.08);
    }}
    .mic-button {{
        width: 76px;
        height: 76px;
        border-radius: 50%;
        border: none;
        cursor: pointer;
        font-size: 2.1rem;
        color: #ffffff;
        background: linear-gradient(135deg, #1b7332 0%, #0f441c 100%);
        box-shadow: 0 6px 18px rgba(27, 115, 50, 0.35);
        transition: all 0.25s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .mic-button:hover {{
        transform: scale(1.06);
        box-shadow: 0 8px 24px rgba(27, 115, 50, 0.45);
    }}
    .mic-button.recording {{
        background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
        animation: pulseMic 1.2s infinite;
    }}
    @keyframes pulseMic {{
        0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }}
        70% {{ box-shadow: 0 0 0 20px rgba(239, 68, 68, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
    }}
    .transcript-banner {{
        min-height: 48px;
        width: 90%;
        max-width: 600px;
        background: #fffbeb;
        border: 2px solid #f59e0b;
        border-radius: 14px;
        padding: 12px 18px;
        text-align: center;
        color: #78350f;
        font-size: 1.12rem;
        font-weight: 700;
        word-break: break-word;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.15);
        display: none;
    }}
    .status-badge {{
        font-size: 0.92rem;
        color: #166534;
        font-weight: 600;
        background: #f0fdf4;
        padding: 4px 16px;
        border-radius: 999px;
        border: 1px solid #bbf7d0;
    }}
    .send-voice-btn {{
        display: none;
        padding: 10px 28px;
        background: linear-gradient(135deg, #1b7332 0%, #15803d 100%);
        color: #ffffff;
        border: none;
        border-radius: 999px;
        cursor: pointer;
        font-size: 1.05rem;
        font-weight: 700;
        box-shadow: 0 6px 18px rgba(27, 115, 50, 0.3);
        transition: transform 0.2s ease;
    }}
    .send-voice-btn:hover {{
        transform: translateY(-2px);
    }}
    </style>
    <div class="voice-hub">
        <button class="mic-button" id="micBtn" onclick="toggleRecord()">🎤</button>
        <div class="status-badge" id="statusBadge">{L["tap_mic"]}</div>
        <div class="transcript-banner" id="transcriptBanner"></div>
        <button class="send-voice-btn" id="sendVoiceBtn" onclick="sendTranscript()">{L["use_answer"]}</button>
    </div>
    <script>
    var recognition = null, capturedText = '', isListening = false;
    function toggleRecord() {{
        isListening ? recognition.stop() : startListening();
    }}
    function startListening() {{
        var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {{
            document.getElementById('statusBadge').innerText = "{L["no_support"]}";
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
        document.getElementById('statusBadge').innerText = '{L["listening"]}';
        var banner = document.getElementById('transcriptBanner');
        banner.style.display = 'block';
        banner.innerText = '...';
        document.getElementById('sendVoiceBtn').style.display = 'none';

        recognition.onresult = function(e) {{
            var interim = '';
            for (var i = e.resultIndex; i < e.results.length; i++) {{
                if (e.results[i].isFinal) {{
                    capturedText += e.results[i][0].transcript;
                }} else {{
                    interim += e.results[i][0].transcript;
                }}
            }}
            banner.innerText = capturedText || interim;
        }};

        recognition.onend = function() {{
            isListening = false;
            btn.classList.remove('recording');
            btn.innerText = '🎤';
            document.getElementById('statusBadge').innerText = capturedText ? '{L["got_it"]}' : '{L["try_again"]}';
            if (capturedText) {{
                document.getElementById('sendVoiceBtn').style.display = 'inline-block';
            }}
        }};

        recognition.onerror = function(e) {{
            isListening = false;
            btn.classList.remove('recording');
            btn.innerText = '🎤';
            document.getElementById('statusBadge').innerText = '{L["try_again"]}';
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
    """, height=220)
    return None

# ============================================================
# PERSISTENT TOP NAVIGATION BAR
# ============================================================
def render_topbar():
    lang = st.session_state.language
    L = LABELS[lang]

    c1, c2, c3, c4 = st.columns([4, 2.5, 2.5, 1.5])

    with c1:
        st.markdown(
            '<div style="font-size: 1.6rem; font-weight: 800; color: #134e23; display: flex; align-items: center; gap: 8px;">'
            '🌾 Uzhavar AI &nbsp;<span style="color:#1b7332; font-weight:700;">· உழவர் AI</span></div>'
            '<div style="font-size: 0.84rem; color: #166534; font-weight: 600;">Grounded Agronomic & Farming Advisory Platform</div>',
            unsafe_allow_html=True
        )

    with c2:
        st.caption(f"**🌐 {L['lang_toggle']}**")
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
        st.caption(f"**🎛️ Interaction Mode**")
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

    with c4:
        st.caption("**Options**")
        if st.button(L["reset"], key="top_reset_btn", use_container_width=True):
            st.session_state.messages = []
            st.session_state.completion_spoken = False
            st.rerun()

    st.markdown("<hr style='margin: 10px 0 18px 0; border: none; border-top: 2px solid #cbd5e1;'>", unsafe_allow_html=True)

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
            st.markdown(f"<div style='font-size:0.95rem; font-weight:700; color:#134e23; margin-bottom:8px;'>{L['type_label']}</div>", unsafe_allow_html=True)
            with st.form(f"form_{step_key}"):
                val = st.text_input("", placeholder=L["type_placeholder"], label_visibility="collapsed", key=f"inp_{step_key}")
                if st.form_submit_button(L["confirm"], use_container_width=True, type="primary") and val.strip():
                    result = val.strip()
    else:
        with st.form(f"form_text_{step_key}"):
            val = st.text_input(L["type_label"], placeholder=L["type_placeholder"], key=f"inp_t_{step_key}")
            if st.form_submit_button(L["next"], use_container_width=True, type="primary") and val.strip():
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
    # NOTE: browser autoplay policy blocks speech before the first user click,
    # so the welcome audio is triggered AFTER the language button is tapped
    # (the intro prompt inside onboarding now handles that first voice).
    st.markdown("""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:65vh; text-align:center; padding:20px;">
        <div style="font-size: 5.5rem; margin-bottom: 0.5rem; filter: drop-shadow(0 8px 16px rgba(27,115,50,0.25)); animation: gentleFloat 3s infinite ease-in-out;">🌾</div>
        <div style="font-size: 3.4rem; font-weight: 800; color: #134e23; letter-spacing: -0.02em;">Uzhavar AI</div>
        <div style="font-size: 1.6rem; font-weight: 700; color: #1b7332; margin-bottom: 0.6rem;">உழவர் AI — தமிழ்நாட்டின் டிஜிட்டல் உழவன் வழிகாட்டி</div>
        <div style="font-size: 1.1rem; color: #334155; max-width: 600px; margin-bottom: 2rem; line-height: 1.6; font-weight: 500;">
            Conversational agricultural guidance for crops, soil, machinery, irrigation, and pest management.
        </div>
        <div style="background: #ffffff; border: 2.5px solid #86efac; border-radius: 999px; padding: 12px 32px; font-size: 1.15rem; font-weight: 700; color: #14532d; box-shadow: 0 6px 20px rgba(0,0,0,0.06); margin-bottom: 2.2rem;">
            🔊 Choose Your Language &nbsp;•&nbsp; மொழியை தேர்வு செய்யவும்
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
            <div class="ob-hero-card">
                <div style="font-size: 4rem; margin-bottom: 10px;">🌾</div>
                <div class="ob-question-title">
                    {"Welcome to Uzhavar AI — your personal farming guide for Tamil Nadu." if lang == "English"
                     else "உழவர் AI-க்கு வரவேற்கிறோம் — தமிழ்நாட்டு விவசாயிகளுக்கான உங்கள் தனிப்பட்ட வழிகாட்டி."}
                </div>
                <p style="color: #334155; font-size: 1.08rem; line-height: 1.7; font-weight: 500;">
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
            <div class="ob-hero-card">
                <div class="ob-step-chip">Step 1 of 5</div>
                <div class="ob-question-title">👤 &nbsp; {question}</div>
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
            <div class="ob-hero-card">
                <div class="ob-step-chip">Step 2 of 5</div>
                <div class="ob-question-title">🎂 &nbsp; {question}</div>
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
                        st.markdown(f"<div style='font-size:0.95rem; font-weight:700; color:#134e23; margin-bottom:8px;'>{L['age_label']}</div>", unsafe_allow_html=True)
                        age_num = st.number_input("", min_value=15, max_value=100, value=35, step=1, label_visibility="collapsed")
                        if st.form_submit_button(L["confirm"], use_container_width=True, type="primary"):
                            info["age"] = str(age_num)
                            st.session_state.onboarding_step = "gender"
                            st.session_state.last_tts_key = None
                            st.rerun()
            else:
                with st.form("form_age_text"):
                    st.markdown(f"<div style='font-size:0.95rem; font-weight:700; color:#134e23; margin-bottom:8px;'>{L['age_label']}</div>", unsafe_allow_html=True)
                    age_num = st.number_input("", min_value=15, max_value=100, value=35, step=1, label_visibility="collapsed")
                    if st.form_submit_button(L["next"], use_container_width=True, type="primary"):
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
            <div class="ob-hero-card">
                <div class="ob-step-chip">Step 3 of 5</div>
                <div class="ob-question-title">🧑 &nbsp; {question}</div>
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
            <div class="ob-hero-card">
                <div class="ob-step-chip">Step 4 of 5</div>
                <div class="ob-question-title">🌱 &nbsp; {question}</div>
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
                if st.button(L["new_farmer"], use_container_width=True, key="ft_new"):
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
            <div class="ob-hero-card">
                <div class="ob-step-chip">Step 5 of 5</div>
                <div class="ob-question-title">📄 &nbsp; {question}</div>
            </div>
            """, unsafe_allow_html=True)

            if lang == "English":
                doc_summary = (
                    "<b>Key Agricultural Documents for TN Farmers:</b><br>"
                    "• Patta / Chitta / Adangal (Land Ownership & Cultivation Record)<br>"
                    "• Aadhaar Card & Farmer ID / PPB Book<br>"
                    "• Active Bank Passbook linked with Aadhaar"
                    if is_existing else
                    "<b>Initial Documents for New Farmers:</b><br>"
                    "• Aadhaar Card & Ration Card<br>"
                    "• Land Title (Patta) or Registered Lease Deed<br>"
                    "• Bank Account Details"
                )
            else:
                doc_summary = (
                    "<b>தமிழ்நாடு விவசாயிகளுக்கான முக்கிய ஆவணங்கள்:</b><br>"
                    "• பட்டா / சிட்டா / அடங்கல் (நில உரிமை மற்றும் சாகுபடி சான்று)<br>"
                    "• ஆதார் அட்டை மற்றும் உழவர் அடையாள அட்டை<br>"
                    "• ஆதாருடன் இணைக்கப்பட்ட வங்கி கணக்கு புத்தகம்"
                    if is_existing else
                    "<b>புதிய விவசாயிகளுக்கான தொடக்க ஆவணங்கள்:</b><br>"
                    "• ஆதார் அட்டை மற்றும் குடும்ப அட்டை<br>"
                    "• நில உரிமை ஆவணம் (பட்டா) அல்லது குத்தகை ஒப்பந்தம்<br>"
                    "• வங்கி கணக்கு விவரங்கள்"
                )

            st.markdown(f'<div class="ob-doc-alert">{doc_summary}</div>', unsafe_allow_html=True)

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                if st.button(L["has_docs"], use_container_width=True, key="doc_yes", type="primary"):
                    info["has_docs"] = True
                    complete_onboarding()
            with d_col2:
                if st.button(L["no_docs"], use_container_width=True, key="doc_no"):
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
            greeting = f"Vanakkam **{farmer_name}**! 🙏 I am **Uzhavar AI**, your verified agricultural guide.\n\n"
            if is_existing:
                greeting += "As an experienced farmer, I am ready to advise you on crop health, drip irrigation, machinery selection, seed treatment, and integrated pest control."
            else:
                greeting += "Since you are starting your farming journey, I will guide you step-by-step through land preparation, soil testing, seed selection, and cultivation techniques."
            if not has_docs:
                greeting += "\n\n💡 *Note: Keeping your land Patta and Chitta updated will ensure seamless farm management in Tamil Nadu.*"
            greeting += "\n\n**How can I help in your fields today?**"
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

    # Quick Question Action Section
    st.markdown(f'<div class="topic-grid-title">{L["suggested"]}</div>', unsafe_allow_html=True)
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

    st.markdown("<hr style='margin: 18px 0; border: none; border-top: 2px solid #e2e8f0;'>", unsafe_allow_html=True)

    # ========================================================
    # RENDER CHAT HISTORY (HIGH-CONTRAST BUBBLES)
    # ========================================================
    for m_idx, msg in enumerate(st.session_state.messages):
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            # Highlighted User Question Card
            escaped_q = html.escape(content).replace("\n", "<br>")
            st.markdown(f"""
            <div class="user-msg-bubble">
                <div class="user-msg-header">
                    <span class="user-badge">👨‍🌾 {L["your_question"]}</span>
                    <span style="font-size:0.8rem; color:#1b7332; font-weight:700;">{farmer_name}</span>
                </div>
                <div class="user-text-content">{escaped_q}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Highlighted AI Response Card
            st.markdown(f"""
            <div class="ai-msg-bubble">
                <div class="ai-msg-header">
                    <span class="ai-badge">🌾 {L["ai_guidance"]}</span>
                    <span class="verified-pill">🛡️ ICAR & TNAU Grounded</span>
                </div>
                <div class="ai-text-content">
            """, unsafe_allow_html=True)

            # Display/spoken content: strip the appended link block (its URL is
            # rendered in the styled card below), keep only the spoken instruction
            # so TTS never reads a raw URL.
            content_display = content
            dl_msg = msg.get("deep_link")
            if dl_msg:
                content_display = content.rsplit("\n\n---\n\n", 1)[0]
                if dl_msg.get("spoken"):
                    content_display += f"\n\n👉 {dl_msg['spoken']}"

            # Markdown formatted output for the content
            st.markdown(content_display)

            st.markdown("</div></div>", unsafe_allow_html=True)

            # Interactive Audio Player — prefer Sarvam (Shubh) voice when the
            # API key is configured; otherwise fall back to browser speech.
            should_auto_play = (st.session_state.voice_mode and st.session_state.get("tts_auto_play_idx") == m_idx)
            if should_auto_play:
                st.session_state.tts_auto_play_idx = None
            speech_text = clean_for_speech(content_display)
            if SARVAM_TTS and speech_text:
                try:
                    spoken = render_sarvam_audio(speech_text[:2500], lang, auto_play=should_auto_play)
                except Exception:
                    spoken = False
            else:
                spoken = False
            if not spoken:
                render_audio_player(speech_text[:600], lang, auto_play=should_auto_play, player_id=f"player_{m_idx}")

            # Citations list
            if msg.get("sources"):
                with st.expander(f"{L['sources_label']} ({len(msg['sources'])})"):
                    for src in msg["sources"]:
                        st.markdown(f"• **{src['source']}** (Page {src['page']}) — *Relevance: {src['score']}*")

            # Demo deep link: one simple, tappable inline link (no big card —
            # keep the UI minimal for farmers new to apps).
            dl = msg.get("deep_link")
            if dl:
                url = dl["url"]
                st.markdown(
                    f'<a href="{url}" target="_blank" style="font-weight:700; color:#15803d; font-size:1.02rem;">🔗 Open the {html.escape(dl.get("label_en") or "demo app")} page</a>',
                    unsafe_allow_html=True,
                )

    # ========================================================
    # DEDICATED LIVE VOICE ASSISTANT BAR (hands-free, auto-rearming)
    # ========================================================
    voice_query = None  # transcripts arrive via st.chat_input injection
    if st.session_state.voice_mode:
        if MIC_STT_AVAILABLE:
            voice_console_auto(lang)
        else:
            st.markdown(f"""
            <div style="background:#ffffff; border:2.5px solid #2e7d32; border-radius:18px; padding:14px 20px; margin: 15px 0 10px 0; box-shadow:0 4px 16px rgba(0,0,0,0.06);">
                <div style="font-size:1.1rem; font-weight:800; color:#134e23; margin-bottom:4px; display:flex; align-items:center; gap:8px;">
                    🎙️ {L["mode_voice"]} — {L["voice_hint"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.caption("🎙️ " + L["no_support"])

    # Text Input Bar (Always Available)
    typed_query = st.chat_input(L["chat_placeholder"])

    # Resolve Query Priority
    active_query = voice_query or typed_query or chosen_prompt

    if active_query:
        # Append user query to conversation
        st.session_state.messages.append({"role": "user", "content": active_query})

        # Show the farmer's question IMMEDIATELY, with the spinner BELOW it
        # while the AI thinks (instead of a bare spinner with no context).
        pending = st.empty()
        with pending.container():
            escaped_q = html.escape(active_query).replace("\n", "<br>")
            st.markdown(f"""
            <div class="user-msg-bubble">
                <div class="user-msg-header">
                    <span class="user-badge">👨‍🌾 {L["your_question"]}</span>
                    <span style="font-size:0.8rem; color:#1b7332; font-weight:700;">{farmer_name}</span>
                </div>
                <div class="user-text-content">{escaped_q}</div>
            </div>
            """, unsafe_allow_html=True)
            with st.spinner(L["spinner"]):
                rag = get_rag_engine()
                if rag:
                    answer_text, contexts, _, _ = rag.answer(
                        question=active_query,
                        profile={
                            "name": info.get("name"),
                            "age": info.get("age"),
                            "gender": info.get("gender"),
                            "farmer_type": info.get("farmer_type"),
                            "has_docs": info.get("has_docs"),
                            "language": lang,
                            "farming_stage": "Planning",
                        },
                        history=[
                            {"role": m["role"], "content": (
                                m["content"].rsplit("\n\n---\n\n", 1)[0]
                                if (m["role"] == "assistant" and m.get("deep_link"))
                                else m["content"]
                            )}
                            for m in st.session_state.messages[:-1]
                        ],
                        return_details=True
                    )
                    deep_link = getattr(rag, "last_deep_link", None)
                else:
                    answer_text = (
                        "Uzhavar AI engine is initializing. Please verify document index configuration."
                        if lang == "English" else
                        "உழவர் AI தயாராகிறது. ஆவண குறியீட்டு அமைப்பை சரிபார்க்கவும்."
                    )
                    contexts = []
                    deep_link = None
        pending.empty()

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
            "sources": sources_stored,
            "deep_link": deep_link,
        })
        if st.session_state.voice_mode:
            st.session_state.tts_auto_play_idx = len(st.session_state.messages) - 1
        st.rerun()

    # Minimal Sidebar with System Status
    with st.sidebar:
        st.markdown("### 🌾 Uzhavar AI")
        if st.button(L["reset"], use_container_width=True, key="sidebar_reset"):
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
                "• Weed Management Guide"
            )
            st.write("**Vector Store:** 1,353 chunks · Qdrant")
            st.write("**Grounded LLM:** Gemini 2.5 Flash")

# ============================================================
# APPLICATION ROUTING
# ============================================================
if st.session_state.language is None:
    view_language_splash()
elif st.session_state.onboarding_step != "done":
    view_onboarding()
else:
    view_main_chat()
