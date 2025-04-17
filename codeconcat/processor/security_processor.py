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
from typing import Dict, List, Tuple

from ..base_types import (
    CodeConCatConfig,
    CustomSecurityPattern,
    SecurityIssue,
    SecuritySeverity,
)

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
    _AWS_SECRET_KEY_REGEX = "(?i)\\baws[_\\-\\s]+secret[_\\-\\s]+(?:access[_\\-\\s]+)?key[\"\\s:=]+[\"]?([A-Za-z0-9/+=]{40})[\"\\s]?"
    _GENERIC_API_KEY_REGEX = "(?i)\\b(?:api[_\\-\\s]*key|key[_\\-\\s]*id|secret[_\\-\\s]*key)[\"'\\s:=]+[\"']?([a-zA-Z0-9\\-._/+=]{8,})[\"']?"
    _GENERIC_PASSWORD_REGEX = "(?i)\\b(?:password|pwd|pass)['\"\\s:=]+['\"]?([a-zA-Z0-9!@#$%^&*()_\\+-]{8,})['\"]?"
    _AWS_SESSION_TOKEN_REGEX = "(?i)aws_session_token[\"\\s:=]+[\"]?([A-Za-z0-9/+=]{16,})[\"\\s]?"

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
        )
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
    _INLINE_IGNORE_PATTERN: re.Pattern[str] = re.compile(
        r"(?:#|//)\s*(?:nosec|codeconcat-ignore-security)\b", re.IGNORECASE
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
    ) -> List[SecurityIssue]:
        """Scan *content* and return a list of :class:`SecurityIssue` objects.

        The method respects *config* settings such as ignore lists and severity
        threshold.  The *file_path* is only used for reporting and for ignore
        matching; it **is not** read from disk.
        """
        if not config.enable_security_scanning:
            return []

        # Resolve path early so downstream helpers can rely on a valid :class:`Path`.
        try:
            abs_path = Path(file_path).expanduser().resolve()
        except Exception:  # pylint: disable=broad-except
            logger.warning(
                "Could not resolve absolute path for '%s'; falling back to the "
                "provided string.",
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

        for idx, line in enumerate(content.splitlines()):  # ``idx`` is zero‑based.
            lineno = idx + 1

            if cls._should_skip_line(idx, content.splitlines()):
                continue

            for rule_name, (pattern, issue_type, default_sev) in compiled_patterns.items():
                for match in pattern.finditer(line):
                    try:
                        group_index = 1 if pattern.groups >= 1 and match.group(1) is not None else 0
                        raw_finding = match.group(group_index)
                        start_col, _ = match.span(group_index)
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
                        masked_finding = cls._get_masked_finding(raw_finding)
                        issue = SecurityIssue(
                            rule_id=rule_name,
                            description=f"Potential {issue_type} detected.",
                            file_path=str(abs_path),
                            line_number=lineno,
                            severity=current_severity,
                            context=line.strip(),
                        )
                        issues.append(issue)
                    except IndexError:
                        pass
                    except Exception as exc:  # pylint: disable=broad-except
                        logger.warning("Failed to process match: %s", exc, exc_info=True)
                        pass

        return issues

    # ----------------------------------------------------------------------------------
    # Internal helpers -------------------------------------------------------------------
    # ----------------------------------------------------------------------------------
    @classmethod
    def _compile_patterns(
        cls, config: CodeConCatConfig
    ) -> Dict[str, Tuple[re.Pattern[str], str, SecuritySeverity]]:
        """Return merged dict of compiled built‑in and custom patterns."""
        compiled: Dict[str, Tuple[re.Pattern[str], str, SecuritySeverity]] = {}

        # --- Compile Built-in Patterns ---
        for name, (raw_regex, issue_type, severity) in cls._RAW_BUILT_IN_PATTERNS.items():
            try:
                compiled[name] = (re.compile(raw_regex), issue_type, severity)
            except re.error as exc:
                logger.error(
                    "Failed to compile built-in security pattern '%s': %s", name, exc
                )

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
                    "Failed to compile custom security pattern '%s': %s", custom.name, exc
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
                    fnmatch.fnmatch(parent.as_posix(), normalized)
                    for parent in abs_path.parents
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
        """Helper handling inline ``# nosec`` style comments on *line_idx* or previous."""
        if cls._has_inline_ignore(lines[line_idx]):
            return True
        if line_idx > 0 and cls._has_inline_ignore(lines[line_idx - 1]):
            return True
        return False

    @classmethod
    def _has_inline_ignore(cls, line: str) -> bool:  # noqa: D401 — short helper
        return bool(cls._INLINE_IGNORE_PATTERN.search(line))

    # --------------------------------------------------------------------- severity logic
    @classmethod
    def _determine_severity(
        cls, default: SecuritySeverity, abs_path: Path, config: CodeConCatConfig
    ) -> SecuritySeverity:
        """Return severity, optionally downgrading for test/example files."""
        path_lc = abs_path.as_posix().lower()
        is_test = any(
            token in path_lc
            for token in (
                "/tests/",
                "/test/",
                "/examples/",
                "/example/",
            )
        ) or abs_path.name.startswith("test_") or abs_path.name.endswith(
            (
                "_test.py",
                "_spec.rb",
                ".test.js",
                ".spec.js",
                ".test.ts",
                ".spec.ts",
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
        """Return *line* with the secret portion of *match* hidden."""
        try:
            group_index = 1 if pattern.groups >= 1 and match.group(1) else 0
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
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to mask sensitive data: %s", exc, exc_info=True)
            return line[: match.start()] + "[***MASKED***]" + line[match.end() :]

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
        """Pretty‑print *issues* with respect to *config* threshold."""
        if not issues:
            return "Security Scan Results: No issues found."

        threshold = cls._resolve_threshold(config)
        filtered: List[SecurityIssue] = [
            issue for issue in issues if issue.severity >= threshold
        ]
        if not filtered:
            return (
                "Security Scan Results: No issues found at or above the "
                f"'{threshold.name}' threshold."
            )

        filtered.sort(key=lambda i: (i.severity, i.file_path, i.line_number), reverse=True)

        lines: List[str] = [
            "Security Scan Results:",
            "=" * 20,
            f"Found {len(filtered)} issue(s) at or above the '{threshold.name}' threshold:",
        ]
        for issue in filtered:
            lines.extend(
                [
                    "",
                    f"Severity : {issue.severity.name}",
                    f"Type     : {issue.issue_type}",
                    f"File     : {issue.file_path}",
                    f"Line {issue.line_number}: {issue.line_content.strip()}",
                    f"Description: {issue.description}",
                    "-" * 20,
                ]
            )
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
