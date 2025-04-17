"""Token counting functionality using tiktoken."""

from dataclasses import dataclass
from typing import Dict

import tiktoken
from transformers import GPT2TokenizerFast


@dataclass
class TokenStats:
    """Token statistics for a file."""

    gpt3_tokens: int
    gpt4_tokens: int
    davinci_tokens: int
    claude_tokens: int


# Cache for encoders to avoid recreating them
_ENCODER_CACHE: Dict[str, tiktoken.Encoding] = {}

# Load Claude tokenizer once
_CLAUDE_TOKENIZER = GPT2TokenizerFast.from_pretrained("Xenova/claude-tokenizer")


def get_encoder(model: str = "gpt-3.5-turbo") -> tiktoken.Encoding:
    """Get or create a tiktoken encoder for the specified model."""
    if model not in _ENCODER_CACHE:
        _ENCODER_CACHE[model] = tiktoken.encoding_for_model(model)
    return _ENCODER_CACHE[model]


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count the number of tokens in a text string using the specified model's tokenizer."""
    encoder = get_encoder(model)
    return len(encoder.encode(text))


def get_token_stats(text: str) -> TokenStats:
    """Get token statistics for different models."""
    return TokenStats(
        gpt3_tokens=count_tokens(text, "gpt-3.5-turbo"),
        gpt4_tokens=count_tokens(text, "gpt-4"),
        davinci_tokens=count_tokens(text, "text-davinci-003"),
        claude_tokens=len(_CLAUDE_TOKENIZER.encode(text)),
    )
