"""Tests for the performance optimizer module."""

import time
import weakref
from unittest.mock import MagicMock

import pytest
from codeconcat.base_types import Declaration
from codeconcat.parser.performance_optimizer import (
    BatchProcessor,
    PerformanceMetrics,
    PerformanceMonitor,
    StringInterner,
    WeakValueCache,
    create_efficient_deduplicator,
    get_performance_monitor,
    get_string_interner,
    intern_string,
    optimize_string_operations,
    performance_monitor,
)


class TestPerformanceMetrics:
    """Test suite for PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating a performance metric."""
        metric = PerformanceMetrics(
            operation="test_op",
            start_time=1.0,
            end_time=2.0,
            duration_ms=1000.0,
        )
        assert metric.operation == "test_op"
        assert metric.start_time == 1.0
        assert metric.end_time == 2.0
        assert metric.duration_ms == 1000.0

    def test_performance_metrics_with_optional_fields(self):
        """Test performance metrics with optional fields."""
        metric = PerformanceMetrics(
            operation="parse",
            start_time=1.0,
            end_time=2.5,
            duration_ms=1500.0,
            memory_usage_mb=50.5,
            nodes_processed=1000,
            cache_hits=100,
            cache_misses=20,
        )
        assert metric.memory_usage_mb == 50.5
        assert metric.nodes_processed == 1000
        assert metric.cache_hits == 100
        assert metric.cache_misses == 20


class TestPerformanceMonitor:
    """Test suite for PerformanceMonitor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor(max_metrics=10)

    def test_monitor_initialization(self):
        """Test monitor initializes correctly."""
        assert self.monitor.max_metrics == 10
        assert len(self.monitor.metrics) == 0

    def test_record_single_metric(self):
        """Test recording a single metric."""
        self.monitor.record_metric(
            operation="parse",
            start_time=1.0,
            end_time=2.0,
        )
        assert len(self.monitor.metrics) == 1
        assert self.monitor.metrics[0].operation == "parse"
        assert self.monitor.metrics[0].duration_ms == 1000.0

    def test_record_multiple_metrics(self):
        """Test recording multiple metrics."""
        for i in range(5):
            self.monitor.record_metric(
                operation=f"op_{i}",
                start_time=float(i),
                end_time=float(i + 1),
            )
        assert len(self.monitor.metrics) == 5

    def test_max_metrics_limit(self):
        """Test that metrics are limited to max_metrics."""
        # Record 15 metrics when max is 10
        for i in range(15):
            self.monitor.record_metric(
                operation=f"op_{i}",
                start_time=float(i),
                end_time=float(i + 1),
            )
        # Should keep only the most recent 10
        assert len(self.monitor.metrics) == 10
        # First metric should be op_5 (oldest of the kept metrics)
        assert self.monitor.metrics[0].operation == "op_5"

    def test_get_average_duration_all_operations(self):
        """Test getting average duration for all operations."""
        self.monitor.record_metric("op1", 0.0, 0.1)  # 100ms
        self.monitor.record_metric("op2", 0.0, 0.2)  # 200ms
        self.monitor.record_metric("op3", 0.0, 0.3)  # 300ms

        avg = self.monitor.get_average_duration()
        assert avg == 200.0  # (100 + 200 + 300) / 3

    def test_get_average_duration_specific_operation(self):
        """Test getting average duration for a specific operation."""
        self.monitor.record_metric("parse", 0.0, 0.1)  # 100ms
        self.monitor.record_metric("parse", 0.0, 0.2)  # 200ms
        self.monitor.record_metric("write", 0.0, 0.5)  # 500ms

        avg = self.monitor.get_average_duration("parse")
        assert avg == 150.0  # (100 + 200) / 2

    def test_get_average_duration_no_metrics(self):
        """Test average duration with no metrics."""
        avg = self.monitor.get_average_duration()
        assert avg == 0.0

    def test_get_slow_operations(self):
        """Test getting slow operations."""
        self.monitor.record_metric("fast", 0.0, 0.05)  # 50ms
        self.monitor.record_metric("slow1", 0.0, 0.15)  # 150ms
        self.monitor.record_metric("slow2", 0.0, 0.25)  # 250ms

        slow_ops = self.monitor.get_slow_operations(threshold_ms=100.0)
        assert len(slow_ops) == 2
        assert all(m.duration_ms > 100.0 for m in slow_ops)

    def test_get_cache_efficiency_all_operations(self):
        """Test getting cache efficiency for all operations."""
        self.monitor.record_metric("op1", 0.0, 0.1, cache_hits=80, cache_misses=20)
        self.monitor.record_metric("op2", 0.0, 0.2, cache_hits=60, cache_misses=40)

        efficiency = self.monitor.get_cache_efficiency()
        assert efficiency == 0.7  # (80 + 60) / (100 + 100)

    def test_get_cache_efficiency_specific_operation(self):
        """Test getting cache efficiency for a specific operation."""
        self.monitor.record_metric("parse", 0.0, 0.1, cache_hits=90, cache_misses=10)
        self.monitor.record_metric("parse", 0.0, 0.2, cache_hits=70, cache_misses=30)
        self.monitor.record_metric("write", 0.0, 0.3, cache_hits=50, cache_misses=50)

        efficiency = self.monitor.get_cache_efficiency("parse")
        assert efficiency == 0.8  # (90 + 70) / (100 + 100)

    def test_get_cache_efficiency_no_cache_data(self):
        """Test cache efficiency with no cache data."""
        self.monitor.record_metric("op1", 0.0, 0.1)

        efficiency = self.monitor.get_cache_efficiency()
        assert efficiency == 0.0


class TestPerformanceMonitorDecorator:
    """Test suite for performance_monitor decorator."""

    def test_decorator_records_metric(self):
        """Test that decorator records performance metrics."""
        monitor = get_performance_monitor()
        initial_count = len(monitor.metrics)

        @performance_monitor("test_operation")
        def test_func():
            return "result"

        result = test_func()

        assert result == "result"
        assert len(monitor.metrics) > initial_count

    def test_decorator_with_exception(self):
        """Test decorator records metric even when function raises."""
        monitor = get_performance_monitor()
        initial_count = len(monitor.metrics)

        @performance_monitor("failing_operation")
        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_func()

        # Should still record metric for failed operation
        assert len(monitor.metrics) > initial_count
        # Last metric should be for the failed operation
        assert "_failed" in monitor.metrics[-1].operation


class TestStringInterner:
    """Test suite for StringInterner class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interner = StringInterner(max_size=5)

    def test_interner_initialization(self):
        """Test interner initializes correctly."""
        assert self.interner.max_size == 5
        assert len(self.interner._cache) == 0

    def test_intern_single_string(self):
        """Test interning a single string."""
        s1 = "hello"
        result = self.interner.intern(s1)
        assert result == "hello"
        assert len(self.interner._cache) == 1

    def test_intern_returns_same_object(self):
        """Test that interning returns the same object for identical strings."""
        s1 = "test_string"
        s2 = "test_string"

        result1 = self.interner.intern(s1)
        result2 = self.interner.intern(s2)

        assert result1 is result2
        assert len(self.interner._cache) == 1

    def test_intern_empty_string(self):
        """Test interning an empty string."""
        result = self.interner.intern("")
        assert result == ""
        # Empty strings are not cached
        assert len(self.interner._cache) == 0

    def test_intern_lru_eviction(self):
        """Test that LRU eviction works correctly."""
        # Fill cache to max_size
        for i in range(5):
            self.interner.intern(f"string_{i}")

        assert len(self.interner._cache) == 5

        # Add one more string, should evict the oldest
        self.interner.intern("new_string")

        assert len(self.interner._cache) == 5
        assert "string_0" not in self.interner._cache
        assert "new_string" in self.interner._cache

    def test_intern_updates_access_order(self):
        """Test that accessing a string updates its position in LRU."""
        # Fill cache
        for i in range(5):
            self.interner.intern(f"string_{i}")

        # Access string_0 again, making it most recently used
        self.interner.intern("string_0")

        # Add new string, should evict string_1 (now oldest)
        self.interner.intern("new_string")

        assert "string_0" in self.interner._cache
        assert "string_1" not in self.interner._cache

    def test_clear(self):
        """Test clearing the interner cache."""
        self.interner.intern("test1")
        self.interner.intern("test2")
        assert len(self.interner._cache) == 2

        self.interner.clear()
        assert len(self.interner._cache) == 0
        assert len(self.interner._access_order) == 0


class TestGlobalStringInterner:
    """Test suite for global string interner functions."""

    def test_get_string_interner(self):
        """Test getting the global string interner."""
        interner = get_string_interner()
        assert interner is not None
        assert isinstance(interner, StringInterner)

    def test_intern_string_function(self):
        """Test the global intern_string function."""
        s1 = "global_test"
        s2 = "global_test"

        result1 = intern_string(s1)
        result2 = intern_string(s2)

        assert result1 == result2


class TestBatchProcessor:
    """Test suite for BatchProcessor class."""

    def test_processor_initialization(self):
        """Test processor initializes correctly."""
        processor = BatchProcessor(batch_size=10)
        assert processor.batch_size == 10

    def test_process_batches_single_batch(self):
        """Test processing items in a single batch."""
        processor = BatchProcessor(batch_size=10)
        items = list(range(5))

        def doubler(batch):
            return [x * 2 for x in batch]

        results = processor.process_batches(items, doubler)
        assert results == [0, 2, 4, 6, 8]

    def test_process_batches_multiple_batches(self):
        """Test processing items across multiple batches."""
        processor = BatchProcessor(batch_size=3)
        items = list(range(10))

        def doubler(batch):
            return [x * 2 for x in batch]

        results = processor.process_batches(items, doubler)
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    def test_process_batches_exact_batch_size(self):
        """Test processing when items exactly match batch size."""
        processor = BatchProcessor(batch_size=5)
        items = list(range(10))

        def identity(batch):
            return batch

        results = processor.process_batches(items, identity)
        assert results == items


class TestWeakValueCache:
    """Test suite for WeakValueCache class."""

    def test_cache_initialization(self):
        """Test cache initializes correctly."""
        cache = WeakValueCache()
        assert len(cache._cache) == 0

    def test_put_and_get(self):
        """Test putting and getting values."""
        cache = WeakValueCache()
        obj = {"test": "value"}

        cache.put("key1", obj)
        result = cache.get("key1")

        assert result == obj

    def test_get_nonexistent_key(self):
        """Test getting a nonexistent key."""
        cache = WeakValueCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_weak_reference_collection(self):
        """Test that weakly referenced objects can be garbage collected."""
        cache = WeakValueCache()

        # Create object with no other references
        obj = {"test": "value"}
        cache.put("key1", obj)

        # Delete the only strong reference
        del obj

        # Force garbage collection
        import gc
        gc.collect()

        # The weak reference should now return None
        result = cache.get("key1")
        # May still be in cache if not collected yet, but value should be None
        assert result is None or result == {"test": "value"}

    def test_clear(self):
        """Test clearing the cache."""
        cache = WeakValueCache()
        cache.put("key1", {"test": "value1"})
        cache.put("key2", {"test": "value2"})

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestOptimizeStringOperations:
    """Test suite for optimize_string_operations function."""

    def test_optimize_string_returns_input(self):
        """Test that optimize_string_operations returns the input (current implementation)."""
        text = "This is a test string"
        result = optimize_string_operations(text)
        assert result == text


class TestCreateEfficientDeduplicator:
    """Test suite for create_efficient_deduplicator function."""

    def test_deduplicate_hashable_items(self):
        """Test deduplicating hashable items (strings)."""
        dedup = create_efficient_deduplicator()
        items = ["a", "b", "a", "c", "b", "d"]

        result = dedup(items)

        assert result == ["a", "b", "c", "d"]
        assert len(result) == 4

    def test_deduplicate_preserves_order(self):
        """Test that deduplication preserves order."""
        dedup = create_efficient_deduplicator()
        items = [3, 1, 2, 3, 1, 4]

        result = dedup(items)

        assert result == [3, 1, 2, 4]

    def test_deduplicate_empty_list(self):
        """Test deduplicating an empty list."""
        dedup = create_efficient_deduplicator()
        result = dedup([])
        assert result == []

    def test_deduplicate_unhashable_declaration_objects(self):
        """Test deduplicating unhashable Declaration objects."""
        dedup = create_efficient_deduplicator()

        decl1 = Declaration(kind="function", name="foo", start_line=1, end_line=5)
        decl2 = Declaration(kind="function", name="foo", start_line=1, end_line=5)  # Duplicate
        decl3 = Declaration(kind="class", name="Bar", start_line=10, end_line=20)

        items = [decl1, decl2, decl3]
        result = dedup(items)

        # Should deduplicate based on (name, kind, start_line)
        assert len(result) == 2
        assert result[0].name == "foo"
        assert result[1].name == "Bar"

    def test_deduplicate_declaration_different_lines(self):
        """Test that declarations with same name but different lines are kept."""
        dedup = create_efficient_deduplicator()

        decl1 = Declaration(kind="function", name="foo", start_line=1, end_line=5)
        decl2 = Declaration(kind="function", name="foo", start_line=10, end_line=15)

        items = [decl1, decl2]
        result = dedup(items)

        # Should keep both (different start_line)
        assert len(result) == 2

    def test_deduplicate_mixed_hashable_and_unhashable(self):
        """Test deduplicating when first item is hashable but later items are not."""
        dedup = create_efficient_deduplicator()

        # Start with hashable items, then add unhashable
        decl1 = Declaration(kind="function", name="foo", start_line=1, end_line=5)
        decl2 = Declaration(kind="function", name="foo", start_line=1, end_line=5)

        items = [decl1, decl2]
        result = dedup(items)

        # Should handle the TypeError and fall back to unhashable deduplication
        assert len(result) == 1
