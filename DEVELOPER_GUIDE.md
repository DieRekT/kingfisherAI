# Kingfisher 2465 - Developer Guide

## Quick Reference

### Environment Setup
```bash
# Clone and install
git clone https://github.com/DieRekT/kingfisherAI.git
cd kingfisherAI
python -m venv .venv && source .venv/bin/activate
pip install -r apps/api/requirements.txt
npm --prefix apps/web install

# Configure
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

### Running Locally
```bash
# Terminal 1: API
source .venv/bin/activate
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Web
npm --prefix apps/web run dev

# Open http://localhost:3000
```

### Development Commands
```bash
# Python linting
ruff check apps/api tests
ruff format apps/api tests  # auto-format

# Type checking
mypy apps/api

# Tests
pytest tests/ -v                    # All tests
pytest tests/test_health_ready.py  # Specific test
CI=1 pytest tests/ -v              # With stub responses

# Web TypeScript
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
```

---

## API Architecture

### Request Flow
```
POST /api/chat
  ↓
1. Pass-1: pass1_analyze_and_plan()
   - OpenAI with JSON Schema (if enabled)
   - Auto-repair on invalid JSON
   - Returns: {text, needs_fresh_facts, tool_calls[], lesson_plan[], image_queries[]}
  ↓
2. Pass-2a: real_images_for_queries()
   - Parallel image fetching (Unsplash → Pexels)
   - Attach to cards via attach_images_to_cards()
  ↓
3. Pass-2b: run_tools_parallel()
   - Fan-out: search, weather, marine (asyncio.gather)
   - 10s timeout per tool
   - Returns: {search: {...}, weather: {...}, marine: {...}}
  ↓
4. Pass-2c: merge_tool_results_into_cards()
   - Attach citations to cards/steps
   - Enrich plan cards with conditions
  ↓
5. Return ChatResponse
```

### SSE Streaming Flow
```
GET /api/chat/stream?message=...
  ↓
Event 1: {"type": "status", "stage": "planning"}
Event 2: {"type": "cards", "cards": [...], "text": "..."}
Event 3: {"type": "tool", "name": "weather", "ok": true}
Event 4: {"type": "tool", "name": "marine", "ok": true}
Event 5: {"type": "result", "payload": {...}}
```

---

## Tool Development

### Adding a New Tool

1. **Create tool function** in `apps/api/tools/`
```python
# apps/api/tools/tides.py
async def get_tides(lat: float, lon: float, date: str) -> Dict:
    if settings.ci:
        return {"tides": [{"time": "06:15", "height": 1.2, "type": "high"}]}
    # ... real implementation
```

2. **Export in** `apps/api/tools/__init__.py`
```python
from .tides import get_tides
__all__ = [..., "get_tides"]
```

3. **Wire into orchestrator** `run_tool_with_timeout()`
```python
elif tool_name == "tides":
    return await get_tides(lat, lon, date)
```

4. **Update schemas** `ToolCallType` enum
```python
class ToolCallType(str, Enum):
    ...
    tides = "tides"
```

5. **Update JSON Schema** `PASS1_JSON_SCHEMA`
```python
"enum": [..., "tides"]
```

6. **Add test** in `tests/test_chat_happy.py`

---

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | (required) | OpenAI API access |
| `AI_MODEL_CHAT` | `gpt-5-mini` | Chat model |
| `AI_USE_JSON_SCHEMA` | `1` | Enable structured outputs |
| `SEARCH_PROVIDER` | `responses_api` | Search backend |
| `CACHE_TTL_S` | `1800` | Cache duration (30 min) |
| `APP_ORIGIN` | `http://localhost:3000` | CORS origin |
| `CI` | `0` | Enable stub responses for tests |

### Feature Flags

- `AI_USE_JSON_SCHEMA=0` → Disable JSON Schema, use fallback parsing
- `CI=1` → All tools return canned responses (test-safe)
- `SEARCH_PROVIDER=duckduckgo` → Use DDG instead of Responses API

---

## Testing Strategy

### Unit Tests
- **Mocked dependencies**: OpenAI, tools (search, weather, marine)
- **CI stubs**: When `CI=1`, tools return deterministic data
- **Fast & reliable**: No external API calls during tests

### Integration Tests
- Run with real API keys (local only, not in CI)
- Set `CI=0` and provide real `OPENAI_API_KEY`

### Manual Smoke Test
```bash
# Start both servers
# Terminal 1: API
source .venv/bin/activate && uvicorn apps.api.main:app --reload

# Terminal 2: Web
npm --prefix apps/web run dev

# Test queries:
# 1. "How to tie a uni knot?" (images only)
# 2. "Fishing plan Clarence River this weekend" (weather + marine)
# 3. "What is fly fishing?" (search + citations)
```

---

## Monitoring

### Prometheus Metrics

Access at `http://127.0.0.1:8000/metrics`

**Key metrics**:
- `kf_requests_total` - Request count by endpoint/status
- `kf_request_duration_seconds` - Latency histogram
- `kf_tool_calls_total` - Tool usage counter
- `kf_tool_latency_seconds` - Per-tool latency

### Health Checks

```bash
# Basic health
curl http://127.0.0.1:8000/health
# → {"ok": true, "app": "Kingfisher 2465"}

# Upstream check (hits OpenAI)
curl http://127.0.0.1:8000/ready
# → {"ok": true, "upstream": "healthy"}
```

---

## Troubleshooting

### "Module not found" errors
```bash
# Reinstall dependencies
pip install -r apps/api/requirements.txt
npm --prefix apps/web install
```

### JSON Schema errors
```bash
# Disable JSON Schema temporarily
export AI_USE_JSON_SCHEMA=0
# Fallback parser will handle responses
```

### Tool timeouts
```bash
# Increase timeout in orchestrator.py
timeout=20.0  # Default is 10.0
```

### SSE not working
- Frontend falls back to `/api/chat` automatically
- Check CORS settings in `.env` → `APP_ORIGIN`
- Verify EventSource support in browser

---

## Code Style

### Python (PEP 8 + Ruff)
- Line length: 120 chars
- Auto-format: `ruff format apps/api tests`
- Type hints preferred but not required

### TypeScript (Next.js conventions)
- Strict mode enabled
- ESLint: next/core-web-vitals
- Prefer functional components

### Commit Messages
```
feat: Add weather/marine tools with Open-Meteo
fix: Handle JSON parse errors in Pass-1
test: Add SSE streaming tests
docs: Update README with 2025 features
```

---

**Questions?** See `IMPLEMENTATION_SUMMARY.md` for detailed changelog.

