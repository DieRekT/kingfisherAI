import time, asyncio, json
from typing import Dict, Any, List, Optional
from .config import settings
from openai import OpenAI
from .images import search_unsplash, search_pexels
from .schemas import PASS1_JSON_SCHEMA, Citation

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PRIME = f"""You are Harwood — friendly Clarence River guide on the surface, calm polymath underneath.
Rules:
- Tools-first for time/place data; tag prompts with tool_calls: ["weather", "marine", "search"] when relevant.
- Timezone: {settings.app_timezone}; short, useful answers first.
- When the user asks "how to", prefer structured lesson cards: headings + steps.
- Mark needs_fresh_facts: true if query needs current data (weather, tides, search).
- Fetch real images first; only "generate" when none found (return a 'placeholder' url and 'provider': 'generate').
- Keep it concise; avoid purple prose.
Output must be valid JSON with keys: text (string), needs_fresh_facts (boolean), tool_calls (array), lesson_plan (array of cards {{kind,title,theme,summary?,steps[]}}), image_queries (array of short queries for each card/step).
Do not include code fences.
"""

async def pass1_analyze_and_plan(prompt: str) -> Dict[str, Any]:
    """Use OpenAI to plan lesson cards with JSON Schema when enabled."""
    model = settings.ai_model_chat
    
    # Build request kwargs
    request_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PRIME},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": settings.ai_max_output_tokens
    }
    
    # Add JSON Schema if enabled
    if settings.ai_use_json_schema:
        request_kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": PASS1_JSON_SCHEMA
        }
    
    try:
        resp = client.chat.completions.create(**request_kwargs)
        content = resp.choices[0].message.content.strip()
        plan = json.loads(content)
    except json.JSONDecodeError as e:
        # Auto-repair attempt: ask AI to fix invalid JSON
        try:
            repair_resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a JSON repair assistant. Return ONLY valid JSON, no other text."},
                    {"role": "user", "content": f"Fix this invalid JSON and return strictly valid JSON:\n{content}"}
                ],
                temperature=0.1,
                max_tokens=settings.ai_max_output_tokens
            )
            plan = json.loads(repair_resp.choices[0].message.content.strip())
        except Exception:
            # Graceful fallback to safe defaults
            plan = {
                "text": content if isinstance(content, str) else "I encountered an error processing your request.",
                "lesson_plan": [],
                "image_queries": [],
                "tool_calls": [],
                "needs_fresh_facts": False
            }
    except Exception as e:
        # Fallback for any other errors
        plan = {
            "text": f"Error: {str(e)}",
            "lesson_plan": [],
            "image_queries": [],
            "tool_calls": [],
            "needs_fresh_facts": False
        }
    
    return plan | {"_model_used": model}

async def real_images_for_queries(queries: List[str]) -> Dict[str, List[Dict]]:
    results: Dict[str, List[Dict]] = {}
    order = [s.strip() for s in settings.image_provider_order.split(",")]
    for q in queries:
        images: List[Dict] = []
        for provider in order:
            if provider == "unsplash":
                images = await search_unsplash(q, 3)
            elif provider == "pexels":
                images = await search_pexels(q, 3)
            elif provider == "generate":
                # placeholder only; generation path can be added later
                images = [{"url": f"https://dummyimage.com/1200x800/111/fff&text={q.replace(' ','+')}",
                           "alt": q, "credit": "Generated", "provider": "generate"}]
            if images:
                break
        results[q] = images
    return results

def attach_images_to_cards(plan: Dict[str, Any], bag: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
    cards = plan.get("lesson_plan", [])
    for card in cards:
        # attach first matching query per step (simple heuristic)
        for step in card.get("steps", []):
            q = step.get("image_query") or step.get("title") or card.get("title")
            imgs = bag.get(q, [])
            if imgs:
                step["image"] = imgs[0]
        # also attach a hero if none
        if not card.get("images"):
            hero_q = card.get("title")
            imgs = bag.get(hero_q, [])
            if imgs:
                card["images"] = [imgs[0]]
    return cards

async def run_tool_with_timeout(tool_name: str, context: Dict[str, Any], timeout: float = 10.0) -> Optional[Dict]:
    """Run a single tool with timeout and retry logic."""
    from .tools import search_web, get_weather, get_marine, geocode
    
    async def _run_tool():
        try:
            if tool_name == "search":
                query = context.get("query", context.get("text", ""))[:100]
                return await search_web(query, k=3)
            
            elif tool_name == "weather":
                lat = context.get("lat")
                lon = context.get("lon")
                if lat is None or lon is None:
                    # Try to geocode from place name
                    place = context.get("place", "Clarence River, NSW")
                    geo = await geocode(place)
                    if geo:
                        lat, lon = geo["lat"], geo["lon"]
                    else:
                        return {"error": "Could not geocode location"}
                return await get_weather(lat, lon, days=3)
            
            elif tool_name == "marine":
                lat = context.get("lat")
                lon = context.get("lon")
                if lat is None or lon is None:
                    place = context.get("place", "Clarence River, NSW")
                    geo = await geocode(place)
                    if geo:
                        lat, lon = geo["lat"], geo["lon"]
                    else:
                        return {"error": "Could not geocode location"}
                return await get_marine(lat, lon, days=3)
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            return {"error": str(e)}
    
    try:
        # Run with timeout
        return await asyncio.wait_for(_run_tool(), timeout=timeout)
    except asyncio.TimeoutError:
        return {"error": f"Tool {tool_name} timed out after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}

async def run_tools_parallel(tool_calls: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run multiple tools in parallel with time budgets.
    
    Args:
        tool_calls: List of tool names to call
        context: Context dict with query, location info, etc.
    
    Returns:
        {
            "search": {...},
            "weather": {...},
            "marine": {...},
            ...
        }
    """
    if not tool_calls:
        return {}
    
    # Create tasks for each tool (excluding "images" as it's handled separately)
    tasks = {}
    for tool in tool_calls:
        if tool not in ["images"]:
            tasks[tool] = run_tool_with_timeout(tool, context, timeout=10.0)
    
    if not tasks:
        return {}
    
    # Run all tools in parallel
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    
    # Map results back to tool names
    tool_results = {}
    for tool_name, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            tool_results[tool_name] = {"error": str(result)}
        else:
            tool_results[tool_name] = result
    
    return tool_results

def merge_tool_results_into_cards(cards: List[Dict], tool_results: Dict[str, Any], user_prompt: str) -> List[Dict]:
    """
    Merge tool results (search, weather, marine) into lesson cards.
    Attaches citations and enriches card content.
    """
    # Extract citations from search results
    citations = []
    if "search" in tool_results and not tool_results["search"].get("error"):
        search_data = tool_results["search"]
        for cit in search_data.get("citations", []):
            citations.append(cit)
    
    # Add weather/marine data as text enrichment or new steps
    enrichments = []
    
    if "weather" in tool_results and not tool_results["weather"].get("error"):
        weather = tool_results["weather"]
        if weather.get("current"):
            curr = weather["current"]
            enrichments.append(f"Current conditions: {curr.get('temp', 'N/A')}°C, wind {curr.get('wind_speed', 'N/A')} km/h")
    
    if "marine" in tool_results and not tool_results["marine"].get("error"):
        marine = tool_results["marine"]
        if marine.get("current"):
            curr = marine["current"]
            enrichments.append(f"Marine: waves {curr.get('wave_height', 'N/A')}m, period {curr.get('wave_period', 'N/A')}s")
    
    # Attach enrichments and citations to cards
    for card in cards:
        # Add citations to the card
        if citations and not card.get("citations"):
            card["citations"] = citations[:2]  # Top 2 citations per card
        
        # If it's a plan card, enrich the first step with conditions
        if card.get("kind") == "plan" and enrichments and card.get("steps"):
            if len(card["steps"]) > 0:
                # Append to first step body
                card["steps"][0]["body"] = card["steps"][0].get("body", "") + "\n\n" + " | ".join(enrichments)
                # Add citations to first step too
                if citations and not card["steps"][0].get("citations"):
                    card["steps"][0]["citations"] = citations[:1]
    
    return cards

async def two_pass_answer(user_prompt: str) -> Dict[str, Any]:
    t0 = time.time()
    plan = await pass1_analyze_and_plan(user_prompt)
    img_queries = plan.get("image_queries", [])
    tool_calls = plan.get("tool_calls", [])
    needs_fresh_facts = plan.get("needs_fresh_facts", False)
    
    # Phase 2a: Fetch images (existing logic)
    img_bag = await real_images_for_queries(img_queries) if img_queries else {}
    cards = attach_images_to_cards(plan, img_bag)
    
    # Phase 2b: Run tools in parallel
    context = {
        "query": user_prompt,
        "text": plan.get("text", ""),
        "place": "Clarence River, NSW"  # Default location; could be extracted from prompt
    }
    tool_results = await run_tools_parallel(tool_calls, context)
    
    # Phase 2c: Merge tool results into cards
    cards = merge_tool_results_into_cards(cards, tool_results, user_prompt)
    
    # Track which tools were actually called
    actual_tools = ["images"] if img_queries else []
    actual_tools.extend([t for t in tool_calls if t != "images"])
    
    took_ms = int((time.time() - t0) * 1000)
    return {
        "text": plan.get("text",""),
        "lesson_cards": cards,
        "tool_calls": actual_tools,
        "model": plan.get("_model_used"),
        "took_ms": took_ms,
        "needs_fresh_facts": needs_fresh_facts
    }


# Compatibility re-exports (legacy support)
from apps.api.compat import run_chat as run_chat  # noqa: F401
from apps.api.compat import ChatRequest as ChatRequest  # noqa: F401
