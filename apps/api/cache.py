from __future__ import annotations
import time
from typing import Any, Dict, Optional
from .config import settings

class TTLCache:
    """Simple in-memory TTL cache with size limit."""
    
    def __init__(self, ttl_s: Optional[int] = None, max_size: int = 1000):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_s or settings.cache_ttl_s
        self._max_size = max_size
    
    def get(self, key: str) -> Any | None:
        """Get value if exists and not expired."""
        if key not in self._cache:
            return None
        value, expires_at = self._cache[key]
        if time.time() > expires_at:
            del self._cache[key]
            return None
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set value with TTL expiration, evicting old entries if needed."""
        # Clean expired entries first
        self._evict_expired()
        
        # If still over limit, remove oldest entries
        if len(self._cache) >= self._max_size:
            self._evict_oldest(count=max(1, self._max_size // 10))
        
        expires_at = time.time() + self._ttl
        self._cache[key] = (value, expires_at)
    
    def _evict_expired(self) -> None:
        """Remove all expired entries."""
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._cache.items() if now > exp]
        for k in expired_keys:
            del self._cache[k]
    
    def _evict_oldest(self, count: int) -> None:
        """Remove the oldest N entries by expiration time."""
        if not self._cache or count <= 0:
            return
        sorted_items = sorted(self._cache.items(), key=lambda x: x[1][1])
        for k, _ in sorted_items[:count]:
            del self._cache[k]
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
    
    def size(self) -> int:
        """Return current cache size (after cleaning expired)."""
        self._evict_expired()
        return len(self._cache)

