#!/usr/bin/env python3
"""
CodeConCat CLI - Modern command-line interface using Typer.

This module provides the main CLI application with sub-commands for various operations.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from codeconcat.version import __version__

from .commands import api, diagnose, init, keys, reconstruct, run
from .config import GlobalState
from .utils import setup_logging

# Initialize Rich console for beautiful terminal output with colors and formatting
console = Console()

# Create the main Typer app with Rich markup support
# Rich markup allows using [color] tags in help text for styled output
app = typer.Typer(
    name="codeconcat",
    help="CodeConCat - LLM-friendly code aggregator & documentation extractor",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    add_completion=True,  # Explicitly enable completion support
)

# Global state management - singleton pattern for sharing state across commands
state = GlobalState()


def version_callback(value: bool):
    """Callback to display version information."""
    if value:
        version_text = Text(f"CodeConCat v{__version__}", style="bold cyan")
        console.print(Panel(version_text, expand=False, border_style="cyan"))
        raise typer.Exit(0)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(  # noqa: ARG001
        False,
        "--version",
        "-V",
        help="Show version information and exit",
        is_eager=True,
        callback=version_callback,
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Increase verbosity level (-v for INFO, -vv for DEBUG)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Quiet mode: suppress progress information",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
):
    """
    Main callback function for the CodeConCat CLI application.

    This function handles global options and initialization before any sub-command
    is executed. It manages version display, verbosity settings, logging configuration,
    and displays a welcome panel when no command is provided.

    Args:
        ctx: Typer context object containing command information
        version: Flag to display version information and exit
        verbose: Verbosity level counter (-v for INFO, -vv for DEBUG)
        quiet: Flag to suppress progress information
        config: Optional path to configuration file

    Raises:
        typer.Exit: When version is displayed or no command is provided

    Note:
        This callback is invoked for every command execution, setting up the
        global state and logging configuration before delegating to sub-commands.
    """

    # Store global settings in state singleton for access across commands
    state.verbose = verbose
    state.quiet = quiet
    state.config_path = config

    # Setup logging based on verbosity level
    # Priority: quiet mode > debug (vv) > info (v) > error (default for cleaner output)
    log_level = (
        "ERROR" if quiet else ("DEBUG" if verbose > 1 else "INFO" if verbose > 0 else "ERROR")
    )
    setup_logging(log_level, quiet)

    # If no command is provided, show welcome panel with quick start guide
    if ctx.invoked_subcommand is None:
        console.print(
            Panel(
                "[bold cyan]Welcome to CodeConCat![/bold cyan]\n\n"
                "Transform your codebase into LLM-friendly documentation.\n\n"
                "[yellow]Quick Start:[/yellow]\n"
                "  • Run on current directory: [green]codeconcat run[/green]\n"
                "  • Initialize config: [green]codeconcat init[/green]\n"
                "  • Start API server: [green]codeconcat api[/green]\n"
                "  • Get help: [green]codeconcat --help[/green]",
                title="CodeConCat",
                border_style="cyan",
            )
        )
        raise typer.Exit(0)


# Register run command directly (not as sub-app) for cleaner command structure
# This avoids nested sub-commands like 'codeconcat run run'
app.command(name="run")(run.run_command)  # Uses docstring from run_command

# Register init and reconstruct commands directly to avoid confusion
# Init has validate as a subcommand, but we'll handle it differently
app.command(name="init")(init.init_command)  # Uses docstring from init_command
app.command(name="validate")(init.validate_config)  # Uses docstring from validate_config
app.command(name="reconstruct")(
    reconstruct.reconstruct_command
)  # Uses docstring from reconstruct_command
app.add_typer(api.app, name="api", help="Start the CodeConCat API server")
app.add_typer(diagnose.app, name="diagnose", help="Diagnostic and verification tools")
app.add_typer(keys.app, name="keys", help="Manage API keys for AI providers")


# Add a default command that maps to 'run' for backward compatibility
# This allows 'codeconcat path' or 'codeconcat url' to work like 'codeconcat run path/url'
@app.command(hidden=True)
def default(
    ctx: typer.Context,
    target: Optional[str] = typer.Argument(None),
):
    """
    Hidden default command for backward compatibility.

    This command allows users to run CodeConCat without specifying 'run'
    explicitly, maintaining compatibility with the legacy CLI interface.
    Also supports direct URL/shorthand usage.

    Args:
        ctx: Typer context from parent command
        target: Optional target path, URL, or GitHub shorthand

    Note:
        This is a hidden command that won't appear in help output.
        It forwards all arguments to the run command.

    Example:
        codeconcat /path/to/project           # Legacy style (local)
        codeconcat https://github.com/o/r     # GitHub URL
        codeconcat owner/repo                  # GitHub shorthand
        codeconcat run /path/to/project       # New style (equivalent)
    """
    # Forward to run command by manipulating context and argv
    run_ctx = ctx.parent
    if run_ctx:
        run_ctx.invoked_subcommand = "run"
    if target:
        sys.argv.insert(1, str(target))
    run.run_command(target)


if __name__ == "__main__":
    app()
