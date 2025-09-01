"""
Diagnose command - Diagnostic and verification tools.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table
from typing_extensions import Annotated

from codeconcat.diagnostics import diagnose_parser, verify_tree_sitter_dependencies

from ..utils import console, print_error, print_info, print_success, print_warning

app = typer.Typer()


@app.command(name="verify")
def verify_dependencies():
    """
    Verify that all Tree-sitter grammars are properly installed.

    This command checks each supported language to ensure its Tree-sitter
    grammar is available and functioning correctly.

    \b
    Examples:
      codeconcat diagnose verify         # Check all language parsers
    """
    console.print(
        Panel(
            "[bold cyan]Verifying Tree-sitter Dependencies[/bold cyan]\n\n"
            "Checking all supported language grammars...",
            title="Dependency Verification",
            border_style="cyan",
        )
    )

    success, successful_langs, failed_langs = verify_tree_sitter_dependencies()

    # Create a table for results
    table = Table(title="Language Support Status", show_header=True, header_style="bold cyan")
    table.add_column("Language", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Parser")

    # Add successful languages
    for lang in sorted(successful_langs):
        table.add_row(lang, "[green]✓[/green]", "Tree-sitter")

    # Add failed languages
    for error in failed_langs:
        # Extract language from error message
        if ":" in error:
            lang = error.split(":")[0].strip()
            table.add_row(lang, "[red]✗[/red]", "Not available")

    console.print(table)

    # Print summary
    if success:
        print_success(f"All {len(successful_langs)} Tree-sitter grammars are properly installed.")
    else:
        print_warning("Some grammars are missing or failed to load.")
        console.print(f"  [green]✓[/green] Successful: {len(successful_langs)} languages")
        console.print(f"  [red]✗[/red] Failed: {len(failed_langs)} languages")

        if failed_langs:
            console.print("\n[yellow]To fix missing grammars:[/yellow]")
            console.print("  1. Run: [cyan]pip install tree-sitter-languages[/cyan]")
            console.print(
                "  2. Or install individual grammars: [cyan]pip install tree-sitter-<language>[/cyan]"
            )

    raise typer.Exit(0 if success else 1)


@app.command(name="parser")
def diagnose_parser_command(
    language: Annotated[
        str,
        typer.Argument(
            help="Language to diagnose (e.g., python, javascript, java)",
        ),
    ],
    test_file: Annotated[
        Optional[Path],
        typer.Option(
            "--test-file",
            "-f",
            help="Test file to parse for diagnosis",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            rich_help_panel="Diagnostic Options",
        ),
    ] = None,
):
    """
    Run diagnostic checks on the parser for a specific language.

    This command tests whether parsers are available for a language
    and optionally parses a test file to verify functionality.

    \b
    Examples:
        codeconcat diagnose parser python                     # Check Python parser
        codeconcat diagnose parser javascript -f test.js      # Test with file
    """
    language = language.lower()

    console.print(
        Panel(
            f"[bold cyan]Parser Diagnostics[/bold cyan]\n\n"
            f"Language: [green]{language}[/green]\n"
            f"Test file: [green]{test_file or 'None'}[/green]",
            title="🔬 Parser Diagnosis",
            border_style="cyan",
        )
    )

    # Find test file if not provided
    if not test_file:
        test_corpus_path = (
            Path(__file__).parent.parent.parent.parent / "tests" / "parser_test_corpus" / language
        )

        if test_corpus_path.exists():
            for filename in ["basic.py", "basic.js", "basic.java", f"basic.{language}"]:
                candidate = test_corpus_path / filename
                if candidate.exists():
                    test_file = candidate
                    print_info(f"Using test file: {test_file}")
                    break

    # Run diagnostics
    success, results = diagnose_parser(language, str(test_file) if test_file else None)

    # Display parser availability
    console.print("\n[bold]Parser Availability:[/bold]")
    for parser_type, parser_name in results.get("parsers_found", {}).items():
        if isinstance(parser_name, str):
            status = "[green]✓[/green]" if parser_name else "[red]✗[/red]"
            console.print(
                f"  {parser_type.capitalize():12} {status} {parser_name or 'Not available'}"
            )

    # Display test results if available
    if test_file and "parsers_tested" in results:
        console.print("\n[bold]Parser Test Results:[/bold]")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Parser", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Declarations")
        table.add_column("Imports")
        table.add_column("Notes")

        for parser_type, result in results.get("parsers_tested", {}).items():
            status = "[green]✓[/green]" if result.get("success") else "[red]✗[/red]"
            declarations = str(result.get("declarations_count", "-"))
            imports = str(result.get("imports_count", "-"))
            error = result.get("error", "")

            table.add_row(
                parser_type.capitalize(),
                status,
                declarations,
                imports,
                error[:30] + "..." if error and len(error) > 30 else error or "",
            )

        console.print(table)

    # Show errors if any
    if results.get("errors"):
        print_warning("Diagnostic errors encountered:")
        for error in results["errors"]:
            console.print(f"  [red]•[/red] {error}")

    # Final status
    if success:
        print_success(f"Parser diagnostics completed successfully for {language}")
    else:
        print_error(f"Parser diagnostics failed for {language}")
        raise typer.Exit(1)


@app.command(name="system")
def system_info():
    """
    Display system information and CodeConCat configuration.
    """
    import platform
    import sys

    from codeconcat.version import __version__

    console.print(
        Panel(
            f"[bold cyan]System Information[/bold cyan]\n\n"
            f"[yellow]CodeConCat:[/yellow]\n"
            f"  Version: [green]{__version__}[/green]\n"
            f"  Python: [green]{sys.version.split()[0]}[/green]\n"
            f"  Platform: [green]{platform.platform()}[/green]\n\n"
            f"[yellow]Dependencies:[/yellow]\n"
            f"  Typer: [green]Installed[/green]\n"
            f"  Rich: [green]Installed[/green]\n"
            f"  Tree-sitter: [green]Installed[/green]\n"
            f"  Pydantic: [green]Installed[/green]\n\n"
            f"[yellow]Paths:[/yellow]\n"
            f"  Config: [cyan]~/.codeconcat/config.yml[/cyan]\n"
            f"  Cache: [cyan]~/.codeconcat/cache[/cyan]\n"
            f"  Logs: [cyan]~/.codeconcat/logs[/cyan]",
            title="ℹ️ System Information",
            border_style="cyan",
        )
    )


@app.command(name="languages")
def list_languages():
    """
    List all supported programming languages.
    """
    # Import language mappings from the parser module
    from codeconcat.constants import SOURCE_CODE_EXTENSIONS
    from codeconcat.parser.language_parsers import LANGUAGE_EXTENSION_MAP

    # Convert extension map to a format suitable for display
    # Remove the dot prefix from extensions for cleaner display
    LANGUAGE_MAPPING = {}
    for ext in SOURCE_CODE_EXTENSIONS:
        ext_clean = ext.lstrip(".")
        # Check if this extension has a language mapping
        if ext in LANGUAGE_EXTENSION_MAP:
            LANGUAGE_MAPPING[ext_clean] = LANGUAGE_EXTENSION_MAP[ext]
        else:
            # Determine language from extension for non-parser languages
            if ext in [".md"]:
                LANGUAGE_MAPPING[ext_clean] = "markdown"
            elif ext in [".yml", ".yaml"]:
                LANGUAGE_MAPPING[ext_clean] = "yaml"
            elif ext in [".json"]:
                LANGUAGE_MAPPING[ext_clean] = "json"
            elif ext in [".xml"]:
                LANGUAGE_MAPPING[ext_clean] = "xml"
            elif ext in [".html", ".htm"]:
                LANGUAGE_MAPPING[ext_clean] = "html"
            elif ext in [".css", ".scss", ".sass", ".less"]:
                LANGUAGE_MAPPING[ext_clean] = "css"
            elif ext in [".toml"]:
                LANGUAGE_MAPPING[ext_clean] = "toml"
            elif ext in [".ini", ".cfg", ".conf"]:
                LANGUAGE_MAPPING[ext_clean] = "ini"
            elif ext in [".sh", ".bash"]:
                LANGUAGE_MAPPING[ext_clean] = "shell"
            elif ext in [".rb"]:
                LANGUAGE_MAPPING[ext_clean] = "ruby"
            elif ext in [".swift"]:
                LANGUAGE_MAPPING[ext_clean] = "swift"
            elif ext in [".kt"]:
                LANGUAGE_MAPPING[ext_clean] = "kotlin"
            elif ext in [".scala"]:
                LANGUAGE_MAPPING[ext_clean] = "scala"
            elif ext in [".lua"]:
                LANGUAGE_MAPPING[ext_clean] = "lua"
            elif ext in [".pl"]:
                LANGUAGE_MAPPING[ext_clean] = "perl"
            elif ext in [".vue"]:
                LANGUAGE_MAPPING[ext_clean] = "vue"
            elif ext in [".svelte"]:
                LANGUAGE_MAPPING[ext_clean] = "svelte"
            elif ext in [".rst"]:
                LANGUAGE_MAPPING[ext_clean] = "restructuredtext"
            elif ext in [".txt"]:
                LANGUAGE_MAPPING[ext_clean] = "text"

    console.print(
        Panel(
            "[bold cyan]Supported Languages[/bold cyan]\n\n"
            "The following programming languages are supported:",
            title="🗣️ Language Support",
            border_style="cyan",
        )
    )

    # Group languages by parser type
    tree_sitter_langs = []
    regex_langs = []

    # Languages that have tree-sitter support (from LANGUAGE_EXTENSION_MAP)
    tree_sitter_supported = set(LANGUAGE_EXTENSION_MAP.values())

    for ext, lang in sorted(LANGUAGE_MAPPING.items()):
        if lang in tree_sitter_supported:
            tree_sitter_langs.append((ext, lang))
        else:
            regex_langs.append((ext, lang))

    # Display Tree-sitter supported languages
    if tree_sitter_langs:
        console.print("\n[bold]Tree-sitter Parser Support:[/bold]")
        for ext, lang in tree_sitter_langs:
            console.print(f"  [cyan].{ext}[/cyan] → [green]{lang}[/green]")

    # Display regex-only languages
    if regex_langs:
        console.print("\n[bold]Regex Parser Support:[/bold]")
        for ext, lang in regex_langs:
            console.print(f"  [cyan].{ext}[/cyan] → [yellow]{lang}[/yellow]")

    console.print(f"\n[dim]Total: {len(LANGUAGE_MAPPING)} file extensions supported[/dim]")
