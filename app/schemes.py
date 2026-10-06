"""
Uzhavar AI - Deterministic Government Scheme Eligibility Engine
Implements Section 8, 9, 10, 11 of Uzhavar AI architecture.

Core Principles:
1. Eligibility is handled deterministically, separated from the LLM.
2. Evaluates farmer profile against official government criteria (District, Crop, Land acres, Farmer Category).
3. Produces potential match score, transparent reasons, and official Uzhavar portal link.
4. Transparent disclaimer: "Final eligibility is subject to government verification."
"""

from typing import List, Dict, Any, Optional
import re

# Curated Tamil Nadu Government Agricultural Schemes
TAMIL_NADU_SCHEMES: List[Dict[str, Any]] = [
    {
        "id": "pmksy_micro_irrigation",
        "name": "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY) - Micro Irrigation Support",
        "tamil_name": "நுண்ணீர்ப் பாசனத் திட்டம் (சொட்டு நீர் / தெளிப்பு நீர் பாசனம்)",
        "category": "Irrigation",
        "department": "Department of Horticulture & Plantation Crops / Agricultural Engineering",
        "description": "Subsidies for installation of Drip and Sprinkler irrigation systems to improve water use efficiency. 100% subsidy for Small & Marginal farmers, 75% for Other farmers in Tamil Nadu.",
        "subsidy_details": "100% subsidy for Small/Marginal farmers (up to 5 acres); 75% for other farmers (up to 12.5 acres).",
        "eligible_districts": "ALL",  # Available across all TN districts
        "max_land_acres": 12.5,
        "eligible_crops": [
            "all", "vegetables", "tomato", "chilli", "brinjal", "banana", "sugarcane", 
            "coconut", "cotton", "maize", "groundnut", "flowers", "horticulture"
        ],
        "ineligible_crops": ["paddy_flood"],  # Flood paddy usually uses canal/borewell, though drip paddy is emerging
        "eligible_categories": ["marginal", "small", "medium", "large"],
        "keywords": [
            "drip", "sprinkler", "micro irrigation", "irrigation subsidy", "water saving",
            "சொட்டு நீர்", "தெளிப்பு நீர்", "பாசனம்", "drip irrigation", "pipe", "borewell subsidy"
        ],
        "official_url": "https://www.tnagrisnet.tn.gov.in/uzhavan/",
        "required_documents": [
            "Land Patta / Chitta",
            "Adangal issued by VAO",
            "Aadhaar Card",
            "Ration Card / Smart Card",
            "Small/Marginal Farmer Certificate",
            "Bank Passbook copy"
        ]
    },
    {
        "id": "smam_farm_mechanization",
        "name": "Sub-Mission on Agricultural Mechanization (SMAM) - Farm Machinery Subsidy",
        "tamil_name": "வேளாண் இயந்திரமயமாக்கல் திட்டம் (பவர் டில்லர் / டிராக்டர் மானியம்)",
        "category": "Machinery",
        "department": "Agricultural Engineering Department, Government of Tamil Nadu",
        "description": "Assistance for purchase of agricultural machinery including Power Tillers, Rotavators, Multi-Crop Thrashers, Power Weeders, and Tractors.",
        "subsidy_details": "40% to 50% subsidy on purchase price (up to Rs. 85,000 for Power Tiller; specialized rates for tractors and implements). Priority for SC/ST, women, and small/marginal farmers.",
        "eligible_districts": "ALL",
        "max_land_acres": 25.0,
        "eligible_crops": ["all", "paddy", "sugarcane", "cotton", "maize", "pulses", "vegetables"],
        "eligible_categories": ["marginal", "small", "medium", "large"],
        "keywords": [
            "machinery", "tractor", "power tiller", "rotavator", "weeder", "harvester", "tiller", 
            "equipment subsidy", "machine subsidy", "இயந்திரம்", "டிராக்டர்", "பவர் டில்லர்", "களை எடுக்கும் கருவி"
        ],
        "official_url": "https://aed.tn.gov.in/",
        "required_documents": [
            "Land Patta / Chitta copy",
            "Aadhaar Card",
            "Quotation from authorized implement dealer",
            "Bank Account Details",
            "Farmer Category / Community Certificate"
        ]
    },
    {
        "id": "tn_solar_pump_scheme",
        "name": "Tamil Nadu Solar Powered Pump Sets Scheme (PM-KUSUM Component-B)",
        "tamil_name": "முதலமைச்சரின் சூரியசக்தி பம்ப் செட்டுகள் திட்டம் (70% மானியம்)",
        "category": "Energy & Irrigation",
        "department": "Agricultural Engineering Department",
        "description": "70% subsidy (30% Central + 40% State Government) to install stand-alone 5HP to 10HP solar-powered water pumping systems for off-grid farmers.",
        "subsidy_details": "70% total subsidy; farmer contributes only 30% of the capital cost.",
        "eligible_districts": "ALL",
        "max_land_acres": 20.0,
        "eligible_crops": ["all"],
        "eligible_categories": ["marginal", "small", "medium", "large"],
        "keywords": [
            "solar", "solar pump", "solar motor", "electricity", "borewell pump", "kusum",
            "சூரிய சக்தி", "சோலார் பம்ப்", "சோலார் மோட்டார்", "solar subsidy"
        ],
        "official_url": "https://aed.tn.gov.in/",
        "required_documents": [
            "Land Patta / Chitta",
            "Proof of reliable water source (Open well / Borewell)",
            "Certificate stating no existing TANGEDCO free agricultural electricity service connection",
            "Aadhaar Card",
            "Bank Passbook"
        ]
    },
    {
        "id": "kaviadp_all_village_scheme",
        "name": "Kalaignarin All Village Integrated Agriculture Development Programme (KAVIADP)",
        "tamil_name": "கலைஞரின் அனைத்து கிராம ஒருங்கிணைந்த வேளாண் வளர்ச்சித் திட்டம்",
        "category": "Integrated Farming",
        "department": "Agriculture & Farmers Welfare Department, Tamil Nadu",
        "description": "Holistic transformation of village panchayats through fallow land development, water resource creation, distribution of certified seeds, fruit saplings, battery sprayers, and soil health cards.",
        "subsidy_details": "Subsidized seeds (50%), free fruit sapling kits, subsidized battery/power sprayers, soil test kits.",
        "eligible_districts": "ALL",
        "max_land_acres": 15.0,
        "eligible_crops": ["all", "paddy", "pulses", "oilseeds", "horticulture", "millets"],
        "eligible_categories": ["marginal", "small", "medium"],
        "keywords": [
            "kalaignar", "village scheme", "seeds subsidy", "saplings", "sprayer subsidy",
            "fallow land", "integrated agriculture", "soil health", "அனைத்து கிராம திட்டம்", "விதை மானியம்"
        ],
        "official_url": "https://www.tnagrisnet.tn.gov.in/",
        "required_documents": [
            "Land Record (Patta/Chitta)",
            "Aadhaar Card",
            "Soil Health Card (or application for testing)"
        ]
    },
    {
        "id": "pm_fasal_bima_yojana",
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY) - Crop Insurance",
        "tamil_name": "பிரதம மந்திரி பயிர் காப்பீட்டுத் திட்டம் (பயிர் காப்பீடு)",
        "category": "Risk Management & Insurance",
        "department": "Department of Agriculture, Tamil Nadu",
        "description": "Comprehensive yield risk coverage against natural calamities, pests, droughts, floods, and unseasonal rains for notified crops in notified revenue villages.",
        "subsidy_details": "Farmers pay nominal premium: 1.5% for Rabi, 2% for Kharif food crops/oilseeds, 5% for annual commercial/horticultural crops. Balance premium subsidized by TN & Union Government.",
        "eligible_districts": "ALL",
        "max_land_acres": 50.0,
        "eligible_crops": ["paddy", "cotton", "maize", "groundnut", "sugarcane", "banana", "pulses", "onion"],
        "eligible_categories": ["marginal", "small", "medium", "large"],
        "keywords": [
            "insurance", "crop insurance", "loss", "flood", "drought", "damage", "compensation", "fasal bima",
            "காப்பீடு", "பயிர் இழப்பீடு", "வறட்சி", "வெள்ளம்"
        ],
        "official_url": "https://pmfby.gov.in/",
        "required_documents": [
            "Land Record (Chitta/Patta)",
            "Sowing Certificate issued by VAO",
            "Aadhaar Card",
            "Active Bank Account with IFSC"
        ]
    },
    {
        "id": "kuruvai_special_package",
        "name": "Kuruvai Paddy Cultivation Package Scheme (Cauvery Delta Districts)",
        "tamil_name": "குறுவை சாகுபடி சிறப்புத் தொகுப்புத் திட்டம் (டெல்டா மாவட்டங்கள்)",
        "category": "Crop Inputs",
        "department": "Agriculture & Farmers Welfare Department, Tamil Nadu",
        "description": "Special input assistance package offering 100% subsidized certified paddy seeds, chemical fertilizers (Urea, DAP, Potash), and micro-nutrient mixtures for Kuruvai paddy farmers in delta regions.",
        "subsidy_details": "Free seed kits and subsidized fertilizers per acre (up to ceiling limits).",
        "eligible_districts": [
            "thanjavur", "tiruvarur", "nagapattinam", "mayiladuthurai",
            "cuddalore", "tiruchirappalli", "pudukkottai", "ariyalur"
        ],
        "max_land_acres": 5.0,
        "eligible_crops": ["paddy"],
        "eligible_categories": ["marginal", "small"],
        "keywords": [
            "kuruvai", "delta", "paddy subsidy", "fertilizer subsidy", "cauvery", "free seeds",
            "குறுவை", "நெல் மானியம்", "உரம் மானியம்", "டெல்டா"
        ],
        "official_url": "https://www.tnagrisnet.tn.gov.in/",
        "required_documents": [
            "Patta / Chitta copy",
            "VAO Certificate of Paddy cultivation in Kuruvai season",
            "Aadhaar Card"
        ]
    }
]


def detect_scheme_intent(query: str) -> bool:
    """
    Determines if a farmer's natural language question is relevant
    to government schemes, subsidies, machinery assistance, or financial aid.
    """
    query_lower = query.lower()
    
    intent_triggers = [
        "scheme", "subsidy", "subsidies", "government", "assistance", "support",
        "grant", "eligible", "eligibility", "apply", "qualify", "drip", "sprinkler",
        "tiller", "tractor", "solar pump", "solar motor", "insurance", "compensation",
        "fasal bima", "pm-kisan", "pm kisan", "kuruvai package", "free seeds", "kalaignar",
        "மானியம்", "திட்டம்", "அரசு", "தகுதி", "விண்ணப்பம்", "சொட்டு நீர்", "டிராக்டர்", "காப்பீடு"
    ]
    
    for trigger in intent_triggers:
        if trigger in query_lower:
            return True
            
    return False


def evaluate_scheme_eligibility(
    query: str,
    profile: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Deterministic rule-based eligibility evaluation engine.
    Matches farmer profile attributes (district, land acres, crop, category)
    against official scheme conditions.
    
    Returns structured matches with match percentage, match reasons, and official portal links.
    """
    matched_schemes = []
    query_lower = query.lower()
    
    district = str(profile.get("district") or "").strip().lower()
    land_acres = profile.get("land_acres")
    try:
        land_acres = float(land_acres) if land_acres is not None else 2.0
    except (ValueError, TypeError):
        land_acres = 2.0
        
    crop = str(profile.get("crop") or "").strip().lower()
    category = str(profile.get("farmer_category") or "").strip().lower()
    
    # Auto-infer farmer category if not provided
    if not category:
        if land_acres <= 2.5:
            category = "marginal"
        elif land_acres <= 5.0:
            category = "small"
        else:
            category = "medium"

    for scheme in TAMIL_NADU_SCHEMES:
        reasons = []
        score = 0
        total_checks = 0
        
        # 1. Topic relevance check (Query keywords)
        keyword_hit = any(kw.lower() in query_lower for kw in scheme["keywords"])
        total_checks += 1
        if keyword_hit:
            score += 35
            reasons.append("Topic matches your specific farming inquiry")
        else:
            # If not explicitly asked, give base score if farm situation fits category
            score += 10
            
        # 2. District eligibility check
        total_checks += 1
        if scheme["eligible_districts"] == "ALL":
            score += 20
            if district:
                reasons.append(f"District '{district.title()}' is covered under this state-wide initiative")
            else:
                reasons.append("Applicable across all agricultural districts of Tamil Nadu")
        elif isinstance(scheme["eligible_districts"], list):
            if district in scheme["eligible_districts"]:
                score += 25
                reasons.append(f"Special priority for Cauvery Delta district: '{district.title()}'")
            elif district:
                # Disqualified if district specific
                continue
            else:
                score += 10
                reasons.append("Subject to notified district classification")
                
        # 3. Land Area check
        total_checks += 1
        max_acres = scheme.get("max_land_acres", 100)
        if land_acres <= max_acres:
            score += 25
            reasons.append(f"Land size of {land_acres} acres fits within the allowable limit (≤ {max_acres} acres)")
        else:
            reasons.append(f"Farm size exceeds the standard small-holder ceiling of {max_acres} acres")
            score -= 10
            
        # 4. Crop suitability check
        total_checks += 1
        scheme_crops = [c.lower() for c in scheme.get("eligible_crops", [])]
        if "all" in scheme_crops:
            score += 15
            reasons.append("Open to all agricultural and horticultural crops")
        elif crop and any(c in crop for c in scheme_crops):
            score += 20
            reasons.append(f"Selected crop '{crop.title()}' qualifies under approved crop schedules")
        elif not crop:
            score += 10
            reasons.append("Crop-dependent verification needed")
            
        # 5. Farmer category bonus (e.g. Small / Marginal farmers get higher subsidies in TN)
        if category in scheme.get("eligible_categories", []):
            score += 10
            if category in ["marginal", "small"]:
                reasons.append(f"Categorized as '{category.title()} Farmer' (eligible for highest subsidy tier)")
                
        # Normalize score between 0 and 98% (never 100% since final approval rests with government)
        match_percentage = min(max(score, 30), 96)
        
        # Only return if there is either an explicit keyword hit or high contextual relevance
        if keyword_hit or match_percentage >= 70:
            matched_schemes.append({
                "scheme_id": scheme["id"],
                "name": scheme["name"],
                "tamil_name": scheme["tamil_name"],
                "category": scheme["category"],
                "department": scheme["department"],
                "description": scheme["description"],
                "subsidy_details": scheme["subsidy_details"],
                "potential_match": match_percentage,
                "reasons": reasons,
                "official_url": scheme["official_url"],
                "required_documents": scheme["required_documents"],
                "disclaimer": (
                    "Scheme recommendations are based on farmer-provided context and indicate potential "
                    "eligibility. Final verification and approvals are conducted strictly by the Department of "
                    "Agriculture / Uzhavar Platform."
                )
            })

    # Sort by potential match score descending
    matched_schemes.sort(key=lambda s: s["potential_match"], reverse=True)
    return matched_schemes
