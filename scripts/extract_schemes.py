"""Extract TN Farmer Welfare Dept Citizen Charter into structured schemes.json.

Column-aware extraction (pymupdf find_tables keeps the charter's
scheme | eligibility | officer grid intact, unlike page-text flattening).
Each positive row is sent to Gemini 2.5 Flash (temp 0, strict JSON) to be
structured into: scheme_name, department, benefits, eligibility,
documents_required, how_to_apply, officer_contact + provenance.

Human gate: every entry is manually inspected against its source page
(scripts/verify_schemes.py renders the referenced pages side-by-side)
before anything is committed. The PDF stays ground truth.
"""

import json
import os
import re
import sys
import time

import pymupdf
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
load_dotenv()

PDF_PATH = os.path.join(ROOT, "data", "schemes", "Farmers_welfare_dept.pdf")
OUT_PATH = os.path.join(ROOT, "data", "schemes", "schemes.json")

from app.config import GEMINI_API_KEY  # noqa: E402

if not GEMINI_API_KEY:
    sys.exit("GEMINI_API_KEY missing in .env - needed for row structuring.")

ROW_SCHEMA_PROMPT = """You are structuring ONE row of a government scheme table
(Tamil Nadu Farmers Welfare Dept, Citizen Charter 2025-26). Given the raw text
of the three table cells, produce STRICT JSON with EXACTLY these keys:
- "scheme_name": concise scheme/sub-scheme name (capitalized; translate identity, keep TN govt official English wording)
- "department": department name (usually "Agriculture"; use the section dept: Agriculture / Horticulture / Agricultural Engineering / Agricultural Marketing / TNAU / Seed Certification...)
- "benefits": ARRAY of concrete benefit strings, each with numbers/amounts EXACTLY as in the source (e.g. "Rs.300 per soil sample")
- "eligibility": ARRAY of eligibility/condition strings (verbatim-derived, concise)
- "documents_required": ARRAY of documents/conditions the farmer must have or do ("" -> empty array)
- "how_to_apply": short application instruction (may be empty string if absent)
- "officer_contact": the officer(s) to contact, one string (preserve titles)
- "keywords": ARRAY of 4-8 short bilingual search keywords (EN + Tamil transliteration) that a farmer might use for this scheme
Rules: use ONLY the information in the given cells; if a field is absent use "" or []; never invent amounts or titles.

CELL 1 (scheme & benefits):
%s

CELL 2 (eligibility & conditions):
%s

CELL 3 (officer to be contacted):
%s

STRICT JSON only."""


def _cells_clean(cell: str) -> str:
    if not cell:
        return ""
    t = re.sub(r"\s*\n\s*", " ", cell)
    return re.sub(r" +", " ", t).strip()


def extract_rows(resume_from: int = 4):
    """Resume-able: pass the 1-based page to start from (extract4.log's last
    page printed + 1). Writes partial results to schemes_partial.jsonl each
    page so a timeout never loses progress."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_API_KEY)

    doc = pymupdf.open(PDF_PATH)
    entries = []
    seen_names = {}
    partial_path = OUT_PATH.replace("schemes.json", "schemes_partial.jsonl")
    # load previous partials to merge/dedup across interrupted runs
    try:
        with open(partial_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                e = json.loads(line)
                k = e["scheme_name"].lower()
                if k not in seen_names:
                    seen_names[k] = e
                    entries.append(e)
    except FileNotFoundError:
        pass

    for pno in range(resume_from, doc.page_count - 12):
        page = doc[pno]
        tables = page.find_tables()
        if not tables.tables:
            continue
        for tab in tables.tables:
            rows = tab.extract()
            if not rows:
                continue
            header = rows[0]
            # skip index pages / non-scheme tables
            if not any("Welfare scheme" in (c or "") for c in header):
                continue
            for r in rows[1:]:
                c0, c1, c2 = (_cells_clean(r[i] or "") for i in range(3))
                if not c0 or len(c0) < 12:
                    continue
                if re.fullmatch(r"[\d. ]+", c0):
                    continue
                struct = structure_row(client, c0, c1, c2)
                if not struct or not struct.get("scheme_name"):
                    continue
                name = struct["scheme_name"].strip()
                key = name.lower()
                if key in seen_names:
                    # merge into the existing entry (multi-page schemes)
                    prev = seen_names[key]
                    for fld in ("benefits", "eligibility", "documents_required"):
                        for item in struct.get(fld) or []:
                            if item and item not in prev.get(fld, []):
                                prev[fld].append(item)
                    if pno + 1 not in prev["provenance"]["pages"]:
                        prev["provenance"]["pages"].append(pno + 1)
                    continue
                struct["id"] = re.sub(r"[^a-z0-9]+", "-", key)[:48].strip("-")
                struct["department"] = struct.get("department") or "Agriculture"
                struct["provenance"] = {
                    "source_pdf": os.path.basename(PDF_PATH),
                    "pages": [pno + 1],
                    "confidence": "llm_extracted",
                }
                seen_names[key] = struct
                entries.append(struct)
                with open(partial_path, "a", encoding="utf-8") as pf:
                    pf.write(json.dumps(struct, ensure_ascii=False) + "\n")
                print(f"p{pno+1:3d}  {struct['scheme_name'][:64]}", flush=True)
                time.sleep(0.4)  # free-tier politeness

    return entries


def structure_row(client, c0, c1, c2):
    from google.genai import types
    prompt = ROW_SCHEMA_PROMPT % (c0[:3000], c1[:1500], c2[:1200])
    for attempt in range(2):
        try:
            resp = client.models.generate_content(
                model="gemini-3.1-flash-lite",   # lite: same-project 2.5-flash daily quota is exhausted
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                    max_output_tokens=900,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
            raw = (resp.text or "").strip()
            m = re.search(r"\{.*\}", raw, re.S)
            if not m:
                continue
            data = json.loads(m.group(0))
            for fld in ("eligibility", "documents_required", "keywords", "benefits"):
                if not isinstance(data.get(fld), list):
                    data[fld] = [data[fld]] if data.get(fld) else []
            data["scheme_name"] = (data.get("scheme_name") or "").strip()
            data["officer_contact"] = (data.get("officer_contact") or "").strip()
            data["how_to_apply"] = (data.get("how_to_apply") or "").strip()
            if not data["scheme_name"]:
                return None
            return data
        except Exception as e:
            name = type(e).__name__
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                # honor RetryInfo but CAP the sleep — some 3.x responses
                # report hours-long per-project daily expiry; retrying a
                # couple of times then skipping keeps the run moving.
                import re as _re
                m = _re.search(r"retryDelay[^\d]*(\d+)s", str(e)) or _re.search(r"retry in (\d+)", str(e))
                wait_s = min(int(m.group(1)) + 1, 60) if m else 15
                if wait_s >= 60 or "PerDay" in str(e):
                    print("    daily quota hit on lite — abort extraction", file=sys.stderr)
                    return None
                time.sleep(wait_s)
                continue
            print(f"    ERR {name}: {str(e)[:80]}", file=sys.stderr)
            continue
    return None


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", type=int, default=4,
                    help="1-based page number to resume from")
    ap.add_argument("--finalize", action="store_true",
                    help="dedupe partials into schemes.json and exit")
    args = ap.parse_args()

    partial_path = OUT_PATH.replace("schemes.json", "schemes_partial.jsonl")

    if args.finalize:
        seen, entries = {}, []
        with open(partial_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                e = json.loads(line)
                k = e["scheme_name"].lower()
                if k in seen:
                    prev = seen[k]
                    for fld in ("benefits", "eligibility", "documents_required"):
                        for item in e.get(fld) or []:
                            if item and item not in prev.get(fld, []):
                                prev[fld].append(item)
                    for p in e.get("provenance", {}).get("pages", []):
                        if p not in prev["provenance"]["pages"]:
                            prev["provenance"]["pages"].append(p)
                else:
                    seen[k] = e
                    entries.append(e)
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"wrote {len(entries)} scheme entries -> {OUT_PATH}")
        return

    entries = extract_rows(resume_from=args.resume)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"\nwrote {len(entries)} scheme entries -> {OUT_PATH}")


if __name__ == "__main__":
    main()
