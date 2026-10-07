import streamlit as st
import time

# Set page configuration first
st.set_page_config(
    page_title="Uzhavar AI — Intelligent Farmer Journey & Scheme Discovery",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Agricultural Branding & Polished UI
st.markdown("""
<style>
    /* Primary color variables & fonts */
    :root {
        --agri-dark: #1b5e20;
        --agri-primary: #2e7d32;
        --agri-light: #e8f5e9;
        --agri-accent: #f57f17;
        --agri-border: #c8e6c9;
    }

    .main-title {
        color: #1b5e20;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #4b6b4e;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }

    /* Farmer Journey Stage Indicator */
    .journey-container {
        background: linear-gradient(135deg, #f1f8e9 0%, #e8f5e9 100%);
        border: 1px solid #c8e6c9;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .journey-title {
        font-weight: 700;
        color: #1b5e20;
        font-size: 0.95rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .stage-pill {
        display: inline-block;
        padding: 4px 10px;
        margin: 2px 3px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .stage-completed {
        background-color: #c8e6c9;
        color: #1b5e20;
        border: 1px solid #81c784;
    }
    .stage-current {
        background-color: #2e7d32;
        color: #ffffff !important;
        box-shadow: 0 0 6px rgba(46,125,50,0.4);
    }
    .stage-upcoming {
        background-color: #f5f5f5;
        color: #757575;
        border: 1px solid #e0e0e0;
    }

    /* Scheme Recommendation Card */
    .scheme-card {
        background: #ffffff;
        border: 2px solid #2e7d32;
        border-radius: 12px;
        padding: 18px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(46,125,50,0.12);
    }
    .scheme-badge {
        background: #e8f5e9;
        color: #1b5e20;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 8px;
        border: 1px solid #81c784;
    }
    .scheme-title {
        color: #1b5e20;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .scheme-tamil {
        color: #558b2f;
        font-size: 0.95rem;
        font-weight: 500;
        margin-bottom: 10px;
    }
    .match-pill {
        background: #ffecb3;
        color: #e65100;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        float: right;
    }
    .reason-item {
        color: #2e7d32;
        font-weight: 500;
        margin: 4px 0;
        font-size: 0.9rem;
    }
    .disclaimer-box {
        font-size: 0.78rem;
        color: #616161;
        background: #fafafa;
        border-left: 3px solid #ffa000;
        padding: 8px 12px;
        margin-top: 12px;
        border-radius: 4px;
    }

    /* Citation / Source box */
    .source-tag {
        background: #f1f8e9;
        color: #33691e;
        border: 1px solid #dcedc8;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Import lightweight scheme helpers and stages
try:
    from app.models import FARMING_STAGES
    from app.schemes import evaluate_scheme_eligibility, detect_scheme_intent, TAMIL_NADU_SCHEMES
except ImportError:
    import sys
    sys.path.append(".")
    from app.models import FARMING_STAGES
    from app.schemes import evaluate_scheme_eligibility, detect_scheme_intent, TAMIL_NADU_SCHEMES


@st.cache_resource(show_spinner=False)
def get_rag_engine():
    """Cache the heavy RAG models once in memory on-demand."""
    try:
        from app.rag import RAG
        return RAG()
    except Exception as e:
        st.error(f"⚠️ Error initializing RAG Engine: {e}")
        return None


# Default profile — to be replaced by voice input in future
DEFAULT_PROFILE = {
    "district": None,
    "land_acres": None,
    "farmer_category": None,
    "crop": None,
    "water_source": None,
    "ownership": None,
    "goal": None,
    "language": "English",
    "farming_stage": "Planning"
}

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Vanakkam! 🙏 I am **Uzhavar AI (உழவர் AI)**, your personalized farming companion and digital guide.\n\n"
                "I guide you throughout your entire agricultural journey — from crop selection, soil and water management, "
                "to farm machinery, pest control, and government subsidies.\n\n"
                "**How can I help you today?** Feel free to ask a question below or choose a suggested topic!"
            ),
            "sources": [],
            "schemes": []
        }
    ]

if "farmer_stage" not in st.session_state:
    st.session_state.farmer_stage = "Planning"

# ---------------- SIDEBAR: Only System Info ----------------
with st.sidebar:
    st.markdown("### ℹ️ System Info")

    if st.button("🗑️ Reset Conversation", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Vanakkam! Conversation reset. How can I guide you on your farm today?",
                "sources": [],
                "schemes": []
            }
        ]
        st.session_state.farmer_stage = "Planning"
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
        st.write("**Vector DB:** 1,353 verified chunks")
        st.write("**Embedder:** BAAI/bge-m3")
        st.write("**Reranker:** BAAI/bge-reranker-v2-m3")


# ---------------- MAIN CONTENT AREA ----------------

# Header
st.markdown('<div class="main-title">🌾 Uzhavar AI — உழவர் AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Intelligent Farmer Journey Companion & Grounded Agricultural Guidance with Contextual Government Scheme Discovery</div>',
    unsafe_allow_html=True
)

# ---------------- 10-STAGE FARMER JOURNEY TRACKER ----------------
current_stage_idx = FARMING_STAGES.index(st.session_state.farmer_stage) if st.session_state.farmer_stage in FARMING_STAGES else 0

st.markdown('<div class="journey-container">', unsafe_allow_html=True)
col_j_title, col_j_select = st.columns([3, 1])
with col_j_title:
    st.markdown(
        f'<div class="journey-title">🌱 <b>FARMER JOURNEY STAGE TRACKER</b> — Current Active Stage: <span style="color:#2e7d32; font-weight:800;">{st.session_state.farmer_stage}</span> (Stage {current_stage_idx + 1}/10)</div>',
        unsafe_allow_html=True
    )
with col_j_select:
    new_stage = st.selectbox(
        "Update Farming Stage",
        FARMING_STAGES,
        index=current_stage_idx,
        label_visibility="collapsed",
        key="stage_selector"
    )
    if new_stage != st.session_state.farmer_stage:
        st.session_state.farmer_stage = new_stage
        st.rerun()

# Render interactive stage pills
pills_html = ""
for idx, stage_name in enumerate(FARMING_STAGES):
    if idx < current_stage_idx:
        pills_html += f'<span class="stage-pill stage-completed">✓ {stage_name}</span>'
    elif idx == current_stage_idx:
        pills_html += f'<span class="stage-pill stage-current">● {stage_name}</span>'
    else:
        pills_html += f'<span class="stage-pill stage-upcoming">○ {stage_name}</span>'

st.markdown(pills_html, unsafe_allow_html=True)

STAGE_TIPS = {
    "Planning": "💡 Focus: Soil testing, financial planning, climate suitability, water resource audit.",
    "Crop Selection": "💡 Focus: Matching crop variety with soil type, market demand, and water availability.",
    "Land Preparation": "💡 Focus: Primary plowing, summer ploughing, levelling, FYM / bio-fertilizer application.",
    "Seed/Input Selection": "💡 Focus: Certified seeds, seed treatment with Trichoderma viride or Azospirillum.",
    "Sowing": "💡 Focus: Spacing, seed rate, nursery raising, machine transplanting or direct seeding.",
    "Crop Management": "💡 Focus: Drip fertigation, intercultural weeding, mulching, micro-nutrients.",
    "Pest/Disease Management": "💡 Focus: Integrated Pest Management (IPM), yellow sticky traps, neem oil, bio-control.",
    "Harvest": "💡 Focus: Optimal moisture content, mechanical harvesting, post-harvest threshing.",
    "Selling / Marketing": "💡 Focus: Uzhavar Sandhai, e-NAM, MSP procurement centers, direct FPO marketing.",
    "Next Season Planning": "💡 Focus: Crop rotation with pulses for nitrogen fixation, soil replenishment."
}
st.caption(STAGE_TIPS.get(st.session_state.farmer_stage, "Follow stage advisories."))
st.markdown('</div>', unsafe_allow_html=True)


# ---------------- SUGGESTED QUESTIONS ----------------
st.markdown("##### 💡 Suggested Farming Questions:")
col_q1, col_q2, col_q3 = st.columns(3)
col_q4, col_q5, col_q6 = st.columns(3)

chosen_prompt = None

with col_q1:
    if st.button("🌱 How do I start farming?", use_container_width=True):
        chosen_prompt = "How do I start farming? What are the key first steps?"
with col_q2:
    if st.button("🌾 What crop should I grow?", use_container_width=True):
        chosen_prompt = "What crop should I grow? Help me choose the right crop."
with col_q3:
    if st.button("🚜 What machinery do I need?", use_container_width=True):
        chosen_prompt = "What farm machinery do I need and how do I use it?"
with col_q4:
    if st.button("💧 How to install drip irrigation?", use_container_width=True):
        chosen_prompt = "How can I install drip irrigation? How much water does it save?"
with col_q5:
    if st.button("🐛 How can I control pests & weeds?", use_container_width=True):
        chosen_prompt = "What are the best methods to control pests and weeds in my farm?"
with col_q6:
    if st.button("🏛️ Are there subsidies for my farm?", use_container_width=True):
        chosen_prompt = "Am I eligible for a drip irrigation or machinery subsidy from the government?"


# ---------------- CHAT HISTORY DISPLAY ----------------
for msg in st.session_state.messages:
    role = msg["role"]
    avatar = "👨‍🌾" if role == "user" else "🌾"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

        # Display Scheme Card if present
        if msg.get("schemes"):
            for scheme in msg["schemes"]:
                st.markdown(f"""
                <div class="scheme-card">
                    <span class="match-pill">🎯 Potential Match: {scheme['potential_match']}%</span>
                    <span class="scheme-badge">🏛️ {scheme['category']} Government Scheme</span>
                    <div class="scheme-title">{scheme['name']}</div>
                    <div class="scheme-tamil">{scheme.get('tamil_name', '')}</div>
                    <p style="font-size: 0.92rem; color: #424242; margin-bottom: 8px;">{scheme['description']}</p>
                    <p style="font-size: 0.9rem; font-weight: 600; color: #1b5e20;"><b>Subsidy Details:</b> {scheme['subsidy_details']}</p>
                    <div style="margin-top: 10px;">
                        <b>Why this may match:</b>
                        {"".join(f"<div class='reason-item'>✓ {reason}</div>" for reason in scheme['reasons'])}
                    </div>
                    <div class="disclaimer-box">
                        ⚠️ <b>Statutory Notice:</b> {scheme['disclaimer']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_btn, _ = st.columns([2, 3])
                with col_btn:
                    if st.button("🔗 [ Continue to Uzhavar ]", key=f"btn_{scheme['scheme_id']}_{time.time()}"):
                        st.success(
                            f"✅ Directing to Uzhavar Portal: `{scheme['official_url']}`\n\n"
                            "*(Prototype Mode: In production, this links to the official Uzhavar application)*"
                        )

        # Display Citations
        if msg.get("sources"):
            with st.expander(f"📚 Verified Sources ({len(msg['sources'])} citations)"):
                for s in msg["sources"]:
                    st.markdown(f"• **{s['source']}** (Page {s['page']}) — *Relevance: {s['score']}*")


# ---------------- CHAT INPUT & EXECUTION ----------------
user_query = st.chat_input("Ask any farming or scheme question (e.g. 'How to start tomato nursery?')")

if chosen_prompt:
    user_query = chosen_prompt

if user_query:
    # 1. Append user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user", avatar="👨‍🌾"):
        st.markdown(user_query)

    # 2. Build minimal profile — profile info will come from voice in future
    profile_dict = {
        **DEFAULT_PROFILE,
        "farming_stage": st.session_state.farmer_stage,
    }

    # 3. Build history turns for conversation memory
    chat_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    # 4. Generate answer and evaluate schemes
    with st.chat_message("assistant", avatar="🌾"):
        with st.spinner("🔍 Consulting verified agricultural guides & checking scheme criteria..."):
            rag = get_rag_engine()
            if rag:
                answer, contexts, matched_schemes, stage = rag.answer(
                    question=user_query,
                    profile=profile_dict,
                    history=chat_history,
                    return_details=True
                )
            else:
                answer = "Uzhavar AI engine is initializing. Please check Qdrant/Gemini configuration."
                contexts = []
                matched_schemes = evaluate_scheme_eligibility(user_query, profile_dict)
                stage = st.session_state.farmer_stage

            st.markdown(answer)

            # Display Schemes if relevant
            if matched_schemes:
                for scheme in matched_schemes:
                    st.markdown(f"""
                    <div class="scheme-card">
                        <span class="match-pill">🎯 Potential Match: {scheme['potential_match']}%</span>
                        <span class="scheme-badge">🏛️ {scheme['category']} Government Scheme</span>
                        <div class="scheme-title">{scheme['name']}</div>
                        <div class="scheme-tamil">{scheme.get('tamil_name', '')}</div>
                        <p style="font-size: 0.92rem; color: #424242; margin-bottom: 8px;">{scheme['description']}</p>
                        <p style="font-size: 0.9rem; font-weight: 600; color: #1b5e20;"><b>Subsidy Details:</b> {scheme['subsidy_details']}</p>
                        <div style="margin-top: 10px;">
                            <b>Why this may match:</b>
                            {"".join(f"<div class='reason-item'>✓ {reason}</div>" for reason in scheme['reasons'])}
                        </div>
                        <div class="disclaimer-box">
                            ⚠️ <b>Statutory Notice:</b> {scheme['disclaimer']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col_btn, _ = st.columns([2, 3])
                    with col_btn:
                        if st.button("🔗 [ Continue to Uzhavar ]", key=f"btn_new_{scheme['scheme_id']}_{time.time()}"):
                            st.success(
                                f"✅ Directing to Uzhavar Portal: `{scheme['official_url']}`\n\n"
                                "*(Prototype Mode: In production, this links to the official Uzhavar application)*"
                            )

            # Display Citations
            if contexts:
                with st.expander(f"📚 Verified Sources ({len(contexts)} citations)"):
                    for c in contexts:
                        st.markdown(
                            f"• **{c['source']}** (Page {c['page']}) — *Relevance: {round(c.get('rerank_score', c.get('score', 0.0)), 4)}*"
                        )

            # Save to messages state
            sources_to_store = [
                {
                    "source": c["source"],
                    "page": c["page"],
                    "score": round(c.get("rerank_score", c.get("score", 0.0)), 4)
                }
                for c in contexts
            ]

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources_to_store,
                "schemes": matched_schemes
            })
