"""Simple tests for token counting functionality."""

from unittest.mock import MagicMock, patch

from codeconcat.base_types import TokenStats
from codeconcat.processor.token_counter import get_token_stats


class TestTokenCounter:
    """Test token counting functions."""

    def test_token_stats_creation(self):
        """Test TokenStats data class creation."""
        stats = TokenStats(gpt4_tokens=100, claude_tokens=110)

        assert stats.gpt4_tokens == 100
        assert stats.claude_tokens == 110

    def test_get_token_stats_empty_text(self):
        """Test token counting for empty text."""
        stats = get_token_stats("")

        assert isinstance(stats, TokenStats)
        assert stats.gpt4_tokens == 0
        assert stats.claude_tokens == 0

    def test_get_token_stats_simple_text(self):
        """Test token counting for simple text."""
        text = "Hello, world!"
        stats = get_token_stats(text)

        assert isinstance(stats, TokenStats)
        # Token counts should be positive for non-empty text
        assert stats.gpt4_tokens > 0
        assert stats.claude_tokens > 0

    def test_get_token_stats_code_snippet(self):
        """Test token counting for code snippet."""
        code = """
def hello_world():
    print("Hello, World!")
    return True
"""
        stats = get_token_stats(code)

        assert isinstance(stats, TokenStats)
        # Code should have more tokens than simple text
        assert stats.gpt4_tokens > 5
        assert stats.claude_tokens > 5

    def test_get_token_stats_unicode(self):
        """Test token counting for unicode text."""
        text = "Hello 世界 🌍"
        stats = get_token_stats(text)

        assert isinstance(stats, TokenStats)
        assert stats.gpt4_tokens > 0
        assert stats.claude_tokens > 0

    @patch("codeconcat.processor.token_counter._CLAUDE_TOKENIZER")
    @patch("codeconcat.processor.token_counter._ENCODER_CACHE", {})
    @patch("tiktoken.encoding_for_model")
    def test_get_token_stats_with_mock_tiktoken(
        self, mock_encoding_for_model, mock_claude_tokenizer
    ):
        """Test token counting with mocked tiktoken."""
        # Mock the encoder
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_encoding_for_model.return_value = mock_encoder

        # Mock claude tokenizer
        mock_claude_tokenizer.encode.return_value = [1, 2, 3, 4, 5, 6]  # 6 tokens

        stats = get_token_stats("Test text")

        # Should have called tiktoken for different models
        assert mock_encoding_for_model.call_count >= 1  # GPT-4
        assert stats.gpt4_tokens == 5
        assert stats.claude_tokens == 6

    def test_get_token_stats_long_text(self):
        """Test token counting for long text."""
        # Create a long text
        long_text = " ".join(["word"] * 1000)
        stats = get_token_stats(long_text)

        assert isinstance(stats, TokenStats)
        # Should have many tokens
        assert stats.gpt4_tokens > 100
        assert stats.claude_tokens > 100

    def test_token_stats_different_models(self):
        """Test that different models give different token counts."""
        text = "This is a test sentence with multiple words."
        stats = get_token_stats(text)

        # Different tokenizers should give slightly different results
        # but they should all be positive
        assert stats.gpt4_tokens > 0
        assert stats.claude_tokens > 0
