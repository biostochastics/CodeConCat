"""Security findings reporter module.

This module provides structured reporting of security findings,
separating test file findings from production code findings.
"""

import json
import logging
import threading
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

logger = logging.getLogger(__name__)
console = Console()


class SecurityReporter:
    """Collects and reports security findings in a structured format."""

    def __init__(self, write_test_report: bool = False, test_report_path: Path | None = None):
        """Initialize the security reporter.

        Args:
            write_test_report: Whether to write test findings to a separate file
            test_report_path: Path for the test findings report file
        """
        self.findings: dict[str, list[dict]] = defaultdict(list)
        self.test_findings: dict[str, list[dict]] = defaultdict(list)
        self.write_test_report = write_test_report
        self.test_report_path = test_report_path or Path(".codeconcat_test_security.json")
        self.total_files_scanned = 0
        self.patterns_found: set[str] = set()

    def is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file based on its path.

        Security: This function ONLY identifies test files, not dependencies.
        Dependency directories (node_modules, venv, etc.) are NOT test files
        and their findings must be reported in the main security report.

        Args:
            file_path: Path to check

        Returns:
            True if the file is in a test directory or has test naming pattern
        """
        path_str = str(file_path).lower()
        return any(
            pattern in path_str
            for pattern in [
                "/test_",
                "_test.py",
                "/tests/",
                "/test/",
                "/__pycache__/",
                "/.pytest_cache/",
                "/fixtures/",
                "/mocks/",
                "/stubs/",
                "/__tests__/",
                ".test.js",
                ".spec.js",
                ".test.ts",
                ".spec.ts",
            ]
        )

    def is_dependency_file(self, file_path: Path) -> bool:
        """Check if a file is in a dependency directory (supply-chain code).

        These files contain production dependencies and must be scanned
        for security issues. They should NOT be suppressed from reports.

        Args:
            file_path: Path to check

        Returns:
            True if the file is in a dependency directory
        """
        path_str = str(file_path).lower()
        return any(
            pattern in path_str
            for pattern in [
                "/node_modules/",
                "/venv/",
                "/.venv/",
                "/env/",
                "/.env/",
                "/vendor/",
                "/third_party/",
                "/packages/",
                "/.cargo/",
                "/target/release/",
            ]
        )

    def add_finding(self, file_path: Path, finding: dict) -> None:
        """Add a security finding for a file.

        Args:
            file_path: Path to the file with findings
            finding: Dictionary containing finding details
        """
        self.total_files_scanned += 1

        if "name" in finding:
            self.patterns_found.add(finding["name"])

        if self.is_test_file(file_path):
            self.test_findings[str(file_path)].append(finding)
        else:
            self.findings[str(file_path)].append(finding)

    def get_summary_stats(self) -> dict:
        """Get summary statistics of findings.

        Returns:
            Dictionary with summary statistics
        """
        prod_files_with_issues = len(self.findings)
        test_files_with_issues = len(self.test_findings)

        prod_issue_count = sum(len(findings) for findings in self.findings.values())
        test_issue_count = sum(len(findings) for findings in self.test_findings.values())

        severity_counts: defaultdict[str, int] = defaultdict(int)
        for findings_list in self.findings.values():
            for finding in findings_list:
                severity = finding.get("severity", "UNKNOWN")
                severity_counts[severity] += 1

        return {
            "total_files_scanned": self.total_files_scanned,
            "production_files_with_issues": prod_files_with_issues,
            "test_files_with_issues": test_files_with_issues,
            "total_production_issues": prod_issue_count,
            "total_test_issues": test_issue_count,
            "unique_patterns_found": len(self.patterns_found),
            "severity_distribution": dict(severity_counts),
            "patterns_found": sorted(self.patterns_found),
        }

    def write_test_report_file(self) -> None:
        """Write test findings to a separate JSON file."""
        if not self.write_test_report or not self.test_findings:
            return

        report = {
            "test_security_findings": self.test_findings,
            "summary": {
                "total_test_files_with_issues": len(self.test_findings),
                "total_test_issues": sum(len(f) for f in self.test_findings.values()),
            },
        }

        try:
            with open(self.test_report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            logger.debug(f"Test security report written to {self.test_report_path}")
        except Exception as e:
            logger.warning(f"Failed to write test security report: {e}")

    def display_summary(self, verbose: bool = False) -> None:
        """Display a structured summary of security findings.

        Args:
            verbose: Whether to show detailed findings
        """
        stats = self.get_summary_stats()

        # Don't display anything if no issues found
        if stats["total_production_issues"] == 0 and stats["total_test_issues"] == 0:
            return

        # Create summary table
        table = Table(title="Security Scan Summary", show_header=True, header_style="bold cyan")
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right", style="yellow")

        table.add_row("Files Scanned", str(stats["total_files_scanned"]))

        if stats["total_production_issues"] > 0:
            table.add_row("Production Issues", f"[red]{stats['total_production_issues']}[/red]")
            table.add_row(
                "Production Files Affected", f"[red]{stats['production_files_with_issues']}[/red]"
            )

        if stats["total_test_issues"] > 0:
            table.add_row(
                "Test File Issues", f"[dim yellow]{stats['total_test_issues']}[/dim yellow]"
            )
            table.add_row(
                "Test Files Affected", f"[dim yellow]{stats['test_files_with_issues']}[/dim yellow]"
            )

        # Display severity distribution for production issues
        if stats["severity_distribution"]:
            table.add_section()
            for severity, count in sorted(stats["severity_distribution"].items()):
                color = "red" if severity == "HIGH" else "yellow" if severity == "MEDIUM" else "dim"
                table.add_row(f"{severity} Severity", f"[{color}]{count}[/{color}]")

        console.print("\n")
        console.print(table)

        # Show pattern summary if not too many
        if stats["unique_patterns_found"] > 0 and stats["unique_patterns_found"] <= 10:
            patterns_text = Text("Patterns detected: ", style="cyan")
            patterns_text.append(", ".join(stats["patterns_found"]), style="dim")
            console.print(patterns_text)

        # Write test report if configured
        if self.write_test_report and self.test_findings:
            self.write_test_report_file()
            console.print(
                f"\n[dim]Test file security findings written to: {self.test_report_path}[/dim]"
            )

        # Show hint about verbosity
        if not verbose and stats["total_production_issues"] > 0:
            console.print("\n[dim]Use -v flag for detailed security findings[/dim]")


# Global reporter instance with thread-safe initialization
_reporter: SecurityReporter | None = None
_reporter_lock = threading.Lock()


def get_reporter() -> SecurityReporter:
    """Get or create the global security reporter instance (thread-safe)."""
    global _reporter
    if _reporter is None:
        with _reporter_lock:
            # Double-check after acquiring lock
            if _reporter is None:
                _reporter = SecurityReporter()
    return _reporter


def init_reporter(write_test_report: bool = False, test_report_path: Path | None = None):
    """Initialize a new security reporter (thread-safe).

    Args:
        write_test_report: Whether to write test findings to file
        test_report_path: Path for test findings report
    """
    global _reporter
    with _reporter_lock:
        _reporter = SecurityReporter(write_test_report, test_report_path)
    return _reporter
