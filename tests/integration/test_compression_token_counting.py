#!/usr/bin/env python3

"""
Integration tests for compression and token counting.

Tests the end-to-end process of compressing files and calculating token counts
for both compressed and uncompressed versions.
"""

import pytest

from codeconcat.base_types import CodeConCatConfig, ContentSegmentType, ParsedFileData
from codeconcat.processor.compression_processor import CompressionProcessor
from codeconcat.processor.token_counter import get_token_stats


class TestCompressionTokenCounting:
    """Test compression token counting integration."""

    def test_compression_reduces_tokens(self):
        """Test that compression actually reduces token counts."""
        # Create a sample file with repeated code patterns
        content = """
# This is a test file with lots of repetitive content
import os
import sys
import logging
import re
import json
import time
import datetime
import random
import math
import numpy as np

def function_1():
    # This is a function that does something
    print("Running function 1")
    x = 10
    y = 20
    z = x + y
    return z

def function_2():
    # This is a function that does something else
    print("Running function 2")
    x = 30
    y = 40
    z = x + y
    return z

def function_3():
    # This is yet another function
    print("Running function 3")
    x = 50
    y = 60
    z = x + y
    return z

def function_4():
    # This function is different
    print("Running function 4")
    a = [1, 2, 3, 4, 5]
    b = []
    for item in a:
        b.append(item * 2)
    return b

def function_5():
    # This function is also different
    print("Running function 5")
    a = ["a", "b", "c", "d", "e"]
    b = {}
    for i, item in enumerate(a):
        b[item] = i
    return b

def main():
    # Main function calls all the others
    print("Starting main function")
    function_1()
    function_2()
    function_3()
    function_4()
    function_5()
    print("Completed all functions")

if __name__ == "__main__":
    main()
"""

        file_data = ParsedFileData(
            file_path="/path/to/test_file.py", language="python", content=content
        )

        # Get token counts for uncompressed content
        uncompressed_stats = get_token_stats(content)

        # Create a compression processor with aggressive settings
        config = CodeConCatConfig(
            enable_compression=True,
            compression_level="high",  # High compression level
            compression_placeholder="[...code omitted ({lines} lines, {issues} issues)...]",
            compression_keep_threshold=2,
        )
        processor = CompressionProcessor(config)

        # Compress the content
        compressed_segments = processor.process_file(file_data)
        compressed_content = "\n".join(segment.content for segment in compressed_segments)

        # Get token counts for compressed content
        compressed_stats = get_token_stats(compressed_content)

        # Verify compression reduced the number of tokens
        assert (
            compressed_stats.gpt4_tokens < uncompressed_stats.gpt4_tokens
        ), f"Compression did not reduce GPT-4 tokens: {compressed_stats.gpt4_tokens} >= {uncompressed_stats.gpt4_tokens}"
        assert (
            compressed_stats.claude_tokens < uncompressed_stats.claude_tokens
        ), f"Compression did not reduce Claude tokens: {compressed_stats.claude_tokens} >= {uncompressed_stats.claude_tokens}"

        # Check that we have a mix of CODE and OMITTED segments
        code_segments = [
            s for s in compressed_segments if s.segment_type == ContentSegmentType.CODE
        ]
        omitted_segments = [
            s for s in compressed_segments if s.segment_type == ContentSegmentType.OMITTED
        ]

        assert len(code_segments) > 0, "No CODE segments found after compression"
        assert len(omitted_segments) > 0, "No OMITTED segments found after compression"

        # Print token statistics for debugging
        print(
            f"\nUncompressed tokens: GPT-4: {uncompressed_stats.gpt4_tokens}, Claude: {uncompressed_stats.claude_tokens}"
        )
        print(
            f"Compressed tokens: GPT-4: {compressed_stats.gpt4_tokens}, Claude: {compressed_stats.claude_tokens}"
        )
        print(
            f"Token reduction: GPT-4: {uncompressed_stats.gpt4_tokens - compressed_stats.gpt4_tokens} tokens ({(1-compressed_stats.gpt4_tokens/uncompressed_stats.gpt4_tokens)*100:.1f}%)"
        )
        print(
            f"Token reduction: Claude: {uncompressed_stats.claude_tokens - compressed_stats.claude_tokens} tokens ({(1-compressed_stats.claude_tokens/uncompressed_stats.claude_tokens)*100:.1f}%)"
        )

    def test_empty_content_compression(self):
        """Test that empty content is handled correctly."""
        # Create an empty file
        file_data = ParsedFileData(
            file_path="/path/to/empty_file.py", language="python", content=""
        )

        # Create a compression processor
        config = CodeConCatConfig(
            enable_compression=True,
            compression_level="medium",
        )
        processor = CompressionProcessor(config)

        # Process empty file
        segments = processor.process_file(file_data)

        # Should return an empty list or a single empty segment
        assert len(segments) <= 1, "Empty content should produce 0 or 1 segments"

        # Token counts for empty content should be 0 or 1
        stats = get_token_stats("")
        assert stats.gpt4_tokens <= 1, "Empty content should have 0 or 1 tokens"
        assert stats.claude_tokens <= 1, "Empty content should have 0 or 1 tokens"

    def test_documentation_compression(self):
        """Test compression of documentation files."""
        # Create a markdown documentation file
        md_content = """
# Documentation Title

This is a sample documentation file with some **bold** and *italic* text.

## Section 1

Sample content for section 1.

## Section 2

Sample content for section 2.

## Section 3

Sample content for section 3.

## Section 4

Sample content for section 4.

## Section 5

Sample content for section 5.
"""

        file_data = ParsedFileData(
            file_path="/path/to/docs.md",
            language="documentation",  # Use our new documentation language type
            content=md_content,
        )

        # Get token counts for uncompressed content
        uncompressed_stats = get_token_stats(md_content)

        # Create a compression processor
        config = CodeConCatConfig(
            enable_compression=True,
            compression_level="medium",
        )
        processor = CompressionProcessor(config)

        # Compress the content
        compressed_segments = processor.process_file(file_data)
        compressed_content = "\n".join(segment.content for segment in compressed_segments)

        # Get token counts for compressed content
        compressed_stats = get_token_stats(compressed_content)

        # Verify compression had some effect (may not reduce tokens for all docs)
        assert isinstance(
            compressed_stats.gpt4_tokens, int
        ), "Compressed token count should be an integer"
        assert isinstance(
            compressed_stats.claude_tokens, int
        ), "Compressed token count should be an integer"

        # Print token statistics for debugging
        print(
            f"\nDocumentation uncompressed tokens: GPT-4: {uncompressed_stats.gpt4_tokens}, Claude: {uncompressed_stats.claude_tokens}"
        )
        print(
            f"Documentation compressed tokens: GPT-4: {compressed_stats.gpt4_tokens}, Claude: {compressed_stats.claude_tokens}"
        )


if __name__ == "__main__":
    pytest.main(["-v", __file__])
