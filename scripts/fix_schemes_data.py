"""
Fix scheme categories and enhance Tamil keywords for key schemes.
Run once: python fix_schemes_data.py
"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

JSON_PATH = 'data/schemes/schemes.json'

with open(JSON_PATH, encoding='utf-8') as f:
    data = json.load(f)

# ── Category corrections ──────────────────────────────────────────────────────
CATEGORY_FIXES = {
    'solar-powered-driers-and-solar-fencing-subsidy': 'solar',
    'nhm-apiculture-beekeeping-subsidy': 'horticulture',
    'pmksy-watershed-development-component-wdc': 'watershed',
    'analysis-of-irrigation-water-sample': 'irrigation',
    'swma-supplementary-water-management-subsidy': 'irrigation',
    # Re-classify all crop water management schemes as irrigation
}

# ── Extra Tamil keywords for high-priority schemes ────────────────────────────
EXTRA_KEYWORDS = {
    'pmksy-per-drop-more-crop-drip-irrigation': [
        'சொட்டு நீர் பாசனம்', 'நுண் பாசனம்', 'தெளிப்பு நீர்', 'பாசன மானியம்',
        'drip subsidy', 'micro irrigation', 'sprinkler', 'பாசனம்',
        'PMKSY', 'Per Drop More Crop', 'நீர் மேலாண்மை',
    ],
    'chief-ministers-solar-powered-pumpsets-pm-kusum': [
        'சூரிய மின் பம்பு', 'சோலார் பம்பு', 'சூரிய சக்தி', 'PM KUSUM',
        'solar pump subsidy', 'solar motor', 'solar pumpset',
        'சோலார் மோட்டார்', 'முதலமைச்சர் சோலார்', 'சோலார் மானியம்',
    ],
    'agricultural-mechanization-tractor-rotavator-subsidy': [
        'டிராக்டர் மானியம்', 'பவர் டில்லர்', 'ரோட்டாவேட்டர்',
        'tractor subsidy', 'power tiller', 'rotavator', 'cultivator',
        'harvester', 'farm machinery', 'வேளாண் இயந்திரம்',
        'SMAM', 'Agricultural Mechanization',
    ],
    'solar-powered-driers-and-solar-fencing-subsidy': [
        'சூரிய உலர்விப்பான்', 'சோலார் வேலி', 'solar drier', 'solar fencing',
        'solar fence', 'விளைபொருள் உலர்த்தல்', 'சோலார்',
    ],
    'distribution-of-traditional-paddy-variety-seeds': [
        'நெல் விதை', 'பாரம்பரிய நெல்', 'விதை மானியம்', 'விதை நெல்',
        'paddy seed', 'seed subsidy', 'traditional variety', 'seed distribution',
    ],
    'assistance-to-farmers-for-crop-insurance': [
        'பயிர் காப்பீடு', 'காப்பீட்டு மானியம்', 'PMFBY', 'crop insurance',
        'insurance subsidy', 'பயிர் இழப்பீடு', 'பயிர் காப்பீட்டு திட்டம்',
    ],
    'pradhan-mantri-fasal-bima-yojana-pmfby': [
        'PMFBY', 'பயிர் காப்பீடு', 'crop insurance', 'Fasal Bima',
        'பயிர் நஷ்ட இழப்பீடு', 'காப்பீடு', 'insurance premium subsidy',
    ],
    'uzhavar-sandhais-direct-farmer-marketing': [
        'உழவர் சந்தை', 'விவசாயி நேரடி விற்பனை', 'farmers market',
        'direct marketing', 'uzhavar sandhai', 'சந்தை', 'விற்பனை',
    ],
    'organic-farming-promotion-scheme': [
        'இயற்கை விவசாயம்', 'ஆர்கானிக் விவசாயம்', 'organic farming',
        'natural farming', 'biofertilizer', 'இயற்கை உரம்', 'மண்புழு உரம்',
        'vermicompost', 'organic certification',
    ],
    'tnocd-organic-farming-certification-scheme': [
        'இயற்கை சான்றிதழ்', 'ஆர்கானிக் சான்றிதழ்', 'organic certificate',
        'TNOCD', 'organic farming certification', 'இயற்கை விவசாயம்',
    ],
    'assistance-to-farmers-for-improving-the-soil-health': [
        'மண் பரிசோதனை', 'மண் வளம்', 'மண் அட்டை', 'soil health card',
        'soil testing', 'soil test subsidy', 'மண் ஆரோக்கியம்', 'Soil Health Card',
    ],
    'pm-kisan-samman-nidhi': [
        'PM Kisan', 'பிரதம மந்திரி கிசான்', 'கிசான் மானியம்', 'வருடாந்திர உதவி',
        '6000 subsidy', 'pm kisan samman', 'farmer income support',
        'நேரடி பலன்', 'DBT',
    ],
    'smam-custom-hiring-centers-chc': [
        'CHC', 'Custom Hiring Centre', 'இயந்திரம் வாடகை', 'வாடகை இயந்திரம்',
        'farm machinery rental', 'கூட்டு இயந்திரம்', 'SMAM',
    ],
    'swma-supplementary-water-management-subsidy': [
        'SWMA', 'நீர் மேலாண்மை', 'water management', 'canal irrigation',
        'lift irrigation', 'பாசன வசதி', 'irrigation subsidy',
    ],
    'price-support-scheme-msp-pulses-copra': [
        'MSP', 'குறைந்தபட்ச விலை', 'Minimum Support Price', 'price support',
        'பருப்பு வகை விலை', 'copra price', 'pulses MSP', 'PSS',
    ],
}

# ── Apply fixes ───────────────────────────────────────────────────────────────
updated = 0
for s in data:
    sid = s.get('id', '')
    
    # Fix categories
    if sid in CATEGORY_FIXES:
        old_cat = s.get('category')
        s['category'] = CATEGORY_FIXES[sid]
        if old_cat != s['category']:
            print(f"  Category fixed: {sid[:50]} → {s['category']}")
            updated += 1
    
    # Add extra keywords (avoid duplicates)
    if sid in EXTRA_KEYWORDS:
        existing = set(kw.lower() for kw in s.get('keywords', []))
        new_kws = [kw for kw in EXTRA_KEYWORDS[sid] if kw.lower() not in existing]
        if new_kws:
            s.setdefault('keywords', []).extend(new_kws)
            print(f"  Keywords added to {sid[:40]}: +{len(new_kws)}")
            updated += 1

# ── Normalize: add 'name' alias = 'scheme_name' for forward compat ─────────
for s in data:
    if 'name' not in s and 'scheme_name' in s:
        s['name'] = s['scheme_name']

print(f"\nTotal records modified: {updated}")

# ── Write back ────────────────────────────────────────────────────────────────
with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"Written {len(data)} schemes to {JSON_PATH}")

# ── Final category audit ──────────────────────────────────────────────────────
cats = {}
for s in data:
    c = s.get('category','')
    cats[c] = cats.get(c,0)+1
print("\nFinal category breakdown:")
for k,v in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
