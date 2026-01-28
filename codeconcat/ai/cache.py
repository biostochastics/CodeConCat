"""Caching system for AI summaries."""

import asyncio
import contextlib
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, cast


def normalize_content_for_hash(content: str) -> str:
    """Normalize content for cache key hashing to improve cache hit rate.

    PERFORMANCE: This normalization ensures that whitespace-only or comment-only
    changes don't invalidate the cache. The normalized content is only used for
    hashing, not for the actual AI summarization.

    Normalization steps:
    1. Remove single-line comments (// and #)
    2. Remove multi-line comments (/* ... */)
    3. Collapse multiple whitespace to single space
    4. Strip leading/trailing whitespace from lines
    5. Remove empty lines

    Args:
        content: The original code content

    Returns:
        Normalized content string suitable for hashing
    """
    # Remove multi-line comments (/* ... */ and ''' ... ''' and \"\"\" ... \"\"\")
    content = re.sub(r"/\*[\s\S]*?\*/", "", content)
    content = re.sub(r"'''[\s\S]*?'''", "", content)
    content = re.sub(r'"""[\s\S]*?"""', "", content)

    # Remove single-line comments (// and #)
    # Be careful not to remove # in strings or URLs
    lines = content.split("\n")
    normalized_lines = []
    for line in lines:
        # Simple heuristic: remove // and # comments at end of line
        # This won't catch all edge cases but covers common patterns
        line = re.sub(r"//.*$", "", line)
        line = re.sub(r"#.*$", "", line)
        # Strip whitespace and skip empty lines
        line = line.strip()
        if line:
            # Collapse internal whitespace
            line = re.sub(r"\s+", " ", line)
            normalized_lines.append(line)

    return "\n".join(normalized_lines)


class SummaryCache:
    """Cache for AI-generated summaries to avoid redundant API calls."""

    def __init__(self, cache_dir: Path | None = None, ttl: int = 604800):
        """Initialize the cache.

        Args:
            cache_dir: Directory to store cache files (uses temp if None)
            ttl: Time-to-live in seconds for cache entries (default: 7 days)
                 PERFORMANCE: Increased from 1 hour to 7 days for better cache persistence
        """
        if cache_dir is None:
            import tempfile

            self.cache_dir = Path(tempfile.gettempdir()) / "codeconcat_ai_cache"
        else:
            self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self._lock = asyncio.Lock()
        self._memory_cache: dict[str, dict[str, Any]] = {}

    def _get_cache_file(self, key: str) -> Path:
        """Get the cache file path for a given key."""
        return self.cache_dir / f"{key}.json"

    def _read_cache_file(self, cache_file: Path) -> dict[str, Any] | None:
        """Read cache file synchronously (for use with asyncio.to_thread)."""
        try:
            with open(cache_file) as f:
                data = json.load(f)
                return cast(dict[str, Any], data)
        except (OSError, json.JSONDecodeError, KeyError):
            return None

    def _delete_cache_file(self, cache_file: Path) -> None:
        """Delete cache file synchronously (for use with asyncio.to_thread)."""
        with contextlib.suppress(OSError):
            cache_file.unlink(missing_ok=True)

    async def get(self, key: str) -> str | None:
        """Retrieve a cached summary if it exists and is not expired.

        Args:
            key: Cache key

        Returns:
            Cached summary or None if not found/expired
        """
        # Check memory cache first (async lock)
        async with self._lock:
            entry = self._memory_cache.get(key)
            if entry and time.time() - entry["timestamp"] < self.ttl:
                return str(entry["summary"])
            elif entry:
                # Expired, remove from memory cache
                del self._memory_cache[key]

        # Check file cache (non-blocking file I/O)
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            entry = await asyncio.to_thread(self._read_cache_file, cache_file)

            if entry is None:
                # Corrupted cache file, remove it
                await asyncio.to_thread(self._delete_cache_file, cache_file)
                return None

            if time.time() - entry["timestamp"] < self.ttl:
                # Load into memory cache
                async with self._lock:
                    self._memory_cache[key] = entry
                return str(entry["summary"])
            else:
                # Expired, remove file
                await asyncio.to_thread(self._delete_cache_file, cache_file)

        return None

    def _write_cache_file(self, cache_file: Path, entry: dict[str, Any]) -> None:
        """Write cache file synchronously (for use with asyncio.to_thread)."""
        try:
            with open(cache_file, "w") as f:
                json.dump(entry, f, indent=2)
        except OSError:
            # Failed to write cache file, continue without caching to disk
            pass

    async def set(self, key: str, summary: str, metadata: dict[str, Any] | None = None):
        """Store a summary in the cache.

        Args:
            key: Cache key
            summary: Summary to cache
            metadata: Optional metadata to store with the summary
        """
        entry = {"summary": summary, "timestamp": time.time(), "metadata": metadata or {}}

        # Store in memory cache (async lock)
        async with self._lock:
            self._memory_cache[key] = entry

        # Store in file cache (non-blocking file I/O)
        cache_file = self._get_cache_file(key)
        await asyncio.to_thread(self._write_cache_file, cache_file, entry)

    def generate_key(
        self, content: str, provider: str, model: str, operation: str, **kwargs
    ) -> str:
        """Generate a cache key based on content and parameters.

        PERFORMANCE: Content is normalized before hashing to improve cache hit rate.
        Whitespace-only and comment-only changes won't invalidate the cache.

        Args:
            content: The content being summarized
            provider: AI provider name
            model: Model name
            operation: Operation type (e.g., "summarize_code", "summarize_function")
            **kwargs: Additional parameters to include in the key

        Returns:
            SHA256 hash as cache key
        """
        # Normalize content for better cache hit rate
        # This strips comments and normalizes whitespace so formatting changes
        # don't invalidate the cache
        normalized_content = normalize_content_for_hash(content)
        key_data = {
            "content_hash": hashlib.sha256(normalized_content.encode()).hexdigest(),
            "provider": provider,
            "model": model,
            "operation": operation,
            **kwargs,
        }
        # Use default=str to handle non-JSON-serializable values (Path, datetime, etc.)
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _clear_all_cache_files(self) -> None:
        """Clear all cache files synchronously (for use with asyncio.to_thread)."""
        import contextlib

        for cache_file in self.cache_dir.glob("*.json"):
            with contextlib.suppress(OSError):
                cache_file.unlink()

    async def clear(self):
        """Clear all cached entries."""
        async with self._lock:
            self._memory_cache.clear()

        # Clear file cache (non-blocking)
        await asyncio.to_thread(self._clear_all_cache_files)

    def _clear_expired_files(self) -> None:
        """Clear expired cache files synchronously (for use with asyncio.to_thread)."""
        current_time = time.time()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file) as f:
                    entry = json.load(f)

                if current_time - entry["timestamp"] >= self.ttl:
                    cache_file.unlink()
            except (OSError, json.JSONDecodeError, KeyError):
                # Corrupted or inaccessible file, remove it
                cache_file.unlink(missing_ok=True)

    async def clear_expired(self):
        """Remove expired entries from the cache."""
        current_time = time.time()

        # Clear expired from memory (async lock)
        async with self._lock:
            expired_keys = [
                key
                for key, entry in self._memory_cache.items()
                if current_time - entry["timestamp"] >= self.ttl
            ]
            for key in expired_keys:
                del self._memory_cache[key]

        # Clear expired from disk (non-blocking)
        await asyncio.to_thread(self._clear_expired_files)

    def get_stats(self) -> dict[str, Any]:
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
