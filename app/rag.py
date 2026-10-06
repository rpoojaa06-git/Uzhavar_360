from pathlib import Path
import re
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple

import pymupdf
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from .config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    TOP_K,
    RERANK_TOP_K,
    GEMINI_API_KEY,
    GEMINI_MODEL
)
from .schemes import evaluate_scheme_eligibility, detect_scheme_intent


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()

        if chunk:
            chunks.append(chunk)

        if end == len(words):
            break

        start = end - overlap

    return chunks


def pdf_chunks(pdf_path: Path):
    doc = pymupdf.open(pdf_path)

    try:
        for page_number, page in enumerate(doc, start=1):
            text = clean_text(page.get_text("text"))

            if not text:
                continue

            for chunk_index, chunk in enumerate(chunk_text(text)):
                yield {
                    "source": pdf_path.name,
                    "page": page_number,
                    "chunk_index": chunk_index,
                    "text": chunk
                }
    finally:
        doc.close()


def point_id(source: str, page: int, chunk_index: int) -> str:
    value = f"{source}|{page}|{chunk_index}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


class RAG:

    def __init__(self):
        if not QDRANT_URL:
            raise ValueError("QDRANT_URL is missing from .env")

        if not QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY is missing from .env")

        # Load models efficiently from local cache
        try:
            self.embedder = SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
        except Exception:
            self.embedder = SentenceTransformer(EMBEDDING_MODEL)

        try:
            self.reranker = CrossEncoder(RERANKER_MODEL, local_files_only=True)
        except Exception:
            self.reranker = CrossEncoder(RERANKER_MODEL)

        self.qdrant = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=300
        )

        self.llm = None

        if GEMINI_API_KEY:
            from google import genai
            self.llm = genai.Client(api_key=GEMINI_API_KEY)

    def _ensure_collection(self):
        dim = self.embedder.get_embedding_dimension()

        if not self.qdrant.collection_exists(COLLECTION_NAME):
            self.qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=dim,
                    distance=Distance.COSINE
                )
            )

    def _upsert(self, points):
        for attempt in range(3):
            try:
                self.qdrant.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points,
                    wait=True,
                    timeout=300
                )
                return

            except Exception:
                if attempt == 2:
                    raise

                time.sleep(3 * (attempt + 1))

    def ingest(self, data_dir: str = "data"):
        self._ensure_collection()
        total = 0
        batch_size = 8

        pdf_files = sorted(Path(data_dir).glob("*.pdf"))

        if not pdf_files:
            raise FileNotFoundError(
                f"No PDF files found in {Path(data_dir).resolve()}"
            )

        for pdf_path in pdf_files:
            print(f"Processing: {pdf_path.name}")

            items = list(pdf_chunks(pdf_path))

            if not items:
                print(f"Skipped: {pdf_path.name} (no text found)")
                continue

            for start in range(0, len(items), batch_size):
                batch_items = items[start:start + batch_size]
                texts = [item["text"] for item in batch_items]

                vectors = self.embedder.encode(
                    texts,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    batch_size=8
                )

                points = []

                for item, vector in zip(batch_items, vectors):
                    payload = {
                        **item,
                        "region": "Tamil Nadu",
                        "document_type": "agriculture"
                    }

                    points.append(
                        PointStruct(
                            id=point_id(
                                item["source"],
                                item["page"],
                                item["chunk_index"]
                            ),
                            vector=vector.tolist(),
                            payload=payload
                        )
                    )

                self._upsert(points)

                total += len(points)

                print(
                    f"Uploaded {start + len(points)}/{len(items)} "
                    f"chunks from {pdf_path.name}"
                )

        count = self.qdrant.count(
            collection_name=COLLECTION_NAME,
            exact=True
        ).count

        print(f"Total chunks in Qdrant: {count}")

        return total

    def retrieve(self, question: str):
        qvec = self.embedder.encode(
            question,
            normalize_embeddings=True
        ).tolist()

        results = self.qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=qvec,
            limit=TOP_K,
            with_payload=True
        ).points

        candidates = [
            {
                "text": r.payload["text"],
                "source": r.payload["source"],
                "page": r.payload["page"],
                "score": float(r.score)
            }
            for r in results
        ]

        if not candidates:
            return []

        pairs = [
            (question, c["text"])
            for c in candidates
        ]

        rerank_scores = self.reranker.predict(pairs)

        for c, score in zip(candidates, rerank_scores):
            c["rerank_score"] = float(score)

        candidates.sort(
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        return candidates[:RERANK_TOP_K]

    def answer(
        self,
        question: str,
        profile: dict,
        history: Optional[List[Dict[str, str]]] = None,
        return_details: bool = False
    ):
        """
        Generates context-aware, grounded agricultural guidance with multi-turn memory
        and farming journey stage awareness.
        """
        contexts = self.retrieve(question)

        # Evaluate potential scheme eligibility
        matched_schemes = evaluate_scheme_eligibility(question, profile)
        scheme_intent = detect_scheme_intent(question)
        top_scheme = matched_schemes[0] if (matched_schemes and (scheme_intent or matched_schemes[0]["potential_match"] >= 75)) else None

        if not contexts and not top_scheme:
            msg = "I could not find enough information in the trusted agricultural documents to answer this specific question."
            if return_details:
                return msg, [], [], None
            return msg, []

        context_text = "\n\n".join(
            f"[Source {i + 1}] {c['source']}, page {c['page']}\n{c['text']}"
            for i, c in enumerate(contexts)
        ) if contexts else "No direct PDF matches retrieved."

        profile_text = "\n".join(
            f"- {k}: {v}"
            for k, v in profile.items()
            if v not in (None, "", [])
        )

        language = profile.get("language") or "English"
        current_stage = profile.get("farming_stage") or "Planning"

        history_text = ""
        if history:
            formatted_turns = []
            for h in history[-6:]:  # Keep recent turns
                role = "Farmer" if h.get("role") in ["user", "farmer"] else "Uzhavar AI"
                formatted_turns.append(f"{role}: {h.get('content', '')}")
            history_text = "\n".join(formatted_turns)

        system = f"""
You are Uzhavar AI (உழவர் AI), an intelligent agricultural guide and farming journey companion for farmers in Tamil Nadu.

CORE RESPONSIBILITIES:
1. Provide grounded, reliable farming guidance using the retrieved agricultural documents (ICAR advisories, crop guides, drip irrigation manuals, farm machinery manuals).
2. Maintain awareness of the farmer's ongoing journey through these 10 stages:
   [1. Planning -> 2. Crop Selection -> 3. Land Preparation -> 4. Seed/Input Selection -> 5. Sowing -> 6. Crop Management -> 7. Pest/Disease Management -> 8. Harvest -> 9. Selling / Marketing -> 10. Next Season Planning]
3. Current Farmer Stage: "{current_stage}". Tailor recommendations specifically to this stage and the farmer's land scale, soil, water source, and crop.
4. Recommend the logical NEXT STEP in the farmer's journey at the end of your guidance.
5. Do NOT invent dosage, chemicals, or ungrounded claims. If data is limited in the documents, state so clearly.
6. Language: If requested language is Tamil or user asks in Tamil, reply in clear Tamil. If English, reply in English.
7. Government Schemes: Scheme matching is handled deterministically by the system. If government subsidies or schemes are relevant, briefly note that potential assistance may be available under government programs, and refer them to the scheme card displayed on screen. Never guarantee eligibility or official approval.

FARMER PROFILE & CONTEXT:
{profile_text}

RECENT CONVERSATION HISTORY:
{history_text if history_text else "None (Start of conversation)"}

RETRIEVED AGRICULTURAL SOURCES:
{context_text}
""".strip()

        if not self.llm:
            fallback = "\n\n".join(
                f"{c['source']} p.{c['page']}: {c['text']}"
                for c in contexts
            )
            if return_details:
                return fallback, contexts, matched_schemes, current_stage
            return fallback, contexts

        prompt_content = f"{system}\n\nFarmer Question:\n{question}"

        response = self.llm.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt_content
        )

        answer_text = response.text

        if return_details:
            return answer_text, contexts, (matched_schemes if top_scheme else []), current_stage

        return answer_text, contexts