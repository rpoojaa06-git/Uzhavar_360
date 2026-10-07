import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

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

        # Load embedding model from local cache first
        try:
            self.embedder = SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
        except Exception:
            self.embedder = SentenceTransformer(EMBEDDING_MODEL)

        # Load reranker model with local cache to eliminate unauthenticated HF warnings
        try:
            self.reranker = CrossEncoder(RERANKER_MODEL, automodel_args={"local_files_only": True})
        except Exception:
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
            print("No PDF files found.")
            return 0

        for pdf_path in pdf_files:
            batch = []

            for chunk_data in pdf_chunks(pdf_path):
                batch.append(chunk_data)

                if len(batch) >= batch_size:
                    texts = [c["text"] for c in batch]

                    embeddings = self.embedder.encode(
                        texts,
                        batch_size=batch_size,
                        show_progress_bar=False,
                        normalize_embeddings=True
                    ).tolist()

                    points = [
                        PointStruct(
                            id=point_id(c["source"], c["page"], c["chunk_index"]),
                            vector=emb,
                            payload={
                                "source": c["source"],
                                "page": c["page"],
                                "chunk_index": c["chunk_index"],
                                "text": c["text"]
                            }
                        )
                        for c, emb in zip(batch, embeddings)
                    ]

                    self._upsert(points)
                    total += len(points)
                    batch = []

            if batch:
                texts = [c["text"] for c in batch]

                embeddings = self.embedder.encode(
                    texts,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    normalize_embeddings=True
                ).tolist()

                points = [
                    PointStruct(
                        id=point_id(c["source"], c["page"], c["chunk_index"]),
                        vector=emb,
                        payload={
                            "source": c["source"],
                            "page": c["page"],
                            "chunk_index": c["chunk_index"],
                            "text": c["text"]
                        }
                    )
                    for c, emb in zip(batch, embeddings)
                ]

                self._upsert(points)
                total += len(points)

        count = self.qdrant.count(
            collection_name=COLLECTION_NAME,
            exact=True
        ).count

        print(f"Total chunks in Qdrant: {count}")
        return total

    def retrieve(self, question: str):
        # 1. Fast vector similarity search from Qdrant
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

        # 2. Optimized Cross-Encoder reranking (batched & truncated for fast CPU inference)
        pairs = [
            (question, c["text"][:500])  # First 500 chars provide sharp relevance while 3x faster
            for c in candidates
        ]

        try:
            rerank_scores = self.reranker.predict(
                pairs,
                batch_size=len(pairs),
                show_progress_bar=False
            )
            for c, score in zip(candidates, rerank_scores):
                c["rerank_score"] = float(score)

            candidates.sort(
                key=lambda x: x.get("rerank_score", x.get("score", 0.0)),
                reverse=True
            )
        except Exception:
            # Fallback to cosine similarity if reranker fails
            candidates.sort(key=lambda x: x.get("score", 0.0), reverse=True)

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

        if not contexts:
            msg = "I could not find enough information in the trusted agricultural documents to answer this specific question."
            if return_details:
                return msg, [], [], None
            return msg, []

        context_text = "\n\n".join(
            f"[Source {i + 1}] {c['source']}, page {c['page']}\n{c['text']}"
            for i, c in enumerate(contexts)
        )

        profile_text = "\n".join(
            f"- {k}: {v}"
            for k, v in profile.items()
            if v not in (None, "", [])
        )

        current_stage = profile.get("farming_stage") or "Planning"

        history_text = ""
        if history:
            formatted_turns = []
            for h in history[-6:]:
                role = "Farmer" if h.get("role") in ["user", "farmer"] else "Uzhavar AI"
                formatted_turns.append(f"{role}: {h.get('content', '')}")
            history_text = "\n".join(formatted_turns)

        system = f"""
You are Uzhavar AI (உழவர் AI), an intelligent agricultural guide and farming companion for farmers in Tamil Nadu.

CORE RESPONSIBILITIES:
1. Provide grounded, reliable farming guidance using the retrieved agricultural documents (ICAR advisories, crop guides, drip irrigation manuals, farm machinery manuals).
2. Recommend practical, actionable steps for the farmer's stage and crops.
3. Language: If the user asks in Tamil or requested language is Tamil, respond in clear, respectful Tamil. If English, reply in English.
4. Focus exclusively on practical farming guidance (crops, land preparation, machinery, irrigation, pest management, harvesting, soil health). Do NOT speculate on government scheme percentages without verified records.
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
                return fallback, contexts, [], current_stage
            return fallback, contexts

        prompt_content = f"{system}\n\nFarmer Question:\n{question}"

        # Disable AFC in GenerateContentConfig to eliminate terminal warning
        from google.genai import types
        gen_config = types.GenerateContentConfig(
            temperature=0.3,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
        )

        response = self.llm.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt_content,
            config=gen_config
        )

        answer_text = response.text

        if return_details:
            return answer_text, contexts, [], current_stage

        return answer_text, contexts