"""Shared parser infrastructure components.

This module provides reusable components for all parsers to reduce duplication
and improve consistency across language implementations.
"""

from .comment_extractor import CommentExtractor
from .modern_patterns import MODERN_PATTERNS, check_modern_syntax, get_modern_patterns
from .result_merger import MergeStrategy, ResultMerger

__all__ = [
    "CommentExtractor",
    "MODERN_PATTERNS",
    "get_modern_patterns",
    "check_modern_syntax",
    "MergeStrategy",
    "ResultMerger",
]
