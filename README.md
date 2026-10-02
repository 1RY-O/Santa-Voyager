# Santa-Voyager — Ultimate Gift / Hangout Generator
Streamlit MVP for the Nebius x NVIDIA Hackathon. Takes hyper-specific constraints and returns curated gift ideas or hangout plans with strict constraint reporting.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # leave APP_MODE=demo for samples
streamlit run app.py
# open http://localhost:8501
```

## Env vars (dev)
| Var | Required | Default | Purpose |
|---|---|---|---|
| `NEBIUS_API_KEY` | live only | empty | Server-side Nebius API key. Never printed, logged, or shown in UI. |
| `NEBIUS_API_ENDPOINT` | no | `https://api.studio.nebius.com/v1/chat/completions` | OpenAI-compatible chat endpoint. |
| `NEBIUS_MODEL` | no | `meta-llama/Meta-Llama-3.1-70B-Instruct` | Model name sent in payload. |
| `APP_MODE` | no | `demo` | `demo` = deterministic samples; `live` + key = real calls. |

`.env` is git-ignored (see `.gitignore`). Never commit keys.

## Architecture
```
app.py (Streamlit UI only: forms, validation display, states)
 ├─ gift_generator.py / hangout_generator.py (prompt building, fallback)
 ├─ ai_provider.py (NebiusProvider ↔ DemoProvider via create_provider()/is_live_mode())
 ├─ models.py (Pydantic: ConstraintInput, GiftOutput, HangoutOutput, InputValidator)
 └─ constraints.py (Must-have / Must-avoid / Preferences / Budget checks)
```
- Keys stay on the server (`os.getenv`, `python-dotenv`); UI only shows Demo/Live banner.
- Structured JSON outputs validated against Pydantic schemas; `extract_json()` handles raw, fenced, or embedded JSON and falls back gracefully.
- Hard constraints prioritized: budget uses range upper-bound (e.g. `$45-65` vs `$20` → violation); avoidances are substring-checked and reported; conflicts surface in UI instead of being silently ignored.
- Client+server validation: required/optional text (500-char cap), budget `0.01–10000`, comma-list normalization (20-item cap).

## Connect the official Nebius API
1. Create key at https://studio.nebius.com/ → copy to `.env` as `NEBIUS_API_KEY=...`
2. Set `APP_MODE=live` in `.env` (optionally override `NEBIUS_MODEL`).
3. `streamlit run app.py` → sidebar/banner flips from `🔓 Demo` to `✅ Live`.
4. Payload uses OpenAI-compatible `POST {endpoint}` with `{model, messages, temperature, response_format:{json_object}}` + `Authorization: Bearer` over HTTPS.

## UX states
Loading (`st.spinner`), Empty (first-run placeholder), Validation Error (per-field `st.error`), Demo Mode (prominent top banner + sidebar + sample watermark). Results are scannable cards with Clear/Edit regeneration; `aria-live="polite"`, `:focus-visible` outlines, mobile media query; no fake testimonials/ratings.

## Tests
```bash
python3 -m pytest -q
python3 -m py_compile app.py models.py constraints.py ai_provider.py gift_generator.py hangout_generator.py
curl localhost:8501/_stcore/health  # with app running → ok
```

## Known limitations
- Demo outputs are deterministic samples, not personalized.
- Price/budget parsing is heuristic (`max(numbers)`); verify real costs.
- Avoidance matching is case-insensitive substring, not semantic.
- No web search, maps, or availability checks — assumptions listed for user verification.
