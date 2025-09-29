"""Unit tests for ResultMerger with multiple merge strategies."""

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.shared import MergeStrategy, ResultMerger


class TestResultMerger:
    """Test ResultMerger functionality."""

    def test_merge_single_result(self):
        """Test merging a single result returns it unchanged."""
        result = ParseResult(
            declarations=[Declaration(name="func1", kind="function", start_line=1, end_line=5)],
            imports=["import os"],
        )

        merged = ResultMerger.merge_parse_results([result])
        assert merged == result

    def test_merge_empty_results(self):
        """Test merging empty results returns empty result."""
        merged = ResultMerger.merge_parse_results([])
        assert merged.declarations == []
        assert merged.imports == []

    def test_confidence_weighted_merge(self):
        """Test confidence-weighted merge strategy."""
        # Create results with different quality levels
        ts_result = ParseResult(
            declarations=[
                Declaration(
                    name="func1",
                    kind="function",
                    start_line=1,
                    end_line=5,
                    docstring="Docstring from tree-sitter",
                    signature="def func1(x: int) -> str:",
                ),
            ],
            imports=["import os"],
            parser_quality="full",
            engine_used="tree-sitter",
        )

        enhanced_result = ParseResult(
            declarations=[
                Declaration(
                    name="func1",
                    kind="function",
                    start_line=1,
                    end_line=5,
                    docstring="Docstring from enhanced",
                ),
                Declaration(
                    name="func2",  # Only enhanced found this
                    kind="function",
                    start_line=10,
                    end_line=15,
                ),
            ],
            imports=["import sys"],
            parser_quality="partial",
            engine_used="enhanced",
        )

        merged = ResultMerger.merge_parse_results(
            [ts_result, enhanced_result], strategy=MergeStrategy.CONFIDENCE_WEIGHTED
        )

        # Should have both functions
        assert len(merged.declarations) == 2
        assert {d.name for d in merged.declarations} == {"func1", "func2"}

        # Should have both imports
        assert set(merged.imports) == {"import os", "import sys"}

        # Should use tree-sitter as base (higher confidence)
        assert merged.parser_quality == "merged"
        assert "tree-sitter" in merged.engine_used

    def test_feature_union_merge(self):
        """Test feature union merge strategy."""
        result1 = ParseResult(
            declarations=[
                Declaration(name="func1", kind="function", start_line=1, end_line=5),
            ],
            imports=["import os"],
        )

        result2 = ParseResult(
            declarations=[
                Declaration(name="func2", kind="function", start_line=10, end_line=15),
            ],
            imports=["import sys"],
        )

        result3 = ParseResult(
            declarations=[
                Declaration(name="func3", kind="function", start_line=20, end_line=25),
            ],
            imports=["import json"],
        )

        merged = ResultMerger.merge_parse_results(
            [result1, result2, result3], strategy=MergeStrategy.FEATURE_UNION
        )

        # Should have all functions
        assert len(merged.declarations) == 3
        assert {d.name for d in merged.declarations} == {"func1", "func2", "func3"}

        # Should have all imports
        assert set(merged.imports) == {"import os", "import sys", "import json"}

        assert merged.parser_quality == "union"

    def test_fast_fail_merge(self):
        """Test fast-fail merge strategy."""
        # High confidence result
        high_conf_result = ParseResult(
            declarations=[
                Declaration(name="func1", kind="function", start_line=1, end_line=5),
            ],
            imports=["import os"],
            parser_quality="full",
            confidence_score=0.9,
        )

        # Lower confidence result
        low_conf_result = ParseResult(
            declarations=[
                Declaration(name="func2", kind="function", start_line=10, end_line=15),
            ],
            imports=["import sys"],
            parser_quality="basic",
            confidence_score=0.5,
        )

        merged = ResultMerger.merge_parse_results(
            [high_conf_result, low_conf_result], strategy=MergeStrategy.FAST_FAIL
        )

        # Should return first high-confidence result
        assert len(merged.declarations) == 1
        assert merged.declarations[0].name == "func1"

    def test_best_of_breed_merge(self):
        """Test best-of-breed merge strategy."""
        result1 = ParseResult(
            declarations=[
                Declaration(
                    name="func1",
                    kind="function",
                    start_line=1,
                    end_line=5,
                    docstring="Full docstring",
                    signature="def func1():",
                ),
                Declaration(name="Class1", kind="class", start_line=10, end_line=20),  # Incomplete
            ],
            imports=["import os"],
        )

        result2 = ParseResult(
            declarations=[
                Declaration(
                    name="func1", kind="function", start_line=1, end_line=5
                ),  # Less complete
                Declaration(
                    name="Class1",
                    kind="class",
                    start_line=10,
                    end_line=20,
                    docstring="Class docstring",
                    modifiers={"public"},
                ),  # More complete
            ],
            imports=["import sys"],
        )

        merged = ResultMerger.merge_parse_results(
            [result1, result2], strategy=MergeStrategy.BEST_OF_BREED
        )

        # Should have both declarations
        assert len(merged.declarations) == 2

        # Find func1 - should be the complete one from result1
        func1 = next(d for d in merged.declarations if d.name == "func1")
        assert func1.docstring == "Full docstring"
        assert func1.signature == "def func1():"

        # Find Class1 - should be the complete one from result2
        class1 = next(d for d in merged.declarations if d.name == "Class1")
        assert class1.docstring == "Class docstring"
        assert "public" in class1.modifiers

    def test_duplicate_detection(self):
        """Test that duplicates are correctly detected and removed."""
        result1 = ParseResult(
            declarations=[
                Declaration(name="func1", kind="function", start_line=1, end_line=5),
            ],
            imports=[],
        )

        result2 = ParseResult(
            declarations=[
                Declaration(name="func1", kind="function", start_line=1, end_line=5),  # Duplicate
            ],
            imports=[],
        )

        merged = ResultMerger.merge_parse_results([result1, result2])

        # Should only have one func1
        assert len(merged.declarations) == 1
        assert merged.declarations[0].name == "func1"

    def test_error_handling(self):
        """Test handling of results with errors."""
        good_result = ParseResult(
            declarations=[
                Declaration(name="func1", kind="function", start_line=1, end_line=5),
            ],
            imports=["import os"],
        )

        error_result = ParseResult(
            declarations=[],
            imports=[],
            error="Parse error",
        )

        # Should use good result and ignore error result
        merged = ResultMerger.merge_parse_results([good_result, error_result])

        assert len(merged.declarations) == 1
        assert merged.declarations[0].name == "func1"
        assert not merged.error

    def test_all_errors_handling(self):
        """Test handling when all results have errors."""
        error_result1 = ParseResult(
            declarations=[
                Declaration(name="func1", kind="function", start_line=1, end_line=5),
            ],
            imports=[],
            error="Parse error 1",
        )

        error_result2 = ParseResult(
            declarations=[],
            imports=[],
            error="Parse error 2",
        )

        # Should return result with most declarations
        merged = ResultMerger.merge_parse_results([error_result1, error_result2])

        assert len(merged.declarations) == 1
        assert merged.declarations[0].name == "func1"

    def test_calculate_confidence(self):
        """Test confidence score calculation."""
        # High quality with declarations
        high_quality = ParseResult(
            declarations=[
                Declaration(
                    name="func1",
                    kind="function",
                    start_line=1,
                    end_line=5,
                    docstring="Docstring",
                    signature="def func1():",
                ),
            ],
            imports=["import os"],
            parser_quality="full",
        )

        confidence = ResultMerger._calculate_confidence(high_quality)
        assert 0.6 < confidence <= 1.0  # Should be reasonably high

        # Low quality with no declarations
        low_quality = ParseResult(
            declarations=[],
            imports=[],
            parser_quality="basic",
        )

        confidence = ResultMerger._calculate_confidence(low_quality)
        assert 0.0 < confidence < 0.3  # Should be low

        # With error
        error_result = ParseResult(
            declarations=[],
            imports=[],
            error="Parse error",
        )

        confidence = ResultMerger._calculate_confidence(error_result)
        assert confidence == 0.3  # Fixed low confidence for errors

    def test_missed_features_intersection(self):
        """Test that missed features are correctly intersected."""
        result1 = ParseResult(
            declarations=[],
            imports=[],
            missed_features=["generics", "async"],
        )

        result2 = ParseResult(
            declarations=[],
            imports=[],
            missed_features=["generics", "decorators"],
        )

        merged = ResultMerger.merge_parse_results([result1, result2])

        # Should only include features missed by all parsers
        assert merged.missed_features == ["generics"]

    def test_security_issues_union(self):
        """Test that security issues are unioned from all parsers."""
        result1 = ParseResult(
            declarations=[],
            imports=[],
            security_issues=["SQL injection risk"],
        )

        result2 = ParseResult(
            declarations=[],
            imports=[],
            security_issues=["XSS vulnerability"],
        )

        merged = ResultMerger.merge_parse_results([result1, result2])

        # Should include all security issues
        assert set(merged.security_issues) == {"SQL injection risk", "XSS vulnerability"}

    def test_language_specific_merge(self):
        """Test language-specific optimization in merging."""
        result1 = ParseResult(
            declarations=[
                Declaration(name="func1", kind="function", start_line=1, end_line=5),
            ],
            imports=["import os"],
        )

        result2 = ParseResult(
            declarations=[
                Declaration(name="func2", kind="function", start_line=10, end_line=15),
            ],
            imports=["import sys"],
        )

        # Test with language parameter
        merged = ResultMerger.merge_parse_results(
            [result1, result2],
            strategy=MergeStrategy.CONFIDENCE_WEIGHTED,
            language="python",
        )

        assert len(merged.declarations) == 2
        assert set(merged.imports) == {"import os", "import sys"}
