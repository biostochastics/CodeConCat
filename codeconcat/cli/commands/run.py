"""
Run command - Main processing functionality.
"""

import os
from enum import Enum
from pathlib import Path
from typing import List, Optional

import typer
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from typing_extensions import Annotated

from codeconcat.config.config_builder import ConfigBuilder
from codeconcat.errors import CodeConcatError
from codeconcat.main import _write_output_files, run_codeconcat
from codeconcat.validation.security_reporter import init_reporter
from codeconcat.validation.unsupported_reporter import init_reporter as init_unsupported_reporter

from ..config import get_state
from ..utils import console, print_error, print_success, print_warning, show_quote

# We don't need a separate Typer app here since run_command is used directly
# app = typer.Typer()


class OutputFormat(str, Enum):
    """Output format options."""

    MARKDOWN = "markdown"
    JSON = "json"
    XML = "xml"
    TEXT = "text"


class OutputPreset(str, Enum):
    """Output preset options."""

    LEAN = "lean"
    MEDIUM = "medium"
    FULL = "full"


class ParserEngine(str, Enum):
    """Parser engine options."""

    TREE_SITTER = "tree_sitter"
    REGEX = "regex"


class CompressionLevel(str, Enum):
    """Compression level options."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AGGRESSIVE = "aggressive"


def run_command(
    target: Annotated[
        Optional[Path],
        typer.Argument(
            help="Target directory or file to process",
            exists=True,
            resolve_path=True,
        ),
    ] = Path.cwd(),
    # Output options
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output file path (auto-detected from format if omitted)",
            resolve_path=True,
            rich_help_panel="Output Options",
        ),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            "-f",
            help="Output format",
            case_sensitive=False,
            rich_help_panel="Output Options",
        ),
    ] = OutputFormat.MARKDOWN,
    preset: Annotated[
        Optional[OutputPreset],
        typer.Option(
            "--preset",
            "-p",
            help="Configuration preset (overrides config file)",
            rich_help_panel="Output Options",
        ),
    ] = None,
    # Source options
    source_url: Annotated[
        Optional[str],
        typer.Option(
            "--source-url",
            help="URL or owner/repo shorthand for remote repositories",
            rich_help_panel="Source Options",
        ),
    ] = None,
    github_token: Annotated[
        Optional[str],
        typer.Option(
            "--github-token",
            help="GitHub PAT for private repositories",
            envvar="GITHUB_TOKEN",
            rich_help_panel="Source Options",
        ),
    ] = None,
    source_ref: Annotated[
        Optional[str],
        typer.Option(
            "--source-ref",
            help="Branch, tag, or commit hash for Git source",
            rich_help_panel="Source Options",
        ),
    ] = None,
    # Filtering options
    include_paths: Annotated[
        Optional[List[str]],
        typer.Option(
            "--include-path",
            "-ip",
            help="Glob patterns for files/directories to include",
            rich_help_panel="Filtering Options",
        ),
    ] = None,
    exclude_paths: Annotated[
        Optional[List[str]],
        typer.Option(
            "--exclude-path",
            "-ep",
            help="Glob patterns for files/directories to exclude",
            rich_help_panel="Filtering Options",
        ),
    ] = None,
    include_languages: Annotated[
        Optional[List[str]],
        typer.Option(
            "--include-language",
            "-il",
            help="Languages to include (e.g., python, java)",
            rich_help_panel="Filtering Options",
        ),
    ] = None,
    exclude_languages: Annotated[
        Optional[List[str]],
        typer.Option(
            "--exclude-language",
            "-el",
            help="Languages to exclude",
            rich_help_panel="Filtering Options",
        ),
    ] = None,
    use_gitignore: Annotated[
        bool,
        typer.Option(
            "--use-gitignore/--no-gitignore",
            help="Respect .gitignore files",
            rich_help_panel="Filtering Options",
        ),
    ] = True,
    use_default_excludes: Annotated[
        bool,
        typer.Option(
            "--use-default-excludes/--no-default-excludes",
            help="Use built-in default excludes",
            rich_help_panel="Filtering Options",
        ),
    ] = True,
    # Processing options
    parser_engine: Annotated[
        Optional[ParserEngine],
        typer.Option(
            "--parser-engine",
            help="Parser engine to use",
            rich_help_panel="Processing Options",
        ),
    ] = None,
    max_workers: Annotated[
        int,
        typer.Option(
            "--max-workers",
            help="Number of parallel workers for processing",
            min=1,
            max=32,
            rich_help_panel="Processing Options",
        ),
    ] = 4,
    # Feature toggles
    extract_docs: Annotated[
        bool,
        typer.Option(
            "--docs/--no-docs",
            help="Extract standalone documentation files",
            rich_help_panel="Feature Options",
        ),
    ] = False,
    merge_docs: Annotated[
        bool,
        typer.Option(
            "--merge-docs/--no-merge-docs",
            help="Merge docs into main output",
            rich_help_panel="Feature Options",
        ),
    ] = False,
    disable_annotations: Annotated[
        bool,
        typer.Option(
            "--no-annotations",
            help="Skip code annotation",
            rich_help_panel="Feature Options",
        ),
    ] = False,
    remove_docstrings: Annotated[
        bool,
        typer.Option(
            "--remove-docstrings",
            help="Strip docstrings from code",
            rich_help_panel="Feature Options",
        ),
    ] = False,
    remove_comments: Annotated[
        bool,
        typer.Option(
            "--remove-comments",
            help="Strip comments from code",
            rich_help_panel="Feature Options",
        ),
    ] = False,
    # Compression options
    enable_compression: Annotated[
        bool,
        typer.Option(
            "--compress/--no-compress",
            help="Enable intelligent code compression",
            rich_help_panel="Compression Options",
        ),
    ] = False,
    compression_level: Annotated[
        CompressionLevel,
        typer.Option(
            "--compression-level",
            help="Compression intensity level",
            rich_help_panel="Compression Options",
        ),
    ] = CompressionLevel.MEDIUM,
    # AI Summarization options
    enable_ai_summary: Annotated[
        bool,
        typer.Option(
            "--ai-summary/--no-ai-summary",
            help="Enable AI-powered code summarization",
            rich_help_panel="AI Summarization Options",
        ),
    ] = False,
    ai_provider: Annotated[
        Optional[str],
        typer.Option(
            "--ai-provider",
            help="AI provider (openai, anthropic, openrouter, ollama, llamacpp)",
            rich_help_panel="AI Summarization Options",
        ),
    ] = None,
    ai_model: Annotated[
        Optional[str],
        typer.Option(
            "--ai-model",
            help="Specific AI model to use (e.g., gpt-3.5-turbo, claude-3-haiku)",
            rich_help_panel="AI Summarization Options",
        ),
    ] = None,
    ai_api_key: Annotated[
        Optional[str],
        typer.Option(
            "--ai-api-key",
            help="API key for AI provider (or use env vars)",
            envvar=["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"],
            rich_help_panel="AI Summarization Options",
        ),
    ] = None,
    ai_summarize_functions: Annotated[
        bool,
        typer.Option(
            "--ai-functions/--no-ai-functions",
            help="Also summarize individual functions/methods",
            rich_help_panel="AI Summarization Options",
        ),
    ] = False,
    # Security options
    enable_security: Annotated[
        bool,
        typer.Option(
            "--security/--no-security",
            help="Enable security scanning",
            rich_help_panel="Security Options",
        ),
    ] = True,
    security_threshold: Annotated[
        str,
        typer.Option(
            "--security-threshold",
            help="Minimum severity for security findings",
            rich_help_panel="Security Options",
        ),
    ] = "MEDIUM",
    enable_semgrep: Annotated[
        bool,
        typer.Option(
            "--semgrep/--no-semgrep",
            help="Enable Semgrep security scanning",
            rich_help_panel="Security Options",
        ),
    ] = False,
    write_test_security_report: Annotated[
        bool,
        typer.Option(
            "--test-security-report",
            help="Write test file security findings to separate file",
            rich_help_panel="Security Options",
        ),
    ] = False,
    write_unsupported_report: Annotated[
        bool,
        typer.Option(
            "--unsupported-report",
            help="Write unsupported/skipped files report to JSON file",
            rich_help_panel="Reporting Options",
        ),
    ] = False,
    # Display options
    show_config: Annotated[
        bool,
        typer.Option(
            "--show-config",
            help="Print configuration and exit",
            rich_help_panel="Display Options",
        ),
    ] = False,
    xml_processing_instructions: Annotated[
        Optional[bool],
        typer.Option(
            "--xml-pi/--no-xml-pi",
            help="Include AI processing instructions in XML output",
            rich_help_panel="XML Options",
        ),
    ] = None,
    prompt_file: Annotated[
        Optional[Path],
        typer.Option(
            "--prompt-file",
            help="Custom prompt file for codebase review",
            exists=True,
            resolve_path=True,
            rich_help_panel="Analysis Options",
        ),
    ] = None,
    prompt_var: Annotated[
        Optional[List[str]],
        typer.Option(
            "--prompt-var",
            help="Prompt variables (format: KEY=value)",
            rich_help_panel="Analysis Options",
        ),
    ] = None,
    # Privacy / Path redaction
    redact_paths: Annotated[
        bool,
        typer.Option(
            "--redact-paths/--no-redact-paths",
            help="Redact absolute filesystem paths in outputs/logs (replace with relative or placeholders)",
            rich_help_panel="Display Options",
        ),
    ] = False,
    disable_progress: Annotated[
        bool,
        typer.Option(
            "--no-progress",
            help="Disable progress bars",
            rich_help_panel="Display Options",
        ),
    ] = False,
):
    """
    Process files and generate LLM-friendly output.

    This is the main command that processes your codebase and generates
    documentation in various formats optimized for LLM consumption.

    \b
    Examples:
      codeconcat run                           # Process current directory
      codeconcat run /path/to/project          # Process specific directory
      codeconcat run -f json -o output.json    # JSON output
      codeconcat run --compress --preset lean  # Compressed lean output
      codeconcat run --xml-pi --format xml     # XML with AI instructions
      codeconcat run --prompt-file default     # With analysis prompt
    """
    state = get_state()

    try:
        # Show quote unless in quiet mode
        if not state.quiet:
            show_quote()

        # Show processing header
        if not state.quiet:
            console.print(
                Panel(
                    "[bold cyan]CodeConCat Processing[/bold cyan]\n\n"
                    f"Target: [green]{target or 'Current directory'}[/green]\n"
                    f"Format: [yellow]{format.value}[/yellow]\n"
                    f"Preset: [yellow]{preset or 'Default'}[/yellow]",
                    title="Processing Configuration",
                    border_style="cyan",
                    padding=(1, 2),
                )
            )

        # Build configuration
        with console.status("[bold green]Loading configuration...[/bold green]", spinner="dots"):
            config_builder = ConfigBuilder()
            config_builder.with_defaults()

            if preset:
                config_builder.with_preset(preset.value)

            if state.config_path:
                config_builder.with_yaml_config(str(state.config_path))

            # Apply CLI arguments
            cli_args = {
                "target_path": str(target) if target else ".",
                "output": str(output) if output else None,
                "format": format.value,
                "source_url": source_url,
                "github_token": github_token,
                "source_ref": source_ref,
                "include_paths": include_paths,
                "exclude_paths": exclude_paths,
                "include_languages": include_languages,
                "exclude_languages": exclude_languages,
                "use_gitignore": use_gitignore,
                "use_default_excludes": use_default_excludes,
                "parser_engine": parser_engine.value if parser_engine else None,
                "max_workers": max_workers,
                "extract_docs": extract_docs,
                "merge_docs": merge_docs,
                "disable_annotations": disable_annotations,
                "remove_docstrings": remove_docstrings,
                "remove_comments": remove_comments,
                "enable_compression": enable_compression,
                "compression_level": compression_level.value,
                "enable_ai_summary": enable_ai_summary,
                "ai_provider": ai_provider,
                "ai_model": ai_model,
                "ai_api_key": ai_api_key,
                "ai_summarize_functions": ai_summarize_functions,
                "enable_security_scanning": enable_security,
                "security_scan_severity_threshold": security_threshold,
                "enable_semgrep": enable_semgrep,
                "disable_progress_bar": disable_progress or state.quiet,
                "verbose": state.verbose > 0,
                "xml_processing_instructions": xml_processing_instructions,
                "redact_paths": redact_paths,
            }

            # Remove None values
            cli_args = {k: v for k, v in cli_args.items() if v is not None}
            config_builder.with_cli_args(cli_args)

            config = config_builder.build()

        # Show configuration if requested
        if show_config:
            console.print(
                Panel(
                    config.model_dump_json(indent=2),
                    title="Current Configuration",
                    border_style="cyan",
                )
            )
            raise typer.Exit(0)

        # Handle prompt generation if requested
        if prompt_file or prompt_var:
            from codeconcat.prompts import PromptManager

            # Parse prompt variables
            prompt_vars = {}
            if prompt_var:
                for var in prompt_var:
                    if "=" not in var:
                        print_error(f"Invalid prompt variable format: {var} (expected KEY=value)")
                        raise typer.Exit(1)
                    key, value = var.split("=", 1)
                    prompt_vars[key.upper()] = value

            # Add some automatic variables
            prompt_vars["REPO_NAME"] = os.path.basename(config.target_path)
            prompt_vars["OUTPUT_FORMAT"] = format.value.upper()

            # Load and prepare prompt
            try:
                manager = PromptManager()
                prepared_prompt = manager.prepare_prompt(
                    str(prompt_file) if prompt_file else None, prompt_vars
                )

                # Store in config for later use
                config.analysis_prompt = prepared_prompt  # noqa: F841

                if not state.quiet:
                    console.print("[bold green]✓[/bold green] Analysis prompt loaded\n")
            except Exception as e:
                print_error(f"Failed to load prompt: {e}")
                raise typer.Exit(1) from e

        # Process files
        # Initialize security reporter if security scanning is enabled
        if enable_security:
            security_report_path = os.getenv(
                "CODECONCAT_SECURITY_REPORT_PATH", ".codeconcat_test_security.json"
            )
            init_reporter(
                write_test_report=write_test_security_report,
                test_report_path=Path(security_report_path),
            )

        # Initialize unsupported files reporter
        unsupported_report_path = os.getenv(
            "CODECONCAT_UNSUPPORTED_REPORT_PATH", ".codeconcat_unsupported_files.json"
        )
        init_unsupported_reporter(
            write_report=write_unsupported_report,
            report_path=Path(unsupported_report_path),
        )

        if not state.quiet:
            console.print(f"\n[bold cyan]Processing files from:[/bold cyan] {config.target_path}\n")

        with Progress(
            SpinnerColumn(spinner_name="dots", style="cyan"),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40, style="cyan", complete_style="green"),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
            disable=disable_progress or state.quiet,
            refresh_per_second=4,
        ) as progress:
            task = progress.add_task("[cyan]Processing files...", total=None)

            try:
                output_content = run_codeconcat(config)
                progress.update(task, completed=100)
            except CodeConcatError as e:
                print_error(f"Processing failed: {e}")
                raise typer.Exit(1) from e

        # Write output
        if output_content:
            _write_output_files(output_content, config)

            # Create success panel
            if not state.quiet:
                success_panel = Panel(
                    f"[bold green]Processing Complete![/bold green]\n\n"
                    f"Output file: [cyan]{config.output}[/cyan]\n"
                    f"Format: [yellow]{config.format}[/yellow]",
                    title="Success",
                    border_style="green",
                    padding=(1, 2),
                )
                console.print("\n", success_panel)

                # Concise summary line (standard output, not too verbose)
                stats = getattr(config, "_run_stats", {})
                if stats:
                    summary = (
                        f"Summary: {stats.get('files_scanned', 0)} files scanned, "
                        f"{stats.get('files_parsed', 0)} parsed, "
                        f"{stats.get('languages_count', 0)} languages, "
                        f"{stats.get('total_lines', 0):,} lines"
                    )
                    console.print(summary)
            else:
                print_success(f"Output written to: {config.output}")

            # Show statistics if verbose
            if state.verbose > 0:
                # Create a nice stats table
                stats_table = Table(
                    title="Processing Statistics", show_header=True, header_style="bold cyan"
                )
                stats_table.add_column("Metric", style="cyan", width=20)
                stats_table.add_column("Value", justify="right", style="green")

                stats_table.add_row("Output format", config.format)
                stats_table.add_row("Compression", "Enabled" if enable_compression else "Disabled")
                stats_table.add_row("Security scan", "Enabled" if enable_security else "Disabled")

                # Add codebase stats if available
                stats = getattr(config, "_run_stats", {})
                if stats:
                    stats_table.add_row("Files scanned", str(stats.get("files_scanned", 0)))
                    stats_table.add_row("Files parsed", str(stats.get("files_parsed", 0)))
                    stats_table.add_row("Docs extracted", str(stats.get("docs_extracted", 0)))
                    stats_table.add_row("Languages", ", ".join(stats.get("languages", [])) or "0")
                    stats_table.add_row("Total lines", f"{stats.get('total_lines', 0):,}")
                    stats_table.add_row("Total bytes", f"{stats.get('total_bytes', 0):,}")

                if hasattr(config, "files_processed"):
                    stats_table.add_row("Files processed", str(len(config.target_path)))

                console.print("\n", stats_table)
        else:
            print_warning("No output generated")

    except KeyboardInterrupt:
        print_warning("Operation cancelled by user")
        raise typer.Exit(130) from None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        if state.verbose > 1:
            console.print_exception()
        raise typer.Exit(1) from e
