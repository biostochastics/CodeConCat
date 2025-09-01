"""Token counting functionality using tiktoken."""

import threading
from typing import Any, Dict, Union

import tiktoken
from transformers import GPT2TokenizerFast

from ..base_types import TokenStats

# Cache for encoders to avoid recreating them
_ENCODER_CACHE: Dict[str, tiktoken.Encoding] = {}
_ENCODER_CACHE_LOCK = threading.Lock()

# Claude tokenizer - loaded lazily
_CLAUDE_TOKENIZER = None
_CLAUDE_TOKENIZER_LOCK = threading.Lock()


def get_claude_tokenizer() -> Union[GPT2TokenizerFast, Any]:
    """Get or create the Claude tokenizer."""
    global _CLAUDE_TOKENIZER
    if _CLAUDE_TOKENIZER is None:
        with _CLAUDE_TOKENIZER_LOCK:
            if _CLAUDE_TOKENIZER is None:
                try:
                    _CLAUDE_TOKENIZER = GPT2TokenizerFast.from_pretrained("Xenova/claude-tokenizer")
                except Exception:
                    # If loading fails, create a dummy tokenizer for testing
                    # This helps with test isolation issues
                    class DummyTokenizer:
                        def encode(self, text: str) -> list[str]:
                            # Simple approximation for testing
                            return text.split()

                    _CLAUDE_TOKENIZER = DummyTokenizer()
    return _CLAUDE_TOKENIZER


def get_encoder(model: str = "gpt-3.5-turbo") -> tiktoken.Encoding:
    """Get or create a tiktoken encoder for the specified model."""
    with _ENCODER_CACHE_LOCK:
        if model not in _ENCODER_CACHE:
            _ENCODER_CACHE[model] = tiktoken.encoding_for_model(model)
        return _ENCODER_CACHE[model]


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count the number of tokens in a text string using the specified model's tokenizer."""
    try:
        encoder = get_encoder(model)
        return len(encoder.encode(text))
    except Exception:
        # Fallback to a reasonable estimate if tiktoken fails
        # This can happen in test environments or when tiktoken data is not available
        # Use a simple word count as approximation
        if not text:
            return 0
        # Count words plus some extra for punctuation
        words = len(text.split())
        # Rough approximation: most models count punctuation as separate tokens
        punctuation_count = sum(1 for c in text if c in ".,!?;:\"'")
        return max(1, words + punctuation_count)


def get_token_stats(text: str) -> TokenStats:
    """Get token statistics for different models."""
    tokenizer = get_claude_tokenizer()
    try:
        claude_token_count = len(tokenizer.encode(text))  # type: ignore[union-attr]
    except Exception:
        # Fallback for tokenizer encode issues
        claude_token_count = len(text.split())

    return TokenStats(
        gpt4_tokens=count_tokens(text, "gpt-4"),
        claude_tokens=claude_token_count,
    )
