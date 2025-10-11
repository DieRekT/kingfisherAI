import httpx
from typing import List, Dict
from .config import settings

async def search_unsplash(q: str, n: int = 3) -> List[Dict]:
    if not settings.unsplash_key:
        return []
    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {settings.unsplash_key}"}
    params = {"query": q, "per_page": n, "orientation": "landscape"}
    async with httpx.AsyncClient(timeout=20) as cx:
        r = await cx.get(url, headers=headers, params=params)
    if r.status_code != 200:
        return []
    data = r.json()
    out = []
    for it in data.get("results", []):
        out.append({
            "url": it["urls"]["regular"],
            "alt": it.get("alt_description") or q,
            "credit": it["user"]["name"],
            "provider": "unsplash"
        })
    return out

async def search_pexels(q: str, n: int = 3) -> List[Dict]:
    if not settings.pexels_key:
        return []
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": settings.pexels_key}
    params = {"query": q, "per_page": n, "orientation": "landscape"}
    async with httpx.AsyncClient(timeout=20) as cx:
        r = await cx.get(url, headers=headers, params=params)
    if r.status_code != 200:
        return []
    data = r.json()
    out = []
    for it in data.get("photos", []):
        out.append({
            "url": it["src"]["large"],
            "alt": it.get("alt") or q,
            "credit": it["photographer"],
            "provider": "pexels"
        })
    return out

