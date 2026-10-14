"""Three-route intent router for Uzhavar AI.

Routes (decided by OBSERVABLE signals only — the LLM's self-reported
confidence is logged, never used as a policy gate):

  route A "agri"    — agronomy RAG (uzhavar_agri, Gemini 2.5 Flash-Lite)
  route B "demo"    — deterministic demo-service template (no LLM, no retrieval)
  route C "scheme"  — TN welfare schemes RAG (uzhavar_schemes, Gemini 2.5 Flash)
  route D "general" — chit-chat, questions about the app/assistant, non-farming
                      doubts: answered by the LLM directly, NO retrieval

Decision order (deterministic, in code):
  1. Sticky: short follow-up (ellipsis/pronoun) inherits last_route.
  2. Tier-1: demo keyword score >= DEMO_ROUTE_THRESHOLD short-circuits to
     route B — UNLESS scheme lexicon markers are present (scheme veto).
  3. Tier-2: Gemini 2.5 Flash-Lite JSON intent label.
     - label == "scheme" or scheme lexicon markers present -> route C.
     - label == "demo" (no Tier-1 match)                    -> route B.
     - label == "agri" and NO scheme markers                -> route A.
     - anything else (LLM error, timeout, mixed signals)    -> "dual",
       meaning the caller must run dual-retrieval arbitration on rerank
       score margins instead of trusting a free-text fallback.

The "dual" outcome is the safe path: instead of a free-text answer from
memory (which is exactly how ungrounded scheme claims get made), the two
collections race and the rerank scores decide which corpus — and therefore
which generator — answers.
"""

import json
import os
import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .config import (
    DEMO_ROUTE_THRESHOLD,
    MIN_FOLLOWUP_CHARS,
)

# --------------------------------------------------------------------------
# Deterministic lexicons (the veto + arbitration trigger inputs)
# --------------------------------------------------------------------------

# Words that almost always mean a government scheme/welfare question. If any
# of these appear, a demo keyword match must NOT short-circuit the router.
SCHEME_MARKERS_EN = [
    "scheme", "yojana", "yojna", "subsidy", "மானியம்", "நிதி",
    "pension", "ஓய்வூதிய", "முதுமை", "eligibility", "eligible", "qualify", "qualification", "தகுதி", "தகுதியான", "தகுதியுள்ள",
    "benefit", "நல", "நலத்திட்டம்", "welfare", "நல்வாழ்வு",
    "government", "govt", "அரசு", "அரசாங்க", "dept", "department",
    "apply", "application", "விண்ணப்ப", "பதிவு செய்ய", "enrol", "enroll",
    "compensation", "இழப்பீடு", "assistance", "relief", "நிவாரண",
    "grant", "amount", "தொகை", "tamilnadu", "tamil nadu",
    "kadp", "kalaignar", "கலைஞர்", "pmkisan", "pm-kisan", "pmfby",
    "quota", "loan waiver", "insurance claim", "காப்பீட்டு உரிமை",
    "soil card", "soil card printing", "soil test", "soil testing",
    "மண் சோதனை", "மண் அட்டை", "மண்ணுக்கு என்ன சோதனை", "soil health", "soil sample",
    "office handles", "which office", "free soil",
    "harvest is destroyed", "crop gets ruined", "crop losss", "crop loss",
    "dried land", "மழையில் பயிர்", "பயிர் அழிந்த", "vaasooli",
    "vasooli", "assistance for dairy", "maaruthuvam",
]

AGRI_MARKERS_EN = [
    "seed", "fertilizer", "pest", "disease", "irrigation", "drip",
    "harvest", "sowing", "transplant", "soil", "yield", "crop",
    "weeds", "weedicid", "pesticid", "fungicid", "spray", "paddy",
    "விதை", "உரம்", "பயிர", "நீர்", "விளைச்சல்", "அறுவடை", "நாற்று",
    "பூச்சி", "நோய்", "களை", "மண்",
]


# Quick, deterministic detection of general conversation (no LLM call needed).
# Only matches when NO farming / scheme markers are present.
# (a) the WHOLE message is chit-chat (so "ok how to plant banana" is NOT general)
_GENERAL_FULL = re.compile(
    r"^\s*((hi+|hello+|hey+|hai|vanakkam|vanakam)(\s+(sir|madam|there|all|anna))?\s+)?"
    r"(hi+|hello+|hey+|hai|vanakkam|vanakam|namaste|good (morning|afternoon|evening|night)|"
    r"thanks?( a lot| you)?|thank you|ok(ay)?|fine|nice|great|good|super|cool|sari|சரி|நன்றி|வணக்கம்|"
    r"how are you|how r u|what'?s up|help( me)?|can you help( me)?|tell me a (joke|story))"
    r"(\s+(sir|madam|ma|there|all|anna|bro|friend|da|uzhavar ai|everyone|you|please))*\s*$",
    re.IGNORECASE,
)
# (b) questions about the assistant / the app itself
_GENERAL_START = re.compile(
    r"^\s*(who are you|what are you|your name|what can you do|what do you do|"
    r"are you (a )?(bot|ai|human|real)|who (made|created|built) you|"
    r"how (do|can|to) ((i|we) )?(use|speak|talk|type|change|switch)( the| to)? (this|app|voice|mic|microphone|language|english|tamil|text)|"
    r"how does (this|the) app|which languages?|do you (speak|know|understand) (english|tamil)|"
    r"நீ யார்|நீங்கள் யார்|உன் பெயர்|உங்கள் பெயர்|என்ன செய்ய முடியும்)\b",
    re.IGNORECASE,
)


def _is_general_chat(question: str) -> bool:
    q = re.sub(r"[^\w\s'\u0b80-\u0bff]", " ", question or "")
    q = re.sub(r"\s+", " ", q).strip()
    if not q or len(q.split()) > 12:
        return False
    return bool(_GENERAL_FULL.match(q) or _GENERAL_START.match(q))


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = re.sub(r"[^\w\s\u0b80-\u0bff]", " ", text)
    return " " + " ".join(text.lower().split()) + " "


def lexicon_scores(question: str) -> Dict[str, int]:
    """Count how many deterministic marker words appear for each intent."""
    q = _normalize(question)
    scheme = sum(1 for m in SCHEME_MARKERS_EN if m in q)
    agri = sum(1 for m in AGRI_MARKERS_EN if m in q)
    return {"scheme": scheme, "agri": agri}


def _has_scheme_markers(question: str) -> bool:
    return lexicon_scores(question)["scheme"] > 0


# Short follow-ups that inherit the previous route ("and what documents...",
# " ellaam evvulai sollunga", "how much?", etc.). Not exhaustive — combined
# with the short-length heuristic this catches the common cases.
_FOLLOWUP_RE = re.compile(
    r"^\s*(and|also|then|so|plus|what about|what docs|which docs|how much|"
    r"how many|why|அது|இன்னும்|என்ன|எவ்வளவு|எப்படி|அடுத்த|மேலும்|"
    r"i have|we have|my land|acres?|ac\b|cents?|hectares?|ஏக்கர்|சென்ட்|"
    r"small|marginal|large|big|sf|mf|சிறு|குறு|பெரிய|yes|no|ஆமாம்|இல்லை|"
    r"borewell|well|கிணறு|ஆழ்துளை|patta|chitta|aadhaar|பட்டா|சிட்டா|ஆதார்)",
    re.IGNORECASE,
)


def _is_followup(question: str, last_route: Optional[str] = None) -> bool:
    if not question:
        return False
    q = question.strip()
    if len(q) <= 80 and _FOLLOWUP_RE.match(q):
        return True
    if len(q) <= MIN_FOLLOWUP_CHARS and _FOLLOWUP_RE.search(q):
        return True
    # If following a scheme turn, check if the user is answering land/acreage/eligibility questions
    if last_route == "scheme":
        if re.search(r"\b\d+(\.\d+)?\s*(acres?|ac\b|cents?|hectares?|ஏக்கர்|சென்ட்)?\b", q, re.IGNORECASE) and len(q) <= 60:
            return True
        if any(w in q.lower() for w in ["acre", "acres", "ஏக்கர்", "சென்ட்", "borewell", "well", "கிணறு", "patta", "பட்டா", "aadhaar", "small", "marginal", "குறு", "சிறு"]):
            return True
    # forms of address but no real content
    if len(q) <= 8 and not any(c.isalpha() for c in q):
        return False
    return False


# --------------------------------------------------------------------------
# Dataclass for the route decision
# --------------------------------------------------------------------------

@dataclass
class RouteResult:
    route: str                  # "agri" | "scheme" | "demo" | "general" | "dual"
    tier: int                   # 1 (lexicon/keyword), 2 (LLM), 0 (sticky)
    scheme_markers: int = 0
    agri_markers: int = 0
    demo_score: int = 0         # Tier-1 keyword score from links_mapping
    demo_card: Optional[str] = None
    llm_label: Optional[str] = None
    llm_confidence_logged: Optional[float] = None  # never used for policy
    llm_latency_ms: Optional[int] = None
    sticky: bool = False
    veto: bool = False          # scheme markers blocked a Tier-1 shortcut
    notes: List[str] = field(default_factory=list)

    def to_log_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route, "tier": self.tier,
            "scheme_markers": self.scheme_markers, "agri_markers": self.agri_markers,
            "demo_score": self.demo_score, "demo_card": self.demo_card,
            "llm_label": self.llm_label, "llm_conf_logged": self.llm_confidence_logged,
            "llm_latency_ms": self.llm_latency_ms, "sticky": self.sticky,
            "veto": self.veto, "notes": self.notes,
        }


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------

def classify(
    question: str,
    lang: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    last_route: Optional[str] = None,
) -> RouteResult:
    """Full synchronous classifier. LLM call only if Tier-1 doesn't resolve."""
    notes: List[str] = []
    scored = lexicon_scores(question)
    demo_card = None
    demo_score = 0

    try:
        from .links_mapping import match_service
        card = match_service(question, lang or "English")
        if card and card.get("id") != "home":
            demo_card = card["id"]
            demo_score = _demo_score(question, lang or "English")
    except Exception:
        pass

    # 1) sticky follow-up: inherit previous route regardless of content
    if last_route is None and history:
        for m in reversed(history):
            c = (m.get("content") or "").lower()
            if any(w in c for w in ["scheme", "subsidy", "pmksy", "kusum", "pmfby", "மானியம்", "திட்டம்", "eligibility", "eligible", "தகுதி"]):
                last_route = "scheme"
                break
            elif any(w in c for w in ["fertilizer", "pest", "crop", "disease", "உரம்", "பூச்சி", "பயிர்", "நோய்"]):
                last_route = "agri"
                break

    if last_route in ("agri", "scheme", "demo") and _is_followup(question, last_route=last_route) and history:
        notes.append("sticky_followup")
        return RouteResult(
            route=last_route, tier=0, sticky=True,
            scheme_markers=scored["scheme"], agri_markers=scored["agri"],
            demo_score=demo_score, demo_card=demo_card, notes=notes,
        )

    veto = _has_scheme_markers(question)

    # 1b) general conversation: recognised instantly, answered by the LLM with no retrieval
    if (scored["scheme"] == 0 and scored["agri"] == 0 and demo_card is None
            and _is_general_chat(question)):
        notes.append("general_pattern")
        return RouteResult(route="general", tier=1, notes=notes)

    # 2) Tier-1 demo short-circuit (unless scheme markers veto it)
    if demo_card and demo_score >= DEMO_ROUTE_THRESHOLD and not veto:
        return RouteResult(
            route="demo", tier=1,
            scheme_markers=scored["scheme"], agri_markers=scored["agri"],
            demo_score=demo_score, demo_card=demo_card, notes=notes,
        )

    # 2b) Fast Tier-1 Scheme shortcut: when strong scheme markers are present,
    # route to scheme immediately without wasting 1.5s waiting for Tier-2 LLM classification
    if veto:
        notes.append("tier1_scheme_fast")
        return RouteResult(
            route="scheme", tier=1,
            scheme_markers=scored["scheme"], agri_markers=scored["agri"],
            demo_score=demo_score, demo_card=demo_card, notes=notes,
        )

    # 2c) Fast Tier-1 Agri shortcut: when agronomy markers are strong and no scheme markers
    if scored["agri"] >= 2 and not veto:
        notes.append("tier1_agri_fast")
        return RouteResult(
            route="agri", tier=1,
            scheme_markers=scored["scheme"], agri_markers=scored["agri"],
            demo_score=demo_score, demo_card=demo_card, notes=notes,
        )

    # 3) Tier-2 LLM label for remaining ambiguous cases
    label, conf, latency = _llm_intent(question, lang, notes)

    # LLM says "general": only trust it when no farming/scheme/service signal is present
    if label == "general":
        if scored["scheme"] == 0 and scored["agri"] == 0 and demo_card is None:
            return RouteResult(
                route="general", tier=2, llm_label=label, llm_confidence_logged=conf,
                llm_latency_ms=latency, notes=notes + ["llm_general"],
            )
        notes.append("llm_general_overridden_by_markers")
        label = "agri" if (scored["agri"] > 0 and not veto) else None

    # --- Deterministic fallback path if the LLM Tier-2 label is unclear ---

    if label is None:
        # LLM failed / returned garbage. Decide by observable signals only.
        if scored["scheme"] >= 1:
            notes.append("lexicon_only_scheme")
            return RouteResult(
                route="scheme", tier=2,
                scheme_markers=scored["scheme"], agri_markers=scored["agri"],
                demo_score=demo_score, demo_card=demo_card,
                llm_label=None, llm_confidence_logged=None,
                llm_latency_ms=latency, veto=veto, notes=notes,
            )
        if scored["agri"] >= 1 and demo_card is None:
            notes.append("lexicon_only_agri")
            return RouteResult(
                route="agri", tier=2,
                scheme_markers=scored["scheme"], agri_markers=scored["agri"],
                demo_score=demo_score, demo_card=demo_card,
                llm_label=None, llm_confidence_logged=None,
                llm_latency_ms=latency, veto=veto, notes=notes,
            )
        notes.append("dual_arbitration_no_signals")
        return RouteResult(
            route="dual", tier=2,
            scheme_markers=scored["scheme"], agri_markers=scored["agri"],
            demo_score=demo_score, demo_card=demo_card,
            llm_label=None, llm_confidence_logged=None,
            llm_latency_ms=latency, veto=veto, notes=notes,
        )

    if label == "scheme" or (veto and label not in ("agri", "demo")):
        return RouteResult(
            route="scheme", tier=2,
            scheme_markers=scored["scheme"], agri_markers=scored["agri"],
            demo_score=demo_score, demo_card=demo_card,
            llm_label=label, llm_confidence_logged=conf,
            llm_latency_ms=latency, veto=veto, notes=notes,
        )
    if label == "demo" and not veto:
        return RouteResult(
            route="demo", tier=2,
            scheme_markers=scored["scheme"], agri_markers=scored["agri"],
            demo_score=demo_score, demo_card=demo_card,
            llm_label=label, llm_confidence_logged=conf,
            llm_latency_ms=latency, notes=notes,
        )

    if label == "agri" and not veto:
        return RouteResult(
            route="agri", tier=2,
            scheme_markers=scored["scheme"], agri_markers=scored["agri"],
            demo_score=demo_score, demo_card=demo_card,
            llm_label=label, llm_confidence_logged=conf,
            llm_latency_ms=latency, notes=notes,
        )

    # disagreement / LLM failure / mixed lexicon signals -> dual arbitration
    notes.append("dual_arbitration")
    return RouteResult(
        route="dual", tier=2,
        scheme_markers=scored["scheme"], agri_markers=scored["agri"],
        demo_score=demo_score, demo_card=demo_card,
        llm_label=label, llm_confidence_logged=conf,
        llm_latency_ms=latency, veto=veto, notes=notes,
    )


def _demo_score(question: str, lang: str) -> int:
    """Same scoring as links_mapping.match_service but returning the raw score."""
    try:
        from .links_mapping import _SERVICES, _HOME_CARD
    except Exception:
        return 0
    q = " " + (question or "").lower() + " "
    best = 0
    for card in [c for c in _SERVICES] + [_HOME_CARD]:
        s = 0
        for key in card["keys"]:
            if key.lower() in q:
                s += len(key)
        best = max(best, s)
    return best


# --------------------------------------------------------------------------
# Tier-2 LLM intent (JSON mode, few-shots optionally loaded from the dataset)
# --------------------------------------------------------------------------

_FEWSHOTS_FALLBACK = [
    ("my paddy leaves are turning yellow, what to spray", "agri"),
    ("நெல் இலை மஞ்சளாக மாறியுள்ளது, என்ன தெளிக்கிறது", "agri"),
    ("PMFBY crop insurance enrolment last date", "scheme"),
    ("முதுமை ஓய்வூதிய தொகை எவ்வளவு", "scheme"),
    ("what is the market price of tomato today", "demo"),
    ("சந்தை விலை என்ன", "demo"),
    ("banana price crashed, which scheme gives compensation", "scheme"),
    ("seed stock la irukka", "demo"),
    ("who are you and what can you do", "general"),
    ("how do I change the language", "general"),
]

_ROUTER_PROMPT = """You classify one farmer's question into exactly ONE intent:
- "agri": practical agronomy — crops, seeds, fertilizer, pest/disease, irrigation,
  soil, machinery use, weather effect on crops, harvesting, storage.
- "scheme": Tamil Nadu government welfare/schemes — subsidies, pensions,
  eligibility, application procedures, benefit amounts, insurance CLAIMS under a
  govt scheme, scheme-related compensation.
- "demo": the farmer wants a LIVE service page (market price today, weather
  TODAY, stock lists, contacts, buying/selling NOW) — something the Uzhavar demo
  app provides directly.
- "general": greetings, chit-chat, thanks, questions about the assistant or how to
  use the app, or any other message that is NOT about farming, schemes or live
  services (jokes, general knowledge, etc. - these get a polite "I can only help
  with agriculture, schemes and this app" reply, no document lookup).
Reply with STRICT JSON only: {"intent": "agri|scheme|demo|general"}
Examples:
%s

Question: %s
JSON:"""


def _fewshots() -> str:
    """Prefer real labeled rows from the dataset train split when present."""
    try:
        import io
        import json as _json
        from .config import GEMINI_API_KEY  # noqa
        path = os.path.join("data", "router_eval", "router_dataset.jsonl")
        if os.path.exists(path):
            rows = []
            with io.open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        r = _json.loads(line)
                    except Exception:
                        continue
                    if r.get("split") == "train" and r.get("hardness") != "hard":
                        rows.append(r)
            if len(rows) >= 12:
                import random
                random.seed(42)
                picks = random.sample(rows, 8)
                return "\n".join(
                    f"Q: {r['question']} -> {r['intent']}" for r in picks
                )
    except Exception:
        pass
    return "\n".join(f"Q: {q} -> {i}" for q, i in _FEWSHOTS_FALLBACK)


def _llm_intent(question: str, lang: Optional[str], notes: List[str]):
    """Returns (label, confidence, latency_ms) or (None, None, latency).

    Two attempts are made per call: 3.x flash-lite occasionally returns an
    empty text with finish_reason=SAFETY/RECITATION on the first pass but
    succeeds on retry — the intermittent 'dual' flip in the harness is
    exactly that, and a retry makes classification deterministic in practice.
    """
    for attempt in range(2):
        label, conf, lat = _llm_intent_once(question, lang, notes, attempt)
        if label is not None:
            return label, conf, lat
        if attempt == 0:
            notes.append("retry_llm_intent")
    return None, None, lat


def _llm_intent_once(question: str, lang: Optional[str], notes: List[str], attempt: int):
    from .config import GEMINI_API_KEY, GEMINI_ROUTER_MODEL
    if not GEMINI_API_KEY:
        notes.append("no_gemini_key")
        return None, None, None

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = _ROUTER_PROMPT % (
            _fewshots(),
            question,
        )
        t0 = time.perf_counter()
        resp = client.models.generate_content(
            model=GEMINI_ROUTER_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                max_output_tokens=30,   # JSON fits; too tight truncates on 3.x
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        latency = int((time.perf_counter() - t0) * 1000)
        raw = (resp.text or "").strip()
        parsed = json.loads(raw)
        label = str(parsed.get("intent", "")).strip().lower()
        conf = parsed.get("confidence")
        try:
            conf = float(conf) if conf is not None else None
        except Exception:
            conf = None
        if label in ("agri", "scheme", "demo", "general"):
            return label, conf, latency
        notes.append(f"bad_label:{raw[:60]}")
        return None, conf, latency
    except json.JSONDecodeError:
        # Flash sometimes pads JSON with a leading "Sure!" line or trailing
        # commentary — retry by extracting the first {...} block.
        try:
            resp.text = resp.text   # no-op; keep structure obvious
        except Exception:
            pass
        m = re.search(r"\{[^}]*\}", raw)
        if m:
            try:
                parsed = json.loads(m.group(0))
                label = str(parsed.get("intent", "")).strip().lower()
                conf = parsed.get("confidence")
                try:
                    conf = float(conf) if conf is not None else None
                except Exception:
                    conf = None
                if label in ("agri", "scheme", "demo", "general"):
                    return label, conf, latency
                notes.append(f"bad_label_after_extract:{m.group(0)[:60]}")
                return None, conf, latency
            except Exception:
                notes.append(f"jsonextract_fail:{raw[:60]}")
                return None, None, latency
        notes.append(f"raw_json_missing:{raw[:60]}")
        return None, None, latency
    except Exception as e:
        # Free-tier 15 RPM per-model quota: a 429 mid-harness looks like an
        # LLM refusal — tag it clearly; the policy's label=None path already
        # falls back to lexicon signals deterministically (no free-text
        # generation, no fake fallback route).
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e)[:120]:
            notes.append("llm_429")
        else:
            notes.append(f"llm_error:{type(e).__name__}")
        return None, None, None


# --------------------------------------------------------------------------
# Router log (feeds the dataset in Phase 1; human-corrected weekly)
# --------------------------------------------------------------------------

def log_route(question: str, lang: Optional[str], rr: RouteResult,
              final_route: Optional[str] = None, latency_ms: int = 0,
              log_path: str = os.path.join("data", "router_log.jsonl")) -> None:
    try:
        d = rr.to_log_dict()
        rec = {
            "ts": int(time.time()),
            "question": question,
            "lang": lang,
            "final_route": final_route or rr.route,
            "latency_ms": latency_ms,
            **d,
        }
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass  # logging must never break the chat
