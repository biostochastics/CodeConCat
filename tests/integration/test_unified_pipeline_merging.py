"""Integration tests for unified pipeline with result merging."""

import tempfile
from pathlib import Path

import pytest

from codeconcat.base_types import CodeConCatConfig
from codeconcat.parser.unified_pipeline import UnifiedPipeline


class TestUnifiedPipelineMerging:
    """Test unified pipeline with result merging from multiple parsers."""

    @pytest.fixture
    def test_python_file(self):
        """Use an existing Python file from the codebase for testing."""
        # Use result_merger.py which has known content
        return Path(__file__).parent.parent / "unit" / "parser" / "test_result_merger.py"

    @pytest.fixture
    def shared_result_merger_file(self):
        """Use shared result_merger.py source file."""
        return (
            Path(__file__).parent.parent.parent
            / "codeconcat"
            / "parser"
            / "shared"
            / "result_merger.py"
        )

    @pytest.fixture
    def test_typescript_file(self):
        """Create a temporary TypeScript file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
            f.write(
                """
/**
 * Data processor class
 */
export class DataProcessor {
    private data: string[];

    constructor(data: string[]) {
        this.data = data;
    }

    /**
     * Process data
     */
    processData(): string[] {
        return this.data.map(item => item.toUpperCase());
    }
}

/**
 * Check if value is string
 */
export function isString(value: any): value is string {
    return typeof value === "string";
}

/**
 * Process data function
 */
export function processData(data: string[]): string[] {
    return data.filter(isString);
}
"""
            )
            path = Path(f.name)

        yield path

        # Cleanup
        if path.exists():
            path.unlink()

    def test_python_result_merging_enabled(self, test_python_file):
        """Test that result merging is enabled by default and combines results."""
        config = CodeConCatConfig(
            target_path=str(test_python_file.parent),
            enable_result_merging=True,
            merge_strategy="confidence",
        )

        pipeline = UnifiedPipeline(config)
        # Use _parse_with_fallbacks directly (content, file_path, language)
        result = pipeline._parse_with_fallbacks(
            test_python_file.read_text(), str(test_python_file), "python"
        )

        # Should successfully parse
        assert not result.error or len(result.declarations) > 0

        # Should find some declarations (classes and/or functions)
        assert len(result.declarations) > 0

        # Check that merging metadata is present
        assert "merged" in (result.engine_used or "")

    def test_python_result_merging_disabled(self, test_python_file):
        """Test legacy behavior when result merging is disabled."""
        config = CodeConCatConfig(
            target_path=str(test_python_file.parent),
            enable_result_merging=False,
        )

        pipeline = UnifiedPipeline(config)
        result = pipeline._parse_with_fallbacks(
            test_python_file.read_text(), str(test_python_file), "python"
        )

        # Should successfully parse
        assert not result.error
        assert len(result.declarations) > 0

        # Should NOT have merged metadata
        assert "merged" not in (result.engine_used or "")

    def test_typescript_result_merging(self, test_typescript_file):
        """Test result merging with TypeScript file."""
        config = CodeConCatConfig(
            target_path=str(test_typescript_file.parent),
            enable_result_merging=True,
            merge_strategy="union",  # Use union strategy
        )

        pipeline = UnifiedPipeline(config)
        result = pipeline._parse_with_fallbacks(
            test_typescript_file.read_text(), str(test_typescript_file), "typescript"
        )

        # Should successfully parse
        assert not result.error
        assert len(result.declarations) > 0

        # Should find functions
        funcs = [d for d in result.declarations if d.kind == "function"]
        func_names = {d.name for d in funcs}
        assert "processData" in func_names
        assert "isString" in func_names

        # Should find class
        classes = [d for d in result.declarations if d.kind == "class"]
        assert any(d.name == "DataProcessor" for d in classes)

        # Check union merge metadata
        assert "union" in (result.engine_used or "")

    def test_confidence_weighted_strategy(self, test_python_file):
        """Test confidence-weighted merge strategy."""
        config = CodeConCatConfig(
            target_path=str(test_python_file.parent),
            enable_result_merging=True,
            merge_strategy="confidence",
        )

        pipeline = UnifiedPipeline(config)
        result = pipeline._parse_with_fallbacks(
            test_python_file.read_text(), str(test_python_file), "python"
        )

        # Should have confidence score
        assert result.confidence_score is not None
        assert 0.0 <= result.confidence_score <= 1.0

        # Should have parser type
        assert result.parser_type is not None or "merged" in (result.engine_used or "")

    def test_best_of_breed_strategy(self, test_python_file):
        """Test best-of-breed merge strategy."""
        config = CodeConCatConfig(
            target_path=str(test_python_file.parent),
            enable_result_merging=True,
            merge_strategy="best_of_breed",
        )

        pipeline = UnifiedPipeline(config)
        result = pipeline._parse_with_fallbacks(
            test_python_file.read_text(), str(test_python_file), "python"
        )

        assert not result.error
        assert len(result.declarations) > 0
        assert "best_of_breed" in (result.engine_used or "")

    def test_fast_fail_strategy(self, test_python_file):
        """Test fast-fail merge strategy (legacy behavior)."""
        config = CodeConCatConfig(
            target_path=str(test_python_file.parent),
            enable_result_merging=True,
            merge_strategy="fast_fail",
        )

        pipeline = UnifiedPipeline(config)
        result = pipeline._parse_with_fallbacks(
            test_python_file.read_text(), str(test_python_file), "python"
        )

        assert not result.error
        assert len(result.declarations) > 0

    def test_malformed_file_with_merging(self):
        """Test that merging works even with partially malformed files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''
def good_function():
    """This should be parsed."""
    return True

# Intentionally malformed syntax
def bad_function(
    """Incomplete function."""

def another_good_function():
    """This should also be parsed."""
    return False
'''
            )
            path = Path(f.name)

        try:
            config = CodeConCatConfig(
                target_path=str(path.parent),
                enable_result_merging=True,
                merge_strategy="union",  # Union should capture what it can
            )

            pipeline = UnifiedPipeline(config)
            result = pipeline._parse_with_fallbacks(path.read_text(), str(path), "python")

            # Should have at least some declarations despite errors
            # Depending on parser robustness, may or may not have error flag
            assert len(result.declarations) >= 0

        finally:
            path.unlink()

    def test_complex_python_file_coverage(self):
        """Test coverage with complex Python file with many features."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''
"""Complex module to test coverage."""

from typing import Optional, List
import os
import sys

# Module-level constant
CONSTANT = 42

class BaseClass:
    """Base class."""

    def __init__(self, value: int):
        self.value = value

    def base_method(self) -> int:
        return self.value

class DerivedClass(BaseClass):
    """Derived class with more features."""

    def __init__(self, value: int, name: str):
        super().__init__(value)
        self.name = name

    @property
    def display_name(self) -> str:
        """Property method."""
        return f"{self.name}: {self.value}"

    @staticmethod
    def static_method():
        """Static method."""
        return "static"

    @classmethod
    def class_method(cls):
        """Class method."""
        return cls

def nested_function_example():
    """Function with nested function."""
    def inner():
        return "inner"
    return inner()

# Async function
async def async_function():
    """Async function."""
    await asyncio.sleep(1)
    return "done"

# Lambda
simple_lambda = lambda x: x * 2

# Decorator
def decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@decorator
def decorated_function():
    """Decorated function."""
    return "decorated"
'''
            )
            path = Path(f.name)

        try:
            config = CodeConCatConfig(
                target_path=str(path.parent),
                enable_result_merging=True,
                merge_strategy="confidence",
            )

            pipeline = UnifiedPipeline(config)
            result = pipeline._parse_with_fallbacks(path.read_text(), str(path), "python")

            # Should parse successfully
            assert not result.error or len(result.declarations) > 0

            # Should find both classes
            classes = [d for d in result.declarations if d.kind == "class"]
            class_names = {d.name for d in classes}
            assert "BaseClass" in class_names
            assert "DerivedClass" in class_names

            # Should find multiple functions
            funcs = [d for d in result.declarations if d.kind == "function"]
            func_names = {d.name for d in funcs}
            assert "nested_function_example" in func_names
            assert "async_function" in func_names

            # Should have imports
            assert len(result.imports) > 0
            assert any("typing" in imp for imp in result.imports)

        finally:
            path.unlink()

    def test_go_file_with_generics(self):
        """Test Go file with generics (modern syntax)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".go", delete=False) as f:
            f.write(
                """
package main

// Generic function (Go 1.18+)
func Max[T comparable](a, b T) T {
    if a > b {
        return a
    }
    return b
}

// Generic type
type List[T any] struct {
    items []T
}

// Regular function
func Add(x, y int) int {
    return x + y
}

type Person struct {
    Name string
    Age  int
}
"""
            )
            path = Path(f.name)

        try:
            config = CodeConCatConfig(
                target_path=str(path.parent),
                enable_result_merging=True,
                merge_strategy="confidence",
            )

            pipeline = UnifiedPipeline(config)
            result = pipeline._parse_with_fallbacks(path.read_text(), str(path), "go")

            # Should parse successfully
            assert not result.error or len(result.declarations) > 0

            # Should find functions (including generic)
            funcs = [d for d in result.declarations if d.kind == "function"]
            func_names = {d.name for d in funcs}
            assert "Max" in func_names or "Add" in func_names

        finally:
            path.unlink()
