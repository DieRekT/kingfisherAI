from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import asyncio
import json
import time
from .config import settings
from .schemas import ChatResponse
from .orchestrator import two_pass_answer, pass1_analyze_and_plan, run_tools_parallel, real_images_for_queries, attach_images_to_cards, merge_tool_results_into_cards
from openai import AsyncOpenAI

app = FastAPI(title=settings.app_name)

# CORS: lock to APP_ORIGIN when set
cors_origins = [settings.app_origin] if settings.app_origin else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
kf_requests_total = Counter("kf_requests_total", "Total API requests", ["endpoint", "status"])
kf_request_duration = Histogram("kf_request_duration_seconds", "Request duration", ["endpoint"])
kf_tool_calls_total = Counter("kf_tool_calls_total", "Total tool calls", ["tool"])
kf_tool_latency_seconds = Histogram("kf_tool_latency_seconds", "Tool call latency", ["tool"])

@app.get("/health")
def health():
    kf_requests_total.labels(endpoint="health", status="200").inc()
    return {"ok": True, "app": settings.app_name}

@app.get("/ready")
async def ready():
    """Health check with upstream reachability test."""
    try:
        # Quick OpenAI API ping (300-500ms budget)
        client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=0.5)
        await client.models.list()
        kf_requests_total.labels(endpoint="ready", status="200").inc()
        return {"ok": True, "upstream": "healthy"}
    except Exception as e:
        kf_requests_total.labels(endpoint="ready", status="503").inc()
        raise HTTPException(503, f"Upstream unhealthy: {str(e)}")

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: dict):
    """Traditional chat endpoint (non-streaming)."""
    t0 = time.time()
    q = (payload.get("message") or "").strip()
    if not q:
        kf_requests_total.labels(endpoint="chat", status="400").inc()
        raise HTTPException(400, "message is required")
    
    try:
        data = await two_pass_answer(q)
        duration = time.time() - t0
        kf_requests_total.labels(endpoint="chat", status="200").inc()
        kf_request_duration.labels(endpoint="chat").observe(duration)
        
        # Track tool calls
        for tool in data.get("tool_calls", []):
            kf_tool_calls_total.labels(tool=tool).inc()
        
        return data
    except Exception as e:
        kf_requests_total.labels(endpoint="chat", status="500").inc()
        raise HTTPException(500, str(e))

async def stream_chat_events(user_prompt: str):
    """Generate SSE events for progressive chat response."""
    try:
        # Event 1: Status (planning)
        yield f"data: {json.dumps({'type': 'status', 'stage': 'planning'})}\n\n"
        await asyncio.sleep(0.1)
        
        # Pass 1: Plan
        plan = await pass1_analyze_and_plan(user_prompt)
        img_queries = plan.get("image_queries", [])
        tool_calls = plan.get("tool_calls", [])
        needs_fresh_facts = plan.get("needs_fresh_facts", False)
        
        # Event 2: Cards (initial, no images/tools yet)
        cards = plan.get("lesson_plan", [])
        yield f"data: {json.dumps({'type': 'cards', 'cards': cards, 'text': plan.get('text', '')})}\n\n"
        await asyncio.sleep(0.1)
        
        # Pass 2a: Fetch images
        img_bag = await real_images_for_queries(img_queries) if img_queries else {}
        cards_with_images = attach_images_to_cards(plan, img_bag)
        
        # Pass 2b: Run tools in parallel
        context = {
            "query": user_prompt,
            "text": plan.get("text", ""),
            "place": "Clarence River, NSW"
        }
        
        # Run tools and emit progress
        if tool_calls:
            yield f"data: {json.dumps({'type': 'status', 'stage': 'fetching_data'})}\n\n"
            
            tool_results = await run_tools_parallel([t for t in tool_calls if t != "images"], context)
            
            # Event 3: Tool results
            for tool_name, result in tool_results.items():
                ok = not result.get("error")
                yield f"data: {json.dumps({'type': 'tool', 'name': tool_name, 'ok': ok})}\n\n"
                kf_tool_calls_total.labels(tool=tool_name).inc()
                await asyncio.sleep(0.05)
        else:
            tool_results = {}
        
        # Pass 2c: Merge tool results
        final_cards = merge_tool_results_into_cards(cards_with_images, tool_results, user_prompt)
        
        # Track actual tools
        actual_tools = ["images"] if img_queries else []
        actual_tools.extend([t for t in tool_calls if t != "images"])
        
        # Event 4: Final result
        final_response = {
            "text": plan.get("text", ""),
            "lesson_cards": final_cards,
            "tool_calls": actual_tools,
            "model": plan.get("_model_used"),
            "needs_fresh_facts": needs_fresh_facts
        }
        yield f"data: {json.dumps({'type': 'result', 'payload': final_response})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.get("/api/chat/stream")
async def chat_stream(message: str = ""):
    """SSE streaming chat endpoint."""
    t0 = time.time()
    if not message.strip():
        kf_requests_total.labels(endpoint="chat_stream", status="400").inc()
        raise HTTPException(400, "message query parameter is required")
    
    kf_requests_total.labels(endpoint="chat_stream", status="200").inc()
    
    async def event_generator():
        async for event in stream_chat_events(message):
            yield event
        duration = time.time() - t0
        kf_request_duration.labels(endpoint="chat_stream").observe(duration)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

