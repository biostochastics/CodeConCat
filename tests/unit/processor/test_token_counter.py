#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for the token counter module.

This tests the token counting functionality and coverage for the recently added
compression token comparison features.
"""

import pytest
from codeconcat.processor.token_counter import get_token_stats, count_tokens
from codeconcat.base_types import TokenStats


class TestTokenCounter:
    """Test class for token counter functionality."""

    def test_token_stats_creation(self):
        """Test that token stats are properly created for a given text."""
        # Test with simple text
        text = "This is a simple test text to count tokens."
        stats = get_token_stats(text)

        # Verify it returns a TokenStats object
        assert isinstance(stats, TokenStats)

        # Verify token counts are positive numbers
        assert stats.gpt3_tokens > 0
        assert stats.gpt4_tokens > 0
        assert stats.davinci_tokens > 0
        assert stats.claude_tokens > 0

        # Simple text should have similar token counts across models
        # They won't be exactly the same due to different tokenization algorithms
        assert 5 <= stats.gpt3_tokens <= 15
        assert 5 <= stats.gpt4_tokens <= 15
        assert 5 <= stats.davinci_tokens <= 15
        assert 5 <= stats.claude_tokens <= 15

    def test_empty_text(self):
        """Test token counting with empty text."""
        stats = get_token_stats("")

        # Empty text should have 0 or 1 tokens depending on the model
        assert 0 <= stats.gpt3_tokens <= 1
        assert 0 <= stats.gpt4_tokens <= 1
        assert 0 <= stats.davinci_tokens <= 1
        assert 0 <= stats.claude_tokens <= 1

    def test_code_text(self):
        """Test token counting with Python code."""
        code = """
def hello_world():
    \"\"\"This is a simple function that prints Hello World.\"\"\"
    print("Hello, World!")
    return True
        """

        stats = get_token_stats(code)

        # Code should have more tokens than the simple text
        assert stats.gpt3_tokens > 15
        assert stats.gpt4_tokens > 15
        assert stats.davinci_tokens > 15
        assert stats.claude_tokens > 15

    def test_count_tokens_specific_model(self):
        """Test counting tokens for a specific model."""
        text = "Testing specific model token counting"

        # Count tokens for each model explicitly
        gpt3_tokens = count_tokens(text, "gpt-3.5-turbo")
        gpt4_tokens = count_tokens(text, "gpt-4")
        davinci_tokens = count_tokens(text, "text-davinci-003")

        # Verify counts are reasonable
        assert 4 <= gpt3_tokens <= 8
        assert 4 <= gpt4_tokens <= 8
        assert 4 <= davinci_tokens <= 8

        # Also verify that the stats object has matching counts
        stats = get_token_stats(text)
        assert stats.gpt3_tokens == gpt3_tokens
        assert stats.gpt4_tokens == gpt4_tokens
        assert stats.davinci_tokens == davinci_tokens

    def test_special_characters(self):
        """Test token counting with special characters."""
        text = "Special characters like: 🔥 😊 ⚡ €£¥ can affect tokenization."

        stats = get_token_stats(text)

        # Verify counts are positive
        assert stats.gpt3_tokens > 0
        assert stats.gpt4_tokens > 0
        assert stats.davinci_tokens > 0
        assert stats.claude_tokens > 0

        # Emojis and special characters often require more tokens
        assert stats.gpt3_tokens > 10

    def test_markdown_text(self):
        """Test token counting with markdown formatting."""
        markdown = """
# Heading

This is a paragraph with **bold** and *italic* text.

- List item 1
- List item 2

```python
def example():
    return "code block"
```
        """

        stats = get_token_stats(markdown)

        # Markdown should have a significant number of tokens
        assert stats.gpt3_tokens > 30
        assert stats.gpt4_tokens > 30
        assert stats.davinci_tokens > 30
        assert stats.claude_tokens > 30


if __name__ == "__main__":
    pytest.main(["-v", __file__])
