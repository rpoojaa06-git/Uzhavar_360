from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
from .models import ChatRequest, ChatResponse, Source, FARMING_STAGES
from .rag import RAG

app = FastAPI(
    title="Uzhavar AI — Intelligent Farmer Agricultural Guidance API",
    description="Conversational agricultural guidance grounded in verified ICAR & TNAU knowledge."
)

rag = RAG()


@app.get("/health")
def health():
    return {"status": "ok", "service": "Uzhavar AI"}


@app.get("/stages")
def get_farming_stages():
    return {"stages": FARMING_STAGES}


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

    answer, contexts, _, stage = rag.answer(
        question=request.question,
        profile=profile,
        history=history,
        return_details=True
    )

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
        next_step_recommendation="Consult local agricultural officer or check next stage advisories."
    )
