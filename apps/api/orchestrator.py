import time, asyncio, json
import logging
from typing import Dict, Any, List, Optional
from .config import settings
from openai import OpenAI
from .images import search_unsplash, search_pexels, unsplash_search
from .schemas import PASS1_JSON_SCHEMA, Citation

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.openai_api_key, timeout=settings.ai_request_timeout_s)

SYSTEM_PRIME = f"""You are Kingfisher 2465, a polymath teaching assistant that produces modern "teacher cards".

OUTPUT CONTRACT (IMPORTANT)
- Return ONLY a JSON object that VALIDATES against the provided strict JSON Schema.
- No markdown. No prose. No comments. No trailing text.
- Disallow extra fields. Use only the properties in the schema.
- Steps must be objects with exactly {{"title","body"}}.

GOALS
- Design a small set of high-utility cards that help the user complete the task or grasp the concept quickly.
- Use clear, everyday, precise language. Prefer actions and concrete details.
- Use metric units by default (°C, km/h, mm, m, kg). If the user clearly implies a different locale, follow it.
- Include short, practical safety notes when relevant.
- Timezone context: {settings.app_timezone}

CARD DESIGN
- kinds: "howto", "concept", "plan", "reference".
- Typical counts:
  - howto: 1–2 cards, 3–7 steps
  - concept: 1 card with 3–5 bullets (use steps as bullets)
  - plan: 1 card with phased steps (e.g., Setup → Execute → Check)
  - reference: 1 card with concise facts / checklists
- Step titles: short, verb-led ("Thread the line"). Step bodies: 1–2 sentences max with numbers, ranges, or examples.
- Themes: choose from "river", "ocean", "earth", "amber", "slate", "emerald", "indigo" based on card context.
- Summary: brief 1-line card description.

TOOLS & FRESHNESS
- Set tool_calls per query using "tool_calls": 
  - "images" when visuals clarify steps or parts
  - "weather" / "marine" for outdoor / fishing / boating context
  - "search" when the answer may depend on fresh facts (news, prices, dates, laws)
- Set "needs_fresh_facts": true if any part requires up-to-date info.

IMAGES
- Populate top-level "image_queries" with 1–4 precise queries useful across the lesson (e.g., "uni knot step sequence", "clarence river estuary aerial").
- Do NOT put image fields inside steps. (Steps only have "title" and "body".)

SCOPE CONTROL
- If the user is vague, pick the most useful, practical slice and plan that.
- If the request is unsafe or disallowed, plan a safe educational alternative (e.g., safety practices, lawful equivalents) and reflect that need in "needs_fresh_facts" if relevant.

RETURN ONLY THE JSON OBJECT.
"""

async def pass1_analyze_and_plan(prompt: str) -> Dict[str, Any]:
    """Use OpenAI to plan lesson cards with JSON Schema when enabled."""
    model = settings.ai_model_chat
    logger.info(f"Pass1 planning: model={model}, prompt_length={len(prompt)}")
    
    # Build request kwargs
    request_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PRIME},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_completion_tokens": settings.ai_max_output_tokens
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
        logger.info(f"Pass1 success: cards={len(plan.get('lesson_plan', []))}, tools={plan.get('tool_calls', [])}")
    except json.JSONDecodeError as e:
        # Auto-repair attempt: ask AI to fix invalid JSON with schema awareness
        logger.warning(f"JSON decode error, attempting schema-aware repair: {str(e)[:100]}")
        try:
            repair_system = f"""Your previous response did not validate against the strict JSON Schema.

TASK
- Return ONLY a single JSON object that now VALIDATES against the provided schema.
- No markdown. No prose. No comments. No surrounding text.

SOURCE MATERIAL
- User prompt: {prompt}
- Previous (invalid) output: {content}

REPAIR RULES (APPLY ALL)
1) Use only fields defined by the schema; remove everything else (additionalProperties=false).
2) Steps must be objects with exactly {{"title","body"}}.
   - If a step was a string, map to {{"title": <string>, "body": ""}}.
   - If "body" is too long, keep its first 1–2 sentences.
3) Keep card structure and intent where clear; otherwise infer conservatively.
4) "kind" ∈ {{"howto","concept","plan","reference"}} — choose the closest match.
5) "tool_calls" only from {{"images","search","weather","marine","tides"}}.
6) Put ALL image intent in top-level "image_queries" (array of strings).
   - Remove any "image_query" fields from steps or cards.
7) Types must match exactly (booleans, arrays, strings). Coerce where obvious; drop if uncertain.
8) Size & shape limits:
   - 1–3 cards; each card 3–7 steps (concept/reference may use 3–5 short bullets).
   - Truncate excessive items; ensure at least one card and one step.
9) Freshness:
   - Set "needs_fresh_facts" = true only if the prompt clearly depends on current conditions, rules, or news.
10) Locale:
   - Use metric units if any units appear (°C, km/h, mm, m, kg).

FALLBACK (IF CONTENT IS UNRECOVERABLE)
- Produce a minimal but valid plan:
  {{
    "text": "Here's a practical guide.",
    "needs_fresh_facts": false,
    "image_queries": ["illustration of the main task"],
    "tool_calls": ["images"],
    "lesson_plan": [{{
      "kind": "howto",
      "title": "Quick Plan",
      "theme": "slate",
      "summary": "Step-by-step guide",
      "steps": [
        {{"title": "Overview", "body": "High-level steps to start."}},
        {{"title": "Next action", "body": "One concrete action to progress."}}
      ]
    }}]
  }}

OUTPUT
- Return ONLY the corrected JSON object that validates against the schema."""

            repair_kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": repair_system},
                    {"role": "user", "content": "Repair the JSON to match the schema."}
                ],
                "temperature": 0.1,
                "max_completion_tokens": settings.ai_max_output_tokens
            }
            
            # Use same strict schema for repair
            if settings.ai_use_json_schema:
                repair_kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": PASS1_JSON_SCHEMA
                }
            
            repair_resp = client.chat.completions.create(**repair_kwargs)
            plan = json.loads(repair_resp.choices[0].message.content.strip())
            logger.info("JSON repair successful")
        except Exception as repair_err:
            # Graceful fallback to safe defaults
            logger.error(f"JSON repair failed: {str(repair_err)}")
            plan = {
                "text": "I've prepared a guide based on your request. Please check the cards below for details.",
                "needs_fresh_facts": False,
                "image_queries": ["fishing guide illustration"],
                "tool_calls": ["images"],
                "lesson_plan": [{
                    "kind": "howto",
                    "title": "Getting Started",
                    "theme": "slate",
                    "summary": "Basic steps to begin",
                    "steps": [
                        {"title": "Preparation", "body": "Gather your materials and review the task."},
                        {"title": "First step", "body": "Start with the most important action."},
                        {"title": "Next steps", "body": "Continue following the sequence carefully."}
                    ]
                }]
            }
    except Exception as e:
        # Fallback for any other errors
        logger.error(f"Pass1 error: {str(e)}", exc_info=True)
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
            q = step.get("title") or card.get("title")
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

async def run_tool_with_timeout(tool_name: str, context: Dict[str, Any], timeout: float = 12.0) -> Optional[Dict]:
    """Run a single tool with timeout and exponential backoff retry logic."""
    from .tools import search_web, get_weather, get_marine
    from .tools.weather import geocode
    
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
    
    # Retry logic with exponential backoff
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Running tool {tool_name}, attempt {attempt + 1}/{max_retries + 1}")
            result = await asyncio.wait_for(_run_tool(), timeout=timeout)
            if not result.get("error"):
                logger.info(f"Tool {tool_name} succeeded on attempt {attempt + 1}")
            return result
        except asyncio.TimeoutError:
            if attempt < max_retries:
                wait_time = 0.5 * (2 ** attempt)  # 0.5s, 1s
                logger.warning(f"Tool {tool_name} timeout, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Tool {tool_name} timed out after {max_retries + 1} attempts")
                return {"error": f"Tool {tool_name} timed out after {timeout}s"}
        except Exception as e:
            logger.error(f"Tool {tool_name} error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (2 ** attempt))
            else:
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

async def write_chat_text(user_prompt: str, cards: List[Dict], tool_results: Dict[str, Any]) -> str:
    """Generate concise chat text that pairs with the lesson cards."""
    
    # Build compact card summary
    card_summaries = []
    for card in cards:
        steps_preview = [s.get("title", "") for s in card.get("steps", [])[:3]]
        card_summaries.append({
            "kind": card.get("kind"),
            "title": card.get("title"),
            "step_titles": steps_preview
        })
    
    # Build compact tool outcomes summary
    tool_outcomes = []
    if "weather" in tool_results and not tool_results["weather"].get("error"):
        w = tool_results["weather"].get("current", {})
        if w:
            tool_outcomes.append(f"Weather: {w.get('temp', 'N/A')}°C, wind {w.get('wind_speed', 'N/A')} km/h")
    
    if "marine" in tool_results and not tool_results["marine"].get("error"):
        m = tool_results["marine"].get("current", {})
        if m:
            tool_outcomes.append(f"Marine: swell {m.get('wave_height', 'N/A')}m, period {m.get('wave_period', 'N/A')}s")
    
    tool_summary = " ".join(tool_outcomes) if tool_outcomes else ""
    
    # Construct prompt for chat writer
    chat_writer_prompt = f"""User asked: "{user_prompt}"

Cards planned ({len(cards)} total):
{json.dumps(card_summaries, indent=2)}

Tool outcomes:
{tool_summary or "No fresh data."}

Write the concise chat text (2-6 sentences) that introduces these cards."""
    
    system_chat_writer = """You are Kingfisher 2465, a clear, friendly teacher. Write a concise reply that pairs with the lesson cards the user will see.

OBJECTIVE
- In 2–6 sentences, tell the user what they'll accomplish and how the cards below help.
- Be specific, practical, and confident. Use metric units by default (°C, km/h, mm, m, kg).
- If safety matters, include one short, practical safety pointer (max 1 sentence).

ALIGNMENT WITH CARDS
- Reflect exactly what the provided cards cover. Do not contradict or re-plan.
- Mention card scope briefly (e.g., "step-by-step how-to", "quick reference", "two-phase plan").
- Do not list steps; that's what the cards are for.

TOOLS & FRESH DATA (if provided)
- If tool outcomes are included (weather/marine/search), summarize how they inform the guidance (no URLs).
  Examples: "Light SE wind and small swell favour estuary mouths." / "Recent size limits are included below."

STYLE
- First sentence: outcome-oriented and helpful ("You'll tie a reliable Uni Knot…").
- Tone: warm, concise, professional—no fluff, no emojis.
- Prefer active voice and numbers ("5 wraps", "20–30 cm leader").
- If assumptions were needed (due to a vague prompt), state them briefly ("Assuming estuary fishing in calm conditions…").

SAFETY & SCOPE
- If the request is risky/illegal, pivot to a safe, educational alternative and say so in one sentence.
- For medical/legal/financial topics: give general guidance only and encourage professional advice.

OUTPUT RULES
- Plain text only. No markdown, no bullet lists, no links.
- Keep to ~50–120 words unless the cards are unusually complex."""
    
    try:
        logger.info("Generating chat text with card context")
        resp = client.chat.completions.create(
            model=settings.ai_model_chat,
            messages=[
                {"role": "system", "content": system_chat_writer},
                {"role": "user", "content": chat_writer_prompt}
            ],
            temperature=0.7,
            max_completion_tokens=300
        )
        text = resp.choices[0].message.content.strip()
        logger.info(f"Chat text generated: {len(text)} chars")
        return text
    except Exception as e:
        logger.error(f"Chat writer error: {str(e)}")
        # Fallback to simple intro
        return f"Here's what I found on {user_prompt}. The cards below walk you through it step by step."


# ---------- Step-visual detection & cardify ----------
_STEP_VISUAL_HINTS = ("knot", "rig", "lure", "assemble", "assembly", "setup", "tie ", "splice", "wrap")

def _is_step_visual_task(user_prompt: str, plan: Dict[str, Any]) -> bool:
    """Detect if this is a step-visual task (knots, rigs, assemblies)."""
    up = (user_prompt or "").lower()
    if any(h in up for h in _STEP_VISUAL_HINTS):
        return True
    for c in plan.get("lesson_plan", []):
        t = (c.get("title") or "").lower()
        if any(h in t for h in _STEP_VISUAL_HINTS):
            return True
    return False

def _overview_title(orig: Dict[str, Any]) -> str:
    """Generate overview title from original card title."""
    t = orig.get("title") or "Overview"
    return t if "overview" in t.lower() else f"{t} — Overview"

def _cardify_steps(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a howto with N steps into:
      - 1 'Overview' howto card (original steps)
      - N per-step 'howto' cards, each with a single step
    Keeps other cards intact.
    """
    new_cards: List[Dict[str, Any]] = []
    for c in plan.get("lesson_plan", []):
        if c.get("kind") == "howto" and c.get("steps") and len(c["steps"]) > 1:
            # Overview card
            overview = dict(c)
            overview["title"] = _overview_title(c)
            new_cards.append(overview)
            # Per-step cards
            for idx, s in enumerate(c["steps"], start=1):
                step_title = s.get("title") if isinstance(s, dict) else str(s)
                step_card = {
                    "title": f"Step {idx}: {step_title}",
                    "kind": "howto",
                    "theme": c.get("theme", "river"),
                    "summary": f"Detailed view of step {idx}",
                    "steps": [s if isinstance(s, dict) else {"title": str(s), "body": ""}],
                }
                new_cards.append(step_card)
        else:
            new_cards.append(c)
    plan["lesson_plan"] = new_cards
    return plan

def _step_query_seed(plan_title: str, step_title: str, idx: int) -> str:
    """Generate step-specific image query."""
    # Remove "Step N:" prefix if present
    clean_step = step_title.replace(f"Step {idx}:", "").strip()
    return f"{plan_title} {clean_step} step {idx} diagram"

async def _attach_step_images(user_prompt: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    For per-step cards, fetch Unsplash image for each step card.
    Attach: card['images'] = [{url, thumb, alt, credit, href}]
    """
    cards = plan.get("lesson_plan", [])
    # Choose a parent howto title as the base seed
    base_title = ""
    for c in cards:
        if c.get("kind") == "howto" and "overview" in c.get("title", "").lower():
            base_title = c.get("title", "").replace(" — Overview", "").replace("—Overview", "")
            break
    if not base_title:
        for c in cards:
            if c.get("kind") == "howto":
                base_title = c.get("title") or base_title
                break
    if not base_title:
        base_title = user_prompt

    async def fetch_for_card(i: int, card: Dict[str, Any]):
        # Only attach to per-step cards (not overview, not multi-step)
        if not (card.get("kind") == "howto" and card.get("steps") and len(card["steps"]) == 1):
            return
        if "overview" in card.get("title", "").lower():
            return
        step = card["steps"][0]
        stitle = step.get("title") if isinstance(step, dict) else str(step)
        q = _step_query_seed(base_title, stitle, i)
        hits = await unsplash_search(q, per_page=1)
        if hits:
            # Attach as card-level images list
            card["images"] = [hits[0]]
            logger.info(f"Attached image to '{card['title']}' from query: {q}")

    # fetch in parallel with small concurrency
    sem = asyncio.Semaphore(6)
    async def _task(i, c):
        async with sem:
            await fetch_for_card(i, c)

    await asyncio.gather(*[_task(i, c) for i, c in enumerate(cards, start=1)], return_exceptions=True)
    return plan

async def two_pass_answer(user_prompt: str) -> Dict[str, Any]:
    t0 = time.time()
    plan = await pass1_analyze_and_plan(user_prompt)
    img_queries = plan.get("image_queries", [])
    tool_calls = plan.get("tool_calls", [])
    needs_fresh_facts = plan.get("needs_fresh_facts", False)
    
    # Check if this is a step-visual task and cardify if needed
    is_step_visual = _is_step_visual_task(user_prompt, plan)
    if is_step_visual:
        logger.info("Detected step-visual task, cardifying steps...")
        plan = _cardify_steps(plan)
    
    # Phase 2a: Fetch images (existing logic for overview queries)
    img_bag = await real_images_for_queries(img_queries) if img_queries else {}
    cards = attach_images_to_cards(plan, img_bag)
    
    # Phase 2a+: Attach step-specific images if step-visual
    if is_step_visual:
        logger.info("Attaching step-specific images...")
        plan = await _attach_step_images(user_prompt, plan)
        cards = plan.get("lesson_plan", [])
    
    # Phase 2b: Run tools in parallel
    context = {
        "query": user_prompt,
        "text": plan.get("text", ""),
        "place": "Clarence River, NSW"  # Default location; could be extracted from prompt
    }
    tool_results = await run_tools_parallel(tool_calls, context)
    
    # Phase 2c: Merge tool results into cards
    cards = merge_tool_results_into_cards(cards, tool_results, user_prompt)
    
    # Phase 2d: Generate chat text based on cards + tool results
    chat_text = await write_chat_text(user_prompt, cards, tool_results)
    
    # Track which tools were actually called
    actual_tools = ["images"] if img_queries else []
    actual_tools.extend([t for t in tool_calls if t != "images"])
    
    took_ms = int((time.time() - t0) * 1000)
    return {
        "text": chat_text,
        "lesson_cards": cards,
        "tool_calls": actual_tools,
        "model": plan.get("_model_used"),
        "took_ms": took_ms,
        "needs_fresh_facts": needs_fresh_facts
    }


# Compatibility re-exports (legacy support)
from apps.api.compat import run_chat as run_chat  # noqa: F401
from apps.api.compat import ChatRequest as ChatRequest  # noqa: F401
