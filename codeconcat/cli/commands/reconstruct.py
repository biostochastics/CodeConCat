"""
Reconstruct command - Reconstruct files from CodeConCat output.
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing_extensions import Annotated

from codeconcat.reconstruction import reconstruct_from_file

from ..utils import console, print_error, print_file_stats, print_success, print_warning

# Sub-commands need their own Typer app
app = typer.Typer()


def reconstruct_command(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="CodeConCat output file to reconstruct from",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Directory to output reconstructed files",
            resolve_path=True,
            rich_help_panel="Output Options",
        ),
    ] = Path("./reconstructed"),
    input_format: Annotated[
        Optional[str],
        typer.Option(
            "--format",
            "-f",
            help="Format of input file (auto-detected if not specified)",
            rich_help_panel="Input Options",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite existing files without confirmation",
            rich_help_panel="Operation Options",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would be reconstructed without creating files",
            rich_help_panel="Operation Options",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed reconstruction progress",
            rich_help_panel="Display Options",
        ),
    ] = False,
):
    """
    Reconstruct source files from CodeConCat output.

    This command takes a CodeConCat output file (markdown, JSON, or XML)
    and reconstructs the original source files from it. Useful for sharing
    code or recovering files from documentation.

    \b
    Examples:
      codeconcat reconstruct output.md                    # Reconstruct from markdown
      codeconcat reconstruct output.json -o ./restored    # Custom output directory
      codeconcat reconstruct output.xml --dry-run         # Preview without creating files
      codeconcat reconstruct output.md --force            # Overwrite existing files
    """
    try:
        # Check if output directory exists
        if output_dir.exists() and not force and not dry_run and any(output_dir.iterdir()):
            overwrite = typer.confirm(
                f"Output directory {output_dir} is not empty. Continue?",
                default=False,
            )
            if not overwrite:
                print_warning("Reconstruction cancelled.")
                raise typer.Exit(0)

        # Show what we're doing
        console.print(
            Panel(
                f"[bold cyan]Reconstructing Files[/bold cyan]\n\n"
                f"Input: [green]{input_file}[/green]\n"
                f"Output: [green]{output_dir}[/green]\n"
                f"Format: [green]{input_format or 'auto-detect'}[/green]\n"
                f"Mode: [green]{'Dry run' if dry_run else 'Normal'}[/green]",
                title="🔧 File Reconstruction",
                border_style="cyan",
            )
        )

        if dry_run:
            print_warning("DRY RUN MODE - No files will be created")
            # For dry run, just show what would happen
            console.print("[dim]Would reconstruct files from input to output directory[/dim]")
            console.print("[dim]Run without --dry-run to actually create files[/dim]")
            return

        # Perform reconstruction
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Reconstructing files...", total=None)

            stats = reconstruct_from_file(
                str(input_file),
                str(output_dir),
                format_type=input_format,
                verbose=verbose,
            )

            progress.update(task, completed=100)

        # Show results
        if stats:
            print_success("Reconstruction complete!")

            # Format stats for display
            display_stats = {
                "Files Processed": stats.get("files_processed", 0),
                "Files Created": stats.get("files_created", 0),
                "Directories Created": stats.get("dirs_created", 0),
                "Errors": stats.get("errors", 0),
                "Total Size": f"{stats.get('total_size', 0):,} bytes",
            }

            print_file_stats(display_stats)

            if not dry_run:
                console.print(f"\n[dim]Reconstructed files are in:[/dim] [cyan]{output_dir}[/cyan]")
        else:
            print_warning("No files were reconstructed")

    except FileNotFoundError as e:
        print_error(f"Input file not found: {e}")
        raise typer.Exit(1) from e
    except PermissionError as e:
        print_error(f"Permission denied: {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        print_error(f"Reconstruction failed: {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1) from e


@app.command(name="preview")
def preview_command(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="CodeConCat output file to preview",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-l",
            help="Maximum number of files to show",
            min=1,
            max=100,
        ),
    ] = 10,
):
    """
    Preview files that would be reconstructed without creating them.

    This command shows a preview of what files are contained in a
    CodeConCat output file without actually reconstructing them.
    """
    # TODO: Implement preview_files function
    try:
        # Use input_file once preview_files is implemented
        _ = input_file  # Suppress unused variable warning
        files: List[str] = []  # preview_files(str(input_file))

        if not files:
            print_warning("No files found in the input file")
            return

        console.print(
            Panel(
                f"[bold cyan]File Preview[/bold cyan]\n\n"
                f"Found [green]{len(files)}[/green] files in the archive",
                title="📋 Preview",
                border_style="cyan",
            )
        )

        # Show files (limited)
        for i, file_path in enumerate(files[:limit], 1):
            # TODO: When preview_files is implemented, extract proper metadata
            console.print(f"  {i:3d}. [cyan]{file_path}[/cyan]")

        if len(files) > limit:
            console.print(f"\n  [dim]... and {len(files) - limit} more files[/dim]")

    except Exception as e:
        print_error(f"Failed to preview files: {e}")
        raise typer.Exit(1) from e
