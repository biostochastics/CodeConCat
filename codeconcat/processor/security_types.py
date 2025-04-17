"""Types for security processing."""

from dataclasses import dataclass


@dataclass
class SecurityIssue:
    """Represents a detected security issue in the code.

    Attributes:
        line_number: Line number where the issue was found.
        line_content: The content of the line containing the issue.
        issue_type: The type/category of the issue.
        severity: The severity level of the issue.
        description: Human-readable description of the issue.
        raw_finding: The raw matched secret/token string (for deduplication).
        file_path: The file path where the issue was found.
    """

    line_number: int
    line_content: str
    issue_type: str
    severity: str
    description: str
    raw_finding: str
    file_path: str
