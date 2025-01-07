"""Types for security processing."""

from dataclasses import dataclass

@dataclass
class SecurityIssue:
    """Represents a detected security issue in the code."""
    line_number: int
    line_content: str
    issue_type: str
    severity: str
    description: str
