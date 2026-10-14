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
    from streamlit_mic_recorder import speech_to_text, mic_recorder
    MIC_STT_AVAILABLE = True
except Exception:  # optional dependency — app degrades to typed input
    speech_to_text = None
    mic_recorder = None
    MIC_STT_AVAILABLE = False

import re
import time
import html
import threading
from app.profile_store import save_farmer_profile, save_chat_state, load_chat_state
from app.links_mapping import link_text

try:
    from app.sarvam_tts import render_sarvam_audio, render_sarvam_sequence, prefetch_speech
    SARVAM_TTS = True
except Exception:
    render_sarvam_audio = None
    render_sarvam_sequence = None
    prefetch_speech = None
    SARVAM_TTS = False


try:
    from app.sarvam_stt import sarvam_speech_to_text, SARVAM_STT_READY
    SARVAM_STT = SARVAM_STT_READY
except Exception:  # STT unavailable — voice falls back to browser speech
    sarvam_speech_to_text = None
    SARVAM_STT = False

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
    --bg-page: #f4f7f2;
    --surface: #ffffff;
    --ink: #10261a;
    --ink-soft: #4b5d52;
    --line: #e1ebe3;
    --g900: #0f3d20;
    --g800: #14532d;
    --g700: #166534;
    --g600: #15803d;
    --g200: #bbf7d0;
    --g100: #dcfce7;
    --g50: #f0fdf4;
    --shadow-sm: 0 1px 2px rgba(16, 38, 26, 0.06), 0 4px 14px rgba(16, 38, 26, 0.06);
    --shadow-md: 0 12px 32px -8px rgba(16, 38, 26, 0.20);
}

/* ---------- Canvas ---------- */
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', 'Noto Sans Tamil', -apple-system, 'Segoe UI', sans-serif;
    color: var(--ink);
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(900px 420px at 92% -8%, #dff3e3 0%, rgba(223, 243, 227, 0) 62%),
        radial-gradient(760px 360px at -8% 2%, #fbf1d8 0%, rgba(251, 241, 216, 0) 58%),
        var(--bg-page) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"], [data-testid="stDeployButton"], [data-testid="stAppDeployButton"], .stAppDeployButton, footer { display: none !important; }
.block-container { max-width: 1240px; padding-top: 1.2rem; padding-bottom: 6rem; }
[data-testid="stBottom"] > div { background: linear-gradient(to top, var(--bg-page) 62%, rgba(244, 247, 242, 0)) !important; }

iframe[height="1"], [data-testid="stIFrame"]:has(iframe[height="1"]) {
    display: none !important;
    position: absolute !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
}

@keyframes fadeInUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes gentleFloat { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }

/* ---------- Buttons ---------- */
div.stButton > button, [data-testid="stFormSubmitButton"] > button {
    border-radius: 14px !important;
    font-weight: 700 !important;
    padding: 0.62rem 1.1rem !important;
    font-size: 0.97rem !important;
    transition: all 0.18s ease !important;
    border: 1px solid #cfe5d3 !important;
    background: var(--surface) !important;
    color: var(--g800) !important;
    box-shadow: var(--shadow-sm) !important;
}
div.stButton > button p, [data-testid="stFormSubmitButton"] > button p { color: inherit !important; font-weight: 700 !important; }
div.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-1px) !important;
    border-color: var(--g700) !important;
    background: var(--g50) !important;
    box-shadow: 0 8px 20px rgba(22, 101, 52, 0.16) !important;
}
div.stButton > button[kind="primary"], div.stButton > button[data-testid^="stBaseButton-primary"],
[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"], [data-testid="stFormSubmitButton"] > button[data-testid^="stBaseButton-primary"] {
    background: linear-gradient(135deg, var(--g700) 0%, var(--g800) 100%) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 6px 16px rgba(20, 83, 45, 0.28) !important;
}
div.stButton > button[kind="primary"]:hover, div.stButton > button[data-testid^="stBaseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]:hover, [data-testid="stFormSubmitButton"] > button[data-testid^="stBaseButton-primary"]:hover {
    background: linear-gradient(135deg, #1a7a3b 0%, var(--g700) 100%) !important;
    color: #ffffff !important;
}

/* ---------- Header bar ---------- */
[class*="st-key-topbar"] {
    background: linear-gradient(135deg, var(--g800) 0%, var(--g700) 55%, var(--g600) 100%);
    border-radius: 22px;
    padding: 20px 24px 24px;
    margin-bottom: 18px;
    box-shadow: var(--shadow-md);
}
.brand-title { font-size: 1.4rem; font-weight: 800; color: #ffffff; letter-spacing: -0.01em; line-height: 1.25; }
.brand-title span { display: block; color: #bbf7d0; font-weight: 700; font-size: 1.05rem; margin-top: 2px; }
.brand-sub { font-size: 0.86rem; color: #d9f5e0; font-weight: 500; margin-top: 4px; }
.ctl-label { font-size: 0.72rem; font-weight: 700; color: #bff0cb; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
div[class*="st-key-topbar"] div.stButton > button { padding-left: 0.5rem !important; padding-right: 0.5rem !important; white-space: nowrap; }
div[class*="st-key-topbar"] div.stButton > button[data-testid^="stBaseButton-secondary"], div[class*="st-key-topbar"] div.stButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.12) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.32) !important;
    box-shadow: none !important;
}
div[class*="st-key-topbar"] div.stButton > button[data-testid^="stBaseButton-secondary"]:hover, div[class*="st-key-topbar"] div.stButton > button[kind="secondary"]:hover {
    background: rgba(255, 255, 255, 0.24) !important;
}
div[class*="st-key-topbar"] div.stButton > button[data-testid^="stBaseButton-primary"], div[class*="st-key-topbar"] div.stButton > button[kind="primary"],
div[class*="st-key-topbar"] div.stButton > button[data-testid^="stBaseButton-primary"]:hover {
    background: #ffffff !important;
    color: var(--g800) !important;
    border: 1px solid #ffffff !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.14) !important;
}

/* ---------- Section headings ---------- */
.topic-grid-title {
    font-size: 0.8rem;
    font-weight: 800;
    color: var(--g800);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 6px 0 10px 2px;
}
.section-rule { border: none; border-top: 1px solid var(--line); margin: 18px 0; }

/* ---------- Suggested questions ---------- */
[class*="st-key-quick_questions"] button {
    justify-content: flex-start !important;
    text-align: left !important;
    min-height: 58px;
    border-radius: 16px !important;
    padding: 0.7rem 1rem !important;
}
[class*="st-key-quick_questions"] button p { text-align: left !important; }

/* ---------- Chat messages ---------- */
.user-msg-bubble {
    max-width: 80%;
    margin: 14px 0 10px auto;
    background: linear-gradient(135deg, var(--g700) 0%, var(--g800) 100%);
    color: #ffffff;
    border-radius: 20px 20px 6px 20px;
    padding: 13px 18px 14px;
    box-shadow: var(--shadow-sm);
}
.user-meta { font-size: 0.78rem; font-weight: 700; color: #bbf7d0; margin-bottom: 4px; }
.user-text-content { font-size: 1.08rem; font-weight: 600; line-height: 1.55; word-break: break-word; }

[class*="st-key-ai_msg_"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-left: 4px solid var(--g700);
    border-radius: 20px 20px 20px 6px;
    padding: 18px 24px 14px;
    margin: 6px 0 20px;
    box-shadow: var(--shadow-sm);
}
[class*="st-key-ai_msg_"] [data-testid="stMarkdownContainer"] { font-size: 1.04rem; line-height: 1.7; }
[class*="st-key-ai_msg_"] h1, [class*="st-key-ai_msg_"] h2, [class*="st-key-ai_msg_"] h3 {
    color: var(--g800); font-weight: 700; font-size: 1.2rem; margin: 6px 0 4px; padding: 0;
}
[class*="st-key-ai_msg_"] li { margin-bottom: 4px; }
.ai-head { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.ai-avatar {
    width: 34px; height: 34px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #22c55e, var(--g800)); font-size: 1.05rem;
}
.ai-name { font-weight: 800; color: var(--g800); font-size: 0.98rem; }
.route-chip {
    margin-left: auto; font-size: 0.74rem; font-weight: 700; color: var(--g700);
    background: var(--g50); border: 1px solid var(--g200); padding: 3px 11px; border-radius: 999px;
}
a.app-link, a.app-link:visited {
    display: inline-flex; align-items: center; gap: 8px;
    margin: 4px 0 10px; padding: 10px 18px;
    background: linear-gradient(135deg, var(--g700), var(--g800));
    color: #ffffff !important; font-weight: 700; font-size: 0.96rem;
    text-decoration: none !important; border-radius: 999px;
    box-shadow: 0 6px 16px rgba(20, 83, 45, 0.26); transition: transform 0.18s ease;
}
a.app-link:hover { transform: translateY(-1px); color: #ffffff !important; }

/* ---------- Scheme cards ---------- */
.scheme-card {
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border-left: 4px solid var(--g700);
    box-shadow: var(--shadow-sm);
    min-height: 160px;
    display: flex;
    flex-direction: column;
}
.scheme-card-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 999px;
    background: var(--g50);
    color: var(--g700);
    border: 1px solid var(--g200);
    margin-bottom: 6px;
    align-self: flex-start;
}
.scheme-card-title {
    font-size: 0.94rem;
    font-weight: 700;
    color: var(--g800);
    line-height: 1.35;
    margin-bottom: 6px;
}
.scheme-card-benefit {
    font-size: 0.84rem;
    color: var(--ink);
    line-height: 1.45;
    flex-grow: 1;
}

/* ---------- Voice console & notes ---------- */
[class*="st-key-voice_box"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 16px 22px 14px;
    margin: 6px 0 14px;
    box-shadow: var(--shadow-sm);
}
.voice-help { font-weight: 600; color: var(--g700); font-size: 0.94rem; padding: 0 0 8px; text-align: center; }
.soft-note { color: var(--ink-soft); font-size: 0.9rem; padding: 4px 2px; }

/* ---------- Splash ---------- */
.splash { display: flex; flex-direction: column; align-items: center; text-align: center; padding: 36px 16px 12px; }
.splash-emblem {
    width: 112px; height: 112px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 3.4rem;
    background: radial-gradient(circle at 30% 25%, #ffffff 0%, #dcfce7 100%);
    box-shadow: 0 16px 40px rgba(22, 101, 52, 0.22), inset 0 0 0 6px #ffffff;
    animation: gentleFloat 3.2s infinite ease-in-out; margin-bottom: 18px;
}
.splash-title { font-size: 3.2rem; font-weight: 800; color: var(--g800); letter-spacing: -0.02em; line-height: 1.1; }
.splash-ta { font-size: 1.4rem; font-weight: 700; color: var(--g600); margin: 8px 0 10px; }
.splash-desc { font-size: 1.08rem; color: var(--ink-soft); max-width: 620px; line-height: 1.65; margin-bottom: 20px; }
.splash-tags { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; max-width: 680px; margin-bottom: 26px; }
.splash-tags span {
    background: #ffffff; border: 1px solid var(--line); color: var(--g800);
    font-size: 0.86rem; font-weight: 600; padding: 6px 14px; border-radius: 999px; box-shadow: var(--shadow-sm);
}
.splash-pill {
    background: var(--g100); border: 1px solid var(--g200); color: var(--g800);
    border-radius: 999px; padding: 10px 28px; font-size: 1.05rem; font-weight: 700; margin-bottom: 8px;
}

/* ---------- Onboarding ---------- */
.ob-hero-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 28px;
    padding: 34px 44px 30px;
    max-width: 720px;
    margin: 12px auto 18px;
    box-shadow: var(--shadow-md);
    text-align: center;
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.35s ease-out;
}
.ob-hero-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 5px;
    background: linear-gradient(90deg, var(--g700), #22c55e, #f59e0b);
}
.ob-step-chip {
    background: var(--g100); color: var(--g700); border: 1px solid var(--g200);
    font-size: 0.74rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;
    padding: 4px 14px; border-radius: 999px; display: inline-block; margin-bottom: 12px;
}
.ob-icon { font-size: 2.6rem; line-height: 1; margin-bottom: 10px; }
.ob-question-title { font-size: 1.55rem; font-weight: 800; color: var(--g900); line-height: 1.4; }
.ob-body { color: var(--ink-soft); font-size: 1.05rem; line-height: 1.7; margin: 14px 0 0; }
.ob-doc-alert {
    background: var(--g50); border: 1px solid var(--g200); border-radius: 16px;
    padding: 16px 22px; text-align: left; margin: 4px auto 16px; max-width: 720px;
    color: var(--g800); font-size: 0.97rem; line-height: 1.7;
}
.field-label { font-size: 0.9rem; font-weight: 700; color: var(--g800); margin-bottom: 8px; }

/* ---------- Inputs & containers ---------- */
[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }
div[data-baseweb="input"], div[data-baseweb="base-input"] { border-radius: 14px !important; background: #ffffff !important; }
div[data-baseweb="input"] { border: 1px solid #cfe5d3 !important; }
[data-testid="stChatInput"] {
    border-radius: 18px !important;
    border: 1.5px solid #b9d9c0 !important;
    box-shadow: var(--shadow-md) !important;
    background: #ffffff !important;
}
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] textarea { background: #ffffff !important; border-radius: 18px !important; }
[data-testid="stBottomBlockContainer"] { max-width: 1240px; }
[data-testid="stChatInput"]:focus-within { border-color: var(--g700) !important; box-shadow: 0 0 0 4px rgba(22, 101, 52, 0.16) !important; }
[data-testid="stExpander"] { background: #ffffff !important; border: 1px solid var(--line) !important; border-radius: 14px !important; box-shadow: none !important; }
[data-testid="stProgress"] { max-width: 720px; margin: 0 auto; }

/* ---------- Accessibility: everything stays clearly visible, even while loading/disabled ---------- */
:root { --ink-soft: #33473a; }
/* Streamlit fades "stale" widgets during reruns - never fade them */
[data-stale="true"], [data-stale="true"] * { opacity: 1 !important; transition: none !important; }
/* Leftovers of the previous SCREEN (language splash / onboarding) must vanish at once,
   not linger while the next screen's audio is being prepared */
[data-stale="true"][class*="st-key-splash_"], [data-stale="true"]:has([class*="st-key-splash_"]),
[data-stale="true"][class*="st-key-ob_"], [data-stale="true"]:has([class*="st-key-ob_"]),
[data-stale="true"][class*="st-key-gen_"], [data-stale="true"]:has([class*="st-key-gen_"]),
[data-stale="true"][class*="st-key-ft_"], [data-stale="true"]:has([class*="st-key-ft_"]),
[data-stale="true"][class*="st-key-doc_"], [data-stale="true"]:has([class*="st-key-doc_"]),
[data-stale="true"][class*="st-key-mic_"], [data-stale="true"]:has([class*="st-key-mic_"]),
[data-stale="true"] .splash, [data-stale="true"] .ob-hero-card, [data-stale="true"] .ob-doc-alert,
[data-stale="true"] [data-testid="stForm"] { display: none !important; }
/* Chat box: dark text, strong placeholder, solid border, visible send button (also when disabled) */
[data-testid="stChatInput"], [data-testid="stChatInput"] * { opacity: 1 !important; }
[data-testid="stChatInput"] { border: 2px solid var(--g700) !important; background: #ffffff !important; }
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea:disabled {
    color: #10261a !important; -webkit-text-fill-color: #10261a !important;
    font-size: 1.05rem !important; font-weight: 500 !important; background: #ffffff !important; cursor: text;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #4b5d52 !important; -webkit-text-fill-color: #4b5d52 !important; opacity: 1 !important; font-weight: 500;
}
[data-testid="stChatInput"] button, [data-testid="stChatInputSubmitButton"] {
    background: var(--g700) !important; color: #ffffff !important; border-radius: 12px !important;
}
[data-testid="stChatInput"] button svg { fill: #ffffff !important; color: #ffffff !important; }
/* Disabled buttons (shown while an answer is being written): dimmed a little but still readable */
div.stButton > button:disabled { opacity: 0.65 !important; cursor: not-allowed; color: var(--g800) !important; }
div[class*="st-key-topbar"] div.stButton > button:disabled { color: #ffffff !important; opacity: 0.7 !important; }
div[class*="st-key-topbar"] div.stButton > button[data-testid^="stBaseButton-primary"]:disabled { color: var(--g800) !important; }
/* Visible blinking cursor + single clean border (no double outline) */
[data-testid="stChatInput"] textarea { caret-color: #0f3d20 !important; padding-left: 14px !important; min-height: 28px; }
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] > div > div { border: none !important; box-shadow: none !important; outline: none !important; }
[data-testid="stChatInput"]:focus-within { border-color: #22c55e !important; box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.30) !important; }
[data-testid="stChatInput"] { min-height: 62px; border-radius: 20px !important; }
[data-testid="stChatInput"] button { width: 44px !important; height: 44px !important; }

/* ---------- Easy-reading enhancements for farmers ---------- */
html { font-size: 17px; }
/* Bigger answer text with comfortable spacing */
[class*="st-key-ai_msg_"] [data-testid="stMarkdownContainer"] { font-size: 1.14rem !important; line-height: 1.8 !important; color: #10261a; }
[class*="st-key-ai_msg_"] li { margin-bottom: 8px; }
.user-text-content { font-size: 1.18rem !important; }
/* Large, easy-to-tap buttons */
div.stButton > button, [data-testid="stFormSubmitButton"] > button { min-height: 52px; font-size: 1.05rem !important; }
[class*="st-key-quick_questions"] button { min-height: 64px !important; font-size: 1.05rem !important; }
/* Keyboard / touch focus is always obvious */
div.stButton > button:focus-visible { outline: 3px solid #f59e0b !important; outline-offset: 2px; }
/* Answer card: clearer separation between messages */
[class*="st-key-ai_msg_"] { border-left-width: 6px !important; box-shadow: 0 2px 6px rgba(16,38,26,0.10), 0 8px 22px rgba(16,38,26,0.08) !important; }
/* Listen button on each answer looks like a clear green call-to-action */
[class*="st-key-listen_"] button { background: #166534 !important; color: #ffffff !important; border: none !important; border-radius: 999px !important; min-height: 46px; }
[class*="st-key-listen_"] button p { color: #ffffff !important; }
[class*="st-key-listen_"] button:hover { background: #14532d !important; }
/* Phones: edge-to-edge cards, bigger header text, stacked controls */
@media (max-width: 640px) {
    .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
    .user-msg-bubble { max-width: 94%; }
    .splash-title { font-size: 2.3rem; }
    [class*="st-key-ai_msg_"] { padding: 14px 16px 10px; }
}

/* ---------- Header: never let one column overlap its neighbour ---------- */
div[class*="st-key-topbar"] [data-testid="stColumn"], div[class*="st-key-topbar"] [data-testid="column"] { min-width: 0 !important; }
div[class*="st-key-topbar"] .brand-sub { line-height: 1.35; margin-top: 6px; }
div[class*="st-key-topbar"] .ctl-label { white-space: nowrap; }
div[class*="st-key-topbar"] div.stButton > button { overflow: hidden; text-overflow: ellipsis; }

/* ---------- App-like polish ---------- */
#MainMenu, [data-testid="stToolbar"], [data-testid="stStatusWidget"], [data-testid="stDecoration"] { display: none !important; }
html, body { -webkit-font-smoothing: antialiased; scroll-behavior: smooth; }
/* Header buttons: keep labels on one line, shrink text slightly so both Options fit side by side */
div[class*="st-key-topbar"] div.stButton > button { font-size: 0.95rem !important; padding-left: 0.3rem !important; padding-right: 0.3rem !important; }
div[class*="st-key-topbar"] div.stButton > button p { white-space: nowrap; overflow: visible; }
/* Sign out is a quiet outline button, New chat stays solid */
div[class*="st-key-top_signout_btn"] button { background: transparent !important; border: 1.5px solid rgba(255,255,255,0.55) !important; }
/* Cards lift slightly on hover, like tappable app tiles */
[class*="st-key-quick_questions"] button:hover { transform: translateY(-2px) !important; }
/* Smooth entrance for the whole page */
@media (max-width: 900px) { div[class*="st-key-topbar"] div.stButton > button { font-size: 0.85rem !important; } }

/* Small helper text */
.soft-note, .ob-body { color: var(--ink-soft); }
/* header subtitle sits on dark green: must stay light */
.brand-sub { color: #eafbef !important; font-weight: 600 !important; font-size: 0.95rem !important; opacity: 1 !important; }
[data-testid="stProgress"] p, [data-testid="stCaptionContainer"] { color: var(--ink) !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# RAG ENGINE LAZY LOADER
# ============================================================
@st.cache_resource(show_spinner=False)
def _rag_holder():
    """Loads the heavy AI models in a background thread the moment the app starts,
    so the first question does not wait for model loading."""
    h = {"rag": None, "err": None, "ready": threading.Event()}

    def _load():
        try:
            from app.rag import RAG
            h["rag"] = RAG()
            h["ready"].set()              # usable now: general chat needs only the LLM client
            warm = getattr(h["rag"], "warm", None)
            if warm:
                warm()                    # model weights keep loading in the background
        except Exception as e:
            h["err"] = e
            h["ready"].set()

    threading.Thread(target=_load, daemon=True).start()
    return h


def get_rag_engine():
    h = _rag_holder()
    if not h["ready"].wait(timeout=240):   # never wait forever
        return None
    if h["err"]:
        st.error(f"⚠️ RAG Engine initialization note: {h['err']}")
        return None
    return h["rag"]


_rag_holder()   # kick off warm-up at app start

# ============================================================
# MULTILINGUAL SCRIPT & CONVERSATION CONTENT
# ============================================================
SCRIPT = {
    "intro_title": {
        "English": "Welcome to Uzhavar AI",
        "Tamil": "உழவர் AI-க்கு வரவேற்கிறோம்",
    },
    "intro_body": {
        "English": (
            "Your personal farming guide for Tamil Nadu. Answer a few quick questions so I can tailor "
            "my advice to your farm. You can speak or type your answers, and switch between voice and "
            "text at any time from the top bar."
        ),
        "Tamil": (
            "தமிழ்நாட்டு விவசாயிகளுக்கான உங்கள் தனிப்பட்ட வழிகாட்டி. உங்கள் பண்ணைக்கு ஏற்ப வழிகாட்ட "
            "சில எளிய கேள்விகள் கேட்கிறேன். நீங்கள் பேசியோ தட்டச்சு செய்தோ பதிலளிக்கலாம்; "
            "திரையின் மேலே உள்ள பொத்தான்கள் மூலம் குரல், உரை முறைகளுக்கு இடையே எப்போது வேண்டுமானாலும் மாறலாம்."
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
        "English": "What is your gender?",
        "Tamil": "உங்கள் பாலினம் என்ன?",
    },
    "ask_farmer_type": {
        "English": "Are you already farming, or planning to start?",
        "Tamil": "நீங்கள் ஏற்கனவே விவசாயம் செய்கிறீர்களா, அல்லது புதிதாகத் தொடங்கப் போகிறீர்களா?",
    },
    "ask_docs_existing": {
        "English": (
            "To manage farm records in Tamil Nadu, farmers usually need a Patta, Chitta or Adangal, "
            "an Aadhaar card and a Farmer ID card. Do you have these land and identity documents?"
        ),
        "Tamil": (
            "தமிழ்நாட்டில் விவசாய ஆவணங்களை பராமரிக்க, விவசாயிகளுக்கு பட்டா, சிட்டா அல்லது அடங்கல், "
            "ஆதார் அட்டை மற்றும் உழவர் அடையாள அட்டை தேவை. இந்த ஆவணங்கள் உங்களிடம் உள்ளனவா?"
        ),
    },
    "ask_docs_new": {
        "English": (
            "To start farming in Tamil Nadu, you will need an Aadhaar card, a ration card, and proof of "
            "land or a lease agreement. Do you have these ready?"
        ),
        "Tamil": (
            "தமிழ்நாட்டில் விவசாயம் தொடங்க, ஆதார் அட்டை, ரேஷன் அட்டை, மற்றும் நில உரிமை அல்லது "
            "குத்தகை ஆவணங்கள் தேவை. இவை உங்களிடம் தயாராக உள்ளனவா?"
        ),
    },
    "ask_docs_short": {
        "English": "Do you have these documents ready?",
        "Tamil": "இந்த ஆவணங்கள் உங்களிடம் தயாராக உள்ளனவா?",
    },
    "splash": {
        "English": "Welcome to Uzhavar AI, your farming guide for Tamil Nadu. Please choose your language.",
        "Tamil": "உழவர் AI-க்கு வரவேற்கிறோம். உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்.",
    },
    "completion": {
        "English": (
            "Thank you, {name}! Your profile is saved. You can now ask me anything about crops, "
            "soil health, machinery, irrigation, pest control, or government subsidy schemes & eligibility."
        ),
        "Tamil": (
            "நன்றி {name}! உங்கள் விவரங்கள் சேமிக்கப்பட்டன. இப்போது பயிர்கள், மண் வளம், "
            "இயந்திரங்கள், பாசனம், பூச்சி மேலாண்மை அல்லது அரசு மானியத் திட்டங்கள் மற்றும் தகுதி பற்றி என்னிடம் கேளுங்கள்."
        ),
    },
}

LABELS = {
    "English": {
        "begin": "Get started",
        "next": "Continue →",
        "male": "Male",
        "female": "Female",
        "other": "Other",
        "existing_farmer": "🧑‍🌾 I'm already farming",
        "new_farmer": "🌱 I'm just starting out",
        "has_docs": "✅ Yes, I have them",
        "no_docs": "📋 Not yet — I'm arranging them",
        "type_label": "Or type your answer:",
        "type_placeholder": "Type your answer",
        "confirm": "Confirm →",
        "chat_placeholder": "Ask a farming question — e.g. which machinery suits 2 acres of paddy?",
        "mode_voice": "🎤 Voice",
        "mode_text": "💬 Text",
        "lang_toggle": "Language",
        "mode_label": "Input mode",
        "options_label": "Options",
        "brand_sub": "Trusted farming advice for Tamil Nadu",
        "suggested": "Suggested questions",
        "reset": "🔄 New chat",
        "signout": "🚪 Sign out",
        "sources_label": "📚 Sources",
        "spinner": "Finding the best answer for you…",
        "translating": "Translating your chat…",
        "translate_failed": "Some earlier messages could not be translated, so they are shown in their original language. Switch the language again to retry.",
        "q1": "🌱 How do I start farming?",
        "q2": "🌾 What crop should I grow?",
        "q3": "🏛️ Check subsidy eligibility",
        "q4": "💧 100% Drip irrigation subsidy",
        "q5": "🐛 How to control pests & weeds?",
        "q6": "🧪 How to test soil health?",
        "q1_full": "How do I start farming? What are the key first steps for land and crop?",
        "q2_full": "What crop should I grow? Help me choose the right crop based on season and soil.",
        "q3_full": "What government subsidies and welfare schemes can I get? What details do I need to provide to check my eligibility?",
        "q4_full": "How can I apply for 100% government subsidy for drip irrigation under the PMKSY scheme?",
        "q5_full": "What are the best methods to control pests and weeds in my farm?",
        "q6_full": "How do I conduct soil testing and prepare my land before sowing?",
        "step_label": "Profile setup",
        "step_of": "Step {n} of {total}",
        "chip_name": "Your name",
        "chip_age": "Age",
        "chip_gender": "Gender",
        "chip_type": "Farming status",
        "chip_docs": "Documents",
        "tap_mic": "🎙 Tap to speak",
        "stop_mic": "⏹ Stop",
        "start_rec": "🎙 Start recording",
        "stop_send": "⏹ Stop and send",
        "voice_help": "Tap start, ask your question, then tap stop and send.",
        "transcribing": "⏳ Transcribing your speech…",
        "no_support": "Voice input isn't available right now. Please type your answer.",
        "age_label": "Your age",
        "your_question": "Your question",
        "ai_name": "Uzhavar AI",
    },
    "Tamil": {
        "begin": "தொடங்குவோம்",
        "next": "தொடரவும் →",
        "male": "ஆண்",
        "female": "பெண்",
        "other": "பிற",
        "existing_farmer": "🧑‍🌾 நான் ஏற்கனவே விவசாயம் செய்கிறேன்",
        "new_farmer": "🌱 நான் புதிதாகத் தொடங்குகிறேன்",
        "has_docs": "✅ ஆம், என்னிடம் உள்ளன",
        "no_docs": "📋 இல்லை — ஏற்பாடு செய்கிறேன்",
        "type_label": "அல்லது இங்கே தட்டச்சு செய்யவும்:",
        "type_placeholder": "உங்கள் பதிலை எழுதவும்",
        "confirm": "உறுதிசெய் →",
        "chat_placeholder": "விவசாய கேள்வியைக் கேளுங்கள் — எ.கா: 2 ஏக்கர் நெல்லுக்கு எந்த இயந்திரம் ஏற்றது?",
        "mode_voice": "🎤 குரல்",
        "mode_text": "💬 உரை",
        "lang_toggle": "மொழி",
        "mode_label": "உள்ளீட்டு முறை",
        "options_label": "விருப்பங்கள்",
        "brand_sub": "தமிழ்நாட்டு விவசாயிகளுக்கான நம்பகமான வழிகாட்டி",
        "suggested": "பரிந்துரைக்கப்பட்ட கேள்விகள்",
        "reset": "🔄 புதிய உரையாடல்",
        "signout": "🚪 வெளியேறு",
        "sources_label": "📚 ஆதாரங்கள்",
        "spinner": "உங்களுக்கான சிறந்த பதிலைத் தேடுகிறேன்…",
        "translating": "உங்கள் உரையாடலை மொழிபெயர்க்கிறேன்…",
        "translate_failed": "சில முந்தைய செய்திகளை மொழிபெயர்க்க முடியவில்லை; அவை அசல் மொழியிலேயே காட்டப்படுகின்றன. மீண்டும் முயல மொழியை ஒருமுறை மாற்றவும்.",
        "q1": "🌱 விவசாயம் எப்படி தொடங்குவது?",
        "q2": "🌾 என்ன பயிர் விளைவிக்கலாம்?",
        "q3": "🏛️ மானியத் தகுதி சரிபார்க்க",
        "q4": "💧 100% சொட்டு நீர் பாசன மானியம்",
        "q5": "🐛 பூச்சி & களை கட்டுப்பாடு எப்படி?",
        "q6": "🧪 மண் பரிசோதனை செய்வது எப்படி?",
        "q1_full": "விவசாயம் எப்படி தொடங்குவது? நிலத்தில் செய்ய வேண்டிய முதல் முக்கிய படிகள் என்ன?",
        "q2_full": "என்ன பயிர் விளைவிக்கலாம்? பருவம் மற்றும் மண்ணுக்கு ஏற்ற பயிரை பரிந்துரைக்கவும்.",
        "q3_full": "எனக்கு என்னென்ன அரசு நலத்திட்ட மானியங்கள் கிடைக்கும்? தகுதியை சரிபார்க்க நான் என்ன விவரங்களை கூற வேண்டும்?",
        "q4_full": "PMKSY திட்டத்தின் கீழ் சொட்டு நீர் பாசனத்திற்கு 100% மானியம் பெறுவது எப்படி?",
        "q5_full": "என் பண்ணையில் பூச்சி மற்றும் களைகளை கட்டுப்படுத்த சிறந்த முறைகள் என்ன?",
        "q6_full": "விதைப்பதற்கு முன் மண் பரிசோதனை செய்வது எப்படி? நிலத்தை எப்படி பண்படுத்துவது?",
        "step_label": "விவர பதிவு",
        "step_of": "படி {n} / {total}",
        "chip_name": "உங்கள் பெயர்",
        "chip_age": "வயது",
        "chip_gender": "பாலினம்",
        "chip_type": "விவசாய நிலை",
        "chip_docs": "ஆவணங்கள்",
        "tap_mic": "🎙 பேச தட்டவும்",
        "stop_mic": "⏹ நிறுத்து",
        "start_rec": "🎙 பதிவைத் தொடங்கு",
        "stop_send": "⏹ நிறுத்தி அனுப்பு",
        "voice_help": "தொடங்கு அழுத்தி உங்கள் கேள்வியைக் கேளுங்கள், பிறகு நிறுத்தி அனுப்பு அழுத்துங்கள்.",
        "transcribing": "⏳ உங்கள் குரலை எழுத்தாக்குகிறேன்…",
        "no_support": "குரல் உள்ளீடு தற்போது கிடைக்கவில்லை. தயவுசெய்து தட்டச்சு செய்யவும்.",
        "age_label": "உங்கள் வயது",
        "your_question": "உங்கள் கேள்வி",
        "ai_name": "உழவர் AI",
    },
}

ROUTE_CHIPS = {
    "scheme": ("Schemes · TN Citizen Charter 2025-26", "நிதித்திட்டம் · தமிழ்நாடு நலத்திட்ட ஆவணம் 2025-26"),
    "demo": ("Uzhavar app · Live service", "உழவர் செயலி · நேரடி சேவை"),
    "agri": ("Farming guidance · Agricultural references", "விவசாய வழிகாட்டி · வேளாண் குறிப்பு ஆவணங்கள்"),
}


def _box(key: str):
    """Keyed container (styled via its st-key-* class); plain container on older Streamlit."""
    try:
        return st.container(key=key)
    except TypeError:
        return st.container()


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
    "tts_open": set(),        # message indices whose audio player is built (lazy TTS)
    "pending_query": None,    # question waiting for its (streamed) answer
}
for key, default in _INITIAL_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================
# SAVED CHATS: the farmer's id lives in the page URL (?u=...), so a refresh
# restores language, profile and conversation instead of showing the splash.
# ============================================================
def _restore_session():
    if st.session_state.get("_restored"):
        return
    st.session_state["_restored"] = True
    uid = st.query_params.get("u")
    saved = load_chat_state(uid) if uid else None
    if not saved or saved.get("language") not in ("English", "Tamil"):
        return
    st.session_state.language = saved["language"]
    st.session_state.voice_mode = bool(saved.get("voice_mode", True))
    st.session_state.farmer_info = saved.get("farmer_info") or {}
    st.session_state.messages = saved.get("messages") or []
    st.session_state.onboarding_step = "done"
    st.session_state.completion_spoken = True      # don't replay the welcome clip
    # refreshed while an answer was still being written -> write it again
    if st.session_state.messages and st.session_state.messages[-1].get("role") == "user":
        last = st.session_state.messages[-1]
        st.session_state.pending_query = {"q": last["content"], "lang": last.get("lang", saved["language"])}


def persist_state():
    info = st.session_state.farmer_info
    uid = info.get("id")
    if not uid or st.session_state.onboarding_step != "done":
        return
    try:
        save_chat_state(uid, {
            "language": st.session_state.language,
            "voice_mode": st.session_state.voice_mode,
            "farmer_info": info,
            "messages": st.session_state.messages,
        })
    except Exception:
        pass   # saving must never break the chat


_restore_session()

# ============================================================
# TEXT-TO-SPEECH (TTS) CLEANER & WEB SPEECH ENGINE
# ============================================================
def clean_for_speech(text: str, lang: str = "English") -> str:
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
    # 7. Symbols TTS must not read aloud -> drop or verbalize based on language
    t = t.replace('&', ' and ' if lang == "English" else ' மற்றும் ')
    t = re.sub(r'https?://\S+', ' ', t)                      # never read URLs
    t = re.sub(r'(?<=\w)/(?=\w)', ' per ' if lang == "English" else ' ஒரு ', t)
    
    if lang == "Tamil":
        t = re.sub(r'(?<=\d)%', ' சதவீதம்', t)
        t = re.sub(r'\bRs\.?\s?', 'ரூபாய் ', t)
        t = re.sub(r'₹\s?', 'ரூபாய் ', t)
    else:
        t = re.sub(r'(?<=\d)%', ' percent', t)
        t = re.sub(r'\bRs\.?\s?', 'rupees ', t)
        t = re.sub(r'₹\s?', 'rupees ', t)

    t = re.sub(r'[#`|•◦▪►✓✔☑→←↔■□{}<>\\/=+^~]', ' ', t)

    # 8. Keep ONLY natural speech punctuation; drop brackets/quotes/dashes etc.
    t = re.sub(r'[^\w\s.,?!:;\'\u0b80-\u0bff]', ' ', t)
    # 9. Tidy spacing around sentence marks (but keep decimals like 0.1 intact)
    t = re.sub(r'\s+([.,?!:;])', r'\1', t)
    t = re.sub(r'([.,?!:;])(?=[A-Za-z\u0b80-\u0bff])', r'\1 ', t)
    # 10. Collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()

    # 11. High-fidelity phonetic adjustments for natural pronunciation
    if lang == "English":
        # 'Ullavar' gives the authentic retroflex-approximated sound without English 'z' buzzing
        t = re.sub(r'\bUzhavar[-\s]*AI\b', 'Ullavar A I', t, flags=re.IGNORECASE)
        t = re.sub(r'\bUzhavar\b', 'Ullavar', t, flags=re.IGNORECASE)
        t = re.sub(r'\bUzhavan\b', 'Ullavan', t, flags=re.IGNORECASE)
        t = re.sub(r'\bVanakkam\b', 'Vanak-kam', t, flags=re.IGNORECASE)
        t = re.sub(r'\bPM[-\s]*KSY\b', 'P M K S Y', t, flags=re.IGNORECASE)
        t = re.sub(r'\bPM[-\s]*KUSUM\b', 'P M Kusum', t, flags=re.IGNORECASE)
        t = re.sub(r'\bPM[-\s]*FBY\b', 'P M F B Y', t, flags=re.IGNORECASE)
        t = re.sub(r'\bTNAU\b', 'T N A U', t)
        t = re.sub(r'\bICAR\b', 'I C A R', t)
        t = re.sub(r'\bAEC\b', 'A E C', t)
        t = re.sub(r'\bAED\b', 'A E D', t)
        t = re.sub(r'\bTNeGA\b|\bTNEGA\b', 'T N E G A', t, flags=re.IGNORECASE)
        t = re.sub(r'\be[-\s]*Vaadagai\b', 'E-Vaadagai', t, flags=re.IGNORECASE)
        t = re.sub(r'\bPatta\b', 'Pat-ta', t, flags=re.IGNORECASE)
        t = re.sub(r'\bChitta\b', 'Chit-ta', t, flags=re.IGNORECASE)
        t = re.sub(r'\bAdangal\b', 'Adan-gal', t, flags=re.IGNORECASE)
        t = re.sub(r'\bAI\b', 'A I', t)
    else:
        # Convert English acronyms and mixed terms in Tamil speech into natural Tamil syllables
        t = re.sub(r'\bUzhavar[-\s]*AI\b', 'உழவர் ஏ.ஐ', t, flags=re.IGNORECASE)
        t = re.sub(r'\bUzhavar\b', 'உழவர்', t, flags=re.IGNORECASE)
        t = re.sub(r'\bUzhavan\b', 'உழவன்', t, flags=re.IGNORECASE)
        t = re.sub(r'\bAI\b', 'ஏ.ஐ', t)
        t = re.sub(r'\bPM[-\s]*KSY\b', 'பி.எம்.கே.எஸ்.ஒய்', t, flags=re.IGNORECASE)
        t = re.sub(r'\bPM[-\s]*KUSUM\b', 'பி.எம் குசும்', t, flags=re.IGNORECASE)
        t = re.sub(r'\bPM[-\s]*FBY\b', 'பி.எம் பயிர் காப்பீடு', t, flags=re.IGNORECASE)
        t = re.sub(r'\bDBT\b', 'டி.பி.டி', t, flags=re.IGNORECASE)
        t = re.sub(r'\bTNAU\b', 'தமிழ்நாடு வேளாண் பல்கலைக்கழகம்', t, flags=re.IGNORECASE)
        t = re.sub(r'\bAEC\b', 'வேளாண் விரிவாக்க மையம்', t, flags=re.IGNORECASE)
        t = re.sub(r'\bAED\b', 'வேளாண் பொறியியல் துறை', t, flags=re.IGNORECASE)
        t = re.sub(r'\bTNeGA\b|\bTNEGA\b', 'டி.என்.இ.ஜி.ஏ', t, flags=re.IGNORECASE)
        t = re.sub(r'\be[-\s]*Vaadagai\b', 'இ-வாடகை', t, flags=re.IGNORECASE)
        t = re.sub(r'\bKisan\b', 'கிசான்', t, flags=re.IGNORECASE)

    return t

def autoscroll(follow: bool = True):
    """Scroll the chat to the newest content, like ChatGPT/Claude.
    follow=True keeps following while an answer streams in (stops as soon as the farmer
    scrolls up); follow=False scrolls once to the bottom when the page has settled."""
    components.html(f"""
    <script>
    (function() {{
        try {{
            var doc = window.parent.document;
            var b = doc.querySelector('[data-testid="stMain"]') || doc.querySelector('section.main') || doc.scrollingElement;
            if (!b) return;
            var follow = {"true" if follow else "false"};
            function bottom() {{ b.scrollTo({{ top: b.scrollHeight, behavior: follow ? 'auto' : 'smooth' }}); }}
            if (!follow) {{ setTimeout(bottom, 120); setTimeout(bottom, 600); return; }}
            var last = b.scrollTop, on = true;
            var timer = setInterval(function() {{
                if (b.scrollTop < last - 30) on = false;      // farmer scrolled up: stop following
                if (on) b.scrollTop = b.scrollHeight;
                last = b.scrollTop;
            }}, 200);
            window.addEventListener('unload', function() {{ clearInterval(timer); }});
        }} catch (e) {{}}
    }})();
    </script>
    """, height=1)


def splash_voice():
    """First screen: a short bilingual voice-over (app name + 'choose your language') using Sarvam AI."""
    items = [(clean_for_speech(SCRIPT["splash"][l], l)[:2500], l) for l in ("English", "Tamil")]
    if SARVAM_TTS:
        try:
            render_sarvam_sequence(items, key="splash_voice", auto_play=True)
        except Exception:
            pass


def prefetch_onboarding(lang: str):
    """Generate every onboarding voice prompt in the background so each step plays
    instantly instead of waiting on a network call."""
    if not (SARVAM_TTS and prefetch_speech):
        return
    texts = [
        f"{SCRIPT['intro_title'][lang]}. {SCRIPT['intro_body'][lang]}",
        SCRIPT["ask_name"][lang], SCRIPT["ask_age"][lang], SCRIPT["ask_gender"][lang],
        SCRIPT["ask_farmer_type"][lang], SCRIPT["ask_docs_existing"][lang], SCRIPT["ask_docs_new"][lang],
    ]
    for t in texts:
        prefetch_speech(clean_for_speech(t, lang)[:2500], lang)


def trigger_tts(text: str, lang: str, key: str, show_controls: bool = True, retry_on_interaction: bool = False):
    """Speaks an onboarding prompt with Sarvam AI voice."""
    if st.session_state.last_tts_key == key:
        return
    st.session_state.last_tts_key = key
    clean_text = clean_for_speech(text, lang)
    if not clean_text:
        return
    if SARVAM_TTS:
        try:
            render_sarvam_audio(clean_text[:2500], lang, auto_play=True, key=key,
                                show_controls=show_controls,
                                retry_on_interaction=retry_on_interaction)
        except Exception:
            pass


def render_audio_player(text: str, lang: str, auto_play: bool = False, player_id: str = "player"):
    """Natural Sarvam AI speech player for chat responses.
    If Sarvam credits are exhausted for the day, displays a polite notice without playing robotic voice.
    """
    clean_text = clean_for_speech(text, lang)
    if not clean_text:
        return
    if SARVAM_TTS:
        try:
            render_sarvam_audio(clean_text[:2500], lang, auto_play=auto_play,
                                key=player_id, show_controls=True)
        except Exception:
            pass


# ============================================================
# LIVE VOICE CAPTURE (STT)
# ============================================================
def voice_capture_widget(step_key: str, lang: str) -> str | None:
    """One-shot speech capture for onboarding steps; returns the transcript.

    Uses MediaRecorder + Sarvam STT (server-side, works in every modern
    browser) and falls back to the browser speech widget (Chrome only).
    """
    L = LABELS[lang]
    if not MIC_STT_AVAILABLE:
        st.markdown(f'<div class="soft-note">🎙️ {L["no_support"]}</div>', unsafe_allow_html=True)
        return None
    if SARVAM_STT and sarvam_speech_to_text:
        audio = mic_recorder(
            start_prompt=L["tap_mic"],
            stop_prompt=L["stop_mic"],
            just_once=True,
            use_container_width=True,
            format="wav",
            key=f"mic_{step_key}",
        )
        if not audio:
            return None
        with st.spinner(L["transcribing"]):
            text, err = sarvam_speech_to_text(audio["bytes"], lang)
        if err:
            st.error(err)
            return None
        return (text or "").strip() or None
    lang_code = "ta-IN" if lang == "Tamil" else "en-IN"
    text = speech_to_text(
        language=lang_code,
        start_prompt=L["tap_mic"],
        stop_prompt=L["stop_mic"],
        use_container_width=True,
        just_once=True,
        key=f"stt_{step_key}",
    )
    return (text or "").strip() or None


def voice_console_auto(lang: str) -> str | None:
    """Chat voice console: Start recording, ask the question, then Stop and send.

    The recording is transcribed server-side with Sarvam STT instead of the
    browser's Web Speech API, which is Chrome-only and fails silently in
    Edge and on networks without Google's speech servers. Nothing is
    captured until the farmer presses Start.
    """
    L = LABELS[lang]
    if not (MIC_STT_AVAILABLE and SARVAM_STT and sarvam_speech_to_text):
        st.markdown(f'<div class="soft-note">🎙️ {L["no_support"]}</div>', unsafe_allow_html=True)
        return None

    with _box("voice_box"):
        st.markdown(f'<div class="voice-help">{L["voice_help"]}</div>', unsafe_allow_html=True)
        audio = mic_recorder(
            start_prompt=L["start_rec"],
            stop_prompt=L["stop_send"],
            just_once=True,
            use_container_width=True,
            format="wav",
            key=f"voice_console_{lang}",
        )
    if not audio:
        return None
    with st.spinner(L["transcribing"]):
        text, err = sarvam_speech_to_text(audio["bytes"], lang)
    if err:
        st.error(err)
        return None
    return (text or "").strip() or None


# ============================================================
# PERSISTENT TOP NAVIGATION BAR
# ============================================================
def set_app_language(lang_val: str):
    st.session_state.tts_auto_play_idx = None
    for m in st.session_state.messages:
        m.get("tx_fail", {}).pop(lang_val, None)
    st.session_state.language = lang_val
    st.session_state.last_tts_key = None

def set_voice_mode(is_voice: bool):
    st.session_state.tts_auto_play_idx = None
    st.session_state.voice_mode = is_voice

def sign_out():
    """Forget this farmer on this browser: back to the language screen.
    The saved chat stays in the database but is no longer linked to this page."""
    persist_state()
    try:
        st.query_params.clear()
    except Exception:
        pass
    for k, v in _INITIAL_STATE.items():
        st.session_state[k] = type(v)() if isinstance(v, (set, dict, list)) else v
    st.session_state.last_tts_key = None
    st.rerun()

def render_topbar():
    lang = st.session_state.language
    L = LABELS[lang]
    busy = st.session_state.get("pending_query") is not None   # answer in progress: lock controls

    with _box("topbar"):
        signed_in = st.session_state.onboarding_step == "done"
        # before sign-in there is no Options area, so the header uses only 3 columns (no empty gap)
        cols = st.columns([3.4, 2.2, 2.5, 3.4] if signed_in else [4.2, 3.0, 3.2], gap="small")
        c1, c2, c3 = cols[0], cols[1], cols[2]
        c4 = cols[3] if signed_in else None

        with c1:
            st.markdown(
                '<div class="brand-title">🌾 Uzhavar AI<span>உழவர் AI</span></div>'
                f'<div class="brand-sub">{L["brand_sub"]}</div>',
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(f'<div class="ctl-label">{L["lang_toggle"]}</div>', unsafe_allow_html=True)
            la, lb = st.columns(2)
            with la:
                st.button(
                    "English",
                    key="top_btn_en",
                    disabled=busy,
                    use_container_width=True,
                    type="primary" if lang == "English" else "secondary",
                    on_click=set_app_language, args=("English",),
                )
            with lb:
                st.button(
                    "தமிழ்",
                    key="top_btn_ta",
                    disabled=busy,
                    use_container_width=True,
                    type="primary" if lang == "Tamil" else "secondary",
                    on_click=set_app_language, args=("Tamil",),
                )

        with c3:
            st.markdown(f'<div class="ctl-label">{L["mode_label"]}</div>', unsafe_allow_html=True)
            va, vb = st.columns(2)
            with va:
                st.button(
                    L["mode_voice"],
                    key="top_btn_voice",
                    disabled=busy,
                    use_container_width=True,
                    type="primary" if st.session_state.voice_mode else "secondary",
                    on_click=set_voice_mode, args=(True,),
                )
            with vb:
                st.button(
                    L["mode_text"],
                    key="top_btn_text",
                    disabled=busy,
                    use_container_width=True,
                    type="primary" if not st.session_state.voice_mode else "secondary",
                    on_click=set_voice_mode, args=(False,),
                )

        if c4 is not None:
          with c4:
            st.markdown(f'<div class="ctl-label">{L["options_label"]}</div>', unsafe_allow_html=True)
            oa, ob = st.columns(2)
            with oa:
                new_chat = st.button(L["reset"], key="top_reset_btn", use_container_width=True, disabled=busy)
            with ob:
                signout = st.button(L["signout"], key="top_signout_btn", use_container_width=True, disabled=busy)
            if new_chat:
                st.session_state.messages = []
                st.session_state.pending_query = None
                st.session_state.tts_open = set()
                st.session_state.tts_auto_play_idx = None
                # completion_spoken stays True: the welcome clip must not replay on a new chat
                st.rerun()
            if signout:
                sign_out()

# ============================================================
# ONBOARDING FLOW & PERSISTENT STORAGE
# ============================================================
STEP_ORDER = ["intro", "name", "age", "gender", "farmer_type", "docs"]

def render_step_progress(step: str):
    steps = STEP_ORDER[1:]
    L = LABELS[st.session_state.language]
    if step not in steps:
        return
    done = steps.index(step) + 1
    label = f'{L["step_label"]} · ' + L["step_of"].format(n=done, total=len(steps))
    st.progress(done / len(steps), text=label)

def ob_card(L: dict, icon: str, title: str, chip_key: str | None = None, body: str = ""):
    """One self-contained onboarding card (a single markdown call, so no stray boxes)."""
    chip = f'<div class="ob-step-chip">{L[chip_key]}</div>' if chip_key else ""
    body_html = f'<p class="ob-body">{html.escape(body)}</p>' if body else ""
    st.markdown(
        f'<div class="ob-hero-card">{chip}<div class="ob-icon">{icon}</div>'
        f'<div class="ob-question-title">{html.escape(title)}</div>{body_html}</div>',
        unsafe_allow_html=True,
    )

def render_dual_input(step_key: str, lang: str) -> str | None:
    L = LABELS[lang]
    result = None

    if st.session_state.voice_mode:
        v_col, t_col = st.columns([1, 1], gap="large")
        with v_col:
            result = voice_capture_widget(step_key, lang)
        with t_col:
            st.markdown(f'<div class="field-label">{L["type_label"]}</div>', unsafe_allow_html=True)
            with st.form(f"form_{step_key}"):
                val = st.text_input(L["type_label"], placeholder=L["type_placeholder"], label_visibility="collapsed", key=f"inp_{step_key}")
                if st.form_submit_button(L["confirm"], use_container_width=True, type="primary") and val.strip():
                    result = val.strip()
    else:
        with st.form(f"form_text_{step_key}"):
            val = st.text_input(L["type_label"], placeholder=L["type_placeholder"], key=f"inp_t_{step_key}")
            if st.form_submit_button(L["next"], use_container_width=True, type="primary") and val.strip():
                result = val.strip()

    return result

def clean_name(raw: str) -> str:
    """'My name is pooja.' -> 'Pooja'. Keeps letters (Latin/Tamil), drops stray punctuation."""
    t = re.sub(r"^(my name is|i am|i'm|this is|name is)\s+", "", raw.strip(), flags=re.IGNORECASE)
    t = re.sub(r"[^A-Za-z\u0B80-\u0BFF\s.'-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" .'-")
    return (t[:40].title() if t else raw.strip()[:40])

def complete_onboarding():
    """Saves the farmer profile to SQLite & JSON, then moves to the main chat."""
    info = st.session_state.farmer_info
    info["language"] = st.session_state.language
    rec = save_farmer_profile(info)
    info["id"] = rec["id"]
    st.query_params["u"] = rec["id"]      # survives a page refresh

    st.session_state.onboarding_step = "done"
    st.session_state.last_tts_key = None
    st.session_state.completion_spoken = False
    st.session_state.messages = []
    st.rerun()

# ============================================================
# VIEW 1: LANGUAGE SELECTION SPLASH
# ============================================================
def view_language_splash():
    if not st.session_state.get("_splash_prefetched"):
        st.session_state["_splash_prefetched"] = True
        for _l in ("English", "Tamil"):
            if SARVAM_TTS and prefetch_speech:
                prefetch_speech(clean_for_speech(SCRIPT["splash"][_l])[:2500], _l)      # splash voice first
                prefetch_speech(clean_for_speech(f"{SCRIPT['intro_title'][_l]}. {SCRIPT['intro_body'][_l]}")[:2500], _l)
    # Browsers block speech before the first click, so the first spoken
    # prompt plays after a language is chosen (onboarding intro).
    st.markdown("""
    <div class="splash">
        <div class="splash-emblem">🌾</div>
        <div class="splash-title">Uzhavar AI</div>
        <div class="splash-ta">உழவர் AI — தமிழ்நாட்டின் டிஜிட்டல் உழவன் வழிகாட்டி</div>
        <div class="splash-desc">
            Clear, trusted guidance on crops, soil, machinery, irrigation and pest control —
            in English and Tamil, by voice or text.
        </div>
        <div class="splash-tags">
            <span>🌾 Crops · பயிர்கள்</span><span>🧪 Soil · மண்</span><span>💧 Irrigation · பாசனம்</span>
            <span>🚜 Machinery · இயந்திரங்கள்</span><span>🐛 Pests · பூச்சிகள்</span><span>🏛️ Schemes · திட்டங்கள்</span>
        </div>
        <div class="splash-pill">Choose your language · மொழியைத் தேர்ந்தெடுக்கவும்</div>
    </div>
    """, unsafe_allow_html=True)

    _, btn_en_col, _, btn_ta_col, _ = st.columns([2, 3, 0.6, 3, 2])
    with btn_en_col:
        if st.button("English", use_container_width=True, key="splash_btn_en", type="primary"):
            st.session_state.language = "English"
            st.session_state.onboarding_step = "intro"
            st.session_state.last_tts_key = None
            st.rerun()

    with btn_ta_col:
        if st.button("தமிழ்", use_container_width=True, key="splash_btn_ta", type="primary"):
            st.session_state.language = "Tamil"
            st.session_state.onboarding_step = "intro"
            st.session_state.last_tts_key = None
            st.rerun()

    # spoken after the screen is drawn, so the audio fetch never delays the buttons
    splash_voice()

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

    def go(next_step: str):
        st.session_state.onboarding_step = next_step
        st.session_state.last_tts_key = None
        st.rerun()

    _, center, _ = st.columns([1, 4, 1])
    if st.session_state.get("_prefetched_lang") != lang:
        st.session_state["_prefetched_lang"] = lang
        prefetch_onboarding(lang)
    if info.get("name") and SARVAM_TTS and prefetch_speech:
        prefetch_speech(clean_for_speech(SCRIPT["completion"][lang].format(name=info["name"]))[:2500], lang)
    speak = None   # spoken AFTER the screen is drawn, so the network call never delays the UI

    if step == "intro":
        title = SCRIPT["intro_title"][lang]
        body = SCRIPT["intro_body"][lang]
        speak = (f"{title}. {body}", lang, "intro")
        with center:
            ob_card(L, "🌾", title, body=body)
            _, btn_c, _ = st.columns([2, 3, 2])
            with btn_c:
                if st.button(L["begin"], use_container_width=True, key="ob_start_btn", type="primary"):
                    go("name")

    elif step == "name":
        question = SCRIPT["ask_name"][lang]
        speak = (question, lang, "ob_name")
        with center:
            ob_card(L, "👤", question, chip_key="chip_name")
            captured = render_dual_input("ob_name", lang)
            if captured:
                info["name"] = clean_name(captured)
                go("age")

    elif step == "age":
        question = SCRIPT["ask_age"][lang]
        speak = (question, lang, "ob_age")
        with center:
            ob_card(L, "🎂", question, chip_key="chip_age")

            def age_form(form_key: str, submit_label: str):
                with st.form(form_key):
                    st.markdown(f'<div class="field-label">{L["age_label"]}</div>', unsafe_allow_html=True)
                    age_num = st.number_input(L["age_label"], min_value=15, max_value=100, value=35, step=1, label_visibility="collapsed")
                    if st.form_submit_button(submit_label, use_container_width=True, type="primary"):
                        info["age"] = str(age_num)
                        go("gender")

            if st.session_state.voice_mode:
                v_col, t_col = st.columns([1, 1], gap="large")
                with v_col:
                    age_spoken = voice_capture_widget("ob_age", lang)
                    if age_spoken:
                        extracted = "".join(filter(str.isdigit, age_spoken))
                        if extracted:
                            info["age"] = extracted
                            go("gender")
                with t_col:
                    age_form("form_age", L["confirm"])
            else:
                age_form("form_age_text", L["next"])

    elif step == "gender":
        question = SCRIPT["ask_gender"][lang]
        speak = (question, lang, "ob_gender")
        with center:
            ob_card(L, "🧑", question, chip_key="chip_gender")
            g1, g2, g3 = st.columns(3)
            for col, label_key, value, key in (
                (g1, "male", "Male", "gen_male"),
                (g2, "female", "Female", "gen_female"),
                (g3, "other", "Other", "gen_other"),
            ):
                with col:
                    if st.button(L[label_key], use_container_width=True, key=key):
                        info["gender"] = value
                        go("farmer_type")

    elif step == "farmer_type":
        question = SCRIPT["ask_farmer_type"][lang]
        speak = (question, lang, "ob_ftype")
        with center:
            ob_card(L, "🌱", question, chip_key="chip_type")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                if st.button(L["existing_farmer"], use_container_width=True, key="ft_existing", type="primary"):
                    info["farmer_type"] = "existing"
                    go("docs")
            with f_col2:
                if st.button(L["new_farmer"], use_container_width=True, key="ft_new"):
                    info["farmer_type"] = "new"
                    go("docs")

    elif step == "docs":
        is_existing = (info.get("farmer_type") == "existing")
        q_key = "ask_docs_existing" if is_existing else "ask_docs_new"
        speak = (SCRIPT[q_key][lang], lang, f"ob_docs_{info.get('farmer_type')}")

        with center:
            ob_card(L, "📄", SCRIPT["ask_docs_short"][lang], chip_key="chip_docs")

            if lang == "English":
                doc_summary = (
                    "<b>Documents Tamil Nadu farmers usually keep:</b><br>"
                    "• Patta / Chitta / Adangal (land ownership and cultivation record)<br>"
                    "• Aadhaar card and Farmer ID / PPB book<br>"
                    "• Bank passbook linked with Aadhaar"
                    if is_existing else
                    "<b>Documents to start farming:</b><br>"
                    "• Aadhaar card and ration card<br>"
                    "• Land title (Patta) or registered lease deed<br>"
                    "• Bank account details"
                )
            else:
                doc_summary = (
                    "<b>தமிழ்நாடு விவசாயிகளுக்கான முக்கிய ஆவணங்கள்:</b><br>"
                    "• பட்டா / சிட்டா / அடங்கல் (நில உரிமை மற்றும் சாகுபடி சான்று)<br>"
                    "• ஆதார் அட்டை மற்றும் உழவர் அடையாள அட்டை<br>"
                    "• ஆதாருடன் இணைக்கப்பட்ட வங்கி கணக்கு புத்தகம்"
                    if is_existing else
                    "<b>விவசாயம் தொடங்க தேவையான ஆவணங்கள்:</b><br>"
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

    if speak:
        trigger_tts(*speak)

# ============================================================
# VIEW 3: MAIN AGRICULTURAL CHAT INTERFACE
# ============================================================
def _plain(msg: dict) -> str:
    """Message text without the appended deep-link block."""
    c = msg.get("content", "")
    return c.rsplit("\n\n---\n\n", 1)[0] if (msg.get("role") == "assistant" and msg.get("deep_link")) else c


def _msg_lang(m: dict) -> str:
    """Language a message was written in: its stored tag, else detected from the script."""
    return m.get("lang") or ("Tamil" if re.search(r"[\u0B80-\u0BFF]", m.get("content", "")) else "English")


def _needs_tx(m: dict, lang: str) -> bool:
    return bool(
        m.get("kind") != "greeting" and m.get("content")
        and _msg_lang(m) != lang and not m.get("tx", {}).get(lang)
    )


def translate_chat_if_needed(lang: str, L: dict):
    """After a language switch: translate earlier questions/answers into the new language.
    Each message is translated once and cached on it (msg['tx'][lang]). A failed message is
    retried right away; if it still fails it is left in its original language, a note says so,
    and it is tried again the next time the language is switched."""
    for _ in range(2):
        todo = [m for m in st.session_state.messages if _needs_tx(m, lang) and not m.get("tx_fail", {}).get(lang)]
        if not todo:
            break
        with st.spinner(L["translating"]):
            rag = get_rag_engine()
            out = rag.translate([_plain(m) for m in todo], lang) if (rag and hasattr(rag, "translate")) else None
        for i, m in enumerate(todo):
            if out and out[i]:
                m.setdefault("tx", {})[lang] = out[i]
    for m in st.session_state.messages:
        if _needs_tx(m, lang):
            m.setdefault("tx_fail", {})[lang] = True
    if any(_needs_tx(m, lang) for m in st.session_state.messages):
        st.caption(L["translate_failed"])


def render_user_message(text: str, name: str, L: dict):
    escaped_q = html.escape(text).replace("\n", "<br>")
    st.markdown(
        f'<div class="user-msg-bubble"><div class="user-meta">{L["your_question"]} · {html.escape(name)}</div>'
        f'<div class="user-text-content">{escaped_q}</div></div>',
        unsafe_allow_html=True,
    )

def render_assistant_message(msg: dict, m_idx: int, lang: str, L: dict, farmer_name: str = "", info: dict | None = None):
    """One answer card: header, text, app link, audio and sources — all inside a single keyed container."""
    if msg.get("kind") == "greeting":
        msg_lang = lang                                   # greeting always follows the current language
        msg["content"] = build_greeting(lang, farmer_name, info or {})
        tx = None
    else:
        tx = msg.get("tx", {}).get(lang)                  # translated into the current language?
        msg_lang = lang if tx else _msg_lang(msg)         # otherwise keep the language it was written in
    lang = msg_lang
    L = LABELS[lang]
    dl = msg.get("deep_link")
    content = msg["content"]
    display = tx if tx else (content.rsplit("\n\n---\n\n", 1)[0] if dl else content)

    chip = ROUTE_CHIPS.get(msg.get("route"))
    chip_html = ""
    if chip:
        chip_html = f'<span class="route-chip">{html.escape(chip[1] if lang == "Tamil" else chip[0])}</span>'

    with _box(f"ai_msg_{m_idx}"):
        st.markdown(
            f'<div class="ai-head"><span class="ai-avatar">🌾</span>'
            f'<span class="ai-name">{L["ai_name"]}</span>{chip_html}</div>',
            unsafe_allow_html=True,
        )
        if display.strip():
            st.markdown(display)

        if dl:
            card = {"en": dl.get("label_en") or "", "ta": dl.get("label_ta") or dl.get("label_en") or ""}
            st.markdown(
                f'<a class="app-link" href="{html.escape(dl["url"], quote=True)}" target="_blank" rel="noopener">'
                f'{html.escape(link_text(card, lang))} ↗</a>',
                unsafe_allow_html=True,
            )

        should_auto_play = (st.session_state.voice_mode and st.session_state.get("tts_auto_play_idx") == m_idx)
        if should_auto_play:
            # NOT cleared here: the player HTML must stay identical on any extra rerun, so Streamlit
            # keeps the same iframe (no remount, audio not cut off). It is cleared on the next user action.
            st.session_state.tts_open.add(m_idx)
        # Lazy TTS: audio is only generated for the newest voice-mode answer or when
        # the farmer taps Listen — never for every old message on every rerun.
        if m_idx in st.session_state.tts_open:
            spoken_source = display
            if dl and dl.get("spoken"):
                spoken_source += "\n\n" + dl["spoken"]
            speech_text = clean_for_speech(spoken_source, lang)
            spoken = False
            if SARVAM_TTS and speech_text:
                try:
                    spoken = render_sarvam_audio(speech_text[:2500], lang, auto_play=should_auto_play)
                except Exception:
                    spoken = False
            if not spoken:
                render_audio_player(speech_text[:3500], lang, auto_play=should_auto_play, player_id=f"player_{m_idx}")
        elif display.strip():
            if st.button("🔊 " + ("கேள்" if lang == "Tamil" else "Listen"), key=f"listen_{m_idx}"):
                st.session_state.tts_open.add(m_idx)
                st.session_state.tts_auto_play_idx = m_idx
                st.rerun()

        if msg.get("sources"):
            with st.expander(f"{L['sources_label']} ({len(msg['sources'])})"):
                for src in msg["sources"]:
                    if src.get("scheme"):
                        st.markdown(f"**{src['scheme'].title()}** · {src['source']} · page {src['page']}")
                    else:
                        st.markdown(f"**{src['source']}** · page {src['page']} · relevance {src['score']}")

def build_greeting(lang: str, name: str, info: dict) -> str:
    is_existing = (info.get("farmer_type") == "existing")
    has_docs = info.get("has_docs", True)
    if lang == "English":
        greeting = f"Vanakkam **{name}**! 🙏 I'm **Uzhavar AI**, your farming guide.\n\n"
        greeting += (
            "I can help you with crop cultivation, pest management, drip irrigation, machinery selection, and **government subsidy schemes & eligibility**."
            if is_existing else
            "Since you're just starting out, I'll guide you step by step through land preparation, soil testing, crop selection, and **eligible government subsidies**."
        )
        if not has_docs:
            greeting += "\n\n💡 *Tip: keeping your Patta and Chitta up to date makes it easier to apply for farm schemes and services in Tamil Nadu.*"
        greeting += "\n\n**How can I help on your farm today?**"
    else:
        greeting = f"வணக்கம் **{name}**! 🙏 நான் **உழவர் AI**, உங்கள் விவசாய வழிகாட்டி.\n\n"
        greeting += (
            "பயிர் சாகுபடி, பூச்சி மேலாண்மை, சொட்டு நீர் பாசனம், இயந்திரத் தேர்வு மற்றும் **அரசு நலத்திட்ட மானியங்கள் & தகுதி விவரங்களில்** உங்களுக்கு வழிகாட்டுகிறேன்."
            if is_existing else
            "நீங்கள் புதிதாகத் தொடங்குவதால், நிலம் பண்படுத்துதல், மண் பரிசோதனை, பயிர் தேர்வு மற்றும் **உங்களுக்கான அரசு மானியத் திட்டங்களை** படிப்படியாக வழிகாட்டுகிறேன்."
        )
        if not has_docs:
            greeting += "\n\n💡 *குறிப்பு: பட்டா, சிட்டா ஆவணங்களை புதுப்பித்து வைத்திருந்தால், தமிழ்நாட்டில் வேளாண் திட்டங்களுக்கு விண்ணப்பிப்பது எளிதாகும்.*"
        greeting += "\n\n**இன்று உங்கள் பண்ணைக்கு என்ன உதவி வேண்டும்?**"
    return greeting

_STRONG_GREET = {"hi", "hii", "hiii", "hiiii", "hello", "hellow", "helo", "hey", "heyy", "hai", "vanakkam", "vanakam",
                 "namaste", "namaskaram", "வணக்கம்", "ஹாய்", "ஹலோ", "ஹெலோ"}
_GREET_FILLER = {"there", "sir", "madam", "ma", "all", "bro", "anna", "friend", "buddy", "da", "uzhavar", "ai",
                 "how", "are", "you", "u", "r", "good", "morning", "afternoon", "evening", "night", "everyone"}
_GREET_PHRASES = {"how are you", "how r u", "whats up", "good morning", "good afternoon", "good evening",
                  "good night", "எப்படி இருக்கிறீர்கள்", "நலமா"}
_THANKS = {"thanks", "thank you", "thankyou", "thanks a lot", "thank u", "நன்றி", "மிக்க நன்றி"}
_BYE = {"bye", "goodbye", "see you", "bye bye", "பை", "போய் வருகிறேன்"}
_ABOUT = {"who are you", "what can you do", "what do you do", "help", "help me", "நீ யார்", "நீங்கள் யார்", "உதவி"}

def smalltalk_reply(q: str, lang: str, name: str):
    """Instant reply for greetings / thanks / bye / 'who are you'. Returns None for real questions."""
    t = re.sub(r"[^\w\s\u0b80-\u0bff]", "", q.lower()).strip()
    t = re.sub(r"\s+", " ", t)
    toks = t.split()
    if not toks or len(toks) > 6:
        return None
    if t in _THANKS:
        kind = "thanks"
    elif t in _BYE:
        kind = "bye"
    elif t in _ABOUT:
        kind = "about"
    elif t in _GREET_PHRASES or (any(w in _STRONG_GREET for w in toks)
                                 and all(w in _STRONG_GREET or w in _GREET_FILLER for w in toks)):
        kind = "greet"
    else:
        return None
    if lang == "Tamil":
        return {
            "greet": "வணக்கம்! 🙏 பயிர்கள், மண், இயந்திரங்கள், பாசனம், பூச்சி மேலாண்மை அல்லது **அரசு மானியத் திட்டங்கள் & தகுதி** பற்றி என்ன தெரிந்துகொள்ள வேண்டும்?",
            "thanks": "மகிழ்ச்சி! வேறு ஏதேனும் விவசாய கேள்வி இருந்தால் கேளுங்கள்.",
            "bye": "நன்றி! மீண்டும் சந்திப்போம். 🌾",
            "about": "நான் உழவர் AI. பயிர் தேர்வு, மண் பரிசோதனை, சொட்டு நீர் பாசனம், இயந்திரங்கள், பூச்சி கட்டுப்பாடு மற்றும் **அரசுத் திட்டங்கள் & தகுதி** பற்றி உதவுவேன். உங்கள் கேள்வியைக் கேளுங்கள்.",
        }[kind]
    return {
        "greet": "Vanakkam! 🙏 Ask me anything about crops, soil, machinery, irrigation, pest control, or **government subsidy schemes & eligibility**.",
        "thanks": "You're welcome! Ask me anything else about your farm.",
        "bye": "Thank you! See you again soon. 🌾",
        "about": "I'm Uzhavar AI. I can help with crop selection, soil testing, drip irrigation, machinery, pest control and government schemes & eligibility. Just ask your question.",
    }[kind]

def view_main_chat():
    lang = st.session_state.language
    L = LABELS[lang]
    info = st.session_state.farmer_info
    farmer_name = info.get("name", "Farmer")

    if not st.session_state.messages:
        # content is rebuilt at render time so it always matches the CURRENT language
        st.session_state.messages = [{"role": "assistant", "kind": "greeting", "content": "", "sources": []}]

    persist_state()   # flushes the previous run's changes (new messages, language, mode)
    busy = st.session_state.pending_query is not None
    render_topbar()

    st.markdown(f'<div class="topic-grid-title">{L["suggested"]}</div>', unsafe_allow_html=True)
    chosen_prompt = None
    q_items = [("q1", "q1_full"), ("q2", "q2_full"), ("q3", "q3_full"),
               ("q4", "q4_full"), ("q5", "q5_full"), ("q6", "q6_full")]
    with _box("quick_questions"):
        q_rows = [st.columns(3), st.columns(3)]
        for idx, (short_k, full_k) in enumerate(q_items):
            with q_rows[idx // 3][idx % 3]:
                if st.button(L[short_k], use_container_width=True, key=f"sq_{idx}", disabled=busy):
                    chosen_prompt = L[full_k]



    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)

    translate_chat_if_needed(lang, L)

    for m_idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            _tx = msg.get("tx", {}).get(lang)
            render_user_message(_tx if _tx else msg["content"], farmer_name, L)
        else:
            render_assistant_message(msg, m_idx, lang, L, farmer_name, info)

    voice_query = None
    if st.session_state.voice_mode and not busy:
        voice_query = voice_console_auto(lang)
    typed_query = st.chat_input(L["chat_placeholder"], disabled=busy)
    active_query = voice_query or typed_query or chosen_prompt

    if st.session_state.pop("scroll_once", False):
        autoscroll(follow=False)

    # ---- Answer being generated: stream it; no mic is drawn meanwhile, chat box is disabled ----
    if busy:
        autoscroll(follow=True)
        pq = st.session_state.pending_query
        q_lang = pq["lang"]
        rag = None
        answer_text, contexts, deep_link = "", [], None
        with _box("ai_msg_pending"):
            st.markdown(
                f'<div class="ai-head"><span class="ai-avatar">🌾</span>'
                f'<span class="ai-name">{LABELS[q_lang]["ai_name"]}</span></div>',
                unsafe_allow_html=True,
            )
            quick = smalltalk_reply(pq["q"], q_lang, farmer_name)
            try:
                if quick:                                    # hi / thanks / bye: instant, no AI call
                    st.markdown(quick)
                    answer_text = quick
                else:
                    with st.spinner(LABELS[q_lang]["spinner"]):   # model warm-up + retrieval, until first token
                        rag = get_rag_engine()
                        result = None
                        if rag:
                            history = [
                                {"role": m["role"], "content": (
                                    m["content"].rsplit("\n\n---\n\n", 1)[0]
                                    if (m["role"] == "assistant" and m.get("deep_link"))
                                    else m["content"]
                                )}
                                for m in st.session_state.messages[:-1]
                                if m.get("kind") != "greeting" and m["content"]
                            ]
                            result, contexts, _, _ = rag.answer(
                                question=pq["q"],
                                profile={
                                    "name": info.get("name"),
                                    "age": info.get("age"),
                                    "gender": info.get("gender"),
                                    "farmer_type": info.get("farmer_type"),
                                    "farmer_scale": info.get("farmer_scale"),
                                    "farmer_scale_label": info.get("farmer_scale_label_ta" if q_lang == "Tamil" else "farmer_scale_label_en"),
                                    "land_acres": info.get("land_acres"),
                                    "water_source": info.get("water_source"),
                                    "crop": info.get("crop"),
                                    "has_docs": info.get("has_docs"),
                                    "language": q_lang,
                                    "farming_stage": "Planning",
                                },
                                history=history,
                                return_details=True,
                                stream=True,
                            )
                    if not rag:
                        answer_text = (
                            "Uzhavar AI is still starting up. Please try again in a moment."
                            if q_lang == "English" else
                            "உழவர் AI தயாராகிறது. சிறிது நேரம் கழித்து மீண்டும் முயற்சிக்கவும்."
                        )
                        st.markdown(answer_text)
                    elif isinstance(result, str):            # demo / scheme-miss: instant template answer
                        deep_link = getattr(rag, "last_deep_link", None)
                        st.markdown(result.rsplit("\n\n---\n\n", 1)[0] if deep_link else result)
                        answer_text = result
                    else:                                    # LLM answer: tokens appear as they are generated
                        st.write_stream(result)
                        answer_text, deep_link = result.final_text, result.deep_link
            except Exception:
                contexts, deep_link = [], None
                answer_text = (
                    "Sorry, something went wrong while preparing the answer. Please ask again."
                    if q_lang == "English" else
                    "மன்னிக்கவும், பதிலைத் தயாரிக்கும்போது பிழை ஏற்பட்டது. மீண்டும் கேளுங்கள்."
                )
                st.markdown(answer_text)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer_text,
            "lang": q_lang,
            "sources": [
                {
                    "source": c["source"],
                    "page": c["page"],
                    "score": round(c.get("rerank_score", c.get("score", 0.0)), 4),
                    "scheme": c.get("scheme") if c.get("structured") else None,
                }
                for c in contexts
            ],
            "deep_link": deep_link,
            "route": getattr(rag, "last_route", None) if rag else None,
            "route_details": getattr(rag, "last_route_details", None) if rag else None,
        })
        if st.session_state.voice_mode:
            st.session_state.tts_auto_play_idx = len(st.session_state.messages) - 1
        st.session_state.pending_query = None      # always cleared, so the chat can never stay stuck
        st.session_state.scroll_once = True
        st.rerun()

    if active_query and not busy:
        st.session_state.tts_auto_play_idx = None      # new question: old answer must not auto-play again
        # Dynamically detect and extract farmer context (acres, water source, crop, docs) from query
        try:
            from app.schemes import extract_farmer_context
            st.session_state.farmer_info = extract_farmer_context(active_query, st.session_state.farmer_info)
        except Exception:
            pass
        st.session_state.messages.append({"role": "user", "content": active_query, "lang": lang})
        st.session_state.pending_query = {"q": active_query, "lang": lang}
        st.rerun()

    if not st.session_state.completion_spoken:
        st.session_state.completion_spoken = True
        # hidden player, fired after the page is drawn
        trigger_tts(SCRIPT["completion"][lang].format(name=farmer_name), lang, "completion_chat", show_controls=False)


# ============================================================
# APPLICATION ROUTING
# ============================================================
# st.empty() is emitted first on every run: it wipes the previous screen's leftover
# (faded) widgets immediately instead of after the whole script has finished.
_screen = st.empty()
if st.session_state.language is None:
    with _screen.container():
        view_language_splash()
elif st.session_state.onboarding_step != "done":
    with _screen.container():
        view_onboarding()
else:
    view_main_chat()
