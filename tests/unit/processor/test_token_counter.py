#!/usr/bin/env python3

"""
Unit tests for the token counter module.

This tests the token counting functionality and coverage for the recently added
compression token comparison features.
"""

from unittest.mock import MagicMock, call, patch

import pytest

from codeconcat.base_types import TokenStats
from codeconcat.processor.token_counter import (
    _ENCODER_CACHE,
    count_tokens,
    get_encoder,
    get_token_stats,
)


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
        assert stats.gpt4_tokens > 0
        assert stats.claude_tokens > 0

        # Simple text should have similar token counts across models
        # They won't be exactly the same due to different tokenization algorithms
        assert 5 <= stats.gpt4_tokens <= 15
        assert 5 <= stats.claude_tokens <= 15

    def test_empty_text(self):
        """Test token counting with empty text."""
        stats = get_token_stats("")

        # Empty text should have 0 or 1 tokens depending on the model
        assert 0 <= stats.gpt4_tokens <= 1
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
        assert stats.gpt4_tokens > 15
        assert stats.claude_tokens > 15

    def test_count_tokens_specific_model(self):
        """Test counting tokens for a specific model."""
        text = "Testing specific model token counting"

        # Count tokens for each model explicitly
        gpt4_tokens = count_tokens(text, "gpt-4")

        # Verify counts are reasonable
        assert 4 <= gpt4_tokens <= 8

        # Also verify that the stats object has matching counts
        stats = get_token_stats(text)
        assert stats.gpt4_tokens == gpt4_tokens

    def test_special_characters(self):
        """Test token counting with special characters."""
        text = "Special characters like: 🔥 😊 ⚡ €£¥ can affect tokenization."

        stats = get_token_stats(text)

        # Verify counts are positive
        assert stats.gpt4_tokens > 0
        assert stats.claude_tokens > 0

        # Emojis and special characters often require more tokens
        assert stats.gpt4_tokens > 10

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
        assert stats.gpt4_tokens > 30
        assert stats.claude_tokens > 30


class TestGetEncoder:
    """Test suite for get_encoder function."""

    @patch("codeconcat.processor.token_counter.tiktoken.encoding_for_model")
    def test_get_encoder_creates_new(self, mock_encoding_for_model):
        """Test creating a new encoder for a model."""
        # Clear cache first
        _ENCODER_CACHE.clear()

        # Mock encoder
        mock_encoder = MagicMock()
        mock_encoding_for_model.return_value = mock_encoder

        # Get encoder
        encoder = get_encoder("gpt-3.5-turbo")

        assert encoder == mock_encoder
        assert "gpt-3.5-turbo" in _ENCODER_CACHE
        assert _ENCODER_CACHE["gpt-3.5-turbo"] == mock_encoder
        mock_encoding_for_model.assert_called_once_with("gpt-3.5-turbo")

    @patch("codeconcat.processor.token_counter.tiktoken.encoding_for_model")
    def test_get_encoder_uses_cache(self, mock_encoding_for_model):
        """Test using cached encoder for a model."""
        # Clear cache and add a cached encoder
        _ENCODER_CACHE.clear()
        cached_encoder = MagicMock()
        _ENCODER_CACHE["gpt-3.5-turbo"] = cached_encoder

        # Get encoder (should use cache)
        encoder = get_encoder("gpt-3.5-turbo")

        assert encoder == cached_encoder
        mock_encoding_for_model.assert_not_called()


class TestMockedCountTokens:
    """Test suite for count_tokens function with mocks."""

    @patch("codeconcat.processor.token_counter.get_encoder")
    def test_count_tokens_mocked(self, mock_get_encoder):
        """Test basic token counting with mocks."""
        # Mock encoder
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_get_encoder.return_value = mock_encoder

        # Count tokens
        count = count_tokens("Hello world", "gpt-3.5-turbo")

        assert count == 5
        mock_get_encoder.assert_called_once_with("gpt-3.5-turbo")
        mock_encoder.encode.assert_called_once_with("Hello world")


class TestMockedGetTokenStats:
    """Test suite for get_token_stats function with mocks."""

    @patch("codeconcat.processor.token_counter._CLAUDE_TOKENIZER")
    @patch("codeconcat.processor.token_counter.count_tokens")
    def test_get_token_stats_mocked(self, mock_count_tokens, mock_claude_tokenizer):
        """Test getting token statistics with mocks."""
        # Mock token counts
        mock_count_tokens.side_effect = [12]  # GPT-4
        mock_claude_tokenizer.encode.return_value = [1] * 15  # 15 tokens for Claude

        # Get token stats
        text = "This is a test text"
        stats = get_token_stats(text)

        # Verify stats
        assert isinstance(stats, TokenStats)
        assert stats.gpt4_tokens == 12
        assert stats.claude_tokens == 15

        # Verify calls
        expected_calls = [
            call(text, "gpt-4"),
        ]
        mock_count_tokens.assert_has_calls(expected_calls)
        mock_claude_tokenizer.encode.assert_called_once_with(text)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
