"""External security scanner integration for CodeConCat.

This module provides functions to invoke and parse results from external
security tools (e.g., Semgrep) and convert them to the internal
SecurityIssue format.
"""

import subprocess
import json
import sys
import re
from pathlib import Path
from typing import List, Optional

from .security_types import SecurityIssue
from ..base_types import CodeConCatConfig, SecuritySeverity


def run_semgrep_scan(
    file_path: str | Path,
    config: Optional[CodeConCatConfig] = None,
    semgrep_path: str = "semgrep",
    rules: Optional[str] = "p/ci",  # Default to Semgrep's community ruleset
) -> List[SecurityIssue]:
    """Run Semgrep on the given file and return SecurityIssue objects.

    Args:
        file_path: The file to scan.
        config: Optional config object.
        semgrep_path: Path to the semgrep executable.
        rules: Optional ruleset (directory, file, or registry string).
               Defaults to Semgrep's 'p/ci' community ruleset.

    Returns:
        List of SecurityIssue objects.
    """
    # Validate inputs to prevent command injection
    path = str(file_path)
    if not Path(path).exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return []

    # Validate semgrep_path - must be alphanumeric with optional path separators
    if not re.match(r"^[a-zA-Z0-9_./\\-]+$", semgrep_path):
        print(f"Error: Invalid semgrep path: {semgrep_path}", file=sys.stderr)
        return []

    # Validate rules parameter - allow only safe patterns
    if rules:
        # Allow: p/something, path/to/file.yml, ./rules, etc.
        # Disallow: shell metacharacters and command separators
        if not re.match(r"^[a-zA-Z0-9_./\\:@-]+$", rules):
            print(f"Error: Invalid rules parameter: {rules}", file=sys.stderr)
            return []

    cmd = [semgrep_path, "--json", "--quiet", path]
    if rules:
        cmd.extend(["--config", rules])
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
            text=True,
            encoding="utf-8",  # Ensure consistent encoding
        )
        # Semgrep exit codes:
        # 0: clean run, no findings
        # 1: clean run, findings found
        # 2: CLI usage error
        # >2: other errors
        if result.returncode not in (0, 1):
            print(
                f"Semgrep error scanning {path}. Exit code: {result.returncode}. "
                f"Stderr: {result.stderr.strip()}",
                file=sys.stderr,
            )
            return []
        if not result.stdout:
            # Should only happen if --json wasn't respected or Semgrep errored early
            print(
                f"Semgrep produced no JSON output for {path}. " f"Stderr: {result.stderr.strip()}",
                file=sys.stderr,
            )
            return []
        data = json.loads(result.stdout)
    except FileNotFoundError:
        print(
            f"Error: '{semgrep_path}' command not found. Is Semgrep installed and in PATH?",
            file=sys.stderr,
        )
        return []
    except json.JSONDecodeError:
        print(
            f"Error: Failed to decode Semgrep JSON output for {path}. "
            f"Output length: {len(result.stdout)}. First 100 chars: {result.stdout[:100]}",
            file=sys.stderr,
        )
        return []
    except Exception as e:
        print(f"An unexpected error occurred running Semgrep on {path}: {e}", file=sys.stderr)
        return []

    issues = []
    for finding in data.get("results", []):
        sev_str = finding.get("extra", {}).get("severity", "INFO").upper()
        # Map Semgrep severities (INFO, WARNING, ERROR) to our enum
        if sev_str == "ERROR":
            severity = SecuritySeverity.HIGH
        elif sev_str == "WARNING":
            severity = SecuritySeverity.MEDIUM
        else:  # INFO or other/unknown maps to LOW
            severity = SecuritySeverity.LOW

        # Extract line content if available
        line_content = finding.get("extra", {}).get("lines", "").strip()
        # Use the finding message as description
        description = finding.get("extra", {}).get("message", "Semgrep finding").strip()
        # Try to get the specific matched code snippet (often in metavars)
        raw_finding = ""
        metavars = finding.get("extra", {}).get("metavars", {})
        if isinstance(metavars, dict):
            # Look for common metavar keys that might hold the finding
            for key in ("$X", "$VAR", "$FUNC", "$ARG", "$PARAM"):
                if key in metavars and isinstance(metavars[key], dict):
                    raw_finding = metavars[key].get("abstract_content", "")
                    if raw_finding:
                        break
        if not raw_finding:
            raw_finding = line_content  # Fallback to line content

        issues.append(
            SecurityIssue(
                line_number=finding.get("start", {}).get("line", 0),
                line_content=line_content,  # Store the line Semgrep provides
                issue_type=finding.get("check_id", "semgrep"),
                severity=severity,
                description=description,
                raw_finding=str(raw_finding).strip(),  # Store matched code or relevant part
                file_path=finding.get("path", str(path)),  # Use path from Semgrep result
            )
        )
    return issues


# Example usage (if run directly for testing)
# if __name__ == '__main__':
#     test_file = 'path/to/your/test_file.py' # Replace with an actual file path
#     if Path(test_file).exists():
#         scan_results = run_semgrep_scan(test_file)
#         if scan_results:
#             print(f"Found {len(scan_results)} issues in {test_file}:", file=sys.stderr)
#             for issue in scan_results:
#                 print(f"- Line {issue.line_number}: [{issue.severity}] {issue.issue_type} - {issue.description}", file=sys.stderr)
#         else:
#             print(f"No issues found in {test_file} by Semgrep.", file=sys.stderr)
#     else:
#         print(f"Test file not found: {test_file}", file=sys.stderr)
