"""Web search tool with TTL cache and CI stub support."""
import time
import httpx
from typing import Dict, List
from ..config import settings

# Simple TTL cache: {query: (results, expiry_time)}
_search_cache: Dict[str, tuple] = {}

def _get_cached(query: str) -> Dict | None:
    """Get cached result if still valid."""
    if query in _search_cache:
        results, expiry = _search_cache[query]
        if time.time() < expiry:
            return results
        else:
            del _search_cache[query]
    return None

def _set_cache(query: str, results: Dict):
    """Cache results with TTL."""
    expiry = time.time() + settings.cache_ttl_s
    _search_cache[query] = (results, expiry)

async def search_web(query: str, k: int = 5) -> Dict[str, List[Dict]]:
    """
    Search the web and return results with citations.
    
    Args:
        query: Search query string
        k: Number of results to return (default 5)
    
    Returns:
        {
            "results": [{"title": str, "url": str, "snippet": str}, ...],
            "citations": [{"url": str, "title": str}, ...]
        }
    """
    # Check cache first
    cached = _get_cached(query)
    if cached:
        return cached
    
    # CI stub: return canned results
    if settings.ci:
        stub_result = {
            "results": [
                {
                    "title": f"Test Result for {query}",
                    "url": "https://example.com/test",
                    "snippet": f"This is a test search result for: {query}"
                }
            ],
            "citations": [
                {
                    "url": "https://example.com/test",
                    "title": f"Test Result for {query}"
                }
            ]
        }
        _set_cache(query, stub_result)
        return stub_result
    
    # Real search based on provider
    provider = settings.search_provider.lower()
    
    if provider == "responses_api":
        # Placeholder for OpenAI Responses API (when available)
        # For now, use a simple fallback
        result = await _fallback_search(query, k)
    else:
        result = await _fallback_search(query, k)
    
    _set_cache(query, result)
    return result

async def _fallback_search(query: str, k: int) -> Dict[str, List[Dict]]:
    """
    Fallback search using a simple method.
    In production, replace with actual search API.
    """
    # For MVP, return a placeholder that indicates search was attempted
    results = []
    citations = []
    
    # Try DuckDuckGo HTML scraping (simple, no API key needed)
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            params = {"q": query, "format": "json", "no_html": "1"}
            resp = await client.get("https://api.duckduckgo.com/", params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Extract results from DDG API
                if data.get("Abstract"):
                    results.append({
                        "title": data.get("Heading", "Result"),
                        "url": data.get("AbstractURL", ""),
                        "snippet": data.get("Abstract", "")
                    })
                    citations.append({
                        "url": data.get("AbstractURL", ""),
                        "title": data.get("Heading", "Result")
                    })
                
                # Add related topics
                for topic in data.get("RelatedTopics", [])[:k-1]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "")[:100],
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", "")
                        })
                        if topic.get("FirstURL"):
                            citations.append({
                                "url": topic["FirstURL"],
                                "title": topic.get("Text", "")[:100]
                            })
    except Exception:
        # If search fails, return empty but valid structure
        pass
    
    return {
        "results": results[:k],
        "citations": citations[:k]
    }

