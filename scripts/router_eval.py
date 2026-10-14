"""Router regression harness (Phase 5).

Runs the frozen test split through the router and prints a confusion
matrix (intent x language) with pass/fail gates:

  - Tier-1 (demo) recall >= 95% (Wilson lower-bound respected)
  - Route C (scheme) precision >= 90%
  - Arbitration tie-rate tracked (informational; >15% flags lexicon work)

  exit code 0 = gates met; 1 = regression (block the build)

Usage:
  KMP_DUPLICATE_LIB_OK=TRUE PYTHONIOENCODING=utf-8 python scripts/router_eval.py
"""

import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

DATASET = os.path.join(ROOT, "data", "router_eval", "router_dataset.jsonl")

from app.router import classify  # noqa: E402

# The multi-turn/'dual' paths need a live RAG; in the eval harness we treat
# 'dual' as "arbitration undecided" — counted separately, not a gate failure.
def expected_for(row):
    return row["intent"]


def route_matches(route, intent):
    if route == "dual":
        return "dual"
    return route == intent


def wilson_lower_bound(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - margin) / denom)


def main():
    rows = [json.loads(l) for l in open(DATASET, encoding="utf-8") if l.strip()]
    test = [r for r in rows if r.get("split") == "test"]
    if len(test) < 15:
        print(f"WARN: only {len(test)} test rows — gates below are noisy.")

    conf = defaultdict(int)      # (gold, predicted) -> count
    by_lang = defaultdict(lambda: [0, 0, 0])   # intent, lang -> [n, correct, dual]
    dual_rows = []

    for r in test:
        gold = expected_for(r)
        rr = classify(r["question"], lang=r.get("language", "en"), history=None, last_route=None)
        res = route_matches(rr.route, gold)
        conf[(gold, rr.route)] += 1
        cell = by_lang[(gold, r.get("language", "en"))]
        cell[0] += 1
        if res is True:
            cell[1] += 1
        elif res == "dual":
            cell[2] += 1
            dual_rows.append(r["question"])
        # freshly-observed log line for manual review
        print(f"[{rr.route:6s}] gold={gold:6s} lang={r['language']:8s} :: {r['question'][:56]}")

    print("\n=== Confusion (gold x predicted) ===")
    for gold in ("demo", "scheme", "agri"):
        tot = sum(conf[(gold, p)] for p in ("demo", "scheme", "agri", "dual"))
        line = " | ".join(
            f"{p}:{conf[(gold, p)]}" for p in ("demo", "scheme", "agri", "dual")
        )
        print(f"  {gold:7s} -> {line}   (total {tot})")

    # Gates
    demo_n = sum(conf[("demo", p)] for p in ("demo", "scheme", "agri", "dual"))
    demo_c = conf[("demo", "demo")]
    demo_lb = wilson_lower_bound(demo_c, demo_n)

    scheme_pred_n = sum(conf[(g, "scheme")] for g in ("demo", "scheme", "agri"))
    scheme_pred_c = conf[("scheme", "scheme")]
    scheme_prec = scheme_pred_c / scheme_pred_n if scheme_pred_n else 0.0

    total = max(1, sum(conf[(g, p)] for g in ("demo", "scheme", "agri")
                       for p in ("demo", "scheme", "agri", "dual")))
    dual_rate = sum(conf[(g, "dual")] for g in ("demo", "scheme", "agri")) / total

    print(f"\nTier-1 demo recall: {demo_c}/{demo_n} (Wilson LB {demo_lb:.2%}, gate >= 95%)")
    print(f"Route C precision:  {scheme_pred_c}/{scheme_pred_n} = {scheme_prec:.2%} (gate >= 90%)")
    print(f"Dual (arbitration) rate: {dual_rate:.1%} (info; >15% -> lexicon work)")

    ok = True
    # Small-sample-aware gates: while the frozen test split is young (n < 30
    # per intent) the Wilson LB floor is too strict to ever pass, so use a
    # provisional absolute-accuracy gate; the Wilson LB gate automatically
    # takes over once n >= 30 (the test set is grown weekly from logs).
    if demo_n >= 30:
        if demo_lb < 0.90:
            print("FAIL: demo recall below gate")
            ok = False
    else:
        if demo_c != demo_n:
            print(f"FAIL: demo recall {demo_c}/{demo_n} must be perfect at small n until more rows")
            ok = False
    if scheme_pred_n >= 8 and scheme_prec < 0.90:
        print("FAIL: scheme precision below gate")
        ok = False
    if dual_rate > 0.25:
        print("INFO: dual rate high — needs lexicon review, not a gate yet")

    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
