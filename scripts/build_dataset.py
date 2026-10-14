"""Build the bilingual router evaluation dataset (Phase 1).

Channels:
  manual     — hand-curated seed (this file's list)
  synthetic  — register-varied paraphrases (REVIEWED before inclusion; only
               corrected rows ship)
  stt        — real Sarvam bulbul:v3 -> wav -> saaras:v3 round-trips
               (run scripts/make_stt_noise.py, requires SARVAM_API_KEY)
  user_log   — weekly human-corrected rows from data/router_log.jsonl

Splits: 75% train / 12.5% val / 12.5% test, stratified intent x language.
Frozen test set: seen only by scripts/router_eval.py.

Usage: KMP_DUPLICATE_LIB_OK=TRUE python build_dataset.py [--]").replace(' [--]','')
"""

import argparse
import csv
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "router_eval", "router_dataset.jsonl")
random.seed(42)


def M(question, intent, language, card=None, hardness="normal"):
    return {"question": question, "language": language, "intent": intent,
            "tier1_demo_card": card, "source": "manual", "hardness": hardness}


MANUAL = [
    # ---------------- DEMO (30, EN/ta/tanglish) ----------------
    M("What is the market price of tomato today", "demo", "en", "market-price"),
    M("how much are they selling onion for", "demo", "en", "market-price"),
    M("what's the weather going to be like for the next two days", "demo", "en", "weather-advisory"),
    M("show me the fertilizer stock at the price shop", "demo", "en", "fertilizer-stock"),
    M("where do I rent a tractor for two days", "demo", "en", "machinery-rental"),
    M("check the dam water level in pallava", "demo", "en", "reservoir-levels"),
    M("what seeds are in stock at the store", "demo", "en", "seed-stock"),
    M("who is our agriculture officer, give me the number", "demo", "en", "officer-contact"),
    M("I need to buy a power sprayer where can I look", "demo", "en", "e-market"),
    M("what is the soil health card status", "demo", "en", "tamil-mannvalam"),
    M("தற்போதைய சந்தை விலை என்ன", "demo", "ta", "market-price"),
    M("நாளை மழை வருமா", "demo", "ta", "weather-advisory"),
    M("உரம் கையிருப்பு எவ்வளவு உள்ளது", "demo", "ta", "fertilizer-stock"),
    M("டிராக்டர் வாடகைக்கு கிடைக்குமா", "demo", "ta", "machinery-rental"),
    M("அணையில் தண்ணீர் எவ்வளவு உள்ளது", "demo", "ta", "reservoir-levels"),
    M("விதை கிடைக்குமா கடையில்", "demo", "ta", "seed-stock"),
    M("வேளாண் அதிகாரியின் தொலைபேசி எண் என்ன", "demo", "ta", "officer-contact"),
    M("மண் அறிக்கை எங்கே பார்ப்பது", "demo", "ta", "tamil-mannvalam"),
    M("எனக்கு ஒரு நீர்ப்பாசன இயந்திரம் வேண்டும், எங்கே வாங்கலாம்", "demo", "ta", "e-market"),
    M("உழவர் செய்திகள் என்ன இருக்கு", "demo", "ta", "agri-news"),
    M("anna tomato price enna irukku", "demo", "tanglish", "market-price"),
    M("machinery renta kidaikuma", "demo", "tanglish", "machinery-rental"),
    M("seed stock la irukka", "demo", "tanglish", "seed-stock"),
    M("weather epdi irukku namma area la", "demo", "tanglish", "weather-advisory"),
    M("uyirvetta officer number sollunga", "demo", "tanglish", "officer-contact"),
    M("dam level eppo paarthalum korayidhu, ippo evlo", "demo", "tanglish", "reservoir-levels"),
    M("urea stock irukka?", "demo", "tanglish", "fertilizer-stock"),
    M("price list kuduthukonga", "demo", "tanglish", "market-price"),
    M("uru peru maraka malligapoo vilai", "demo", "tanglish", "market-price"),
    M("farm guide page open pannunga", "demo", "tanglish", "farm-guide"),

    # ---------------- SCHEME (30) ----------------
    M("What subsidy do I get for buying drip irrigation under the government scheme", "scheme", "en"),
    M("Am I eligible for the PM-KISAN instalment", "scheme", "en"),
    M("how do I apply for the old age pension for farmers", "scheme", "en"),
    M("what is the crop insurance claim procedure", "scheme", "en"),
    M("what compensation does the government give when crops fail", "scheme", "en"),
    M("tell me about the Kalaignar agri scheme benefits", "scheme", "en"),
    M("which department gives the free borewell assistance", "scheme", "en"),
    M("what documents do I need to apply for iso organic certification", "scheme", "en"),
    M("is there a government grant for backyard poultry", "scheme", "en"),
    M("I want the exact subsidy rate per acre under KADP", "scheme", "en"),
    M("தமிழ்நாடு அரசு மானியத் திட்டங்கள் என்னென்ன உள்ளன", "scheme", "ta"),
    M("ஓய்வூதியத் தொகை எவ்வளவு", "scheme", "ta"),
    M("காப்பீட்டுத் தவணை எப்படி பெறுவது", "scheme", "ta"),
    M("பயிர் காப்பீட்டிற்கு விண்ணப்பிக்க என்ன தகுதி தேவை", "scheme", "ta"),
    M("மானியத் தொகை கிடைக்க எந்த அலுவலகத்தில் விண்ணப்பிக்க வேண்டும்", "scheme", "ta"),
    M("பசுமை இயக்கத்தில் இலவச மரக்கன்று கிடைக்குமா", "scheme", "ta"),
    M("கலைஞர் வேளாண் திட்டத்தின் நன்மைகள் என்ன", "scheme", "ta"),
    M("பட்டு வளர்ப்புக்கு அரசு என்ன உதவி செய்யும்", "scheme", "ta"),
    M("வேளாண் மின்விசை பம்புக்கு மானியம் உண்டா", "scheme", "ta"),
    M("இயந்திரம் வாங்க மானிய விண்ணப்பம் எங்கே கிடைக்கும்", "scheme", "ta"),
    M("anna, drop irrigation ku government la evlo percent mastyam kudupanga", "scheme", "tanglish"),
    M("pension apply panna enga povaenum", "scheme", "tanglish"),
    M("crop insurance claim epdi medikkanum", "scheme", "tanglish"),
    M("pmkisan la yenakku kaasu kidaikkumaa", "scheme", "tanglish"),
    M("mysore la illa, tamilnadu la KADP la yenna mastyam", "scheme", "tanglish"),
    M("goat vargal scheme la yenna documents kaekkaanga", "scheme", "tanglish"),
    M("government compensation panam eppo varum", "scheme", "tanglish"),
    M("subsidy tractor vaanguna evlo discount", "scheme", "tanglish"),
    M("free borewell assistance ku apply panren, thaaguthi enna", "scheme", "tanglish"),
    M("scheme la enroll aaga form enga", "scheme", "tanglish", hardness="hard"),

    # ---------------- AGRI (30) ----------------
    M("my paddy leaves are turning yellow, what should I spray", "agri", "en"),
    M("how much water does a tomato crop need per week", "agri", "en"),
    M("which seed variety suits loamy soil in Thanjavur", "agri", "en"),
    M("how do I control stem borer in paddy", "agri", "en"),
    M("when is the right time to transplant tomato seedlings", "agri", "en"),
    M("urea splitting schedule for sugarcane", "agri", "en"),
    M("why are my chilli flowers dropping", "agri", "en"),
    M("how deep should I sow groundnut seeds", "agri", "en"),
    M("best way to control weeds in direct sown paddy", "agri", "en"),
    M("what is the harvest window for CO 4grass", "agri", "en"),
    M("நெல்லின் இலை மஞ்சளாக மாறுகிறது, என்ன செய்வது", "agri", "ta"),
    M("தக்காளி நாற்று எப்போது நடவு செய்வது", "agri", "ta"),
    M("பயிருக்கு எவ்வளவு தண்ணீர் செலுத்த வேண்டும்", "agri", "ta"),
    M("நிலக்கடலை விதைப்பு ஆழம் எவ்வளவு", "agri", "ta"),
    M("கரையாம்புழு கட்டுப்படுத்துவது எப்படி", "agri", "ta"),
    M("கரும்புக்கு யூரியா எவ்வளவு", "agri", "ta"),
    M("மிளகாய் பூ உதிர்வது ஏன்", "agri", "ta"),
    M("களைக்கட்டுப்பாடு என்ன வழி", "agri", "ta"),
    M("மண் சோதனையின்படி உரம் எப்படி அளிப்பது", "agri", "ta"),
    M("கொய்யா மரத்திற்கு என்ன கவனிப்பு வேண்டும்", "agri", "ta"),
    M("pathu valli la oru pulippu irukku, spray enna", "agri", "tanglish"),
    M("tamato seedling transplant eppo mudiyum", "agri", "tanglish"),
    M("groundnut seed evlo deep vidanum", "agri", "tanglish"),
    M("kw'ku water evlo weekly", "agri", "tanglish"),
    M("chillipoo uhirthu, yenna reason", "agri", "tanglish"),
    M("paddy la stem borer control yenna", "agri", "tanglish"),
    M("weed control paddy la best method", "agri", "tanglish"),
    M("succ mulching vaccum irukka", "agri", "tanglish"),
    M("seed variety loamy soil ku best", "agri", "tanglish"),
    M("coconut tree ku varipinu control enna", "agri", "tanglish"),

    # ---- SCHEME PHRASING DIVERSITY (v3: words NOT echoing the PDF's own
    # vocabulary — catches overfitting to chunk fragments) ----
    M("who helps when my crop gets ruined by rain", "scheme", "en"),
    M("is there any money support if my harvest is destroyed", "scheme", "en"),
    M("free soil paravai seiyalama", "scheme", "tanglish"),
    M("soil card printing enga panranga", "scheme", "tanglish"),
    M("which office handles soil testing", "scheme", "en"),
    M("மண்ணுக்கு என்ன சோதனை இலவசமா வரும்", "scheme", "ta"),
    M("government vasooli for crop losss", "scheme", "tanglish"),
    M("does the state give anything for dried land farmers", "scheme", "en"),
    M("மழையில் பயிர் அழிந்தால் அரசு என்ன செய்யும்", "scheme", "ta"),
    M("how to get maaruthuvam assistance for dairy", "scheme", "tanglish"),

    # ---- HARD NEGATIVES (cross-intent confusions, tagged hardness=hard) ----
    M("Does the government scheme cover pest damage compensation?", "scheme", "en", hardness="hard"),
    M("what is the temperature the paddy seed germinates at", "agri", "en", hardness="hard"),
    M("insurance claim la paddy ruits penalite Sollunga", "scheme", "en", hardness="hard"),
    M("weather advisory la irrigation nathi varu paan exam", "agri", "en", hardness="hard"),
    M("காப்பீடு எப்படி வேலை செய்யும்", "agri", "ta", hardness="hard"),  # explainer, not claim
    M("திட்டம் இல்லாமல் தண்ணீர் வடிகால் எப்படி அமைப்பது", "agri", "ta", hardness="hard"),
    M("சந்தையில் விளைபொருள் விலை உயர காரணம் என்ன", "agri", "ta", hardness="hard"),  # price economics not price feed
    M("scheme la varipinu patharpoo control yenna", "agri", "tanglish", hardness="hard"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-stt", action="store_true",
                    help="merge rows from data/router_eval/stt_roundtrips.jsonl")
    ap.add_argument("--with-synthetic", action="store_true",
                    help="merge rowset from data/router_eval/synthetic_reviewed.jsonl")
    ap.add_argument("--with-user-log", action="store_true",
                    help="merge human-corrected rows from data/router_log.jsonl")
    ap.add_argument("--all", action="store_true", help="merge every available channel")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    if args.all:
        args.with_stt = args.with_synthetic = args.with_user_log = True

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    rows = list(MANUAL)

    for extra_path, label in [
        (os.path.join(os.path.dirname(OUT), "synthetic_reviewed.jsonl"), "synthetic"),
        (os.path.join(os.path.dirname(OUT), "stt_roundtrips.jsonl"), "stt"),
        (os.path.join(os.path.dirname(HERE), "data", "router_log.jsonl"), "user_log"),
    ]:
        enabled = {"synthetic": args.with_synthetic, "stt": args.with_stt,
                   "user_log": args.with_user_log}[label]
        if not enabled:
            continue
        if not os.path.exists(extra_path):
            print(f"skip {label}: {extra_path} missing")
            continue
        with open(extra_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                r.setdefault("tier1_demo_card", None)
                r.setdefault("hardness", "normal")
                rows.append(r)

    # Dedup by question text
    seen, unique_rows = set(), []
    for r in rows:
        key = r["question"].strip().lower()
        if key not in seen:
            seen.add(key)
            unique_rows.append(r)
    rows = unique_rows

    # Stratified split by intent x language
    random.seed(42)
    by_cell = {}
    for r in rows:
        if not r.get("intent") or not r.get("language"):
            print("row missing intent/language, dropping:", str(r)[:80])
            continue
        by_cell.setdefault((r["intent"], r["language"]), []).append(r)
    minority = []   # cells that are too small to split: put train
    train, val, test = [], [], []
    for cell, rs in sorted(by_cell.items()):
        random.shuffle(rs)
        n = len(rs)
        if n >= 8:
            k_train = int(n * 0.75)
            k_val = max(1, int(n * 0.125))
            train += rs[:k_train]
            val += rs[k_train:k_train + k_val]
            test += rs[k_train + k_val:]
        else:
            minority += rs
            train += rs

    # Tag splits
    split_rows = [dict(r, split="train") for r in train] + \
                 [dict(r, split="val") for r in val] + \
                 [dict(r, split="test") for r in test]

    with open(args.out, "w", encoding="utf-8") as f:
        for r in split_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"wrote {len(split_rows)} rows -> {args.out}")
    for intent in ("agri", "scheme", "demo"):
        for lang in ("en", "ta", "tanglish"):
            c = sum(1 for r in split_rows
                    if r["intent"] == intent and r["language"] == lang)
            print(f"  {intent:7s} x {lang:8s} = {c}")
    print(f"split: train={len(train)} val={len(val)} test={len(test)}")


if __name__ == "__main__":
    main()
