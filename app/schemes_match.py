"""Deterministic lookup into data/schemes/schemes.json (Phase 1c).

Loads the human-verified structured scheme rows and matches a farmer
question against them with bilingual keyword scoring. Used by the
dispatcher BEFORE chunk retrieval: if a row matches strongly, the LLM is
prompted with that row alone — zero retrieval-miss risk.

Graceful no-op when schemes.json is absent (extraction pending).
"""

import json
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "schemes", "schemes.json")
_cache: Optional[List[Dict[str, Any]]] = None

# Words that make a question a *live-data* ask; those never route to the
# structured rows (they belong to the demo template route).
_LIVE_MARKERS = ["price today", "stock", "weather", "forecast", "news", "விலை என்ன"]


def load_rows() -> List[Dict[str, Any]]:
    global _cache
    if _cache is not None:
        return _cache
    _cache = []
    try:
        with open(_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            _cache = [r for r in data if isinstance(r, dict) and r.get("scheme_name")]
    except Exception:
        pass
    return _cache


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    return " " + text.lower() + " "


_WORD_RE = re.compile(r"[^\s.,;:!?()\[\]{}\"'\u201c\u201d\u2018\u2019/\\|]+")


def _stem(word: str) -> str:
    """Light plural stripping for English words only (seeds -> seed, schemes -> scheme)."""
    return word[:-1] if (word.isascii() and len(word) > 4 and word.endswith("s")) else word


def _stemmed(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "").lower()
    return " " + " ".join(_stem(w) for w in _WORD_RE.findall(text)) + " "


def _present(tok: str, q_norm: str, q_stem: str) -> bool:
    """Single English words match as whole words with plurals folded ('rice' must not hit
    'price', 'seeds' matches 'seed'); multi-word phrases and Tamil tokens match as before
    (Tamil attaches suffixes to the word, so it keeps substring matching)."""
    if not tok.isascii():
        return tok in q_norm
    if " " in tok:
        return tok in q_norm
    return f" {_stem(tok)} " in q_stem


def _row_tokens(row: Dict[str, Any]) -> List[Tuple[str, int]]:
    """(token, weight) pairs describing the row: scheme name tokens weigh most."""
    name = row.get("scheme_name") or ""
    toks: List[Tuple[str, int]] = []
    for w in name.lower().replace("&", " ").replace("--", " ").split():
        if len(w) >= 4 and not w.isdigit():
            toks.append((w, 3))
    for w in (row.get("keywords") or []):
        w = (w or "").strip().lower()
        if len(w) >= 4:
            toks.append((w, 4))  # curated keywords weigh most
    for fld, weight in (("benefits", 1), ("eligibility", 1), ("officer_contact", 1)):
        for v in row.get(fld) or []:
            for w in str(v).lower().replace("&", " ").split():
                if len(w) >= 5 and not w.isdigit():
                    toks.append((w, weight))
    return toks


MIN_SCORE = 6          # one curated keyword (~4) plus any name token (~3) clears it
RELATIVE_CUTOFF = 0.5  # extra rows must score at least this fraction of the best row


def match_schemes(question: str, lang: str = "English", top_k: int = 5, profile: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Best structured rows for the question, powered by app.schemes."""
    if not question:
        return []
    q = _norm(question)
    if any(m in q for m in _LIVE_MARKERS):
        return []
    try:
        from .schemes import search_schemes
        results = search_schemes(question, profile=profile, lang=lang, top_k=top_k)
        if results:
            return results
    except Exception:
        pass

    rows = load_rows()
    if not rows:
        return []
    q_stem = _stemmed(question)
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for row in rows:
        score = 0
        seen = set()
        for tok, w in _row_tokens(row):
            if tok in seen:
                continue
            seen.add(tok)
            if _present(tok, q, q_stem):
                score += w
        if score >= MIN_SCORE:
            scored.append((score, row))
    if not scored:
        return []
    scored.sort(key=lambda x: -x[0])
    best = scored[0][0]
    return [dict(r, _score=s) for s, r in scored[:top_k] if s >= best * RELATIVE_CUTOFF]


def match_scheme(question: str, lang: str = "English", profile: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Single best structured row (kept for callers that want one) or None."""
    hits = match_schemes(question, lang, top_k=1, profile=profile)
    return hits[0] if hits else None


def is_thin(row: Dict[str, Any]) -> bool:
    """True when extraction left the row without any usable detail."""
    return not any(row.get(k) for k in ("benefits", "eligibility", "how_to_apply", "documents_required"))


def row_to_context_text(row: Dict[str, Any]) -> str:
    """Flatten one structured row into the grounded-source block format used
    by the scheme prompt. File and page stay out of the text so the model cannot echo them."""
    parts = [f"SCHEME: {row.get('scheme_name')}"]
    parts.append(f"DEPARTMENT: {row.get('department') or 'Agriculture'}")
    if row.get("benefits"):
        parts.append("BENEFITS: " + "; ".join(str(b) for b in row["benefits"]))
    if row.get("eligibility"):
        parts.append("ELIGIBILITY: " + "; ".join(str(e) for e in row["eligibility"]))
    if row.get("documents_required"):
        parts.append("DOCUMENTS REQUIRED: " + "; ".join(str(d) for d in row["documents_required"]))
    if row.get("how_to_apply"):
        parts.append("HOW TO APPLY: " + row["how_to_apply"])
    if row.get("officer_contact"):
        parts.append("OFFICER TO CONTACT: " + row["officer_contact"])
    return "\n".join(parts)
