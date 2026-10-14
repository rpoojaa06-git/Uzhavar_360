"""Live end-to-end check of the deep-link integration with real .env credentials."""
import sys, time
sys.path.insert(0, '.')
t0 = time.time()

from app.rag import RAG

print(f"[{time.time()-t0:6.1f}s] loading engine (embedder + reranker + qdrant)...", flush=True)
rag = RAG()
print(f"[{time.time()-t0:6.1f}s] ENGINE READY", flush=True)

# 1) live retrieval
ctx = rag.retrieve("What is the market price of tomato?")
print(f"[{time.time()-t0:6.1f}s] RETRIEVE: {len(ctx)} chunks; top:",
      (ctx[0]['source'], 'page', ctx[0]['page']) if ctx else None, flush=True)

# 2) live Gemini answer, EN, matching question
ans, contexts, _, stage = rag.answer(
    question="What is the market price of tomato today?",
    profile={"language": "English", "name": "Test"},
    return_details=True,
)
print(f"[{time.time()-t0:6.1f}s] EN answer len={len(ans)}; sources={len(contexts)}; stage={stage}", flush=True)
print("EN_TAIL>>>", ans[-280:].replace("\n", " | "), flush=True)
link = rag.last_deep_link
print("EN_LINK>>>", link, flush=True)
assert link and link["id"] == "market-price", "EN market-price link FAILED"
assert "uzhavar-demo.vercel.app/#/market-price" in ans, "EN link block missing in answer"
print("[PASS] EN market-price flow", flush=True)

# 3) live Tamil question
ans2, _, _, _ = rag.answer(
    question="சந்தை விலை என்ன?",
    profile={"language": "Tamil", "name": "Test"},
    return_details=True,
)
print(f"[{time.time()-t0:6.1f}s] TA answer len={len(ans2)}", flush=True)
print("TA_TAIL>>>", ans2[-200:].replace("\n", " | "), flush=True)
assert rag.last_deep_link and rag.last_deep_link["id"] == "market-price", "TA link FAILED"
print("[PASS] TA market-price flow", flush=True)

# 4) agronomy question with real retrieval (should retrieve, and NOT link)
ans3, contexts3, _, _ = rag.answer(
    question="How do I prepare my land before sowing paddy?",
    profile={"language": "English", "name": "Test"},
    return_details=True,
)
print(f"[{time.time()-t0:6.1f}s] AGRONOMY answer len={len(ans3)}; sources={len(contexts3)}", flush=True)
print("AG_TAIL>>>", ans3[-140:].replace("\n", " | "), flush=True)
print("AG_LINK>>>", rag.last_deep_link, flush=True)
assert rag.last_deep_link is None, "agronomy question should NOT link"
print("[PASS] agronomy no-link flow", flush=True)

print("ALL LIVE RAG CHECKS PASSED", flush=True)
