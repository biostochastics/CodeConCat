"""Token counting utilities for accurate cost estimation."""

import logging
from typing import Any, Dict

import tiktoken

logger = logging.getLogger(__name__)

# Cache for tokenizers to avoid re-initialization
_tokenizer_cache: Dict[str, Any] = {}


class TokenCounter:
    """Accurate token counting for different AI models."""

    @staticmethod
    def get_tokenizer(model: str):
        """Get the appropriate tokenizer for a model.

        Args:
            model: Model name or identifier

        Returns:
            Tokenizer instance or None
        """
        if model in _tokenizer_cache:
            return _tokenizer_cache[model]

        try:
            # OpenAI models using tiktoken
            if "gpt-4o" in model or "o1" in model:
                # GPT-4o and o1 models use o200k_base
                enc = tiktoken.get_encoding("o200k_base")
                _tokenizer_cache[model] = enc
                return enc
            elif "gpt-4" in model:
                # GPT-4 models use cl100k_base
                enc = tiktoken.get_encoding("cl100k_base")
                _tokenizer_cache[model] = enc
                return enc
            elif "gpt-3.5" in model or "turbo" in model:
                # GPT-3.5 models use cl100k_base
                enc = tiktoken.get_encoding("cl100k_base")
                _tokenizer_cache[model] = enc
                return enc
            elif "text-davinci" in model or "davinci" in model:
                # Older models use p50k_base
                enc = tiktoken.get_encoding("p50k_base")
                _tokenizer_cache[model] = enc
                return enc

            # Try to get encoding by model name directly
            try:
                enc = tiktoken.encoding_for_model(model)
                _tokenizer_cache[model] = enc
                return enc
            except KeyError:
                pass

        except Exception as e:
            logger.debug(f"Could not get tiktoken encoder for {model}: {e}")

        return None

    @staticmethod
    def count_tokens(text: str, model: str) -> int:
        """Count tokens for a given text and model.

        Args:
            text: Text to count tokens for
            model: Model identifier

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        # Try to get specific tokenizer
        tokenizer = TokenCounter.get_tokenizer(model)

        if tokenizer:
            try:
                return len(tokenizer.encode(text))
            except Exception as e:
                logger.debug(f"Error counting tokens with tiktoken: {e}")

        # Fallback estimations based on model type
        if "claude" in model.lower() or "anthropic" in model.lower():
            # Claude models: roughly 1 token per 3.5 characters
            return int(len(text) / 3.5)
        elif "gemini" in model.lower() or "google" in model.lower():
            # Gemini models: roughly 1 token per 4 characters
            return int(len(text) / 4)
        elif "llama" in model.lower() or "mistral" in model.lower():
            # Open models: roughly 1 token per 3.8 characters
            return int(len(text) / 3.8)
        elif "deepseek" in model.lower() or "glm" in model.lower():
            # Chinese models: handle multibyte better
            # Count Unicode characters differently
            char_count = len(text)
            multibyte_count = sum(1 for c in text if ord(c) > 127)
            # Multibyte chars often tokenize to ~1.5 tokens
            return int((char_count - multibyte_count) / 4 + multibyte_count * 1.5)
        else:
            # Default fallback: 1 token per 4 characters
            return int(len(text) / 4)

    @staticmethod
    def count_messages_tokens(messages: list, model: str) -> int:
        """Count tokens for a list of messages (chat format).

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier

        Returns:
            Total number of tokens
        """
        total = 0

        # Message overhead varies by model
        if "gpt-3.5" in model or "gpt-4" in model:
            # OpenAI chat models have specific token overhead
            tokens_per_message = 3  # <|start|>role<|end|>
            tokens_per_name = 1
            total += 3  # Assistant reply prefix
        else:
            tokens_per_message = 2
            tokens_per_name = 0

        for message in messages:
            total += tokens_per_message

            # Count role tokens
            if "role" in message:
                total += TokenCounter.count_tokens(message["role"], model)

            # Count content tokens
            if "content" in message:
                total += TokenCounter.count_tokens(message["content"], model)

            # Count name tokens if present
            if "name" in message:
                total += tokens_per_name
                total += TokenCounter.count_tokens(message["name"], model)

        return total

    @staticmethod
    def estimate_cost(
        text: str,
        model: str,
        cost_per_1k_input: float,
        cost_per_1k_output: float,
        max_output_tokens: int = 500,
    ) -> Dict[str, float]:
        """Estimate cost for processing text.

        Args:
            text: Input text
            model: Model identifier
            cost_per_1k_input: Cost per 1000 input tokens
            cost_per_1k_output: Cost per 1000 output tokens
            max_output_tokens: Expected output tokens

        Returns:
            Dict with token counts and cost estimates
        """
        input_tokens = TokenCounter.count_tokens(text, model)

        # Estimate output tokens (usually much less than max)
        estimated_output = min(max_output_tokens, int(input_tokens * 0.3))

        input_cost = (input_tokens / 1000) * cost_per_1k_input
        output_cost = (estimated_output / 1000) * cost_per_1k_output

        return {
            "input_tokens": input_tokens,
            "estimated_output_tokens": estimated_output,
            "total_tokens": input_tokens + estimated_output,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
        }

    @staticmethod
    def truncate_to_token_limit(text: str, model: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            model: Model identifier
            max_tokens: Maximum number of tokens

        Returns:
            Truncated text
        """
        if not text:
            return text

        current_tokens = TokenCounter.count_tokens(text, model)

        if current_tokens <= max_tokens:
            return text

        # Binary search for the right truncation point
        tokenizer = TokenCounter.get_tokenizer(model)

        if tokenizer:
            try:
                tokens = tokenizer.encode(text)
                if len(tokens) > max_tokens:
                    truncated_tokens = tokens[:max_tokens]
                    decoded = tokenizer.decode(truncated_tokens)
                    return str(decoded) if decoded is not None else ""
            except Exception as e:
                logger.debug(f"Error truncating with tiktoken: {e}")

        # Fallback: estimate character count
        ratio = max_tokens / current_tokens
        target_chars = int(len(text) * ratio * 0.95)  # 95% to be safe

        # Try to truncate at a reasonable boundary
        truncated = text[:target_chars]

        # Find last complete sentence or paragraph
        for separator in ["\n\n", "\n", ". ", ", "]:
            last_sep = truncated.rfind(separator)
            if last_sep > target_chars * 0.8:  # Don't truncate too much
                truncated = truncated[: last_sep + len(separator)]
                break

        return truncated + "... (truncated)"


class TokenTracker:
    """Track token usage across multiple requests."""

    def __init__(self):
        """Initialize token tracker."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.requests = 0
        self.by_model: Dict[str, Dict[str, float]] = {}

    def track(self, model: str, input_tokens: int, output_tokens: int, cost: float):
        """Track token usage for a request.

        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Total cost in USD
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost
        self.requests += 1

        if model not in self.by_model:
            self.by_model[model] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
                "requests": 0,
            }

        self.by_model[model]["input_tokens"] += input_tokens
        self.by_model[model]["output_tokens"] += output_tokens
        self.by_model[model]["cost"] += cost
        self.by_model[model]["requests"] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get usage summary.

        Returns:
            Dictionary with usage statistics
        """
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": round(self.total_cost, 4),
            "total_requests": self.requests,
            "average_input_tokens": round(self.total_input_tokens / max(1, self.requests), 1),
            "average_output_tokens": round(self.total_output_tokens / max(1, self.requests), 1),
            "average_cost": round(self.total_cost / max(1, self.requests), 4),
            "by_model": self.by_model,
        }

    def reset(self):
        """Reset all tracking data."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.requests = 0
        self.by_model.clear()
