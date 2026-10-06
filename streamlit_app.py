import streamlit as st
import time
from typing import List, Dict, Any, Optional

# Set page configuration first
st.set_page_config(
    page_title="Uzhavar AI — Intelligent Farmer Journey & Scheme Discovery",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
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

# Tamil Nadu Districts list
TN_DISTRICTS = [
    "Thanjavur", "Tiruvarur", "Nagapattinam", "Mayiladuthurai", "Coimbatore",
    "Madurai", "Tiruchirappalli", "Salem", "Erode", "Dindigul", "Tirunelveli",
    "Theni", "Cuddalore", "Villupuram", "Kallakurichi", "Dharmapuri", "Krishnagiri",
    "Namakkal", "Pudukkottai", "Ramanathapuram", "Sivaganga", "Tenkasi", "Thoothukudi",
    "Karur", "Ariyalur", "Perambalur", "Tirupathur", "Ranipet", "Vellore", "Tiruvannamalai",
    "Kancheepuram", "Chengalpattu", "Tiruvallur", "Kanniyakumari", "Nilgiris", "Virudhunagar"
]

CROPS_LIST = [
    "Paddy (நெல்)", "Tomato (தக்காளி)", "Sugarcane (கரும்பு)", "Banana (வாழை)",
    "Cotton (பருத்தி)", "Maize (மக்காச்சோளம்)", "Groundnut (நிலக்கடலை)", "Chilli (மிளகாய்)",
    "Brinjal (கத்தரிக்காய்)", "Coconut (தென்னை)", "Pulses (பயறு வகைகள்)", "Millets (சிறு தானியங்கள்)",
    "Vegetables (காய்கறிகள்)", "Other / Not Decided Yet"
]

WATER_SOURCES = [
    "Borewell (ஆழ்துளை கிணறு)", "Canal / River (ஆற்றுப்பாசனம் / வாய்க்கால்)",
    "Open Well (திறந்தவெளி கிணறு)", "Drip / Micro-Irrigation (சொட்டுநீர் பாசனம்)",
    "Rainfed / Dryland (மானாவாரி)"
]

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

if "farmer_district" not in st.session_state:
    st.session_state.farmer_district = "Thanjavur"

if "farmer_land" not in st.session_state:
    st.session_state.farmer_land = 2.0

if "farmer_crop" not in st.session_state:
    st.session_state.farmer_crop = "Paddy (நெல்)"

if "farmer_water" not in st.session_state:
    st.session_state.farmer_water = "Borewell (ஆழ்துளை கிணறு)"

if "farmer_ownership" not in st.session_state:
    st.session_state.farmer_ownership = "Owner"

if "farmer_goal" not in st.session_state:
    st.session_state.farmer_goal = "Maximize yield and explore water-saving methods"

if "language" not in st.session_state:
    st.session_state.language = "English"


# ---------------- SIDEBAR: FARMER PROFILE & CONTEXT ----------------
with st.sidebar:
    st.markdown("### 👨‍🌾 Farmer & Farm Profile")
    st.caption("Personalizing agricultural advice and scheme eligibility.")

    # Quick Preset Profiles
    st.markdown("##### ⚡ Quick Presets")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("🌾 Paddy Delta", use_container_width=True, help="3 ac Paddy in Thanjavur (Canal)"):
            st.session_state.farmer_district = "Thanjavur"
            st.session_state.farmer_land = 3.0
            st.session_state.farmer_crop = "Paddy (நெல்)"
            st.session_state.farmer_water = "Canal / River (ஆற்றுப்பாசனம் / வாய்க்கால்)"
            st.session_state.farmer_stage = "Land Preparation"
            st.rerun()
    with col_p2:
        if st.button("🍅 Veg Drip", use_container_width=True, help="2 ac Tomato in Coimbatore (Borewell)"):
            st.session_state.farmer_district = "Coimbatore"
            st.session_state.farmer_land = 2.0
            st.session_state.farmer_crop = "Tomato (தக்காளி)"
            st.session_state.farmer_water = "Borewell (ஆழ்துளை கிணறு)"
            st.session_state.farmer_stage = "Crop Selection"
            st.rerun()

    st.divider()

    # Profile Inputs
    farmer_name = st.text_input("Farmer Name", value="Ramasamy", help="Name or farm reference")

    district = st.selectbox(
        "Location / District (மாவட்டம்)",
        TN_DISTRICTS,
        index=TN_DISTRICTS.index(st.session_state.farmer_district) if st.session_state.farmer_district in TN_DISTRICTS else 0
    )
    st.session_state.farmer_district = district

    land_acres = st.number_input(
        "Farm Land Size (Acres / ஏக்கர்)",
        min_value=0.25,
        max_value=100.0,
        value=float(st.session_state.farmer_land),
        step=0.5
    )
    st.session_state.farmer_land = land_acres

    # Calculate Farmer Category automatically
    if land_acres <= 2.5:
        farmer_category = "Marginal Farmer (குறு விவசாயி)"
        cat_key = "marginal"
    elif land_acres <= 5.0:
        farmer_category = "Small Farmer (சிறு விவசாயி)"
        cat_key = "small"
    else:
        farmer_category = "Medium / Large Farmer (பெரிய விவசாயி)"
        cat_key = "large"

    st.info(f"🏷️ **Category:** {farmer_category}")

    ownership = st.selectbox(
        "Land Ownership",
        ["Owner (சொந்த நிலம்)", "Tenant Farmer (குத்தகை)", "Leased (ஒப்பந்த விவசாயம்)"]
    )
    st.session_state.farmer_ownership = ownership

    crop_val = st.selectbox(
        "Primary Crop (பயிர்)",
        CROPS_LIST,
        index=CROPS_LIST.index(st.session_state.farmer_crop) if st.session_state.farmer_crop in CROPS_LIST else 0
    )
    st.session_state.farmer_crop = crop_val

    water_source = st.selectbox(
        "Water Source / Irrigation (நீர் ஆதாரம்)",
        WATER_SOURCES,
        index=WATER_SOURCES.index(st.session_state.farmer_water) if st.session_state.farmer_water in WATER_SOURCES else 0
    )
    st.session_state.farmer_water = water_source

    farming_goal = st.text_input(
        "Current Farming Goal",
        value=st.session_state.farmer_goal,
        placeholder="e.g. Install drip irrigation, buy power tiller, control weeds"
    )
    st.session_state.farmer_goal = farming_goal

    lang = st.radio(
        "Response Language",
        ["English", "தமிழ் (Tamil)", "Tanglish"],
        horizontal=True
    )
    st.session_state.language = lang

    st.divider()

    # Clear Chat History Button
    if st.button("🗑️ Reset Chat Conversation", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Vanakkam! Conversation reset. How can I guide you on your farm today?",
                "sources": [],
                "schemes": []
            }
        ]
        st.rerun()

    # System Status Expander
    with st.expander("ℹ️ Knowledge Base & System Info"):
        st.write("**Indexed Verified Sources:**")
        st.caption("• Crop production.pdf\n• drip_irrigation.pdf\n• Farm Machinery.pdf\n• ICAR Kharif Agro-Advisories 2025\n• Principles and Practices of Weed Management")
        st.write("**Qdrant Vector DB:** 1,353 chunks")
        st.write(f"**Embedder:** BAAI/bge-m3")
        st.write(f"**Reranker:** BAAI/bge-reranker-v2-m3")


# ---------------- MAIN CONTENT AREA ----------------

# Header Banner
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown('<div class="main-title">🌾 Uzhavar AI — உழவர் AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Intelligent Farmer Journey Companion & Grounded Agricultural Guidance with Contextual Government Scheme Discovery</div>',
        unsafe_allow_html=True
    )
with col_h2:
    st.markdown(f"**District:** {st.session_state.farmer_district}<br>**Land:** {st.session_state.farmer_land} ac", unsafe_allow_html=True)

# ---------------- 10-STAGE FARMER JOURNEY TRACKER ----------------
current_stage_idx = FARMING_STAGES.index(st.session_state.farmer_stage) if st.session_state.farmer_stage in FARMING_STAGES else 0

st.markdown('<div class="journey-container">', unsafe_allow_html=True)
col_j_title, col_j_select = st.columns([2, 1])
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

# Stage-specific guidance hint
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


# ---------------- SUGGESTED QUESTIONS (Pills / Buttons) ----------------
st.markdown("##### 💡 Suggested Farming Questions:")
col_q1, col_q2, col_q3 = st.columns(3)
col_q4, col_q5, col_q6 = st.columns(3)

chosen_prompt = None

with col_q1:
    if st.button("🌱 How do I start farming?", use_container_width=True):
        chosen_prompt = "How do I start farming? What are the key first steps for my land?"
with col_q2:
    if st.button(f"🌾 What crop suits {st.session_state.farmer_land} ac?", use_container_width=True):
        chosen_prompt = f"I have {st.session_state.farmer_land} acres in {st.session_state.farmer_district}. What crop should I grow?"
with col_q3:
    if st.button("🚜 What machinery do I need?", use_container_width=True):
        clean_crop = st.session_state.farmer_crop.split("(")[0].strip()
        chosen_prompt = f"What machinery is required for {clean_crop} on {st.session_state.farmer_land} acres?"
with col_q4:
    if st.button("💧 How to install drip irrigation?", use_container_width=True):
        chosen_prompt = "How can I install drip irrigation? How much water does it save?"
with col_q5:
    if st.button("🐛 How can I control pests & weeds?", use_container_width=True):
        clean_crop = st.session_state.farmer_crop.split("(")[0].strip()
        chosen_prompt = f"What are the best methods to control pests and weeds in {clean_crop}?"
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
                        <b>Why this may match your farm:</b>
                        {"".join(f"<div class='reason-item'>✓ {reason}</div>" for reason in scheme['reasons'])}
                    </div>
                    <div class="disclaimer-box">
                        ⚠️ <b>Statutory Notice:</b> {scheme['disclaimer']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_btn, _ = st.columns([2, 3])
                with col_btn:
                    if st.button(f"🔗 [ Continue to Uzhavar ]", key=f"btn_{scheme['scheme_id']}_{time.time()}"):
                        st.success(
                            f"✅ Directing to Uzhavar Portal destination: `{scheme['official_url']}`\n\n"
                            "*(Prototype Mode: In production, this links securely to the official Uzhavar application)*"
                        )

        # Display Citations / Sources if present
        if msg.get("sources"):
            with st.expander(f"📚 Verified Knowledge Sources ({len(msg['sources'])} citations)"):
                for s in msg["sources"]:
                    st.markdown(
                        f"• **{s['source']}** (Page {s['page']}) — *Relevance Score: {s['score']}*"
                    )


# ---------------- CHAT INPUT & EXECUTION ----------------
user_query = st.chat_input("Ask any farming or scheme question (e.g. 'How to start tomato nursery?')")

# If a quick prompt button was clicked, use it
if chosen_prompt:
    user_query = chosen_prompt

if user_query:
    # 1. Append user message to state
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user", avatar="👨‍🌾"):
        st.markdown(user_query)

    # 2. Build profile dict
    profile_dict = {
        "farmer_name": farmer_name,
        "district": st.session_state.farmer_district,
        "land_acres": st.session_state.farmer_land,
        "farmer_category": cat_key,
        "crop": st.session_state.farmer_crop.split("(")[0].strip(),
        "farming_stage": st.session_state.farmer_stage,
        "water_source": st.session_state.farmer_water.split("(")[0].strip(),
        "ownership": st.session_state.farmer_ownership,
        "goal": st.session_state.farmer_goal,
        "language": st.session_state.language
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
                answer = "Uzhavar AI engine is currently in preview mode. Please check Qdrant/Gemini configuration."
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
                            <b>Why this may match your farm:</b>
                            {"".join(f"<div class='reason-item'>✓ {reason}</div>" for reason in scheme['reasons'])}
                        </div>
                        <div class="disclaimer-box">
                            ⚠️ <b>Statutory Notice:</b> {scheme['disclaimer']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col_btn, _ = st.columns([2, 3])
                    with col_btn:
                        if st.button(f"🔗 [ Continue to Uzhavar ]", key=f"btn_new_{scheme['scheme_id']}_{time.time()}"):
                            st.success(
                                f"✅ Directing to Uzhavar Portal destination: `{scheme['official_url']}`\n\n"
                                "*(Prototype Mode: In production, this links securely to the official Uzhavar application)*"
                            )

            # Display Citations
            if contexts:
                with st.expander(f"📚 Verified Knowledge Sources ({len(contexts)} citations)"):
                    for c in contexts:
                        st.markdown(
                            f"• **{c['source']}** (Page {c['page']}) — *Relevance Score: {round(c.get('rerank_score', c.get('score', 0.0)), 4)}*"
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
