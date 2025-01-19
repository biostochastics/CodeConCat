"""Security processor for detecting potential secrets and sensitive information."""

import re
from typing import List

from ..base_types import SecurityIssue


class SecurityProcessor:
    """Processor for detecting security issues in code."""

    # Common patterns for sensitive information
    PATTERNS = {
        "aws_key": (
            r'(?i)aws[_\-\s]*(?:access)?[_\-\s]*key[_\-\s]*(?:id)?["\'\s:=]+[A-Za-z0-9/\+=]{20,}',
            "AWS Key",
        ),
        "aws_secret": (
            r'(?i)aws[_\-\s]*secret[_\-\s]*(?:access)?[_\-\s]*key["\'\s:=]+[A-Za-z0-9/\+=]{40,}',
            "AWS Secret Key",
        ),
        "github_token": (
            r'(?i)(?:github|gh)[_\-\s]*(?:token|key)["\'\s:=]+[A-Za-z0-9_\-]{36,}',
            "GitHub Token",
        ),
        "generic_api_key": (
            r'(?i)api[_\-\s]*key["\'\s:=]+[A-Za-z0-9_\-]{16,}',
            "API Key",
        ),
        "generic_secret": (
            r'(?i)(?:secret|token|key|password|pwd)["\'\s:=]+[A-Za-z0-9_\-]{16,}',
            "Generic Secret",
        ),
        "private_key": (
            r"(?i)-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY[^-]*-----.*?-----END",
            "Private Key",
        ),
        "basic_auth": (
            r'(?i)(?:authorization|auth)\s*[:=]\s*["\']*basic\s+[A-Za-z0-9+/=]+["\']*',
            "Basic Authentication",
        ),
        "bearer_token": (
            r'(?i)(?:authorization|auth)\s*[:=]\s*["\']*bearer\s+[A-Za-z0-9._\-]+["\']*',
            "Bearer Token",
        ),
    }

    # Patterns for common test/sample values that should be ignored
    IGNORE_PATTERNS = [
        r"(?i)example|sample|test|dummy|fake|mock",
        r"your.*key.*here",
        r"xxx+",
        r"[A-Za-z0-9]{16,}\.example\.com",
    ]

    @classmethod
    def scan_content(cls, content: str, file_path: str) -> List[SecurityIssue]:
        """
        Scan content for potential security issues.

        Args:
            content: The content to scan
            file_path: Path to the file being scanned (for context)

        Returns:
            List of SecurityIssue instances
        """
        issues = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Skip empty lines
            if not line.strip():
                continue

            # Skip if line matches ignore patterns
            if any(re.search(pattern, line) for pattern in cls.IGNORE_PATTERNS):
                continue

            # Check each security pattern
            for pattern_name, (pattern, issue_type) in cls.PATTERNS.items():
                if re.search(pattern, line):
                    # Mask the potential secret in the line content
                    masked_line = cls._mask_sensitive_data(line, pattern)

                    issues.append(
                        SecurityIssue(
                            line_number=line_num,
                            line_content=masked_line,
                            issue_type=issue_type,
                            severity="HIGH",
                            description=f"Potential {issue_type} found in {file_path}",
                        )
                    )

        return issues

    @staticmethod
    def _mask_sensitive_data(line: str, pattern: str) -> str:
        """Mask sensitive data in the line with asterisks."""

        def mask_match(match):
            return (
                match.group()[:4] + "*" * (len(match.group()) - 8) + match.group()[-4:]
            )

        return re.sub(pattern, mask_match, line)

    @classmethod
    def format_issues(cls, issues: List[SecurityIssue]) -> str:
        """Format security issues into a readable string."""
        if not issues:
            return "No security issues found."

        formatted = ["Security Scan Results:", "=" * 20]
        for issue in issues:
            formatted.extend(
                [
                    f"\nIssue Type: {issue.issue_type}",
                    f"Severity: {issue.severity}",
                    f"Line {issue.line_number}: {issue.line_content}",
                    f"Description: {issue.description}",
                    "-" * 20,
                ]
            )

        return "\n".join(formatted)
