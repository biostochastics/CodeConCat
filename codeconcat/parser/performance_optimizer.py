"""
Performance optimization utilities for parsers in the CodeConCat project.

This module provides performance optimization utilities that can be used
across all parser implementations to improve parsing speed and reduce
memory usage.
"""

import logging
import time
import weakref
from collections import OrderedDict
from dataclasses import dataclass
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Union, cast

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for parser operations."""

    operation: str
    start_time: float
    end_time: float
    duration_ms: float
    memory_usage_mb: Optional[float] = None
    nodes_processed: Optional[int] = None
    cache_hits: Optional[int] = None
    cache_misses: Optional[int] = None


class PerformanceMonitor:
    """Monitor and track parser performance metrics."""

    def __init__(self, max_metrics: int = 1000):
        """
        Initialize the performance monitor.

        Args:
            max_metrics: Maximum number of metrics to store
        """
        self.max_metrics = max_metrics
        self.metrics: List[PerformanceMetrics] = []
        self._lock = Lock()

    def record_metric(
        self,
        operation: str,
        start_time: float,
        end_time: float,
        memory_usage_mb: Optional[float] = None,
        nodes_processed: Optional[int] = None,
        cache_hits: Optional[int] = None,
        cache_misses: Optional[int] = None,
    ) -> None:
        """
        Record a performance metric.

        Args:
            operation: Name of the operation
            start_time: Start timestamp
            end_time: End timestamp
            memory_usage_mb: Memory usage in MB
            nodes_processed: Number of nodes processed
            cache_hits: Number of cache hits
            cache_misses: Number of cache misses
        """
        with self._lock:
            metric = PerformanceMetrics(
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                duration_ms=(end_time - start_time) * 1000,
                memory_usage_mb=memory_usage_mb,
                nodes_processed=nodes_processed,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
            )

            self.metrics.append(metric)

            # Keep only the most recent metrics
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics :]

    def get_average_duration(self, operation: Optional[str] = None) -> float:
        """
        Get average duration for an operation.

        Args:
            operation: Operation name (None for all operations)

        Returns:
            Average duration in milliseconds
        """
        with self._lock:
            filtered_metrics = self.metrics
            if operation:
                filtered_metrics = [m for m in self.metrics if m.operation == operation]

            if not filtered_metrics:
                return 0.0

            return sum(m.duration_ms for m in filtered_metrics) / len(filtered_metrics)

    def get_slow_operations(self, threshold_ms: float = 100.0) -> List[PerformanceMetrics]:
        """
        Get operations that exceed the duration threshold.

        Args:
            threshold_ms: Duration threshold in milliseconds

        Returns:
            List of slow operations
        """
        with self._lock:
            return [m for m in self.metrics if m.duration_ms > threshold_ms]

    def get_cache_efficiency(self, operation: Optional[str] = None) -> float:
        """
        Get cache efficiency ratio.

        Args:
            operation: Operation name (None for all operations)

        Returns:
            Cache efficiency ratio (hits / (hits + misses))
        """
        with self._lock:
            filtered_metrics = self.metrics
            if operation:
                filtered_metrics = [m for m in self.metrics if m.operation == operation]

            total_hits = sum(m.cache_hits or 0 for m in filtered_metrics)
            total_misses = sum(m.cache_misses or 0 for m in filtered_metrics)

            if total_hits + total_misses == 0:
                return 0.0

            return total_hits / (total_hits + total_misses)


# Global performance monitor instance
_global_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor."""
    return _global_monitor


def performance_monitor(operation_name: str):
    """
    Decorator to monitor function performance.

    Args:
        operation_name: Name of the operation being monitored
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()

                # Record the metric
                _global_monitor.record_metric(
                    operation=operation_name, start_time=start_time, end_time=end_time
                )

                return result
            except Exception:
                end_time = time.perf_counter()

                # Record the metric even for failures
                _global_monitor.record_metric(
                    operation=f"{operation_name}_failed", start_time=start_time, end_time=end_time
                )

                raise

        return wrapper

    return decorator


class StringInterner:
    """
    String interner to reduce memory usage by reusing common strings.

    This is particularly useful for parser output where many strings
    are repeated (e.g., common identifiers, keywords, etc.).
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize the string interner.

        Args:
            max_size: Maximum number of strings to cache
        """
        self.max_size = max_size
        self._cache: Dict[str, str] = {}
        self._access_order: OrderedDict[str, None] = OrderedDict()  # O(1) LRU tracking
        self._lock = Lock()

    def intern(self, string: str) -> str:
        """
        Return a canonical representation of the string.

        Args:
            string: The string to intern

        Returns:
            The canonical string representation
        """
        if not string:
            return string

        with self._lock:
            if string in self._cache:
                # Update access order with O(1) move_to_end
                self._access_order.move_to_end(string)
                return self._cache[string]

            # Add new string
            if len(self._cache) >= self.max_size and self._access_order:
                # Remove least recently used string with O(1) operation
                oldest = next(iter(self._access_order))
                self._access_order.pop(oldest)
                if oldest in self._cache:
                    del self._cache[oldest]

            self._cache[string] = string
            self._access_order[string] = None
            return string

    def clear(self) -> None:
        """Clear the interner cache."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()


# Global string interner instance
_global_interner = StringInterner()


def get_string_interner() -> StringInterner:
    """Get the global string interner."""
    return _global_interner


def intern_string(string: str) -> str:
    """
    Intern a string using the global string interner.

    Args:
        string: The string to intern

    Returns:
        The canonical string representation
    """
    return _global_interner.intern(string)


class BatchProcessor:
    """
    Batch processor for optimizing operations on multiple items.

    This class helps reduce overhead by processing items in batches
    rather than individually.
    """

    def __init__(self, batch_size: int = 100):
        """
        Initialize the batch processor.

        Args:
            batch_size: Number of items to process in each batch
        """
        self.batch_size = batch_size

    def process_batches(
        self, items: List[Any], processor: Callable[[List[Any]], List[Any]]
    ) -> List[Any]:
        """
        Process items in batches.

        Args:
            items: List of items to process
            processor: Function to process a batch of items

        Returns:
            List of processed results
        """
        results = []

        for i in range(0, len(items), self.batch_size):
            batch = items[i : i + self.batch_size]
            batch_results = processor(batch)
            results.extend(batch_results)

        return results


class WeakValueCache:
    """
    Weak value cache that automatically removes entries when they're no longer referenced.

    This is useful for caching large objects without causing memory leaks.
    """

    def __init__(self):
        """Initialize the weak value cache."""
        self._cache: Dict[Any, Union[weakref.ref, Callable[[], Any]]] = {}
        self._lock = Lock()

    def get(self, key: Any) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: The cache key

        Returns:
            The cached value or None if not found or garbage collected
        """
        with self._lock:
            ref = self._cache.get(key)
            if ref is None:
                return None

            value = ref()
            if value is None:
                # Object was garbage collected, remove the weak reference
                del self._cache[key]
                return None

            return value

    def put(self, key: Any, value: Any) -> None:
        """
        Put a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
        """
        with self._lock:
            try:
                # Prefer weak reference when possible
                self._cache[key] = weakref.ref(value)
            except TypeError:
                # Value is not weak-referenceable (e.g., int/str)
                # Store a callable wrapper that returns a strong reference
                self._cache[key] = cast(Callable[[], Any], lambda v=value: v)

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()


def optimize_string_operations(text: str) -> str:
    """
    Optimize string operations by interning common substrings.

    Args:
        text: The text to optimize

    Returns:
        The optimized text (same content, but with shared string objects)
    """
    # For now, just return the original text
    # In a more sophisticated implementation, we could
    # identify common substrings and intern them
    return text


def create_efficient_deduplicator() -> Callable[[List[Any]], List[Any]]:
    """
    Create an efficient deduplicator function.

    Returns:
        A function that deduplicates a list while preserving order
    """

    def deduplicate(items: List[Any]) -> List[Any]:
        """Deduplicate items while preserving order."""
        if not items:
            return []

        # Try using set-based deduplication for hashable items (fast path)
        try:
            seen = set()
            result = []

            for item in items:
                if item not in seen:
                    seen.add(item)
                    result.append(item)

            return result
        except TypeError:
            # Items are not hashable, use list-based deduplication
            # For Declaration objects, deduplicate based on (name, kind, start_line)
            result = []
            seen_keys = []

            for item in items:
                # Try to create a unique key for comparison
                try:
                    # For Declaration objects
                    key: Union[tuple[Any, Any, Any], str]
                    if (
                        hasattr(item, "name")
                        and hasattr(item, "kind")
                        and hasattr(item, "start_line")
                    ):
                        key = (item.name, item.kind, item.start_line)
                    else:
                        # For other objects, use string representation as fallback
                        key = str(item)

                    if key not in seen_keys:
                        seen_keys.append(key)
                        result.append(item)
                except Exception:
                    # If we can't create a key, just add the item
                    result.append(item)

            return result

    return deduplicate
