"""
Utility functions for the CLI.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from codeconcat.quotes import get_random_quote

console = Console()


def setup_logging(level: str = "WARNING", _quiet: bool = False) -> None:
    """Configure logging for the application."""
    # Suppress HuggingFace tokenizers parallelism warning
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # Configure logging
    numeric_level = getattr(logging, level.upper(), logging.WARNING)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Apply path redaction to all handlers by default to avoid leaking usernames/paths
    # Opt-out by setting CODECONCAT_REDACT_PATHS=0
    if os.environ.get("CODECONCAT_REDACT_PATHS", "1") != "0":
        try:
            home = str(Path.home())
            cwd = str(Path.cwd())

            class PathRedactingFormatter(logging.Formatter):
                """Custom formatter that redacts sensitive path information from logs."""

                def __init__(self, fmt=None, datefmt=None):
                    """Initialize the formatter with optional format strings.

                    Args:
                        fmt: Format string for log messages
                        datefmt: Format string for dates
                    """
                    super().__init__(fmt=fmt, datefmt=datefmt)

                def _redact(self, text: str) -> str:
                    """Replace sensitive paths with placeholders.

                    Args:
                        text: Text potentially containing sensitive paths

                    Returns:
                        Text with paths replaced by <CWD> and <HOME>
                    """
                    if not text:
                        return text
                    # Replace CWD first (more specific), then HOME (more general)
                    # This ensures CWD is properly replaced even when it's a subdirectory of HOME
                    redacted = text.replace(cwd, "<CWD>")
                    redacted = redacted.replace(home, "<HOME>")
                    return redacted

                def format(self, record: logging.LogRecord) -> str:
                    """Format log record with path redaction.

                    Args:
                        record: LogRecord to format

                    Returns:
                        Formatted string with sensitive paths redacted
                    """
                    formatted = super().format(record)
                    return self._redact(formatted)

            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                # Safely get format string from formatter
                fmt = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"  # default
                datefmt = "%Y-%m-%d %H:%M:%S"  # default

                if handler.formatter:
                    # Try to get _fmt attribute safely
                    if hasattr(handler.formatter, "_fmt"):
                        fmt_value = handler.formatter._fmt  # type: ignore[attr-defined]
                        if fmt_value is not None:
                            fmt = fmt_value
                    elif hasattr(handler.formatter, "_style") and hasattr(
                        handler.formatter._style, "_fmt"
                    ):
                        # Python 3.8+ uses PercentStyle internally
                        fmt_value = handler.formatter._style._fmt  # type: ignore[attr-defined]
                        if fmt_value is not None:
                            fmt = fmt_value

                    if hasattr(handler.formatter, "datefmt"):
                        datefmt = handler.formatter.datefmt or datefmt

                handler.setFormatter(PathRedactingFormatter(fmt=fmt, datefmt=datefmt))
        except Exception:
            # If anything goes wrong, continue without redaction to avoid breaking logging
            pass

    # Suppress verbose logs from libraries if not in debug mode
    if numeric_level != logging.DEBUG:
        for logger_name in [
            "charset_normalizer",
            "urllib3",
            "filelock",
            "tree_sitter",
            "tree_sitter_languages",
            "transformers",
        ]:
            logging.getLogger(logger_name).setLevel(logging.WARNING)


def show_quote(quiet: bool = False) -> None:
    """Display a random quote with ASCII cat art unless in quiet mode."""
    if not quiet:
        quote = get_random_quote()

        # ASCII cat art
        cat_art = """      |\\      _,,,---,,_
ZZZzz /,`.-'`'    -.  ;-;;,_
     |,4-  ) )-,_. ,\\ (  `'-'
    '---''(_/--'  `-'\\_)"""

        # Check if it's a cat quote
        is_cat_quote = any(
            word in quote.lower()
            for word in ["cat", "meow", "purr", "kitten", "paw", "whisker", "claw", "nap", "hunt"]
        )

        # Create display with cat and quote
        if is_cat_quote:
            # Cat quote - show in a panel with cat art on the left
            combined = f"{cat_art}\n\n💭 {quote}"
            console.print(
                Panel(
                    Text(combined, style="cyan italic"),
                    title="Cat Wisdom",
                    border_style="cyan",
                    padding=(1, 2),
                )
            )
        else:
            # Regular quote - just show quote in a nice panel
            console.print(
                Panel(
                    Text(quote, style="dim italic"),
                    title="💡 Dev Wisdom",
                    border_style="dim",
                    padding=(0, 2),
                )
            )
        console.print()


def create_progress_spinner(_description: str) -> Progress:
    """Create a Rich progress spinner."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def print_file_stats(stats: Dict[str, Any]) -> None:
    """Print file processing statistics in a nice table."""
    table = Table(title="Processing Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    for key, value in stats.items():
        # Format the key nicely
        formatted_key = key.replace("_", " ").title()
        # Format numbers with commas
        formatted_value = f"{value:,}" if isinstance(value, int) else str(value)
        table.add_row(formatted_key, formatted_value)

    console.print(table)


def is_github_url_or_shorthand(target: str) -> Tuple[bool, str]:
    """
    Detect if a target string is a GitHub URL or shorthand notation.

    Args:
        target: Input string to check

    Returns:
        Tuple of (is_url, cleaned_url) where:
        - is_url: True if target is a GitHub URL/shorthand
        - cleaned_url: The URL/shorthand ready for processing
    """
    # GitHub shorthand patterns (owner/repo or owner/repo/ref)
    shorthand_pattern = r"^[a-zA-Z0-9][\w.-]+/[\w.-]+(?:/.*)?$"

    # GitHub URL patterns
    github_url_patterns = [
        r"^https?://(?:www\.)?github\.com/[\w.-]+/[\w.-]+",
        r"^git@github\.com:[\w.-]+/[\w.-]+",
        r"^github\.com/[\w.-]+/[\w.-]+",
    ]

    # Check if it's a GitHub shorthand
    if re.match(shorthand_pattern, target) and not os.path.exists(target):
        # Looks like owner/repo and not a local path
        return True, target

    # Check if it's a GitHub URL
    for pattern in github_url_patterns:
        if re.match(pattern, target, re.IGNORECASE):
            return True, target

    # Check for other Git hosting services (GitLab, Bitbucket, etc.)
    git_url_patterns = [
        r"^https?://(?:www\.)?gitlab\.com/",
        r"^https?://(?:www\.)?bitbucket\.org/",
        r"^git@gitlab\.com:",
        r"^git@bitbucket\.org:",
    ]

    for pattern in git_url_patterns:
        if re.match(pattern, target, re.IGNORECASE):
            return True, target

    return False, target


def validate_path(path: Path, must_exist: bool = True) -> Path:
    """Validate and resolve a path."""
    resolved = path.resolve()

    if must_exist and not resolved.exists():
        console.print(f"[red]Error: Path does not exist: {resolved}[/red]")
        raise typer.Exit(1)

    return resolved


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask for user confirmation."""
    return bool(typer.confirm(message, default=default))


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_float < 1024.0:
            return f"{size_float:.1f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.1f} PB"


def get_language_color(language: str) -> str:
    """Get a color for syntax highlighting based on language."""
    colors = {
        "python": "yellow",
        "javascript": "cyan",
        "typescript": "blue",
        "java": "red",
        "cpp": "magenta",
        "c": "magenta",
        "rust": "orange1",
        "go": "cyan",
        "ruby": "red",
        "php": "purple",
        "csharp": "green",
        "swift": "orange1",
        "kotlin": "purple",
        "r": "blue",
        "julia": "purple",
    }
    return colors.get(language.lower(), "white")


def print_error(message: str, exit_code: int = 1) -> None:
    """Print an error message and optionally exit."""
    console.print(f"[bold red]Error:[/bold red] {message}")
    if exit_code is not None:
        raise typer.Exit(exit_code)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")
