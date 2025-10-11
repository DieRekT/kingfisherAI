import httpx
import logging
from typing import List, Dict
from .config import settings
from .cache import TTLCache

logger = logging.getLogger(__name__)
_img_cache = TTLCache()

class ImageResult(dict):
    """Normalized image record with url, thumb, alt, credit, href."""
    pass

async def _unsplash_search_raw(query: str, per_page: int = 1) -> dict:
    """Raw Unsplash API call."""
    if not settings.unsplash_key:
        return {"results": []}
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "per_page": per_page,
        "orientation": "landscape",
        "content_filter": "high",
    }
    headers = {
        "Authorization": f"Client-ID {settings.unsplash_key}",
        "Accept-Version": "v1",
    }
    timeout = httpx.Timeout(12.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()

def _unsplash_map(photo: dict) -> ImageResult:
    """Map Unsplash photo response to normalized ImageResult."""
    urls = photo.get("urls", {}) or {}
    user = photo.get("user", {}) or {}
    name = user.get("name") or "Unknown"
    html = photo.get("links", {}).get("html")
    return ImageResult(
        url=urls.get("regular") or urls.get("full") or urls.get("small"),
        thumb=urls.get("thumb"),
        alt=photo.get("alt_description") or "",
        credit=f"Photo by {name} on Unsplash",
        href=html,
        provider="unsplash"
    )

async def unsplash_search(query: str, per_page: int = 1) -> List[ImageResult]:
    """Search Unsplash with caching; returns normalized image results."""
    # CI stub: return deterministic test images
    if settings.ci:
        stub_result = [ImageResult(
            url=f"https://example.com/test/{query.replace(' ', '_')}.jpg",
            thumb=f"https://example.com/test/{query.replace(' ', '_')}_thumb.jpg",
            alt=f"Test image for {query}",
            credit="Photo by Test User on Unsplash",
            href="https://unsplash.com/photos/test",
            provider="unsplash"
        )]
        return stub_result
    
    key = f"unsplash::{per_page}::{query.strip().lower()}"
    hit = _img_cache.get(key)
    if hit is not None:
        logger.debug(f"Cache hit for: {query}")
        return hit
    try:
        j = await _unsplash_search_raw(query, per_page=per_page)
        results = [_unsplash_map(p) for p in (j.get("results") or [])]
        _img_cache.set(key, results)
        logger.info(f"Unsplash search: '{query}' returned {len(results)} results")
        return results
    except Exception as e:
        logger.warning(f"Unsplash search failed for '{query}': {str(e)}")
        _img_cache.set(key, [])
        return []

async def search_unsplash(q: str, n: int = 3) -> List[Dict]:
    """Legacy compatibility wrapper."""
    results = await unsplash_search(q, per_page=n)
    return results

async def search_pexels(q: str, n: int = 3) -> List[Dict]:
    """Search Pexels with error handling and CI stub support."""
    # CI stub: return deterministic test images
    if settings.ci:
        return [{
            "url": f"https://example.com/pexels/{q.replace(' ', '_')}.jpg",
            "alt": f"Test image for {q}",
            "credit": "Test Photographer",
            "href": "https://www.pexels.com/photo/test",
            "provider": "pexels"
        }]
    
    if not settings.pexels_key:
        logger.debug("Pexels: No API key configured")
        return []
    
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": settings.pexels_key}
        params = {"query": q, "per_page": n, "orientation": "landscape"}
        timeout = httpx.Timeout(12.0, connect=5.0)
        
        async with httpx.AsyncClient(timeout=timeout) as cx:
            r = await cx.get(url, headers=headers, params=params)
            r.raise_for_status()
        
        data = r.json()
        out = []
        for it in data.get("photos", []):
            src = it.get("src", {})
            out.append({
                "url": src.get("large") or src.get("original"),
                "thumb": src.get("medium"),
                "alt": it.get("alt") or q,
                "credit": f"Photo by {it.get('photographer', 'Unknown')} on Pexels",
                "href": it.get("url"),
                "provider": "pexels"
            })
        logger.info(f"Pexels search: '{q}' returned {len(out)} results")
        return out
    except httpx.HTTPStatusError as e:
        logger.warning(f"Pexels HTTP error for '{q}': {e.response.status_code}")
        return []
    except Exception as e:
        logger.warning(f"Pexels search failed for '{q}': {str(e)}")
        return []

