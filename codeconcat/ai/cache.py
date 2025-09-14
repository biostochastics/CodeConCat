"""Caching system for AI summaries."""

import hashlib
import json
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional


class SummaryCache:
    """Cache for AI-generated summaries to avoid redundant API calls."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl: int = 3600):
        """Initialize the cache.

        Args:
            cache_dir: Directory to store cache files (uses temp if None)
            ttl: Time-to-live in seconds for cache entries
        """
        if cache_dir is None:
            import tempfile

            self.cache_dir = Path(tempfile.gettempdir()) / "codeconcat_ai_cache"
        else:
            self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self._lock = Lock()
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_file(self, key: str) -> Path:
        """Get the cache file path for a given key."""
        return self.cache_dir / f"{key}.json"

    async def get(self, key: str) -> Optional[str]:
        """Retrieve a cached summary if it exists and is not expired.

        Args:
            key: Cache key

        Returns:
            Cached summary or None if not found/expired
        """
        # Check memory cache first
        with self._lock:
            entry = self._memory_cache.get(key)
            if entry and time.time() - entry["timestamp"] < self.ttl:
                return str(entry["summary"])
            elif entry:
                # Expired, remove from memory cache
                del self._memory_cache[key]

        # Check file cache
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    entry = json.load(f)

                if time.time() - entry["timestamp"] < self.ttl:
                    # Load into memory cache
                    self._memory_cache[key] = entry
                    return str(entry["summary"])
                else:
                    # Expired, remove file
                    cache_file.unlink()
            except (OSError, json.JSONDecodeError, KeyError):
                # Corrupted cache file, remove it
                cache_file.unlink(missing_ok=True)

        return None

    async def set(self, key: str, summary: str, metadata: Optional[Dict[str, Any]] = None):
        """Store a summary in the cache.

        Args:
            key: Cache key
            summary: Summary to cache
            metadata: Optional metadata to store with the summary
        """
        entry = {"summary": summary, "timestamp": time.time(), "metadata": metadata or {}}

        # Store in memory cache
        with self._lock:
            self._memory_cache[key] = entry

        # Store in file cache
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, "w") as f:
                json.dump(entry, f, indent=2)
        except OSError:
            # Failed to write cache file, continue without caching to disk
            pass

    def generate_key(
        self, content: str, provider: str, model: str, operation: str, **kwargs
    ) -> str:
        """Generate a cache key based on content and parameters.

        Args:
            content: The content being summarized
            provider: AI provider name
            model: Model name
            operation: Operation type (e.g., "summarize_code", "summarize_function")
            **kwargs: Additional parameters to include in the key

        Returns:
            SHA256 hash as cache key
        """
        key_data = {
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "provider": provider,
            "model": model,
            "operation": operation,
            **kwargs,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    async def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._memory_cache.clear()

        # Clear file cache
        import contextlib

        for cache_file in self.cache_dir.glob("*.json"):
            with contextlib.suppress(OSError):
                cache_file.unlink()

    async def clear_expired(self):
        """Remove expired entries from the cache."""
        current_time = time.time()

        # Clear expired from memory
        with self._lock:
            expired_keys = [
                key
                for key, entry in self._memory_cache.items()
                if current_time - entry["timestamp"] >= self.ttl
            ]
            for key in expired_keys:
                del self._memory_cache[key]

        # Clear expired from disk
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file) as f:
                    entry = json.load(f)

                if current_time - entry["timestamp"] >= self.ttl:
                    cache_file.unlink()
            except (OSError, json.JSONDecodeError, KeyError):
                # Corrupted or inaccessible file, remove it
                cache_file.unlink(missing_ok=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        file_count = len(list(self.cache_dir.glob("*.json")))
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))

        return {
            "memory_entries": len(self._memory_cache),
            "file_entries": file_count,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
            "ttl_seconds": self.ttl,
        }
