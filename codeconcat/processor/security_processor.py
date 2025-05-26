"""security_processor.py

Security scanning utilities for CodeConCat.

This module provides one public class, :class:`SecurityProcessor`, that can be
used to scan source‐code content for accidental disclosure of credentials
(API keys, passwords, private keys, …).  The implementation supports a rich set
of built‑in regular‑expression rules and allows project‑level configuration of
custom rules, ignore lists, and severity thresholds.

All public methods are class methods; the processor thus keeps no per‑instance
state and can be shared freely.  Any additions or fixes here should remain
free of I/O side‑effects so that the scanner can be used inside both CLI and
library contexts.
"""

from __future__ import annotations

import fnmatch
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from ..base_types import CodeConCatConfig, CustomSecurityPattern, SecuritySeverity
from .security_types import SecurityIssue
from .external_scanners import run_semgrep_scan
from .attack_patterns import scan_content as scan_attack_patterns, Severity as AttackSeverity

__all__ = ["SecurityProcessor"]

logger = logging.getLogger(__name__)


class SecurityProcessor:  # pylint: disable=too-many-public-methods
    """Static helpers for security scanning."""

    # Define severity order for reliable comparison
    SEVERITY_ORDER = [
        SecuritySeverity.INFO,
        SecuritySeverity.LOW,
        SecuritySeverity.MEDIUM,
        SecuritySeverity.HIGH,
        SecuritySeverity.CRITICAL,
    ]

    # ----------------------------------------------------------------------------------
    # Define complex regex patterns as constants first using standard strings
    # ----------------------------------------------------------------------------------
    _AWS_SECRET_KEY_REGEX = '(?i)\\baws[_\\-\\s]+secret[_\\-\\s]+(?:access[_\\-\\s]+)?key["\\s:=]+["]?([A-Za-z0-9/+=]{40})["\\s]?'
    _GENERIC_API_KEY_REGEX = "(?i)\\b(?:api[_\\-\\s]*key|key[_\\-\\s]*id|secret[_\\-\\s]*key)[\"'\\s:=]+[\"']?([a-zA-Z0-9\\-._/+=]{8,})[\"']?"
    _GENERIC_PASSWORD_REGEX = (
        "(?i)\\b(?:password|pwd|pass)['\"\\s:=]+['\"]?([a-zA-Z0-9!@#$%^&*()_\\+-]{8,})['\"]?"
    )
    _AWS_SESSION_TOKEN_REGEX = '(?i)aws_session_token["\\s:=]+["]?([A-Za-z0-9/+=]{16,})["\\s]?'

    # ----------------------------------------------------------------------------------
    # Pattern definitions ----------------------------------------------------------------
    # ----------------------------------------------------------------------------------
    # The raw (un‑compiled) patterns are kept separate from the compiled mapping so we
    # can still expose them (e.g. in docs/tests) while ensuring the runtime path only
    # ever deals with compiled :class:`re.Pattern` objects.

    _RAW_BUILT_IN_PATTERNS: Dict[str, Tuple[str, str, SecuritySeverity]] = {
        # fmt: off  # <‑‑ keep long patterns readable
        "aws_access_key_id": (
            "(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])",
            "AWS Access Key ID",
            SecuritySeverity.CRITICAL,
        ),
        "aws_secret_access_key": (
            _AWS_SECRET_KEY_REGEX,
            "AWS Secret Access Key",
            SecuritySeverity.CRITICAL,
        ),
        "generic_api_key": (
            _GENERIC_API_KEY_REGEX,
            "Generic API Key",
            SecuritySeverity.HIGH,
        ),
        "generic_password": (
            _GENERIC_PASSWORD_REGEX,
            "Generic Password",
            SecuritySeverity.HIGH,
        ),
        "private_key_pem": (
            "-----BEGIN ((EC|RSA|DSA|PGP|OPENSSH)\\s+)?PRIVATE KEY-----",
            "Private Key (PEM Format)",
            SecuritySeverity.CRITICAL,
        ),
        "github_token": (
            "(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}",
            "GitHub Token",
            SecuritySeverity.CRITICAL,
        ),
        "slack_token": (
            "xox[pboa]r?-[0-9a-zA-Z]{10,48}",
            "Slack Token",
            SecuritySeverity.CRITICAL,
        ),
        "google_api_key": (
            "AIza[0-9A-Za-z\\-_]{35}",
            "Google API Key",
            SecuritySeverity.CRITICAL,
        ),
        "heroku_api_key": (
            "[hH]eroku[a-zA-Z0-9]{32}",
            "Heroku API Key",
            SecuritySeverity.CRITICAL,
        ),
        "slack_webhook_url": (
            "https://hooks.slack.com/services/[A-Za-z0-9_/-]+",
            "Slack Webhook URL",
            SecuritySeverity.CRITICAL,
        ),
        "stripe_secret_key": (
            "sk_live_[0-9a-zA-Z]{24}",
            "Stripe Secret Key",
            SecuritySeverity.CRITICAL,
        ),
        "twilio_api_key": (
            "SK[0-9a-fA-F]{32}",
            "Twilio API Key",
            SecuritySeverity.CRITICAL,
        ),
        "jwt_token": (
            "eyJ[a-zA-Z0-9\\-]+?\\.[a-zA-Z0-9\\-]+?\\.[a-zA-Z0-9\\-]+",
            "JWT Token",
            SecuritySeverity.HIGH,
        ),
        "openssh_private_key": (
            "-----BEGIN OPENSSH PRIVATE KEY-----",
            "OpenSSH Private Key",
            SecuritySeverity.CRITICAL,
        ),
        "facebook_access_token": (
            "EAACEdEose0cBA[0-9A-Za-z]+",
            "Facebook Access Token",
            SecuritySeverity.CRITICAL,
        ),
        "aws_session_token": (
            _AWS_SESSION_TOKEN_REGEX,
            "AWS Session Token",
            SecuritySeverity.CRITICAL,
        ),
        "azure_storage_key": (
            "(?i)DefaultEndpointsProtocol=https;AccountName=[a-z0-9]+;"
            "AccountKey=[A-Za-z0-9+/=]+;EndpointSuffix=core.windows.net",
            "Azure Storage Key",
            SecuritySeverity.CRITICAL,
        ),
        # fmt: on
    }

    # Compiled at import‑time; safe for concurrent use.
    _BUILT_IN_PATTERNS: Dict[str, Tuple[re.Pattern[str], str, SecuritySeverity]] = {}
    for _name, (_regex, _issue_type, _severity) in _RAW_BUILT_IN_PATTERNS.items():
        try:
            _BUILT_IN_PATTERNS[_name] = (re.compile(_regex), _issue_type, _severity)
        except re.error as exc:  # pragma: no cover — should never fail.
            logger.error("Invalid built‑in security pattern '%s': %s", _name, exc)

    # Inline‑ignore comment such as ``# nosec`` or ``# codeconcat-ignore-security``
    # Inline ignore patterns:
    #   - '# codeconcat-ignore-security-line' or '# nosec' (single line)
    #   - '# codeconcat-ignore-security-block' ... '# end-ignore' (block)
    _INLINE_IGNORE_LINE_PATTERN: re.Pattern[str] = re.compile(
        r"(?:#|//)\s*(?:nosec|codeconcat-ignore-security(?:-line)?)\b", re.IGNORECASE
    )
    _INLINE_IGNORE_BLOCK_START_PATTERN: re.Pattern[str] = re.compile(
        r"(?:#|//)\s*codeconcat-ignore-security-block\b", re.IGNORECASE
    )
    _INLINE_IGNORE_BLOCK_END_PATTERN: re.Pattern[str] = re.compile(
        r"(?:#|//)\s*end-ignore", re.IGNORECASE
    )

    # ----------------------------------------------------------------------------------
    # Public helpers ---------------------------------------------------------------------
    # ----------------------------------------------------------------------------------
    @classmethod
    def scan_content(
        cls,
        content: str,
        file_path: str | Path,
        config: CodeConCatConfig,
        mask_output_content: bool = False,
    ) -> Tuple[List[SecurityIssue], Optional[str]]:
        """Scan *content* and return a list of :class:`SecurityIssue` objects.

        If *mask_output_content* is True, the second element of the returned tuple
        will be the content string with found secrets masked, otherwise it's None.

        The method respects *config* settings such as ignore lists and severity
        threshold.  The *file_path* is only used for reporting and for ignore
        matching; it **is not** read from disk.

        Supports optional integration with external tools (e.g., Semgrep) if enabled.
        """
        if not config.enable_security_scanning:
            # Return empty list and None for content
            return [], None

        # Resolve path early so downstream helpers can rely on a valid :class:`Path`.
        try:
            abs_path = Path(file_path).expanduser().resolve()
        except Exception:  # pylint: disable=broad-except
            logger.warning(
                "Could not resolve absolute path for '%s'; falling back to the " "provided string.",
                file_path,
            )
            abs_path = Path(str(file_path))

        if cls._should_ignore_path(abs_path, config):
            logger.debug("Skipping security scan for ignored path: %s", abs_path)
            return []

        # Merge built‑in with (optionally validated) custom patterns.
        compiled_patterns = cls._compile_patterns(config)
        logger.debug(f"Compiled patterns available for scan: {list(compiled_patterns.keys())}")
        issues: List[SecurityIssue] = []
        # Use a list for mutable lines if masking
        lines = content.splitlines()
        output_lines = lines[:] if mask_output_content else None

        for idx, line in enumerate(lines):  # ``idx`` is zero‑based.
            lineno = idx + 1

            if cls._should_skip_line(idx, lines):
                continue

            # Keep track if line was modified by masking
            original_line_for_masking = line  # Store original line segment for sequential masking

            for rule_name, (
                pattern,
                issue_type,
                default_sev,
            ) in compiled_patterns.items():
                # Use original line segment for finding matches, but mask the potentially already masked line
                current_line_segment = (
                    output_lines[idx] if mask_output_content and output_lines else line
                )
                for match in pattern.finditer(original_line_for_masking):
                    try:
                        group_index = 1 if pattern.groups >= 1 and match.group(1) is not None else 0
                        raw_finding = match.group(group_index)
                    except Exception as exc:
                        logger.warning(
                            "Failed to extract group from match in file '%s', line %d: %s",
                            file_path,
                            lineno,
                            exc,
                        )
                        continue

                    if not raw_finding or cls._should_ignore_finding(raw_finding, config):
                        continue
                    if cls._is_duplicate(issues, lineno, issue_type, raw_finding, abs_path):
                        continue
                    current_severity = cls._determine_severity(default_sev, abs_path, config)
                    threshold = cls._resolve_threshold(config)
                    # Compare severity indices directly for robustness
                    try:
                        current_sev_index = cls.SEVERITY_ORDER.index(current_severity)
                        threshold_index = cls.SEVERITY_ORDER.index(threshold)
                        if current_sev_index < threshold_index:
                            continue
                    except ValueError:
                        # Handle case where severity might not be in the order list (shouldn't happen)
                        logger.error(
                            "Invalid severity '%s' or '%s'; defaulting to MEDIUM.",
                            current_severity,
                            threshold,
                        )
                        continue

                    # Always generate the masked line for the issue report
                    try:
                        masked_line_for_issue = cls._mask_sensitive_data(
                            current_line_segment, pattern, match
                        )
                    except Exception:
                        # Use the (potentially already masked) line segment if specific masking fails
                        masked_line_for_issue = current_line_segment

                    # Mask the actual output line list if requested
                    if mask_output_content and output_lines:
                        try:
                            # Mask the line in the output_lines list
                            output_lines[idx] = cls._mask_sensitive_data(
                                output_lines[idx], pattern, match
                            )
                        except Exception:
                            # Log error but continue; output_lines[idx] remains as it was
                            logger.warning(
                                f"Failed to mask output line {lineno} in {file_path} for finding: {raw_finding[:10]}...",
                                exc_info=True,
                            )

                    issue = SecurityIssue(
                        line_number=lineno,
                        line_content=masked_line_for_issue,  # Use specifically masked line for issue
                        issue_type=issue_type,
                        severity=current_severity,
                        description=f"Potential {issue_type} detected.",
                        raw_finding=raw_finding,
                        file_path=str(abs_path),
                    )
                    issues.append(issue)

        # Integrate comprehensive attack pattern scanning
        if config.enable_security_scanning:
            # Detect the language from file extension
            language = cls._detect_language(abs_path)
            if language:
                attack_findings = scan_attack_patterns(content, language)
                for finding in attack_findings:
                    # Convert attack pattern severity to SecuritySeverity
                    severity_map = {
                        AttackSeverity.CRITICAL.value: SecuritySeverity.CRITICAL,
                        AttackSeverity.HIGH.value: SecuritySeverity.HIGH,
                        AttackSeverity.MEDIUM.value: SecuritySeverity.MEDIUM,
                        AttackSeverity.LOW.value: SecuritySeverity.LOW,
                        AttackSeverity.INFO.value: SecuritySeverity.INFO,
                    }
                    severity = severity_map.get(finding["severity"], SecuritySeverity.MEDIUM)

                    # Check if this finding meets the threshold
                    threshold = cls._resolve_threshold(config)
                    try:
                        current_sev_index = cls.SEVERITY_ORDER.index(severity)
                        threshold_index = cls.SEVERITY_ORDER.index(threshold)
                        if current_sev_index < threshold_index:
                            continue
                    except ValueError:
                        continue

                    # Extract the line content
                    line_idx = finding["line"] - 1
                    if 0 <= line_idx < len(lines):
                        line_content = lines[line_idx]
                    else:
                        line_content = finding.get("snippet", "")

                    issue = SecurityIssue(
                        line_number=finding["line"],
                        line_content=line_content,
                        issue_type=finding["name"],
                        severity=severity,
                        description=finding["message"],
                        raw_finding=finding.get("snippet", ""),
                        file_path=str(abs_path),
                    )

                    # Check for duplicates
                    if not cls._is_duplicate(
                        issues, issue.line_number, issue.issue_type, issue.raw_finding, abs_path
                    ):
                        issues.append(issue)

        # Optional: integrate external scanners (e.g., Semgrep)
        if getattr(config, "enable_external_semgrep", False):
            semgrep_issues = run_semgrep_scan(
                abs_path, config, rules=getattr(config, "semgrep_ruleset", "p/ci")
            )
            # Add Semgrep issues, avoiding duplicates if possible (basic check)
            existing_issue_keys = {
                (iss.file_path, iss.line_number, iss.issue_type) for iss in issues
            }
            for s_issue in semgrep_issues:
                key = (s_issue.file_path, s_issue.line_number, s_issue.issue_type)
                if key not in existing_issue_keys:
                    issues.append(s_issue)
                    existing_issue_keys.add(key)

        # Join the masked lines if masking was enabled
        final_masked_content = "\n".join(output_lines) if output_lines is not None else None

        return issues, final_masked_content

    # ----------------------------------------------------------------------------------
    # Internal helpers -------------------------------------------------------------------
    # ----------------------------------------------------------------------------------
    @classmethod
    def _detect_language(cls, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".php": "php",
            ".r": "r",
            ".R": "r",
            ".jl": "julia",
            ".rs": "rust",
            ".java": "java",
        }

        suffix = file_path.suffix.lower()
        return extension_map.get(suffix)

    @classmethod
    def _compile_patterns(
        cls, config: CodeConCatConfig
    ) -> Dict[str, Tuple[re.Pattern[str], str, SecuritySeverity]]:
        """Return merged dict of compiled built‑in and custom patterns."""
        compiled: Dict[str, Tuple[re.Pattern[str], str, SecuritySeverity]] = {}

        # --- Compile Built-in Patterns ---
        for name, (
            raw_regex,
            issue_type,
            severity,
        ) in cls._RAW_BUILT_IN_PATTERNS.items():
            try:
                compiled[name] = (re.compile(raw_regex), issue_type, severity)
            except re.error as exc:
                logger.error("Failed to compile built-in security pattern '%s': %s", name, exc)

        # --- Compile and Add/Overwrite with Custom Patterns ---
        for custom in config.security_custom_patterns:
            if not isinstance(custom, CustomSecurityPattern):
                logger.error("Skipping invalid custom security pattern: %s", custom)
                continue

            try:
                severity = SecuritySeverity[custom.severity.upper()]
                issue_type = custom.name
                compiled[custom.name] = (re.compile(custom.regex), issue_type, severity)
            except re.error as exc:
                logger.error(
                    "Failed to compile custom security pattern '%s': %s",
                    custom.name,
                    exc,
                )
            except KeyError:
                logger.error(
                    "Invalid severity '%s' for custom security pattern '%s'.",
                    custom.severity,
                    custom.name,
                )
        return compiled

    # ------------------------------------------------------------------------- path ignore
    @classmethod
    def _should_ignore_path(cls, abs_path: Path, config: CodeConCatConfig) -> bool:
        """Return *True* when the absolute *abs_path* matches an ignore pattern."""
        path_str = abs_path.as_posix()
        for pattern in config.security_ignore_paths:
            normalized = pattern.replace("\\", "/")
            if (
                fnmatch.fnmatch(path_str, normalized)
                or fnmatch.fnmatch(abs_path.name, normalized)
                or any(
                    fnmatch.fnmatch(parent.as_posix(), normalized) for parent in abs_path.parents
                )
            ):
                return True
        return False

    # ---------------------------------------------------------------------- finding ignore
    @classmethod
    def _should_ignore_finding(cls, finding: str, config: CodeConCatConfig) -> bool:
        """Return *True* when the finding matches an ignore regular expression."""
        for pattern in config.security_ignore_patterns:
            try:
                if re.search(pattern, finding):
                    return True
            except re.error as exc:
                logger.warning("Invalid ignore regex '%s': %s", pattern, exc)
        return False

    # --------------------------------------------------------------------- inline ignores
    @classmethod
    def _should_skip_line(cls, line_idx: int, lines: List[str]) -> bool:
        """Handle inline and block ignore comments for security scanning.

        Supports:
        - '# codeconcat-ignore-security-line' or '# nosec' (single line)
        - '# codeconcat-ignore-security-block' ... '# end-ignore' (block)
        Ignores leading/trailing whitespace and both '#' and '//' comment styles.
        """
        # Block ignore
        in_block = False
        for i in range(0, line_idx + 1):
            if cls._INLINE_IGNORE_BLOCK_START_PATTERN.search(lines[i]):
                in_block = True
            elif in_block and cls._INLINE_IGNORE_BLOCK_END_PATTERN.search(lines[i]):
                in_block = False
        if in_block:
            return True
        # Single-line ignore
        if cls._has_inline_ignore_line(lines[line_idx]):
            return True
        if line_idx > 0 and cls._has_inline_ignore_line(lines[line_idx - 1]):
            return True
        return False

    @classmethod
    def _has_inline_ignore_line(cls, line: str) -> bool:
        return bool(cls._INLINE_IGNORE_LINE_PATTERN.search(line))

    # --------------------------------------------------------------------- severity logic
    @classmethod
    def _determine_severity(
        cls, default: SecuritySeverity, abs_path: Path, config: CodeConCatConfig
    ) -> SecuritySeverity:
        """Return severity, optionally downgrading for test/example files."""
        path_lc = abs_path.as_posix().lower()
        is_test = (
            any(
                token in path_lc
                for token in (
                    "/tests/",
                    "/test/",
                    "/examples/",
                    "/example/",
                )
            )
            or abs_path.name.startswith("test_")
            or abs_path.name.endswith(
                (
                    "_test.py",
                    "_spec.rb",
                    ".test.js",
                    ".spec.js",
                    ".test.ts",
                    ".spec.ts",
                )
            )
        )

        if is_test:
            mapping = {
                SecuritySeverity.CRITICAL: SecuritySeverity.HIGH,
                SecuritySeverity.HIGH: SecuritySeverity.MEDIUM,
                SecuritySeverity.MEDIUM: SecuritySeverity.LOW,
            }
            return mapping.get(default, default)
        return default

    # -------------------------------------------------------------------------- misc util
    @staticmethod
    def _get_masked_finding(finding: str) -> str:
        """Return the finding string masked."""
        if not finding:
            return ""

        length = len(finding)
        if length > 8:
            return f"{finding[:3]}****{finding[-3:]}"
        elif length > 4:
            return f"{finding[:2]}****{finding[-2:]}"
        elif length > 2:
            return f"{finding[0]}****{finding[-1]}"
        else:
            return "****"

    @staticmethod
    def _mask_sensitive_data(line: str, pattern: re.Pattern[str], match: re.Match[str]) -> str:
        """Return *line* with the secret portion of *match* hidden. May raise ValueError on failure."""
        group_index = 1 if pattern.groups >= 1 and match.group(1) is not None else 0
        start, end = match.span(group_index)
        finding = match.group(group_index)

        if not finding:
            return line

        length = len(finding)
        if length > 8:
            masked = f"{finding[:3]}****{finding[-3:]}"
        elif length > 4:
            masked = f"{finding[:2]}****{finding[-2:]}"
        elif length > 2:
            masked = f"{finding[0]}****{finding[-1]}"
        else:
            masked = "****"
        return f"{line[:start]}{masked}{line[end:]}"

    @staticmethod
    def _is_duplicate(
        issues: List[SecurityIssue],
        line_no: int,
        issue_type: str,
        raw_finding: str,
        file_path: str | Path,
    ) -> bool:
        """Return *True* when *raw_finding* was already reported for *line_no*."""
        return any(
            iss.line_number == line_no
            and iss.issue_type == issue_type
            and iss.raw_finding == raw_finding
            and Path(iss.file_path) == Path(file_path)
            for iss in issues
        )

    # ------------------------------------------------------------------------- formatting
    @classmethod
    def format_issues(cls, issues: List[SecurityIssue], config: CodeConCatConfig) -> str:
        """Pretty‑print *issues* with respect to *config* threshold.

        Includes the specific finding and context lines for each issue.
        """
        if not issues:
            return "Security Scan Results: No issues found."

        threshold = cls._resolve_threshold(config)
        filtered: List[SecurityIssue] = [issue for issue in issues if issue.severity >= threshold]
        if not filtered:
            return (
                "Security Scan Results: No issues found at or above the "
                f"'{threshold.name}' threshold."
            )

        filtered.sort(key=lambda i: (i.severity, i.file_path, i.line_number), reverse=True)

        # Group issues by file for context
        from collections import defaultdict

        file_to_issues = defaultdict(list)
        for issue in filtered:
            file_to_issues[issue.file_path].append(issue)

        lines: List[str] = [
            "Security Scan Results:",
            "=" * 20,
            f"Found {len(filtered)} issue(s) at or above the '{threshold.name}' threshold:",
        ]
        for file_path, file_issues in file_to_issues.items():
            # Try to read file for context
            try:
                with open(file_path, "r") as f:
                    file_lines = f.readlines()
            except Exception:
                file_lines = None
            for issue in file_issues:
                lines.append("")
                lines.append(f"Severity : {issue.severity.name}")
                lines.append(f"Type     : {issue.issue_type}")
                lines.append(f"File     : {issue.file_path}")
                lines.append(f"Line {issue.line_number}: {issue.line_content.strip()}")
                lines.append(f"Finding  : {issue.raw_finding}")
                lines.append(f"Description: {issue.description}")
                # Add context lines if file is available
                if file_lines:
                    start = max(0, issue.line_number - 3)
                    end = min(len(file_lines), issue.line_number + 2)
                    context = file_lines[start:end]
                    lines.append("Context:")
                    for i, ctx_line in enumerate(context, start=start + 1):
                        prefix = ">>>" if i == issue.line_number else "   "
                        lines.append(f"{prefix} {i:4d}: {ctx_line.rstrip()}")
                lines.append("-" * 20)
        return "\n".join(lines)

    # --------------------------------------------------------------------------- internal
    @staticmethod
    def _resolve_threshold(config: CodeConCatConfig) -> SecuritySeverity:
        """Return the severity threshold as :class:`SecuritySeverity`."""
        if isinstance(config.security_scan_severity_threshold, SecuritySeverity):
            return config.security_scan_severity_threshold
        try:
            return SecuritySeverity[config.security_scan_severity_threshold.upper()]
        except KeyError:
            logger.error(
                "Invalid security_scan_severity_threshold '%s'; defaulting to MEDIUM.",
                config.security_scan_severity_threshold,
            )
            return SecuritySeverity.MEDIUM
