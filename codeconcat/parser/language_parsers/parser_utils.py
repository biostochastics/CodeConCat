"""Common utilities for language parsers."""

import functools
import logging
from typing import Any, Callable, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def _get_parser_name(args) -> str:
    """Extract parser name from function arguments."""
    parser_instance = args[0] if args else None
    return parser_instance.__class__.__name__ if parser_instance else "Unknown"


def safe_parser_method(default_return: Any = None) -> Callable[[F], F]:
    """
    Decorator for parser methods to handle common exceptions gracefully during parsing operations.

    Use this decorator on parser methods that might fail due to invalid node structure
    or missing data to ensure graceful fallback behavior.

    Args:
        default_return: Value to return if an exception occurs

    Returns:
        Decorated function that handles IndexError and KeyError, returning default_return,
        while logging and re-raising other exceptions
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except (IndexError, KeyError) as e:
                parser_name = _get_parser_name(args)
                logger.debug(f"{parser_name}.{func.__name__} encountered {type(e).__name__}: {e}")
                return default_return
            except Exception as e:
                # Log unexpected exceptions but re-raise them
                parser_name = _get_parser_name(args)
                logger.error(
                    f"{parser_name}.{func.__name__} encountered unexpected error: {e}. Args: {args}, Kwargs: {kwargs}",
                    exc_info=True,
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def extract_safe_substring(text: str, start: int, end: int) -> str:
    """
    Safely extract a substring with bounds checking.

    Args:
        text: Source text
        start: Start index
        end: End index

    Returns:
        Extracted substring or empty string if indices are invalid
    """
    if not text or start < 0 or end < 0 or start > end:
        return ""

    # Ensure we don't go beyond text bounds
    start = min(start, len(text))
    end = min(end, len(text))

    return text[start:end]


def get_node_text_safe(node: Optional[Any], source_code: Union[str, bytes]) -> Optional[str]:
    """
    Safely extract text from a tree-sitter node.

    Args:
        node: Tree-sitter node (tree_sitter.Node when available)
        source_code: Source code text

    Returns:
        Node text or None if extraction fails
    """
    try:
        if not node or not hasattr(node, "start_byte") or not hasattr(node, "end_byte"):
            return None

        if isinstance(source_code, bytes):
            source_code = source_code.decode("utf-8", errors="replace")

        return extract_safe_substring(source_code, node.start_byte, node.end_byte)
    except Exception as e:
        logger.error(
            f"Failed to extract node text - Node type: {type(node)}, Source type: {type(source_code)}, Error: {e}",
            exc_info=True,
        )
        return None
