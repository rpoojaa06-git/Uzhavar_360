from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
from .models import ChatRequest, ChatResponse, Source, DeepLink, FARMING_STAGES
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
def ingest(collection: str = "agri"):
    """Re-ingest corpora: collection="agri" (default, data/) or "schemes"
    (data/schemes/ — TN Farmer Welfare Citizen Charter)."""
    if collection == "schemes":
        from .config import COLLECTION_SCHEMES
        count = rag.ingest("data/schemes", collection=COLLECTION_SCHEMES, scheme_headings=True)
    else:
        count = rag.ingest("data")
    return {"status": "ok", "collection": collection, "chunks_indexed": count}


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

    # The deep link into the demo UI was already appended to `answer` by the
    # RAG layer; the structured payload is retained on the engine instance.
    dl = getattr(rag, "last_deep_link", None)
    deep_link = None
    if dl:
        deep_link = DeepLink(
            id=dl["id"],
            label_en=dl["label_en"],
            label_ta=dl["label_ta"],
            emoji=dl["emoji"],
            url=dl["url"],
            spoken=dl["spoken"],
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
        next_step_recommendation="Consult local agricultural officer or check next stage advisories.",
        deep_link=deep_link,
        route=getattr(rag, "last_route", None),
    )


@app.get("/schemes")
def list_schemes(department: Optional[str] = None, category: Optional[str] = None):
    """Retrieve all available schemes, optionally filtered by department or category."""
    from .schemes import load_all_schemes
    schemes = load_all_schemes()
    if department:
        schemes = [s for s in schemes if (s.get("department") or "").lower() == department.lower()]
    if category:
        schemes = [s for s in schemes if (s.get("category") or "").lower() == category.lower()]
    return {"total": len(schemes), "schemes": schemes}


@app.get("/schemes/search")
def search_schemes_api(q: str, lang: str = "English", limit: int = 5):
    """Search schemes using keyword / concept matching in Tamil or English."""
    from .schemes import search_schemes
    results = search_schemes(query=q, lang=lang, limit=limit)
    return {"query": q, "total": len(results), "matches": results}


@app.post("/schemes/recommend")
@app.post("/eligibility/check")
def recommend_schemes_api(profile: Dict[str, Any], limit: int = 4):
    """Deterministic eligibility check and recommendation for a farmer profile."""
    from .schemes import recommend_schemes
    recommendations = recommend_schemes(profile=profile, limit=limit)
    return {"profile": profile, "total": len(recommendations), "recommended_schemes": recommendations}

