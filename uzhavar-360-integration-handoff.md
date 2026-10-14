# Uzhavar_360 — Demo Deep-Link Integration (handoff for Poojaa)

Branch: `integration/deep-links` · Commits: `eda6a82` (deep links) + `5ee9733` (voice console rewrite) — both on top of your `2b8039e "ui changes"`

Optional natural voice: add `SARVAM_API_KEY=<your key>` to `.env` (speaker
defaults to `shubh` via Sarvam bulbul:v3, see `app/sarvam_tts.py`; without the
key the app falls back to browser speech). When the key is present, **Sarvam is
THE voice everywhere** — onboarding prompts, completion message and every chat
answer — not just chat. Note: the very first greeting can only start *after*
the farmer taps a language (browsers block autoplay audio before any user
gesture), so the splash page is visual-only by design.
Patch file: `uzhavar-360-deep-links-integration.patch` — **2 commits** (1528 lines), apply with:

```bash
cd Uzhavar_360
git am uzhavar-360-deep-links-integration.patch
pip install streamlit-mic-recorder   # new voice dependency (also added to requirements.txt)
```

## What this adds

The voice chatbot now hands farmers into the Uzhavar demo UI when a question
matches one of its 24 service pages. The demo app is live at
`https://uzhavar-demo.vercel.app` (HashRouter), so every deep link is simply
`https://uzhavar-demo.vercel.app/#/<service-id>` — no server changes needed.

Example farmer flow (works in both Streamlit and the FastAPI `/chat`):

> Farmer: "What is the market price of tomato today?"
> Bot: grounded answer **+ a green link card: "💹 Uzhavar demo app — Market Price · சந்தை விலை"**
> with a big "Open" button and the spoken instruction
> "…the Uzhavar demo app has a Market Price page — tap the link shown below this answer."

If retrieval finds nothing, the fallback points to the demo home grid
(`/#/`) instead of dead-ending.

## New / changed files

| File | Change |
|---|---|
| `app/links_mapping.py` (new) | Deterministic bilingual matcher: question → demo service id (keywords EN + தமிழ் + Tanglish), builds the link block + spoken instruction. No LLM calls — free and auditable. |
| `app/rag.py` | Appends the link block on every `answer()` return path; retains the structured payload as `RAG.last_deep_link` for API layers. |
| `app/models.py` | `ChatResponse.deep_link: Optional[DeepLink]` — backwards compatible (absent = `null`). |
| `app/main.py` | Populates `deep_link` on `/chat`. |
| `streamlit_app.py` | **Fixes (see audit below)** + renders the link card under AI messages + a "🌐 Browse the full demo app →" footer chip + new bilingual UI strings. |
| `requirements.txt` | Adds `streamlit-mic-recorder`. |

## Bugs fixed (from the audit of your repo @ `2b8039e`)

1. **Fatal:** `st.iframe(...)` does not exist in Streamlit — all 5 call sites
   (splash TTS, step TTS, audio player, voice widget, splash) crashed every
   render path with `AttributeError`. Replaced with
   `streamlit.components.v1.html(...)`.
2. **Fatal:** the voice widget's `?vstep/vresult` query-param round-trip
   reloaded the entire page on every spoken turn. Rewritten (commit `5ee9733`)
   as a **manual 🎙 Start Recording → ⏹ Stop & Send console**
   (`voice_console_auto`): tap Start, ask your question, tap Stop & Send, and
   the audio goes to **Sarvam STT server-side** (`saaras:v3`, see
   `app/sarvam_stt.py`) — no browser speech recognition at all. This also
   fixes the original "Start Recording does nothing in Edge" bug (the old
   console used `webkitSpeechRecognition`, which is Chrome-only and silently
   failed in Edge). Onboarding voice capture (`voice_capture_widget`) uses
   the same mic widget + Sarvam STT, falling back to typed input when the
   package or `SARVAM_API_KEY` is missing. Bilingual error strings cover
   empty audio, no key, network failure, 403/422 (>30 s)/429 and empty
   transcripts.
3. **TTS hygiene:** `clean_for_speech` now strips emojis, symbols, markdown
   and URLs before speaking, converts `%`, `/`, `&`, `₹`/`Rs.` to spoken words,
   and keeps only natural sentence punctuation so the voice pauses correctly.
4. **Answer length & style:** the Gemini system prompt now forbids greetings,
   self-introductions and closing questions, caps answers (~120 words,
   `max_output_tokens=320`) and asks for 1 direct sentence + at most 3-4 key
   bullet points — shorter generation also means faster responses.
5. **Retracted after deeper reading:** the topbar/sidebar reset "fall-through"
   I flagged in planning is *not* a bug — `st.rerun()` raises immediately, so
   the code after it never runs. Left untouched.

Audit items deliberately *not* fixed here (scope): `app/schemes.py` doesn't
exist (README oversells it — nothing to integrate with); Gemini answers are
still synchronous; `data/farmer_profiles.json` (user PII) stays committed.

## Tested

- All 6 Python files parse (`ast.parse`).
- Streamlit booted headless with **no `.env`**: splash → full onboarding
  (name/age/gender/farmer-type/docs) → main chat all clickable, zero errors in
  the server log; mic component mounts; demo footer chip visible.
- Matcher: 21-case suite (EN/தமிழ்/Tanglish, incl. negatives) — all pass.
  ("weeds"-only questions intentionally do NOT link; the RAG's Weed
  Management PDF answers those without a demo page.)
- RAG link paths (with stubbed Qdrant/Gemini): EN link block, TA instruction,
  home fallback — all assert-verified, `last_deep_link` populated.
- FastAPI models: `ChatResponse.deep_link` serializes correctly and is `null`
  when absent.
- **Not** live-tested (needs your real credentials): an actual Gemini+Qdrant
  answer round-trip, and real-mic recording in a browser (use Chrome/Edge;
  grant mic permission). Sarvam STT itself **was** live-tested round-trip
  with a real key: TTS → 16 kHz wav → POST `/speech-to-text` (`saaras:v3`)
  returned the exact transcript, HTTP 200.

## Tuning the matcher

All keywords live in one list in `app/links_mapping.py` (`_SERVICES`). If a
real farmer phrase fails to link or over-links, add/remove entries there —
score = matched keyword length, threshold `MIN_SCORE = 8`.
