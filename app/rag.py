import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path
import re
import logging
import hashlib
import time
import threading
from typing import List, Dict, Any, Optional, Tuple

import pymupdf
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from .config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    COLLECTION_AGRI,
    COLLECTION_SCHEMES,
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    TOP_K,
    RERANK_TOP_K,
    SCHEME_SCORE_FLOOR,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_SCHEME_MODEL
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


def _page_heading(text: str) -> Optional[str]:
    """Detect an ALL-CAPS section heading (e.g. 'MAIZE DEVELOPMENT SCHEME')
    among the first lines of a page. Returns the heading or None."""
    for line in text.split("\n")[:6]:
        line = line.strip()
        # 3+ words in caps, letters only/ampersand, not an index page number
        if 3 <= len(line) <= 90 and re.fullmatch(r"[A-Z][A-Z &,'()\.-]+", line) \
                and not re.fullmatch(r"[A-Z ]*\d[A-Z \d]*", line) \
                and any(c.isalpha() for c in line):
            # require at least 2 spaces-separated words to avoid table debris
            if len(line.split()) >= 2:
                return line.title()
    return None


def pdf_chunks(pdf_path: Path, scheme_heading: Optional[str] = None, capture_heading: bool = False):
    doc = pymupdf.open(pdf_path)

    try:
        current_heading = scheme_heading
        for page_number, page in enumerate(doc, start=1):
            text = clean_text(page.get_text("text"))

            if not text:
                continue

            if capture_heading:
                heading = _page_heading(text)
                if heading:
                    current_heading = heading

            for chunk_index, chunk in enumerate(chunk_text(text)):
                item = {
                    "source": pdf_path.name,
                    "page": page_number,
                    "chunk_index": chunk_index,
                    "text": chunk
                }
                if capture_heading:
                    item["_heading"] = current_heading
                yield item
    finally:
        doc.close()


def point_id(collection: str, source: str, page: int, chunk_index: int) -> str:
    """Keep the SHA scheme, but mix the collection in so the agri and schemes
    corpora can hold the same underlying source without ID collisions."""
    value = f"{collection}|{source}|{page}|{chunk_index}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


_OFFTOPIC_RE = re.compile(
    r"\b(jokes?|stor(y|ies)|songs?|lyrics|poems?|riddles?|movies?|cinema|cricket|ipl|football|"
    r"horoscope|astrology|girlfriend|boyfriend|politics|election)\b|ஜோக்|நகைச்சுவை|கதை|பாடல்|சினிமா|திரைப்படம்|கிரிக்கெட்",
    re.IGNORECASE,
)


def _fallback_answer(contexts, is_ta: bool) -> str:
    """Readable answer used only when no model could respond. Scheme rows from the JSON are
    listed as they are (no model needed); anything else gets a short retry message."""
    structured = [c for c in contexts if c.get("structured")]
    if not structured:
        return ("இப்போது பதிலைத் தயாரிக்க முடியவில்லை. சிறிது நேரம் கழித்து மீண்டும் கேளுங்கள்."
                if is_ta else "I couldn't prepare the answer just now. Please ask again in a moment.")
    labels = (
        {"BENEFITS": "நன்மைகள்", "ELIGIBILITY": "தகுதி", "HOW TO APPLY": "விண்ணப்பிக்கும் முறை", "DOCUMENTS REQUIRED": "தேவையான ஆவணங்கள்"}
        if is_ta else
        {"BENEFITS": "Benefits", "ELIGIBILITY": "Eligibility", "HOW TO APPLY": "How to apply", "DOCUMENTS REQUIRED": "Documents required"}
    )
    out = ["உங்கள் கேள்விக்குப் பொருந்தும் திட்டங்கள்:" if is_ta else "Here are the schemes that match your question:"]
    for c in structured[:3]:
        fields = {}
        for line in c["text"].splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip().upper()] = v.strip()
        block = [f"**{(c.get('scheme') or fields.get('SCHEME') or '').title()}**", ""]
        block += [f"- {labels[k]}: {fields[k]}" for k in labels if fields.get(k)]
        out.append("\n".join(block))
    return "\n\n".join(out)


def _no_thinking(model_name: str, types):
    """Gemini 2.5 Flash 'thinks' by default and those tokens come out of max_output_tokens, which
    can cut the visible answer off mid-sentence. Switch thinking off for the models that allow it."""
    if str(model_name).startswith("gemini-2.5-flash"):
        try:
            return types.ThinkingConfig(thinking_budget=0)
        except Exception:
            return None
    return None


class AnswerStream:
    """Iterable of answer text chunks (for st.write_stream). When exhausted,
    `final_text` holds the complete answer INCLUDING the appended deep-link
    block, and `deep_link` the structured link (or None)."""

    def __init__(self, gen_factory):
        self._factory = gen_factory
        self.final_text = ""
        self.deep_link = None

    def __iter__(self):
        return self._factory(self)


class RAG:
    # number of words after which the appended demo link block is truncated
    LINK_BLOCK_WORD_LIMIT = 400

    def _append_link_block(self, text: str, question: str, lang: Any, has_retrieval: bool) -> Tuple[str, Optional[Dict[str, Any]]]:
        """If the question maps to a demo service (or the home page when retrieval
        found nothing), append the clickable deep-link block to the answer.
        Returns (answer_text, deep_link_dict_or_None). The structured dict is
        also retained on the instance as `last_deep_link` for API layers."""
        self.last_deep_link = None
        try:
            from .links_mapping import match_service, build_link_tail, spoken_instruction, service_url, _HOME_CARD
            card = match_service(question, lang if lang else "English")
            if card is None and getattr(self, "last_route", None) == "scheme":
                card = match_service("subsidy scheme", lang if lang else "English")
            if card is None and not has_retrieval:
                # No documents matched the question: point the farmer at the
                # full demo app so the question can still lead somewhere useful.
                card = dict(_HOME_CARD)
            if card is not None:
                words = text.split()
                if len(words) > self.LINK_BLOCK_WORD_LIMIT:
                    text = " ".join(words[: self.LINK_BLOCK_WORD_LIMIT]) + " …"
                eff_lang = lang if lang else "English"
                text += build_link_tail(card, eff_lang)
                self.last_deep_link = {
                    "id": card["id"],
                    "label_en": card["en"],
                    "label_ta": card["ta"],
                    "emoji": card["emoji"],
                    "url": service_url(card),
                    "spoken": spoken_instruction(card, eff_lang),
                }
                return text, self.last_deep_link
            return text, None
        except Exception:
            return text, None

    def __init__(self):
        if not QDRANT_URL:
            raise ValueError("QDRANT_URL is missing from .env")

        if not QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY is missing from .env")

        # Heavy models load lazily (first retrieval) or via warm(), so general
        # chat answers never wait for them.
        self._model_lock = threading.RLock()
        self._embedder = None
        self._reranker = None

        self.qdrant = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=300
        )

        self.llm = None

        if GEMINI_API_KEY:
            from google import genai
            self.llm = genai.Client(api_key=GEMINI_API_KEY)

        # routing state exposed to UI/API layers
        self.last_route: Optional[str] = None           # "agri"|"scheme"|"demo"
        self.last_route_details: Optional[Dict[str, Any]] = None

    @property
    def embedder(self):
        with self._model_lock:
            if self._embedder is None:
                try:
                    self._embedder = SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
                except Exception:
                    self._embedder = SentenceTransformer(EMBEDDING_MODEL)
            return self._embedder

    @property
    def reranker(self):
        with self._model_lock:
            if self._reranker is None:
                # local cache first, to avoid unauthenticated HF warnings
                try:
                    self._reranker = CrossEncoder(RERANKER_MODEL, automodel_args={"local_files_only": True})
                except Exception:
                    try:
                        self._reranker = CrossEncoder(RERANKER_MODEL, local_files_only=True)
                    except Exception:
                        self._reranker = CrossEncoder(RERANKER_MODEL)
            return self._reranker

    def warm(self):
        """Pre-load the embedding + reranker models (called from a background thread)."""
        _ = self.embedder
        _ = self.reranker

    def _translate_batch(self, texts: List[str], tgt: str) -> Optional[List[str]]:
        """One Gemini call that translates `texts` into `tgt`; None if it fails or the reply is malformed."""
        import json as _json
        import logging
        try:
            from google.genai import types
            prompt = (
                f"Translate every string in this JSON array into {tgt}. Keep numbers, units, names, "
                "line breaks and any leading '- ' bullet markers exactly. Do not add, remove or explain "
                f"anything. Reply with ONLY a JSON array of exactly {len(texts)} strings, same order.\n\n"
                + _json.dumps(texts, ensure_ascii=False)
            )
            r = self.llm.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=16000,
                    response_mime_type="application/json",
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
            raw = (r.text or "").strip()
            if raw.startswith("```"):
                raw = raw.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
            out = _json.loads(raw)
            if isinstance(out, list) and len(out) == len(texts) and all(isinstance(x, str) and x.strip() for x in out):
                return out
            logging.getLogger("uzhavar.translate").warning("unexpected translation reply shape (%s items for %s)", len(out) if isinstance(out, list) else type(out).__name__, len(texts))
        except Exception as e:
            logging.getLogger("uzhavar.translate").warning("translation call failed: %s", e)
        return None

    def translate(self, texts: List[str], target_lang: str) -> Optional[List[Optional[str]]]:
        """Translate chat messages into Tamil/English.
        Returns a list aligned with `texts`; an entry is None when that message could not be
        translated (the UI keeps its original text). Returns None only when no LLM is configured.
        Messages go in small batches so long Tamil output never hits the token limit; a failed
        batch is retried one message at a time."""
        if not self.llm or not texts:
            return None
        tgt = "Tamil" if (target_lang or "").startswith("T") else "English"
        out: List[Optional[str]] = [None] * len(texts)

        batches: List[List[int]] = []
        cur: List[int] = []
        size = 0
        for i, t in enumerate(texts):
            if cur and size + len(t) > 2500:
                batches.append(cur)
                cur, size = [], 0
            cur.append(i)
            size += len(t)
        if cur:
            batches.append(cur)

        for idxs in batches:
            res = self._translate_batch([texts[i] for i in idxs], tgt)
            if res is None and len(idxs) > 1:
                res = [(self._translate_batch([texts[i]], tgt) or [None])[0] for i in idxs]
            if res:
                for i, r in zip(idxs, res):
                    out[i] = r
        return out

    # ------------------------------------------------------------------
    # Route D: general conversation — LLM only, no retrieval
    # ------------------------------------------------------------------
    def answer_general(self, question, profile, history=None, return_details=False, stream=False):
        is_ta = ((profile or {}).get("language") or "English").startswith("T")
        lang_name = "Tamil" if is_ta else "English"
        self.last_deep_link = None
        self.last_route = "general"

        # obvious off-topic requests are declined instantly, with no AI call
        if _OFFTOPIC_RE.search(question or ""):
            decline = (
                "நான் விவசாயம், விவசாயிகளுக்கான அரசுத் திட்டங்கள் மற்றும் இந்த செயலி பற்றிய கேள்விகளுக்கு மட்டுமே உதவ முடியும். அவற்றைப் பற்றி கேளுங்கள்."
                if is_ta else
                "I can only help with agriculture, government schemes for farmers, and questions about this app. Please ask me about those."
            )
            stage0 = (profile or {}).get("farming_stage") or "Planning"
            return (decline, [], [], stage0) if return_details else (decline, [])

        history_text = ""
        if history:
            history_text = "\n".join(
                f"{'Farmer' if h.get('role') in ('user', 'farmer') else 'Uzhavar AI'}: {h.get('content', '')}"
                for h in history[-4:]
            )
        name = (profile or {}).get("name") or ""
        prompt = f"""LANGUAGE (MANDATORY): reply ONLY in {lang_name}. {"Do not use English sentences." if is_ta else "Do NOT use any Tamil words or script."}

You are Uzhavar AI (உழவர் AI), a friendly assistant for farmers in Tamil Nadu.
Reply like a warm, helpful person: 1 to 3 short, simple sentences, plain text, no markdown, no emojis (the reply may be read aloud).
- Do NOT start every reply with repetitive greetings or calling the farmer by name (no "Hello {name}"). Answer naturally and directly.
- Greetings, thanks, chit-chat: respond warmly and ask how you can help on the farm.
- Questions about you or the app: you help with crop selection, soil testing, drip irrigation, farm machinery, pest and weed control, Tamil Nadu government schemes, and live services (market prices, weather) through the Uzhavar app; the farmer can talk or type, in English or Tamil.
- ANYTHING ELSE (jokes, stories, songs, movies, sports, news, politics, general knowledge, personal advice, coding, etc.): do NOT answer it. In ONE short polite sentence say you can only help with agriculture, government schemes for farmers, and questions about this app, and invite one of those.
- Never invent facts, prices, scheme amounts or dates. Do not give detailed crop or scheme advice here; if the farmer needs it, invite them to ask that specific question.

RECENT CONVERSATION:
{history_text or "None"}

Farmer: {question}
Uzhavar AI:"""

        static = (
            "வணக்கம்! நான் உழவர் AI. பயிர்கள், மண், இயந்திரங்கள், பாசனம், பூச்சி கட்டுப்பாடு பற்றி கேளுங்கள்."
            if is_ta else
            "Hello! I'm Uzhavar AI. Ask me about crops, soil, machinery, irrigation or pest control."
        )
        stage = (profile or {}).get("farming_stage") or "Planning"

        def _pack(x):
            return (x, [], [], stage) if return_details else (x, [])

        if not self.llm:
            return _pack(static)

        from google.genai import types
        cfg = types.GenerateContentConfig(
            temperature=0.5,
            max_output_tokens=250,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        if stream:
            def _gen(holder):
                parts = []
                try:
                    for chunk in self.llm.models.generate_content_stream(
                        model=GEMINI_MODEL, contents=prompt, config=cfg
                    ):
                        t = getattr(chunk, "text", None)
                        if t:
                            parts.append(t)
                            yield t
                except Exception:
                    pass
                text = "".join(parts).strip()
                if not text:
                    text = static
                    yield text
                holder.final_text, holder.deep_link = text, None
            return _pack(AnswerStream(_gen))
        try:
            text = (self.llm.models.generate_content(
                model=GEMINI_MODEL, contents=prompt, config=cfg).text or "").strip()
        except Exception:
            text = ""
        return _pack(text or static)

    def _ensure_collection(self, collection: str = COLLECTION_AGRI):
        dim = self.embedder.get_embedding_dimension()

        if not self.qdrant.collection_exists(collection):
            self.qdrant.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(
                    size=dim,
                    distance=Distance.COSINE
                )
            )

    def _upsert(self, points, collection: str = COLLECTION_AGRI):
        for attempt in range(3):
            try:
                self.qdrant.upsert(
                    collection_name=collection,
                    points=points,
                    wait=True,
                    timeout=300
                )
                return

            except Exception:
                if attempt == 2:
                    raise

                time.sleep(3 * (attempt + 1))

    def ingest(self, data_dir: str = "data", collection: str = COLLECTION_AGRI, scheme_headings: bool = False):
        """Ingest every PDF in data_dir into the given Qdrant collection.

        scheme_headings=True (Route C corpora): each point's payload gains a
        "scheme" field with the most recent ALL-CAPS page heading seen so far,
        so every chunk stays attributed to the scheme section it belongs to.
        """
        self._ensure_collection(collection)
        total = 0
        batch_size = 8

        pdf_files = sorted(Path(data_dir).glob("*.pdf"))

        if not pdf_files:
            print("No PDF files found.")
            return 0

        last_scheme = None

        for pdf_path in pdf_files:
            batch = []

            for chunk_data in pdf_chunks(pdf_path, scheme_heading=last_scheme, capture_heading=scheme_headings):
                if scheme_headings and chunk_data.get("_heading"):
                    last_scheme = chunk_data["_heading"]
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
                            id=point_id(collection, c["source"], c["page"], c["chunk_index"]),
                            vector=emb,
                            payload={
                                "source": c["source"],
                                "page": c["page"],
                                "chunk_index": c["chunk_index"],
                                "text": c["text"],
                                "scheme": (c.get("_heading") or last_scheme) if scheme_headings else None,
                            }
                        )
                        for c, emb in zip(batch, embeddings)
                    ]

                    self._upsert(points, collection)
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
                        id=point_id(collection, c["source"], c["page"], c["chunk_index"]),
                        vector=emb,
                        payload={
                            "source": c["source"],
                            "page": c["page"],
                            "chunk_index": c["chunk_index"],
                            "text": c["text"],
                            "scheme": (c.get("_heading") or last_scheme) if scheme_headings else None,
                        }
                    )
                    for c, emb in zip(batch, embeddings)
                ]

                self._upsert(points, collection)
                total += len(points)

        count = self.qdrant.count(
            collection_name=collection,
            exact=True
        ).count

        print(f"Total chunks in Qdrant collection '{collection}': {count}")
        return total

    def retrieve(self, question: str, collection: str = COLLECTION_AGRI, top_k: int = None):
        # 1. Fast vector similarity search from Qdrant
        qvec = self.embedder.encode(
            question,
            normalize_embeddings=True
        ).tolist()

        results = self.qdrant.query_points(
            collection_name=collection,
            query=qvec,
            limit=top_k or TOP_K,
            with_payload=True
        ).points

        candidates = [
            {
                "text": r.payload["text"],
                "source": r.payload["source"],
                "page": r.payload["page"],
                "scheme": r.payload.get("scheme"),
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

    # ------------------------------------------------------------------ #
    # 3-ROUTE DISPATCH (router.py decides; each route has its own corpus
    # and generator. Signature and return shape are unchanged.)
    # ------------------------------------------------------------------ #

    def _answer_from_context(
        self,
        question: str,
        profile: dict,
        history: Optional[List[Dict[str, str]]],
        contexts: List[Dict[str, Any]],
        collection: str,
        return_details: bool = False,
        stream: bool = False,
    ):
        """Shared generation used by Route A and Route C. Mirrors the original
        agronomy answer() prompt except for the corpus-specific rules."""
        _llm_lang = None
        if isinstance(profile, dict):
            _llm_lang = profile.get("language")

        is_scheme = collection == COLLECTION_SCHEMES

        context_text = "\n\n".join(
            f"[Reference {i + 1}]"
            + (f" (scheme: {c['scheme']})" if c.get("scheme") and is_scheme else "")
            + f"\n{c['text']}"
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

        is_ta = (_llm_lang or "English").startswith("T")
        lang_name = "Tamil" if is_ta else "English"
        lang_rule = (
            f"LANGUAGE (MANDATORY - overrides everything else below): the app language is {lang_name}. "
            f"Write the ENTIRE reply, including the final closing line, in {lang_name} only. "
            + ("Do not write full English sentences."
               if is_ta else
               "Do NOT use any Tamil words or Tamil script, even if the farmer's name, earlier messages or sources contain Tamil.")
        )
        next_line = (
            'Tamil: "வேறு என்ன தெரிந்துகொள்ள வேண்டும்?"' if is_ta
            else 'English: "What would you like to know next?" or "Shall I explain any step in detail?"'
        )

        if is_scheme:
            system = f"""
{lang_rule}

You are Uzhavar AI (உழவர் AI), answering questions about Government of Tamil Nadu farmer welfare schemes using ONLY the retrieved department document (Farmer Welfare Dept Citizen Charter 2025-26).

SCHEME ANSWER RULES (STRICT):
0. CONVERSATION OPENING (STRICT): NEVER start the reply with greetings, pleasantries, or self-introductions (no "Hello", "Vanakkam", "Hello {name}", no restating the farmer's name). Start DIRECTLY with the substance of the answer.
1. Quote ONLY numbers, percentages and amounts that appear verbatim in the retrieved sources. If a number the farmer wants is not in the sources, say so plainly and point to the relevant department office.
2. Name the scheme and the department that runs it, because the farmer needs to know where to apply. NEVER mention PDFs, file names, page numbers, a "document", "retrieved" material, "sources" or any [Reference] tag in your reply: the app shows the sources separately. Speak directly to the farmer ("you") and start with the direct answer, for example that there is a 50% subsidy and what it covers, before the details.
3. Never fill gaps from your own memory, never guess eligibility lists or subsidy amounts, never invent closing dates.
4. If the references do not contain the answer, say honestly that you do not have those details and suggest contacting the local agriculture office. Do NOT answer from general knowledge, and do not talk about documents or files.
5. Language: reply only in {lang_name}, as stated in the mandatory language rule above.
6. Keep it short and spoken-friendly: max ~180 words, plain text, short "- " bullets allowed, NO markdown formatting of any kind (no **bold**, no headings/tables — write plain sentences). End with one short line inviting the farmer's next turn.
7. Several sources may be returned. Use only those that match what the farmer actually asked (for example, seed the farmer RECEIVES at a subsidy is different from an incentive paid to seed PRODUCERS) and name at most the three best fits, each with its key benefit and who is eligible. If none of them matches, say so plainly.
8. CONVERSATIONAL ELIGIBILITY GUIDANCE (NON-INTRUSIVE & GROUNDED):
- It is NOT compulsory to ask every farmer about their land or schemes. Only when the farmer explicitly asks about government schemes, subsidies, or eligibility:
  a) State the scheme name, the department running it, and the verified benefit tiers (e.g. 100% subsidy for Small/Marginal farmers up to 5 acres, 75% for other farmers; or 50% for tractors).
  b) Clearly explain what criteria determine eligibility (e.g. landholding size: Marginal up to 2.5 acres, Small 2.5-5 acres, Large >5 acres; water source like borewell/well for drip or solar; documents like Patta/Chitta and Aadhaar).
  c) If their land size is not yet known, POLITELY INVITE them (do not demand): "If you would like me to check your exact eligibility and subsidy percentage, feel free to tell me how many acres of land you cultivate (and if you have a well/borewell)."
  d) IF the farmer has already provided or replies with their landholding (e.g. "I have 3 acres"):
     Directly evaluate their eligibility against the scheme! State their category:
     * Marginal Farmer (குறு விவசாயி - up to 2.5 acres / 1 ha)
     * Small Farmer (சிறு விவசாயி - 2.5 to 5.0 acres / 1 to 2 ha)
     * Other / Large Farmer (பெரிய / பிற விவசாயி - above 5.0 acres / >2 ha)
     And confirm whether they ARE ELIGIBLE or not and what benefit percentage or amount they qualify for.
  e) If the farmer is asking about non-scheme farming topics (pests, crops, fertilizers), answer their farming question directly and DO NOT ask about land size or schemes.

FARMER PROFILE & CONTEXT:
{profile_text}

RECENT CONVERSATION HISTORY:
{history_text if history_text else "None (Start of conversation)"}

RETRIEVED SCHEME SOURCES:
{context_text}
""".strip()
            model_name = GEMINI_SCHEME_MODEL
            temperature = 0.1
            max_tokens = 900
        else:
            system = f"""
{lang_rule}

You are Uzhavar AI (உழவர் AI), an intelligent agricultural guide and farming companion for farmers in Tamil Nadu.

CORE RESPONSIBILITIES:
1. Provide grounded, reliable farming guidance using the retrieved agricultural documents (ICAR advisories, crop guides, drip irrigation manuals, farm machinery manuals).
2. Recommend practical, actionable steps for the farmer's stage and crops.
3. Language: reply only in {lang_name}, as stated in the mandatory language rule above.
4. Focus exclusively on practical farming guidance (crops, land preparation, machinery, irrigation, pest management, harvesting, soil health). Do NOT speculate on government scheme percentages without verified records.

CONVERSATION STYLE (STRICT):
- Answer like a knowledgeable agriculture extension officer in a real conversation, NOT like a letter or an essay.
- NEVER start the reply with greetings, pleasantries or self-introductions. No "Vanakkam", "Hello", "Welcome", "I am Uzhavar AI", no restating the farmer's name. Start DIRECTLY with the substance of the answer.
- Keep the answer SHORT and spoken-friendly: at most 120 words (about 5-6 sentences). This is read aloud to a farmer; long answers waste their time.
- Structure: 1 short direct answer sentence, then at most 3-4 crisp bullet points with only the KEY facts, numbers and steps from the sources. Omit background theory, disclaimers, offers of further help and closing questions.
- If the farmer's message is only a greeting, thanks, small talk or is not a farming question, do NOT give farming advice and do not use the sources: reply with ONE short friendly sentence and ask what they would like help with on their farm.
- NEVER end with questions like "How would you like to proceed?" or offers such as "let me know if you need more help". Just end after the key points.
- Do NOT say what the documents do not contain or apologize for missing data. If asked about something with no source (e.g. live market prices), give at most one practical sentence pointing to the right place (e.g. local Uzhavar Sandhai or e-NAM portal) and stop.
- NEVER mention PDFs, file names, page numbers, [Reference] tags or phrases like "according to the document"; the app lists sources separately. Speak directly to the farmer.
- ALWAYS end the reply with one short line inviting the farmer's next turn, in {lang_name}, e.g. {next_line}. This tells the farmer it is their turn to speak.
- Plain text only: no markdown bold/headings/tables, no emojis. Short "- " bullets are allowed.
FARMER PROFILE & CONTEXT:
{profile_text}

RECENT CONVERSATION HISTORY:
{history_text if history_text else "None (Start of conversation)"}

RETRIEVED AGRICULTURAL SOURCES:
{context_text}
""".strip()
            model_name = GEMINI_MODEL
            temperature = 0.3
            max_tokens = 320

        if not self.llm:
            fallback = _fallback_answer(contexts, is_ta)
            fallback, _ = self._append_link_block(fallback, question, _llm_lang, has_retrieval=True)
            self.last_route = "scheme" if is_scheme else "agri"
            if return_details:
                return fallback, contexts, [], current_stage
            return fallback, contexts

        prompt_content = f"{system}\n\nFarmer Question:\n{question}"

        from google.genai import types
        def _cfg(m, think_off=True):
            return types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                thinking_config=_no_thinking(m, types) if think_off else None,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )

        # if the first model returns nothing (quota, outage, retired model), try the other configured one
        alt = GEMINI_MODEL if model_name != GEMINI_MODEL else GEMINI_SCHEME_MODEL
        models = [model_name] + ([alt] if alt and alt != model_name else [])

        if stream:
            route_name = "scheme" if is_scheme else "agri"

            def _gen(holder):
                parts = []
                for m in models:
                    for think_off in (True, False):
                        last, err = None, None
                        try:
                            for chunk in self.llm.models.generate_content_stream(
                                model=m, contents=prompt_content, config=_cfg(m, think_off)
                            ):
                                last = chunk
                                t = getattr(chunk, "text", None)
                                if t:
                                    parts.append(t)
                                    yield t
                        except Exception as e:
                            err = e
                            logging.getLogger("uzhavar.llm").warning("%s stream failed: %s", m, e)
                        try:
                            if last is not None and "MAX_TOKENS" in str(last.candidates[0].finish_reason):
                                logging.getLogger("uzhavar.llm").warning("%s answer cut off at max_output_tokens=%s", m, max_tokens)
                        except Exception:
                            pass
                        # only an error about the thinking setting justifies retrying the same model
                        if parts or not (think_off and err and "thinking" in str(err).lower()):
                            break
                    if parts:
                        break
                text = "".join(parts).strip()
                if not text:
                    text = _fallback_answer(contexts, is_ta)
                    yield text
                holder.final_text, holder.deep_link = self._append_link_block(
                    text, question, _llm_lang, has_retrieval=True
                )
                self.last_route = route_name

            stream_obj = AnswerStream(_gen)
            if return_details:
                return stream_obj, contexts, [], current_stage
            return stream_obj, contexts

        # Quota/outage failures must degrade honestly, never crash the chat.
        answer_text = ""
        for m in models:
            for think_off in (True, False):
                err = None
                try:
                    answer_text = (self.llm.models.generate_content(
                        model=m, contents=prompt_content, config=_cfg(m, think_off)).text or "").strip()
                except Exception as e:
                    err = e
                    answer_text = ""
                    logging.getLogger("uzhavar.llm").warning("%s call failed: %s", m, e)
                if answer_text or not (think_off and err and "thinking" in str(err).lower()):
                    break
            if answer_text:
                break
        if not answer_text:
            fallback, _ = self._append_link_block(_fallback_answer(contexts, is_ta), question, _llm_lang, has_retrieval=True)
            self.last_route = "scheme" if is_scheme else "agri"
            if return_details:
                return fallback, contexts, [], current_stage
            return fallback, contexts

        answer_text, _ = self._append_link_block(answer_text, question, _llm_lang, has_retrieval=True)

        if return_details:
            return answer_text, contexts, [], current_stage

        return answer_text, contexts
    # ------------------------------------------------------------------
    # Route B: deterministic demo-service answer (no retrieval, no LLM)
    # ------------------------------------------------------------------

    def answer_demo(self, question: str, lang: Optional[str], card: Dict[str, Any], return_details: bool = False):
        """Template answer built purely from the matched demo-service card."""
        try:
            from .links_mapping import build_link_tail, spoken_instruction, service_url
        except Exception:
            build_link_tail = None  # degraded mode handled below

        eff_lang = lang or "English"
        if eff_lang.startswith("T"):
            label = f"{card.get('ta') or card['en']}"
            tmpl = (
                f"உங்கள் கேள்விக்கான நேரடி தகவல் உழவர் செயலியின் \"{label}\" பக்கத்தில் கிடைக்கும்.\n"
                f"- தற்போதைய விவரங்கள் அந்தப் பக்கத்தில் புதுப்பிக்கப்படுகின்றன."
            )
        else:
            label = card["en"]
            tmpl = (
                f"The Uzhavar app's \"{label}\" page has the live details for this.\n"
                f"- The information on that page is kept up to date."
            )

        if build_link_tail is not None:
            text = tmpl + build_link_tail(card, eff_lang)
            self.last_deep_link = {
                "id": card["id"],
                "label_en": card["en"],
                "label_ta": card["ta"],
                "emoji": card["emoji"],
                "url": service_url(card),
                "spoken": spoken_instruction(card, eff_lang),
            }
        else:
            text = tmpl
            self.last_deep_link = None

        self.last_route = "demo"
        if return_details:
            return text, [], [], None
        return text, []

    # ------------------------------------------------------------------
    # Dispatcher — same signature as the old monolithic answer()
    # ------------------------------------------------------------------

    def answer(
        self,
        question: str,
        profile: dict,
        history: Optional[List[Dict[str, str]]] = None,
        return_details: bool = False,
        stream: bool = False,
    ):
        """Route the question (router.classify) then dispatch:
          demo   -> template card answer (no LLM, no retrieval)
          scheme -> uzhavar_schemes retrieval + Gemini 2.5 Flash
          agri   -> uzhavar_agri  retrieval + Gemini 2.5 Flash-Lite
          dual   -> BOTH retrievals race; rerank margin picks the corpus
                    (never a free-text fallback — that's how ungrounded
                    scheme claims get made)
        Every path still appends a demo deep link via _append_link_block.
        Sets self.last_route / self.last_route_details for UI & API.
        """
        _llm_lang = None
        if isinstance(profile, dict):
            _llm_lang = profile.get("language")

        prev_route = self.last_route
        t0 = time.perf_counter()
        from .router import classify, log_route
        rr = classify(
            question,
            lang=_llm_lang,
            history=history,
            last_route=prev_route,
        )
        route = rr.route
        final = route

        if route == "general":
            self.last_route_details = rr.to_log_dict()
            log_route(question, _llm_lang, rr, "general", int((time.perf_counter() - t0) * 1000))
            return self.answer_general(question, profile, history, return_details, stream)

        if route == "demo" and rr.demo_card:
            from .links_mapping import match_service
            card = match_service(question, _llm_lang or "English")
            if card is not None:
                out = self.answer_demo(question, _llm_lang, dict(card), return_details)
                self.last_route_details = rr.to_log_dict()
                log_route(question, _llm_lang, rr, final, int((time.perf_counter() - t0) * 1000))
                return out

        if route in ("agri", "scheme"):
            contexts = []
            if route == "scheme":
                # Fast structured lookup first: instantaneous in-memory match against schemes.json
                try:
                    from .schemes_match import match_schemes, row_to_context_text
                    rows = match_schemes(question, _llm_lang or "English", profile=profile)
                    # If this is an eligibility follow-up (e.g. farmer replied with acres or docs),
                    # search recent turns in history to retain the scheme being discussed
                    if not rows and history:
                        prev_text = " ".join(h.get("content", "") for h in history[-3:])
                        rows = match_schemes(prev_text, _llm_lang or "English", profile=profile)
                except Exception:
                    rows = []
                if not rows:
                    try:
                        from .schemes import recommend_schemes
                        rows = recommend_schemes(profile or {"language": _llm_lang}, limit=3)
                    except Exception:
                        rows = []
                if rows:
                    contexts = [{
                        "text": row_to_context_text(r),
                        "source": (r.get("provenance") or {}).get("source_pdf", "Farmers_welfare_dept.pdf"),
                        "page": ((r.get("provenance") or {}).get("pages") or [1])[0],
                        "scheme": r.get("scheme_name"),
                        "score": 1.0,
                        "rerank_score": 1.0,
                        "structured": True,
                    } for r in rows]
                    rr.notes.append("structured_rows:" + ",".join(str(r.get("id")) for r in rows))
                else:
                    # Fallback to vector search only if structured rows had no match
                    contexts = self.retrieve(question, collection=COLLECTION_SCHEMES)
                collection = COLLECTION_SCHEMES
            else:
                collection = COLLECTION_AGRI
                contexts = self.retrieve(question, collection=COLLECTION_AGRI)
            self.last_route = route
            self.last_route_details = rr.to_log_dict()
            log_route(question, _llm_lang, rr, final, int((time.perf_counter() - t0) * 1000))
            return self._answer_from_context(question, profile, history, contexts, collection, return_details, stream)

        if route == "dual":
            # BOTH collections race; rerank margin decides which corpus
            # (and therefore which generator) answers.
            ctx_scheme = self.retrieve(question, collection=COLLECTION_SCHEMES)
            ctx_agri = self.retrieve(question, collection=COLLECTION_AGRI)

            def _best(ctx):
                if not ctx:
                    return None
                return max(c.get("rerank_score", c.get("score", 0.0)) for c in ctx)

            best_s, best_a = _best(ctx_scheme), _best(ctx_agri)
            from .config import ARBITRATION_MARGIN, SCHEME_SCORE_FLOOR
            margin = (best_a or 0.0) - (best_s or 0.0)
            rr.notes.append(f"margin={margin:+.3f}")

            # Scheme corpus may only answer if its evidence clears the
            # calibrated floor — never quote numbers on weak evidence.
            if best_s is not None and best_s >= SCHEME_SCORE_FLOOR and margin < ARBITRATION_MARGIN and ctx_scheme:
                final = "scheme"
                collection = COLLECTION_SCHEMES
                contexts = ctx_scheme
                self.last_route = "scheme"
            else:
                final = "agri"
                collection = COLLECTION_AGRI
                # Never generate on an empty corpus: if BOTH sides came back
                # empty, return the honest ungrounded message instead of
                # passing [] into the LLM prompt.
                if not ctx_agri and not ctx_scheme:
                    contexts = []
                    final = "agri_ungrounded"
                else:
                    contexts = ctx_agri or ctx_scheme

            if final == "agri_ungrounded":
                if (_llm_lang or "English").startswith("T"):
                    msg = "இந்த கேள்விக்கு இரு தரவுத் தொகுப்புகளிலும் போதுமான தகவல் இல்லை."
                else:
                    msg = "I could not find enough information in my trusted documents to answer this specific question."
                msg, _ = self._append_link_block(msg, question, _llm_lang, has_retrieval=False)
                self.last_route = "agri"
                self.last_route_details = rr.to_log_dict()
                log_route(question, _llm_lang, rr, final, int((time.perf_counter() - t0) * 1000))
                if return_details:
                    return msg, [], [], None
                return msg, []

            self.last_route_details = rr.to_log_dict()
            log_route(question, _llm_lang, rr, final, int((time.perf_counter() - t0) * 1000))
            return self._answer_from_context(question, profile, history, contexts, collection, return_details, stream)

        # Router returned an unknown route value — treat as agri but never
        # generate scheme content without evidence.
        final = "agri"
        contexts = self.retrieve(question, collection=COLLECTION_AGRI)
        if not contexts:
            final = "agri_ungrounded"
            if (_llm_lang or "English").startswith("T"):
                msg = "இந்த கேள்விக்கு நம்பகமான வேளாண் ஆவணங்களில் போதுமான தகவல் இல்லை."
            else:
                msg = "I could not find enough information in the trusted agricultural documents to answer this specific question."
            msg, _ = self._append_link_block(msg, question, _llm_lang, has_retrieval=False)
            self.last_route = "agri"
            self.last_route_details = rr.to_log_dict()
            log_route(question, _llm_lang, rr, final, int((time.perf_counter() - t0) * 1000))
            if return_details:
                return msg, [], [], None
            return msg, []
        self.last_route = "agri"
        self.last_route_details = rr.to_log_dict()
        log_route(question, _llm_lang, rr, final, int((time.perf_counter() - t0) * 1000))
        return self._answer_from_context(question, profile, history, contexts, COLLECTION_AGRI, return_details, stream)
