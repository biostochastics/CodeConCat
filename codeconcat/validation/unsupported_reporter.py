"""Unsupported files reporter module.

This module provides structured reporting of files that are skipped
or unsupported during processing, categorized by reason.
"""

import json
import logging
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


class UnsupportedFilesReporter:
    """Collects and reports unsupported/skipped files in a structured format."""

    def __init__(self, write_report: bool = False, report_path: Path | None = None):
        """Initialize the unsupported files reporter.

        Args:
            write_report: Whether to write findings to a JSON file
            report_path: Path for the report file
        """
        self.skipped_files: dict[str, list[dict]] = defaultdict(list)
        self.write_report = write_report
        self.report_path = report_path or Path(".codeconcat_unsupported_files.json")
        self.total_files_processed = 0
        self.categories: dict[str, int] = defaultdict(int)

    def add_skipped_file(
        self, file_path: Path, reason: str, category: str = "unknown", details: str | None = None
    ) -> None:
        """Add a skipped/unsupported file entry.

        Args:
            file_path: Path to the skipped file
            reason: Human-readable reason for skipping
            category: Category of skip (binary, unsupported_language, excluded_pattern, etc.)
            details: Additional details about why the file was skipped
        """
        self.categories[category] += 1

        # Ensure file_path is a Path object
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        entry = {
            "path": str(file_path),
            "reason": reason,
            "category": category,
            "extension": file_path.suffix if file_path.suffix else "no_extension",
        }

        if details:
            entry["details"] = details

        self.skipped_files[category].append(entry)

    def increment_processed_count(self) -> None:
        """Increment the total files processed counter."""
        self.total_files_processed += 1

    def get_summary_stats(self) -> dict:
        """Get summary statistics of skipped files.

        Returns:
            Dictionary with summary statistics
        """
        total_skipped = sum(self.categories.values())

        # Get extension distribution for unsupported files
        extension_counts: defaultdict[str, int] = defaultdict(int)
        for entries in self.skipped_files.values():
            for entry in entries:
                ext = entry.get("extension", "unknown")
                extension_counts[ext] += 1

        # Get top extensions
        top_extensions = sorted(extension_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_files_processed": self.total_files_processed,
            "total_skipped": total_skipped,
            "skip_percentage": (total_skipped / max(self.total_files_processed, 1)) * 100,
            "categories": dict(self.categories),
            "top_extensions": top_extensions,
        }

    def write_report_file(self) -> None:
        """Write skipped files report to a JSON file."""
        if not self.write_report or not self.skipped_files:
            return

        report = {
            "unsupported_files": dict(self.skipped_files),
            "summary": self.get_summary_stats(),
        }

        try:
            with open(self.report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            logger.debug(f"Unsupported files report written to {self.report_path}")
        except Exception as e:
            logger.warning(f"Failed to write unsupported files report: {e}")

    def display_summary(self, verbose: bool = False) -> None:
        """Display a structured summary of unsupported/skipped files.

        Args:
            verbose: Whether to show detailed listings
        """
        stats = self.get_summary_stats()

        # Don't display anything if no files were skipped
        if stats["total_skipped"] == 0:
            return

        # Create summary table
        table = Table(
            title="Unsupported/Skipped Files Summary", show_header=True, header_style="bold cyan"
        )
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right", style="yellow")

        table.add_row("Total Files Processed", str(stats["total_files_processed"]))
        table.add_row("Total Files Skipped", f"[yellow]{stats['total_skipped']}[/yellow]")
        table.add_row("Skip Percentage", f"[dim]{stats['skip_percentage']:.1f}%[/dim]")

        # Show breakdown by category
        if stats["categories"]:
            table.add_section()
            category_names = {
                "binary": "Binary Files",
                "unsupported_language": "Unsupported Language",
                "unknown_language": "Unknown Language",
                "excluded_pattern": "Excluded by Pattern",
                "parse_error": "Parse Errors",
                "permission_denied": "Permission Denied",
                "too_large": "File Too Large",
            }

            for category, count in sorted(stats["categories"].items()):
                display_name = category_names.get(category, category.replace("_", " ").title())
                table.add_row(display_name, str(count))

        # Show top extensions if available
        if stats["top_extensions"]:
            table.add_section()
            table.add_row("[bold]Top Extensions[/bold]", "")
            for ext, count in stats["top_extensions"]:
                display_ext = ext if ext != "no_extension" else "(no extension)"
                table.add_row(f"  {display_ext}", str(count))

        console.print("\n")
        console.print(table)

        # Write report if configured
        if self.write_report and self.skipped_files:
            self.write_report_file()
            console.print(
                f"\n[dim]Detailed unsupported files report written to: {self.report_path}[/dim]"
            )

        # Show hint about verbosity
        if not verbose and stats["total_skipped"] > 10:
            console.print("\n[dim]Use -v flag to see individual skipped files[/dim]")
        elif verbose and self.skipped_files:
            # Show some examples of skipped files
            console.print("\n[bold cyan]Sample Skipped Files:[/bold cyan]")
            sample_count = 0
            for _category, entries in self.skipped_files.items():
                if sample_count >= 10:
                    break
                for entry in entries[:2]:  # Show max 2 per category
                    if sample_count >= 10:
                        break
                    console.print(f"  [dim]{entry['path']}[/dim] - {entry['reason']}")
                    sample_count += 1

            if stats["total_skipped"] > 10:
                console.print(f"  [dim]... and {stats['total_skipped'] - 10} more[/dim]")


# Global reporter instance
_reporter: UnsupportedFilesReporter | None = None


def get_reporter() -> UnsupportedFilesReporter:
    """Get or create the global unsupported files reporter instance."""
    global _reporter
    if _reporter is None:
        _reporter = UnsupportedFilesReporter()
    return _reporter


def init_reporter(write_report: bool = False, report_path: Path | None = None):
    """Initialize a new unsupported files reporter.

    Args:
        write_report: Whether to write findings to file
        report_path: Path for report file
    """
    global _reporter
    _reporter = UnsupportedFilesReporter(write_report, report_path)
    return _reporter
