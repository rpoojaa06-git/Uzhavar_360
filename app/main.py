from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
from .models import ChatRequest, ChatResponse, Source, SchemeRecommendation, FARMING_STAGES
from .rag import RAG
from .schemes import evaluate_scheme_eligibility, TAMIL_NADU_SCHEMES

app = FastAPI(
    title="Uzhavar AI — Intelligent Farmer Journey & Scheme Discovery API",
    description="Conversational agricultural guidance grounded in verified ICAR & TNAU knowledge with contextual scheme eligibility evaluation."
)

rag = RAG()


@app.get("/health")
def health():
    return {"status": "ok", "service": "Uzhavar AI"}


@app.get("/stages")
def get_farming_stages():
    return {"stages": FARMING_STAGES}


@app.get("/schemes")
def get_all_schemes():
    return {"schemes": TAMIL_NADU_SCHEMES}


@app.post("/eligibility/check")
def check_eligibility(query: str, profile: dict):
    matches = evaluate_scheme_eligibility(query, profile)
    return {"matches": matches}


@app.post("/ingest")
def ingest():
    count = rag.ingest("data")
    return {"status": "ok", "chunks_indexed": count}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")

    # Build comprehensive profile
    if request.profile:
        profile = request.profile.model_dump()
    else:
        profile = {
            "language": request.language or "English",
            "district": request.district or "Thanjavur",
            "land_acres": request.land_acres if request.land_acres is not None else 2.0,
            "crop": request.crop or "Paddy",
            "farming_stage": request.stage or "Planning",
            "water_source": request.water_source or "Borewell",
        }

    history = [m.model_dump() for m in request.history] if request.history else []

    answer, contexts, matched_schemes, stage = rag.answer(
        question=request.question,
        profile=profile,
        history=history,
        return_details=True
    )

    scheme_card = None
    if matched_schemes:
        top_scheme = matched_schemes[0]
        scheme_card = SchemeRecommendation(**top_scheme)

    return ChatResponse(
        answer=answer,
        sources=[
            Source(
                source=c["source"],
                page=c["page"],
                score=round(c.get("rerank_score", c.get("score", 0.0)), 4)
            )
            for c in contexts
        ],
        current_stage=stage,
        next_step_recommendation="Consult local agricultural officer or check next stage advisories.",
        scheme_card=scheme_card
    )
