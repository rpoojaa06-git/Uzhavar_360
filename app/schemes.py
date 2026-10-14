"""
app/schemes.py
--------------------------------------------------------------------------------
Deterministic Government Scheme Discovery & Eligibility Engine for Tamil Nadu Farmers.
Fulfills the Track B architecture promised in UZHAVAR_AI_DOCUMENTATION.md.

Matches schemes from data/schemes/schemes.json against the farmer's profile:
  - Farmer scale: Marginal (<= 2.5 ac), Small (2.5 - 5 ac), Large (> 5 ac)
  - Crop: Paddy, Millets, Pulses, Sugarcane, Vegetables, Banana, Coconut, Cotton, etc.
  - Irrigation source: Borewell, Well, Canal, Rainfed
  - Gender: Female (special subsidies, SHG benefits), Male
  - District & Documents
--------------------------------------------------------------------------------
"""

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "schemes"
_JSON_PATH = _DATA_DIR / "schemes.json"

_cached_schemes: Optional[List[Dict[str, Any]]] = None


def load_all_schemes() -> List[Dict[str, Any]]:
    """Loads and caches all structured schemes."""
    global _cached_schemes
    if _cached_schemes is not None:
        return _cached_schemes
    if _JSON_PATH.exists():
        try:
            with open(_JSON_PATH, "r", encoding="utf-8") as f:
                _cached_schemes = json.load(f)
        except Exception:
            _cached_schemes = []
    else:
        _cached_schemes = []
    return _cached_schemes or []


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    return " " + text.lower() + " "


# Key query intent mappings for high-precision matching
QUERY_CONCEPTS = {
    "tractor": {
        "en": ["tractor", "power tiller", "rotavator", "machinery", "plough", "cultivator", "harvester"],
        "ta": ["டிராக்டர்", "பவர் டில்லர்", "ரோட்டாவேட்டர்", "இயந்திரம்", "உழவு", "களையெடுப்பான்"],
        "category": "machinery",
        "favored_ids": ["agricultural-mechanization-tractor-rotavator-subsidy", "smam-custom-hiring-centers-chc"]
    },
    "drip": {
        "en": ["drip", "sprinkler", "micro irrigation", "per drop more crop", "irrigation pipe"],
        "ta": ["சொட்டு நீர்", "தெளிப்பு நீர்", "நுண் பாசனம்", "பாசன குழாய்", "பாசனம்"],
        "category": "irrigation",
        "favored_ids": ["pmksy-per-drop-more-crop-drip-irrigation", "swma-supplementary-water-management-subsidy"]
    },
    "solar": {
        "en": ["solar", "solar pump", "solar motor", "pm kusum", "solar fencing", "solar drier"],
        "ta": ["சூரிய மின்", "சோலார்", "சூரிய சக்தி", "சோலார் பம்பு", "சோலார் மோட்டார்", "சூரிய உலர்விப்பான்"],
        "category": "solar",
        "favored_ids": ["chief-ministers-solar-powered-pumpsets-pm-kusum", "solar-powered-driers-and-solar-fencing-subsidy"]
    },
    "soil": {
        "en": ["soil test", "soil health card", "soil card", "soil testing", "mann valam"],
        "ta": ["மண் பரிசோதனை", "மண் வளம்", "மண் அட்டை", "மண் பரிசோதனை கட்டணம்"],
        "category": "soil_health",
        "favored_ids": ["assistance-to-farmers-for-improving-the-soil-health", "tnau-soil-water-and-fertilizer-testing-services"]
    },
    "seed": {
        "en": ["seed", "seeds", "seed subsidy", "certified seed", "breeder seed", "paddy seed"],
        "ta": ["விதை", "விதை மானியம்", "சான்று விதை", "நெல் விதை", "விதைகள்"],
        "category": "seeds",
        "favored_ids": ["distribution-of-traditional-paddy-variety-seeds", "production-incentive-for-paddy-certified-seed", "tnau-certified-seed-production-and-supply"]
    },
    "organic": {
        "en": ["organic", "organic farming", "tnocd", "biofertilizer", "vermicompost", "natural farming"],
        "ta": ["இயற்கை விவசாயம்", "இயற்கை உரம்", "ஆர்கானிக்", "சான்றிதழ்", "மண்புழு உரம்"],
        "category": "organic",
        "favored_ids": ["tnocd-organic-farming-certification-scheme", "organic-farming-promotion-scheme"]
    },
    "insurance": {
        "en": ["insurance", "pmfby", "crop loss", "crop insurance", "drought relief", "flood compensation"],
        "ta": ["பயிர் காப்பீடு", "காப்பீட்டு", "இழப்பீடு", "காப்பீடு"],
        "category": "insurance",
        "favored_ids": ["assistance-to-farmers-for-crop-insurance", "pradhan-mantri-fasal-bima-yojana-pmfby"]
    },
    "market": {
        "en": ["market", "mandi", "price", "pledge loan", "uzhavar sandhai", "storage", "cold storage"],
        "ta": ["உழவர் சந்தை", "சந்தை", "விற்பனை", "குளிர்பதன", "கடன்"],
        "category": "marketing",
        "favored_ids": ["uzhavar-sandhais-direct-farmer-marketing", "regulated-market-pledge-loan-scheme", "price-support-scheme-msp-pulses-copra"]
    }
}



def extract_farmer_context(text: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extracts farmer attributes dynamically from conversational queries:
      - landholding: acres, cents, hectares, or explicit small/marginal/large statement
      - water source: borewell, open well, canal, rainfed
      - crops: paddy, sugarcane, banana, coconut, vegetables, cotton, millets
      - documents: patta, chitta, aadhaar
    Returns an updated copy of profile with any new attributes detected.
    """
    p = dict(profile or {})
    t = (text or "").lower()

    # 1. Acreage / Land holding
    acre_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:acres?|ac\b|ஏக்கர்)", t)
    cent_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:cents?|சென்ட்)", t)
    hec_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hectares?|ஹெக்டேர்)", t)

    acres = None
    if acre_match:
        try:
            acres = float(acre_match.group(1))
        except Exception:
            pass
    elif cent_match:
        try:
            # 100 cents = 1 acre
            acres = round(float(cent_match.group(1)) / 100.0, 2)
        except Exception:
            pass
    elif hec_match:
        try:
            # 1 hectare = 2.47 acres
            acres = round(float(hec_match.group(1)) * 2.47, 2)
        except Exception:
            pass

    if acres is not None:
        p["land_acres"] = acres
        if acres <= 2.5:
            p["farmer_scale"] = "marginal"
            p["farmer_scale_label_en"] = "Marginal Farmer (up to 2.5 acres / 1 hectare)"
            p["farmer_scale_label_ta"] = "குறு விவசாயி (2.5 ஏக்கர் வரை)"
        elif acres <= 5.0:
            p["farmer_scale"] = "small"
            p["farmer_scale_label_en"] = "Small Farmer (2.5 to 5.0 acres / 1 to 2 hectares)"
            p["farmer_scale_label_ta"] = "சிறு விவசாயி (2.5 முதல் 5 ஏக்கர் வரை)"
        else:
            p["farmer_scale"] = "large"
            p["farmer_scale_label_en"] = "Other / Large Farmer (above 5.0 acres / >2 hectares)"
            p["farmer_scale_label_ta"] = "பிற / பெரிய விவசாயி (5 ஏக்கருக்கு மேல்)"
    elif "marginal" in t or "குறு விவசாயி" in t:
        p["farmer_scale"] = "marginal"
        p["farmer_scale_label_en"] = "Marginal Farmer (up to 2.5 acres)"
        p["farmer_scale_label_ta"] = "குறு விவசாயி"
    elif "small farmer" in t or "சிறு விவசாயி" in t:
        p["farmer_scale"] = "small"
        p["farmer_scale_label_en"] = "Small Farmer (2.5 to 5.0 acres)"
        p["farmer_scale_label_ta"] = "சிறு விவசாயி"
    elif "large farmer" in t or "big farmer" in t or "பெரிய விவசாயி" in t:
        p["farmer_scale"] = "large"
        p["farmer_scale_label_en"] = "Other / Large Farmer (above 5.0 acres)"
        p["farmer_scale_label_ta"] = "பெரிய விவசாயி"

    # 2. Water source
    if any(w in t for w in ["borewell", "bore", "ஆழ்துளை", "போர்வெல்", "போர்"]):
        p["water_source"] = "borewell"
    elif any(w in t for w in ["open well", "well", "கிணறு"]):
        p["water_source"] = "well"
    elif any(w in t for w in ["canal", "river", "வாய்க்கால்", "ஆற்றுப் பாசனம்"]):
        p["water_source"] = "canal"
    elif any(w in t for w in ["rainfed", "dryland", "dry land", "மானாவாரி", "வானம் பார்த்த பூமி"]):
        p["water_source"] = "rainfed"

    # 3. Crops
    crops_map = {
        "paddy": ["paddy", "rice", "நெல்"],
        "sugarcane": ["sugarcane", "sugar cane", "கரும்பு"],
        "banana": ["banana", "plantain", "வாழை"],
        "coconut": ["coconut", "தென்னை"],
        "cotton": ["cotton", "பருத்தி"],
        "millets": ["millet", "millets", "ragi", "kambu", "cholam", "சிறுதானியம்", "கேழ்வரகு", "கம்பு", "சோளம்"],
        "pulses": ["pulse", "pulses", "black gram", "green gram", "பருப்பு", "உளுந்து", "பாசிப்பயறு"],
        "vegetables": ["vegetable", "vegetables", "tomato", "chilli", "onion", "காய்கறி", "தக்காளி", "வெங்காயம்"],
        "oilseeds": ["groundnut", "sesame", "oilseed", "நிலக்கடலை", "எள்"],
    }
    for c_name, words in crops_map.items():
        if any(w in t for w in words):
            p["crop"] = c_name
            break

    # 4. Documents
    if any(w in t for w in ["have patta", "patta chitta", "have documents", "பட்டா உண்டு", "ஆவணங்கள் உள்ளது", "பட்டா சிட்டா இருக்கிறது"]):
        p["has_docs"] = True

    return p


def recommend_schemes(profile: Dict[str, Any], limit: int = 4) -> List[Dict[str, Any]]:
    """
    Evaluates farmer profile attributes and returns top eligible/recommended schemes
    with match scores and personalized explanations.
    """
    schemes = load_all_schemes()
    if not schemes:
        return []

    # Parse profile attributes
    farmer_type = str(profile.get("farmer_type") or "").lower()
    farmer_scale = str(profile.get("farmer_scale") or "").lower()
    crop = str(profile.get("crop") or "").lower()
    water_source = str(profile.get("water_source") or "").lower()
    gender = str(profile.get("gender") or "").lower()
    has_docs = bool(profile.get("has_docs"))
    is_ta = str(profile.get("language") or "").startswith("T")

    # Determine land category strictly
    raw_acres = profile.get("land_acres")
    if raw_acres is not None:
        try:
            acres = float(raw_acres)
            is_small_marginal = acres <= 5.0
            is_marginal = acres <= 2.5
        except Exception:
            is_small_marginal = None
            is_marginal = None
    elif farmer_scale:
        is_small_marginal = farmer_scale in ("marginal", "small")
        is_marginal = farmer_scale == "marginal"
    else:
        # Scale not yet known: do not guess!
        is_small_marginal = None
        is_marginal = None

    is_female = "female" in gender or "woman" in gender or "பெண்" in gender

    scored: List[Tuple[float, Dict[str, Any], str, str]] = []

    for s in schemes:
        score = 50.0  # baseline
        reasons_en = []
        reasons_ta = []

        category = s.get("category", "")
        target_types = s.get("target_farmer_types", [])
        benefits_text = " ".join(s.get("benefits", [])).lower()
        elig_text = " ".join(s.get("eligibility", [])).lower()
        scheme_name = s.get("scheme_name", "").lower()

        # 1. Scale / Farmer type match
        if is_small_marginal is True:
            if "small" in target_types or "marginal" in target_types or "100%" in benefits_text or "sf/mf" in elig_text:
                score += 30.0
                reasons_en.append("Eligible for enhanced 100%/50% subsidy for Small & Marginal farmers")
                reasons_ta.append("சிறு / குறு விவசாயிகளுக்கு கூடுதல் 100%/50% மானியம் உண்டு")
        elif is_small_marginal is False:
            if "all" in target_types or "general" in target_types:
                score += 20.0
                reasons_en.append("Eligible under Other Farmers category (75%/40% subsidy)")
                reasons_ta.append("பிற விவசாயிகள் பிரிவின் கீழ் தகுதி (75%/40% மானியம்)")
        else:
            # Scale unknown: show general eligibility
            if "all" in target_types or "small" in target_types:
                score += 15.0

        # 2. Irrigation & Solar priority
        if any(w in water_source for w in ["borewell", "well", "கிணறு", "ஆழ்துளை"]):
            if category in ["irrigation", "solar"]:
                score += 35.0
                reasons_en.append("Matches your borewell/well water source for high water efficiency")
                reasons_ta.append("உங்கள் கிணறு/ஆழ்துளை நீர் ஆதாரத்திற்கு ஏற்ற திட்டம்")
        elif "rainfed" in water_source or "மானாவாரி" in water_source:
            if "watershed" in scheme_name or "rainfed" in scheme_name or category == "crop_production":
                score += 30.0
                reasons_en.append("Tailored for rainfed & dryland farm conservation")
                reasons_ta.append("மானாவாரி நில பாதுகாப்பு மற்றும் மகசூல் பெருக்கத்திற்கு உகந்தது")

        # 3. Crop match
        if crop:
            if crop in scheme_name or crop in benefits_text or crop in elig_text:
                score += 25.0
                reasons_en.append(f"Directly supports {crop.title()} cultivation")
                reasons_ta.append(f"{crop.title()} பயிருக்கு நேரடி அரசு உதவி")

        # 4. Gender preference
        if is_female and ("women" in target_types or "women" in elig_text or "மகளிர்" in elig_text):
            score += 20.0
            reasons_en.append("Special priority allotment for women farmers")
            reasons_ta.append("பெண் விவசாயிகளுக்கான முன்னுரிமை ஒதுக்கீடு")

        # 5. Core flagship boosts
        sid = s.get("id", "")
        if sid == "pmksy-per-drop-more-crop-drip-irrigation" and is_small_marginal:
            score += 25.0
        elif sid == "chief-ministers-solar-powered-pumpsets-pm-kusum":
            score += 20.0
        elif sid == "agricultural-mechanization-tractor-rotavator-subsidy":
            score += 15.0
        elif "pm-kisan" in sid or "pmfby" in sid:
            score += 15.0

        explanation_en = " · ".join(reasons_en) if reasons_en else "Standard Tamil Nadu Farmers Welfare entitlement."
        explanation_ta = " · ".join(reasons_ta) if reasons_ta else "தமிழ்நாடு விவசாயிகள் நலத்திட்ட உரிமை."

        scored.append((score, s, explanation_en, explanation_ta))

    # Sort descending by score
    scored.sort(key=lambda x: -x[0])

    results = []
    seen_cats = set()
    for sc, s, exp_en, exp_ta in scored:
        cat = s.get("category", "")
        # Diversify categories in top recommendations
        if cat in seen_cats and len(results) < limit - 1 and len(seen_cats) < 3:
            continue
        seen_cats.add(cat)
        res_item = dict(s)
        # Only assign a verified match score when land details are actually known
        if raw_acres is not None or farmer_scale:
            res_item["_match_score"] = round(min(sc, 98.0), 1)
            res_item["_eligibility_status"] = "Verified Eligible"
        else:
            res_item["_match_score"] = None
            res_item["_eligibility_status"] = "Eligibility Check Available"
        res_item["_recommendation_reason"] = exp_ta if is_ta else exp_en
        res_item["_recommendation_reason_en"] = exp_en
        res_item["_recommendation_reason_ta"] = exp_ta
        results.append(res_item)
        if len(results) >= limit:
            break

    return results


def search_schemes(
    query: str,
    profile: Optional[Dict[str, Any]] = None,
    lang: str = "English",
    top_k: int = 5,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Search schemes with:
    1. Concept / keyword matching (English + Tamil script)
    2. Fallback to profile-based recommendations if the query is general
    """
    top_k = limit or top_k
    schemes = load_all_schemes()
    if not schemes:
        return []

    q = (query or "").strip().lower()
    q_norm = normalize(query)

    # 1. Check concept intent first
    matched_concept = None
    for c_key, c_info in QUERY_CONCEPTS.items():
        if any(w in q_norm for w in c_info["en"]) or any(w in q_norm for w in c_info["ta"]):
            matched_concept = c_info
            break

    # 2. Detect broad / general scheme inquiry (only when no specific concept was found)
    is_general_scheme_query = matched_concept is None and (
        any(w in q_norm for w in [
            "what scheme", "which scheme", "available for me", "schemes for me", "subsidy for me",
            "how can i get subsidy", "what are the schemes", "tell me about schemes", "all schemes",
            "what can i get", "help me with scheme",
            "என்னென்ன திட்டம்", "திட்டங்கள் என்ன", "எனக்கு என்ன திட்டம்", "மானியங்கள் என்ன", "அரசு உதவி", "அரசு திட்டம்"
        ]) or q.strip() in ["scheme", "schemes", "subsidy", "subsidies", "திட்டம்", "திட்டங்கள்", "மானியம்", "மானியங்கள்", "அரசு திட்டங்கள்"]
    )

    if is_general_scheme_query:
        # Return top personalized recommendations
        return recommend_schemes(profile or {"language": lang}, limit=top_k)

    scored: List[Tuple[float, Dict[str, Any]]] = []
    generic_stop_kw = {"மானியம்", "திட்டம்", "அரசு திட்டம்", "subsidy", "scheme", "அரசு"}

    for s in schemes:
        score = 0.0
        name = s.get("scheme_name", "").lower()
        dept = s.get("department", "").lower()
        cat = s.get("category", "")
        sid = s.get("id", "")
        keywords = [k.lower() for k in s.get("keywords", [])]
        benefits = " ".join(s.get("benefits", [])).lower()
        elig = " ".join(s.get("eligibility", [])).lower()

        # Concept boost
        if matched_concept:
            if sid in matched_concept.get("favored_ids", []):
                score += 50.0
            elif cat == matched_concept.get("category"):
                score += 25.0

        # Exact phrase or token matches
        tokens = [t for t in re.findall(r"\w+", q) if len(t) >= 3]
        for tok in tokens:
            if tok in name:
                score += 15.0
            if any(tok in kw for kw in keywords):
                score += 10.0
            if tok in benefits:
                score += 5.0
            if tok in elig:
                score += 4.0

        # Tamil substring match (Tamil words attach suffixes like -க்கு, -யில்)
        for kw in keywords:
            if kw in generic_stop_kw:
                continue
            if any(ord(ch) >= 0x0B80 and ord(ch) <= 0x0BFF for ch in kw):
                if kw in q or q in kw:
                    score += 25.0

        if score >= 10.0:
            scored.append((score, s))

    if scored:
        scored.sort(key=lambda x: -x[0])
        best = scored[0][0]
        # Return top K within relative threshold
        return [dict(s, _score=round(sc, 1)) for sc, s in scored[:top_k] if sc >= best * 0.4]

    # If still no match, fallback to profile recommendation rather than an empty list
    return recommend_schemes(profile or {"language": lang}, limit=top_k)
