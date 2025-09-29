"""
Init command - Initialize configuration interactively.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from typing_extensions import Annotated

from codeconcat.config.interactive_config import run_interactive_setup

from ..utils import console, print_error, print_success, print_warning

app = typer.Typer()


@app.command(name="init")
def init_command(
    output_file: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output path for configuration file",
            rich_help_panel="Configuration Options",
        ),
    ] = Path(".codeconcat.yml"),
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive/--no-interactive",
            "-i/-n",
            help="Use interactive setup wizard",
            rich_help_panel="Configuration Options",
        ),
    ] = True,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing configuration file",
            rich_help_panel="Configuration Options",
        ),
    ] = False,
    preset: Annotated[
        Optional[str],
        typer.Option(
            "--preset",
            "-p",
            help="Use a specific preset (lean, medium, full)",
            rich_help_panel="Configuration Options",
        ),
    ] = None,
):
    """
    Initialize a CodeConCat configuration file.

    This command helps you create a .codeconcat.yml configuration file
    with sensible defaults. You can either use the interactive wizard
    or specify options directly.

    \b
    Examples:
      codeconcat init                    # Interactive setup
      codeconcat init --preset lean      # Use lean preset
      codeconcat init --no-interactive   # Create default config
      codeconcat init -o myconfig.yml    # Custom output path
    """

    # Check if file already exists
    if output_file.exists() and not force:
        if interactive:
            overwrite = typer.confirm(
                f"Configuration file {output_file} already exists. Overwrite?",
                default=False,
            )
            if not overwrite:
                print_warning("Configuration initialization cancelled.")
                raise typer.Exit(0)
        else:
            print_error(
                f"Configuration file {output_file} already exists. Use --force to overwrite."
            )
            raise typer.Exit(1)

    try:
        if interactive:
            console.print(
                Panel(
                    "[bold cyan]Welcome to CodeConCat Configuration Setup![/bold cyan]\n\n"
                    "This wizard will help you create a configuration file\n"
                    "tailored to your project's needs.",
                    title="Configuration Wizard",
                    border_style="cyan",
                )
            )

            # Run interactive setup
            success = run_interactive_setup(str(output_file))

            if success:
                print_success(f"Configuration file created: {output_file}")
                console.print("\n[dim]To use this configuration, run:[/dim]")
                console.print("  [green]codeconcat run[/green]")
            else:
                print_warning("Configuration setup was cancelled.")

        else:
            # Create default configuration
            create_default_config(output_file, preset)
            print_success(f"Configuration file created: {output_file}")

            if preset:
                console.print(f"[dim]Using preset: {preset}[/dim]")

            console.print("\n[dim]To use this configuration, run:[/dim]")
            console.print("  [green]codeconcat run[/green]")

    except Exception as e:
        print_error(f"Failed to create configuration: {e}")
        raise typer.Exit(1) from e


def create_default_config(output_file: Path, preset: Optional[str] = None) -> None:
    """Create a default configuration file."""
    import yaml  # type: ignore[import-untyped]

    # Default configuration
    config = {
        "version": "1.0",
        "output_preset": preset or "medium",
        "format": "markdown",
        "use_gitignore": True,
        "use_default_excludes": True,
        "parser_engine": "tree_sitter",
        "include_file_summary": True,
        "include_repo_overview": True,
        "enable_security_scanning": True,
        "security_scan_severity_threshold": "MEDIUM",
    }

    # Add preset-specific settings
    if preset == "lean":
        config.update(
            {
                "disable_ai_context": True,
                "parser_engine": "regex",
                "include_file_summary": False,
                "include_repo_overview": False,
                "remove_comments": True,
                "remove_docstrings": True,
            }
        )
    elif preset == "full":
        config.update(
            {
                "include_declarations_in_summary": True,
                "include_imports_in_summary": True,
                "include_tokens_in_summary": True,
                "include_security_in_summary": True,
            }
        )

    # Write configuration file
    with open(output_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


@app.command(name="validate")
def validate_config(
    config_file: Annotated[
        Path,
        typer.Argument(
            help="Configuration file to validate",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = Path(".codeconcat.yml"),
):
    """
    Validate a CodeConCat configuration file.

    Checks if the configuration file is valid YAML and conforms to the
    CodeConCat schema. Reports any validation errors with details.

    \b
    Examples:
      codeconcat validate                      # Validate .codeconcat.yml
      codeconcat validate config/custom.yml    # Validate specific file
    """
    import yaml  # type: ignore[import-untyped]
    from pydantic import ValidationError

    from codeconcat.base_types import CodeConCatConfig

    try:
        # Load configuration
        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        # Validate with Pydantic
        config = CodeConCatConfig(**config_data)

        print_success(f"Configuration file is valid: {config_file}")

        # Show summary if verbose
        console.print(
            Panel(
                f"[green]✓ Configuration is valid[/green]\n\n"
                f"Format: {config.format}\n"
                f"Parser: {config.parser_engine}\n"
                f"Security: {'Enabled' if config.enable_security_scanning else 'Disabled'}",
                title="Validation Result",
                border_style="green",
            )
        )

    except yaml.YAMLError as e:
        print_error(f"Invalid YAML syntax: {e}")
        raise typer.Exit(1) from e
    except ValidationError as e:
        print_error("Configuration validation failed:")
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            console.print(f"  [red]•[/red] {field}: {error['msg']}")
        raise typer.Exit(1) from e
    except Exception as e:
        print_error(f"Failed to validate configuration: {e}")
        raise typer.Exit(1) from e
