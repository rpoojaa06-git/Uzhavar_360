"""
Uzhavar Demo Deep-Link Mapper
================================================================================
Deterministic, keyword-based matcher that maps a farmer's question to one of the
24 service pages of the Uzhavar sample/demo UI (uzhavar-ui repo), so the voice
chatbot can append a ready-to-click deep link to its grounded answer.

The demo app is a HashRouter SPA, so every deep link is:

    https://uzhavar-demo.vercel.app/#/<service-id>

This module is intentionally rule-based (no LLM calls): cheap, auditable and
stable. Matching score = total length of matched keyword phrases; a match
needs at least MIN_SCORE characters of matched keywords (a long specific
phrase alone can qualify; short generic words need corroboration).

Public API
----------
match_service(question, lang)  -> dict | None   (service card or special dict)
deep_demo_url()                -> root URL of the demo app
build_link_tail(card, lang)    -> markdown block appended to the answer
"""
from __future__ import annotations

from typing import Dict, List, Optional

DEMO_BASE_URL = "https://uzhavar-demo.vercel.app/#/"
DEMO_HOME_URL = DEMO_BASE_URL
DEMO_LINKS_URL = DEMO_BASE_URL + "links"

MIN_SCORE = 8  # total matched keyword characters required for a link match

# id, bilingual label (labels mirror src/data/services.ts exactly), search keywords
_SERVICES: List[Dict] = [
    {"id": "tamil-mannvalam", "en": "Tamil Mannvalam", "ta": "தமிழ் மண்வளம்", "emoji": "🌍",
     "keys": ["mann valam", "mannvalam", "soil health", "soil type", "soil report", "மண்வளம்", "மண் வளம்", "மண் வகை", "மண் அறிக்கை"]},
    {"id": "subsidy-scheme", "en": "Subsidy Scheme", "ta": "மானிய திட்டம்", "emoji": "💰",
     "keys": ["subsidy scheme", "subsidy", "மானியம்", "மானிய திட்டம்"]},
    {"id": "benefit-registration", "en": "Benefit Registration", "ta": "நல பதிவு", "emoji": "🤝",
     "keys": ["benefit registration", "register benefits", "நல பதிவு", "நலத்திட்டம்"]},
    {"id": "crop-insurance", "en": "Crop Insurance", "ta": "பயிர் காப்பீடு", "emoji": "🛡️",
     "keys": ["crop insurance", "insurance claim", "pmfby", "பயிர் காப்பீடு", "காப்பீடு"]},
    {"id": "fertilizer-stock", "en": "Fertilizer Stock", "ta": "உரம் கையிருப்பு", "emoji": "🧪",
     "keys": ["fertilizer stock", "fertiliser stock", "urea stock", "fertilizer stock list", "உரம் கையிருப்பு", "உர கையிருப்பு"]},
    {"id": "seed-stock", "en": "Seed Stock", "ta": "விதை கையிருப்பு", "emoji": "🌱",
     "keys": ["seed stock", "seed availability", "விதை கையிருப்பு", "விதை கிடைப்பு"]},
    {"id": "machinery-rental", "en": "Agricultural Machinery for Rental", "ta": "விவசாய இயந்திர வாடகை", "emoji": "🛻",
     "keys": ["machinery rental", "machine rental", "tractor rental", "rent a tractor", "tractor for rent", "hire tractor", "இயந்திர வாடகை", "டிராக்டர் வாடகை"]},
    {"id": "market-price", "en": "Market Price", "ta": "சந்தை விலை", "emoji": "💹",
     "keys": ["market price", "current price", "selling price", "price list", "price of", "price for",
              "at what price", "what price", "rate of", "mandi rate", "tomato price", "onion price",
              "சந்தை விலை", "விலை விவரம்", "விலை என்ன", "என்ன விலை", "விலை எவ்வளவு"]},
    {"id": "weather-advisory", "en": "Weather Advisory", "ta": "வானிலை ஆலோசனை", "emoji": "🌦️",
     "keys": ["weather advisory", "weather forecast", "rain forecast", "rain warning", "weather report", "weather", "வானிலை", "மழை எச்சரிக்கை"]},
    {"id": "officer-contact", "en": "Farmer Officer Contact Program", "ta": "அதிகாரி தொடர்பு திட்டம்", "emoji": "👤",
     "keys": ["officer contact", "agricultural officer", "block agriculture officer", "அதிகாரி தொடர்பு", "வேளாண் அதிகாரி"]},
    {"id": "farm-guide", "en": "Farm Guide", "ta": "பண்ணை வழிகாட்டி", "emoji": "📚",
     "keys": ["farm guide", "cultivation guide", "பண்ணை வழிகாட்டி", "சாகுபடி வழிகாட்டி"]},
    {"id": "organic-products", "en": "Organic Products", "ta": "இயற்கை பொருட்கள்", "emoji": "🍃",
     "keys": ["organic products", "organic farming products", "இயற்கை பொருட்கள்"]},
    {"id": "fpo-products", "en": "FPO Products", "ta": "FPO பொருட்கள்", "emoji": "🏪",
     "keys": ["fpo products", "fpo", "FPO பொருட்கள்"]},
    {"id": "reservoir-levels", "en": "Reservoir Levels", "ta": "அணை நீர்மட்டம்", "emoji": "💧",
     "keys": ["reservoir level", "reservoir levels", "dam level", "dam water level", "lake level", "அணை நீர்மட்டம்", "அணை நீர்"]},
    {"id": "agri-news", "en": "Agriculture News", "ta": "வேளாண் செய்திகள்", "emoji": "🗞️",
     "keys": ["agriculture news", "agri news", "latest news", "வேளாண் செய்திகள்"]},
    {"id": "feedback", "en": "Feedback", "ta": "கருத்து தெரிவிப்பு", "emoji": "✍️",
     "keys": ["feedback", "complaint", "suggestion", "கருத்து தெரிவிப்பு", "கருத்து தெரிவி", "புகார்"]},
    {"id": "pest-disease", "en": "Pest/Disease Monitoring", "ta": "பூச்சி/நோய் கண்காணிப்பு", "emoji": "🐛",
     "keys": ["pest control", "pest management", "pest monitoring", "pest", "disease", "பூச்சி", "நோய்"]},
    {"id": "atma-training", "en": "ATMA Training & Demonstration", "ta": "ATMA பயிற்சி & காட்சி", "emoji": "👨‍🏫",
     "keys": ["atma training", "atma", "training programme", "training program", "பயிற்சி"]},
    {"id": "e-market", "en": "Uzhavar e-Market", "ta": "உழவர் இ-சந்தை", "emoji": "🛒",
     "keys": ["e-market", "e market", "emarket", "online market", "uzhavar e-market",
              "buy", "sell", "selling", "buying", "purchase", "order", "shop", "marketplace",
              "where to sell", "where can i sell", "where to buy", "where can i buy",
              "i want to sell", "i want to buy", "விற்க", "வாங்க", "விற்க வேண்டும்",
              "வாங்க வேண்டும்", "விற்பனை", "வாங்குதல்"]},
    {"id": "sericulture", "en": "Department of Sericulture", "ta": "பட்டு வளர்ப்புத் துறை", "emoji": "🦋",
     "keys": ["sericulture", "silk", "பட்டு", "பட்டு வளர்ப்பு"]},
    {"id": "agri-budget", "en": "Agri Budget", "ta": "வேளாண் நிதிநிலை", "emoji": "📊",
     "keys": ["agri budget", "agriculture budget", "வேளாண் நிதிநிலை", "நிதிநிலை"]},
    {"id": "kadp", "en": "KADP", "ta": "கலைஞர் வேளாண் திட்டம்", "emoji": "🏛️",
     "keys": ["kadp", "kalaignar", "கலைஞர் வேளாண்", "கலைஞர் திட்டம்"]},
    {"id": "palmyra-felling", "en": "Applying for Felling of Palmyra Trees", "ta": "பனை வெட்டு அனுமதி", "emoji": "🌴",
     "keys": ["palmyra", "palmyra felling", "felling", "tree cutting", "பனை வெட்டு", "பனை மரம்", "பனை"]},
    {"id": "green-mission", "en": "TN Green Mission — Tree Seedlings", "ta": "பசுமை இயக்கம் — மரக்கன்றுகள்", "emoji": "🌳",
     "keys": ["green mission", "tree seedlings", "seedlings", "பசுமை இயக்கம்", "பசுமை", "மரக்கன்று"]},
]

_HOME_CARD: Dict = {
    "id": "home", "en": "Home — All 24 Services", "ta": "முகப்பு — அனைத்து 24 சேவைகள்",
    "emoji": "🏠",
    "keys": ["uzhavar app", "uzhavar demo", "the uzhavar", "about the uzhavar", "all services", "all the services",
             "all 24", "full demo", "entire app", "all the links", "links page",
             "demo app", "sample ui", "sample app", "the app", "your app", "open the app", "show the app",
             "app home", "home page", "main page", "what about the app", "tell me about the app",
             "செயலி", "செயலியை", "மாதிரி செயலி", "உழவர் செயலி",
             "அனைத்து சேவைகள்", "முகப்பு பக்கம்", "லிங்க் பக்கம்", "செயலி லிங்க்"],
}


def deep_demo_url() -> str:
    """Root of the demo app (home grid)."""
    return DEMO_HOME_URL


def demo_links_page_url() -> str:
    """Cheat-sheet page that lists every deep link."""
    return DEMO_LINKS_URL


def match_service(question: str, _lang: str = "English") -> Optional[Dict]:
    """
    Deterministically map the question to a demo service (or the home card).
    Returns a copy of the card dict, or None when nothing matches clearly.
    Score = total length of matched keyword phrases; MIN_SCORE required.
    Earlier entries win ties (registry order mirrors the demo UI grid).
    """
    if not question:
        return None
    q = " " + question.lower() + " "
    best: Optional[Dict] = None
    best_score = 0
    for card in [c for c in _SERVICES] + [_HOME_CARD]:
        score = 0
        for key in card["keys"]:
            if key.lower() in q:
                score += len(key)
        if score > best_score:
            best, best_score = card, score
    return dict(best) if best_score >= MIN_SCORE else None


def service_url(card: Dict) -> str:
    if card.get("id") == "home":
        return DEMO_HOME_URL
    return DEMO_BASE_URL + (card["id"] or "")


def spoken_instruction(card: Dict, lang: str) -> str:
    if lang == "Tamil":
        label = card["ta"]
        return (f"இதற்கு, Uzhavar மாதிரி செயலியில் {label} பக்கம் உள்ளது — "
                "இந்த பதிலுக்கு கீழே உள்ள லிங்கை தட்டவும்.")
    label = card["en"]
    return (f"For this, the Uzhavar demo app has a {label} page — "
            "tap the link shown below this answer.")


def build_link_tail(card: Dict, lang: str) -> str:
    """
    Markdown block appended to an answer: a clickable card with the visible
    URL plus the spoken instruction. The TTS cleaner strips the raw URL from
    speech, so the farmer only hears the instruction.
    """
    label = f"{card['en']} · {card['ta']}"
    instruction = spoken_instruction(card, lang)
    return (
        "\n\n---\n\n"
        f"{card['emoji']} **Uzhavar demo app — {label}**\n\n"
        f"🔗 {service_url(card)}\n\n"
        f"👉 {instruction}"
    )


def all_services() -> List[Dict]:
    return [dict(c) for c in _SERVICES]
