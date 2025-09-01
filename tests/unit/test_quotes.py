"""Tests for quotes module."""

from unittest.mock import patch

from codeconcat.quotes import get_random_quote


class TestQuotes:
    """Test quote functionality."""

    def test_get_random_quote_returns_string(self):
        """Test that get_random_quote returns a string."""
        quote = get_random_quote()
        assert isinstance(quote, str)
        assert len(quote) > 0

    def test_get_random_quote_from_list(self):
        """Test that quote comes from the quotes list."""
        # Get several quotes to ensure randomness
        quotes = set()
        for _ in range(20):
            quotes.add(get_random_quote())

        # Should have gotten at least 2 different quotes
        assert len(quotes) >= 2

    @patch("codeconcat.quotes.random.choice")
    def test_get_random_quote_uses_random_choice(self, mock_choice):
        """Test that get_random_quote uses random.choice."""
        expected_quote = "Test quote"
        expected_cat_quote = "Test cat quote"
        # Mock needs to return the tuple structure that QUOTES contains
        mock_choice.side_effect = [
            (expected_quote, expected_cat_quote),  # First call for choosing quote
            False,  # Second call for choosing catify
        ]

        quote = get_random_quote()

        assert quote == expected_quote
        assert mock_choice.call_count == 2

    def test_all_quotes_are_strings(self):
        """Test that all quotes in the list are strings."""
        # Import PROGRAMMING_QUOTES to verify
        from codeconcat.base_types import PROGRAMMING_QUOTES

        assert len(PROGRAMMING_QUOTES) > 0
        for quote in PROGRAMMING_QUOTES:
            assert isinstance(quote, str)
            assert len(quote) > 0

    def test_quotes_have_attribution(self):
        """Test that quotes have attribution."""
        from codeconcat.base_types import PROGRAMMING_QUOTES

        for quote in PROGRAMMING_QUOTES:
            # Most quotes should have a dash indicating attribution
            assert " - " in quote or '"' in quote
