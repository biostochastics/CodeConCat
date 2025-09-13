"""
Utility functions for the CLI.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

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
                def __init__(self, fmt=None, datefmt=None):
                    super().__init__(fmt=fmt, datefmt=datefmt)

                def _redact(self, text: str) -> str:
                    if not text:
                        return text
                    # Replace home directory and CWD with placeholders
                    redacted = text.replace(home, "<HOME>")
                    redacted = redacted.replace(cwd, "<CWD>")
                    return redacted

                def format(self, record: logging.LogRecord) -> str:
                    formatted = super().format(record)
                    return self._redact(formatted)

            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                fmt = (
                    handler.formatter._fmt
                    if handler.formatter
                    else "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
                )
                datefmt = handler.formatter.datefmt if handler.formatter else "%Y-%m-%d %H:%M:%S"
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
