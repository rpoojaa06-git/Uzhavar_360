import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Route C (government schemes) uses the stronger flash model: scheme answers
# carry eligibility percentages and subsidy amounts where numeric fidelity
# matters more than speed.
GEMINI_SCHEME_MODEL = os.getenv("GEMINI_SCHEME_MODEL", "gemini-2.5-flash")  # verified working
# Route A agronomy generator. gemini-2.5-flash-lite is retired for new keys;
# default follows the router lite model (verified working for JSON+text).
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
# Router Tier-2 model (classification only; answers never come from this call).
# NOTE: gemini-2.5-flash-lite returns 404 for NEW api keys (Google retired it
# for new users); gemini-3.1-flash-lite is the current lite tier and verified working.
GEMINI_ROUTER_MODEL = os.getenv("GEMINI_ROUTER_MODEL", "gemini-3.1-flash-lite")

QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
# Route A corpus (agronomy: ICAR/_crop/machinery PDFs in data/)
COLLECTION_AGRI = os.getenv("COLLECTION_AGRI", os.getenv("COLLECTION_NAME", "uzhavar_agri"))
# Route C corpus (TN Farmer Welfare Dept Citizen Charter 2025-26, data/schemes/)
COLLECTION_SCHEMES = os.getenv("COLLECTION_SCHEMES", "uzhavar_schemes")

# --- Routing policy constants (observable signals only, no self-reported LLM
# confidence gates routing decisions) ---
# Tier-1 demo keyword score required to short-circuit to Route B
DEMO_ROUTE_THRESHOLD = int(os.getenv("DEMO_ROUTE_THRESHOLD", "12"))
# Below this rerank score Route C refuses to quote. Recalibrated for the
# mapped charter (a real scheme hit can score as low as 0.37 — e.g. "free
# soil sampling" at 0.369): OOS ceiling 0.033, floor 0.25 keeps a wide
# verified margin on both sides.
SCHEME_SCORE_FLOOR = float(os.getenv("SCHEME_SCORE_FLOOR", "0.25"))
# Dual-arbitration margin: |best_agri - best_scheme| <= MARGIN -> answer the
# corpus with stronger evidence (ties logged; >15% tie-rate triggers lexicon work)
ARBITRATION_MARGIN = float(os.getenv("ARBITRATION_MARGIN", "0.10"))
# Sticky multi-turn follow-ups shorter than this inherit the previous route
MIN_FOLLOWUP_CHARS = int(os.getenv("MIN_FOLLOWUP_CHARS", "40"))

TOP_K = int(os.getenv("TOP_K", "8"))
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "4"))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")

# Sarvam AI TTS (optional — natural Indian-language voice)
# Add SARVAM_API_KEY to .env to enable; speaker default: shubh (bulbul:v3)
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
SARVAM_TTS_SPEAKER = os.getenv("SARVAM_TTS_SPEAKER", "shubh")
SARVAM_STT_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v3")