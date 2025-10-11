# Kingfisher 2465 — Polymath Teaching Assistant (Web/Desktop)

Kingfisher turns any question into:
1) A concise **chat** answer, and
2) One or more **lesson-style cards** (headings, steps, images).

**2025 Features:**
- ✅ **Structured outputs** via OpenAI JSON Schema (with auto-repair + graceful fallback)
- ✅ **Real-first images** (Unsplash → Pexels → generate)
- ✅ **Live tools**: Search with citations, Weather/Marine (Open-Meteo)
- ✅ **SSE streaming** for progressive card updates
- ✅ **Prometheus metrics** and `/ready` health checks
- ✅ **Two-pass reasoning** (GPT-5 with smart fallbacks)

## Quick Start
```bash
# 1) Setup
python -m venv .venv && source .venv/bin/activate
pip install -r apps/api/requirements.txt
npm --prefix apps/web install

# 2) Env
cp .env.example .env
# edit .env with your keys (OPENAI_API_KEY required)

# 3) Run API and Web (two terminals)
source .venv/bin/activate && uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
npm --prefix apps/web run dev
```

Open http://localhost:3000  
The web app calls the API at http://127.0.0.1:8000.

## What to try
- **"How do I tie a uni knot?"** → text + step cards + images
- **"Plan a Clarence River evening session for flathead"** → weather/marine tools + lesson cards + citations
- **"Explain the Lachlan Orogen simply"** → concept card + references

## Development

### Testing
```bash
# API tests
pytest tests/ -v

# Linting
ruff check apps/api tests
mypy apps/api

# Frontend type-check
npm --prefix apps/web run typecheck
```

### Endpoints
- `GET /health` - Basic health check
- `GET /ready` - Upstream reachability check (OpenAI API)
- `GET /metrics` - Prometheus metrics
- `POST /api/chat` - Traditional chat (JSON response)
- `GET /api/chat/stream?message=...` - SSE streaming chat

### Tools Available
- **Images**: Unsplash, Pexels, generate (fallback)
- **Search**: Web search with citations (DuckDuckGo fallback)
- **Weather**: Open-Meteo forecast (free, no key)
- **Marine**: Open-Meteo marine/swell data (free, no key)

## Architecture

```
User Query
    ↓
Pass-1: Plan (JSON Schema)
    ├─ Extract: cards[], tool_calls[], image_queries[], needs_fresh_facts
    ↓
Pass-2: Enrich (parallel fan-out)
    ├─ Fetch images (Unsplash/Pexels)
    ├─ Run tools (search, weather, marine) with timeouts
    ├─ Merge results + attach citations
    ↓
Response: text + lesson_cards[] + citations
```

## CI/CD

GitHub Actions workflow runs:
1. **Lint**: ruff, mypy, eslint, tsc
2. **Test**: pytest with mocked dependencies
3. **Build**: Next.js production build

All checks must pass before merge.
