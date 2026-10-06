# 🌾 Uzhavar AI (Uzhavar 360)
### Intelligent Farmer Journey & Grounded Scheme Discovery Platform

**Uzhavar AI** is a conversational AI platform and digital companion for farmers in Tamil Nadu. It provides personalized, grounded agricultural guidance throughout their complete farming journey and contextually discovers government schemes based on their profile and farming needs.

---

## 🌟 Key Features

1. **🌾 Conversational Agricultural Assistant**: Natural language guidance in English, தமிழ் (Tamil), and Tanglish.
2. **🌱 10-Stage Farmer Journey Tracker**: Visual step-by-step guidance from Planning through Harvest and Marketing.
3. **👨‍🌾 Dynamic Farmer Profile**: Remembers district (all 38 TN districts), land scale (Marginal/Small/Large), irrigation source, crop, and ownership.
4. **📚 Grounded RAG (Retrieval-Augmented Generation)**: Answers are strictly grounded in verified ICAR & TNAU agricultural manuals with page-level citations.
5. **🏛️ Deterministic Scheme Discovery**: Rules-based eligibility engine that checks government subsidies (PMKSY, SMAM, Solar Pumps, KAVIADP, PMFBY) without LLM hallucinations.
6. **🔗 Uzhavar Platform Connection**: Direct hand-off link to official government/Uzhavar portals for application filing.

---

## 🏗️ Architecture Overview

```
Farmer / User (Question + Profile Context + Journey Stage)
                          │
                          ▼
            Streamlit Web App / FastAPI Backend
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
    [Agricultural Guidance]   [Scheme Discovery]
              │                       │
      Dense Embedding (bge-m3)  Deterministic Rules Engine
              │                 (District, Acres, Crop, Tier)
    Qdrant Vector DB (1,353 chunks)   │
              │                 Potential Match Score (%)
    Cross-Encoder Reranker            │
              │                       │
              └───────────┬───────────┘
                          ▼
                Google Gemini 2.5 Flash
                          │
                          ▼
        Personalized Grounded Answer + Scheme Card
                          │
                [ Continue to Uzhavar ]
```

For complete technical specifications, see [UZHAVAR_AI_DOCUMENTATION.md](UZHAVAR_AI_DOCUMENTATION.md).

---

## 📁 Project Structure

```text
uzhavar_ai_rag/
├── app/
│   ├── config.py              # Model and database configuration
│   ├── models.py              # Pydantic schemas (Profile, Stages, Schemes)
│   ├── rag.py                 # RAG pipeline (Retrieval, Rerank, Gemini generation)
│   ├── schemes.py             # Deterministic scheme eligibility engine
│   ├── main.py                # FastAPI REST API endpoints
│   └── streamlit_app.py       # App launcher shim
├── data/                      # Verified agricultural knowledge PDFs
├── scripts/                   # Remote ingestion notebook & utilities
├── streamlit_app.py           # Main interactive Streamlit application
├── UZHAVAR_AI_DOCUMENTATION.md# Comprehensive architectural documentation
├── .streamlit/config.toml     # Optimized Streamlit configuration
├── .env.example               # Environment variables template
├── requirements.txt           # Project dependencies
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone & Set Up Virtual Environment

```powershell
git clone https://github.com/rpoojaa06-git/Uzhavar_360.git
cd Uzhavar_360

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file based on `.env.example`:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite

QDRANT_URL=your_qdrant_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
COLLECTION_NAME=uzhavar_agri

EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
TOP_K=8
RERANK_TOP_K=4
```

### 3. Launch the Streamlit Web Application

```powershell
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser.

### 4. (Optional) Run the FastAPI REST Server

```powershell
uvicorn app.main:app --reload --port 8000
```

API documentation will be available at `http://127.0.0.1:8000/docs`.

---

## 📜 Trust & Safety Notice

Scheme recommendations are based on information provided by the farmer and represent an indication of potential eligibility. Final eligibility verification and subsidy sanctioning are conducted exclusively by the Department of Agriculture / official Uzhavar platform.
