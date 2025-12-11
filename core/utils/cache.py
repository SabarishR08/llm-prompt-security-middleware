import functools
from typing import Any, Callable

class Cache:
    """Simple caching utility for analysis results."""
    
    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self._cache = {}
    
    @functools.lru_cache(maxsize=128)
    def cached_analyze(self, prompt: str) -> str:
        """Cached analysis results to avoid redundant processing."""
        return prompt
    
    def clear(self):
        """Clear the cache."""
        self.cached_analyze.cache_clear()
        self._cache.clear()
        print("🧹 Cache cleared")
    
    def get_cache_info(self) -> dict:
        """Get cache statistics."""
        info = self.cached_analyze.cache_info()
        return {
            "hits": info.hits,
            "misses": info.misses,
            "currsize": info.currsize,
            "maxsize": info.maxsize
        }
