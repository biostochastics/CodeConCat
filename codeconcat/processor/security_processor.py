import re
import logging
import fnmatch # For path matching
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Import updated types and config
from ..base_types import SecurityIssue, SecuritySeverity, CodeConCatConfig, CustomSecurityPattern

logger = logging.getLogger(__name__)

class SecurityProcessor:
    # Store patterns as: Dict[RuleName, Tuple[RegexString, IssueTypeName, DefaultSeverity]]
    # Use more specific patterns and add many more common ones.
    BUILT_IN_PATTERNS: Dict[str, Tuple[str, str, SecuritySeverity]] = {
        # Example Refinements & Additions:
        "aws_access_key_id": (
            r'(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])', # More specific AWS Key ID prefix
            "AWS Access Key ID",
            SecuritySeverity.CRITICAL
        ),
        "aws_secret_access_key": (
            # Exclude common examples in variable names / comments
            r'(?i)(?<![a-z])aws[_\-\s]+secret[_\-\s]+(?:access[_\-\s]+)?key(?<!\s*=\s*["\'](?:example|test|dummy|YOUR_))["\'\s:=]+([A-Za-z0-9/+=]{40})',
            "AWS Secret Access Key",
            SecuritySeverity.CRITICAL
        ),
        "generic_api_key": (
            # Avoid simple variable names, look for higher entropy & length
            r'(?i)\b(?:api_?key|apikey|api_?token|apitoken)\b\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            "Generic API Key",
            SecuritySeverity.HIGH # Downgraded slightly from critical without more context
        ),
         "generic_password": (
            # Looks for password assignments, excluding common placeholders
            r'(?i)\b(?:password|passwd|pwd)\b\s*[:=]\s*([\'\"])(?!\1|test|dummy|password|YOUR_PASSWORD).{6,}\1',
            "Generic Password",
            SecuritySeverity.HIGH
        ),
        "private_key_pem": (
             r"-----BEGIN ((EC|RSA|DSA|PGP|OPENSSH)\s+)?PRIVATE KEY-----",
             "Private Key (PEM Format)",
             SecuritySeverity.CRITICAL
        ),
         "github_token": (
             r'(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}', # Common GitHub token prefixes
             "GitHub Token",
             SecuritySeverity.CRITICAL
         ),
         "slack_token": (
              r'xox[pboa]r?-[0-9a-zA-Z]{10,48}',
              "Slack Token",
              SecuritySeverity.CRITICAL
         ),
         # ... Add many more patterns for GCP, Azure, Stripe, Twilio, JWTs, etc. ...
    }

    # Patterns for inline ignores
    INLINE_IGNORE_PATTERN = re.compile(r'(?:#|//)\s*(?:nosec|codeconcat-ignore-security)\b', re.IGNORECASE)

    @classmethod
    def scan_content(cls, content: str, file_path: str, config: CodeConCatConfig) -> List[SecurityIssue]:
        """
        Scans content for potential security issues, respecting configuration.
        """
        # Ensure the config flag is checked using the correct attribute name
        if not config.enable_security_scanning:
            return []

        issues: List[SecurityIssue] = []
        lines = content.split("\n")
        try:
            abs_file_path = Path(file_path).resolve()
        except Exception:
             # Handle cases where file_path might be invalid or non-existent (e.g., during tests with temp names)
             logger.warning(f"Could not resolve absolute path for: {file_path}. Using provided path string.")
             abs_file_path = Path(file_path) # Use the provided path as a fallback Path object

        # 1. Check if file path should be ignored
        if cls._should_ignore_path(abs_file_path, config):
            logger.debug(f"Skipping security scan for ignored path: {file_path}")
            return []

        # 2. Compile all patterns (built-in + custom)
        all_patterns = cls._compile_patterns(config)

        # 3. Iterate through lines
        for line_num_0based, line in enumerate(lines):
            line_num_1based = line_num_0based + 1

            # 3a. Check for inline ignores on this or previous line
            if cls._has_inline_ignore(line) or (line_num_0based > 0 and cls._has_inline_ignore(lines[line_num_0based - 1])):
                continue

            # 3b. Check patterns against the line
            for rule_name, (pattern_obj, issue_type, default_severity) in all_patterns.items():
                for match in pattern_obj.finditer(line):
                    raw_finding = match.group(0) # Or a specific group if needed

                    # 3c. Check if the finding itself should be ignored
                    if cls._should_ignore_finding(raw_finding, config):
                        continue

                    # 3d. Determine severity (apply context if needed)
                    # Pass the original file_path string as well for reporting
                    severity = cls._determine_severity(default_severity, abs_file_path, config)

                    # 3e. Check severity threshold (using the validated min_severity from config)
                    if severity < config.min_severity:
                        continue

                    # 3f. Mask and create issue
                    masked_line = cls._mask_sensitive_data(line, pattern_obj, match)

                    # Avoid duplicate reporting for the same finding on the same line
                    # (Simple check: could be more sophisticated)
                    is_duplicate = any(
                        iss.line_number == line_num_1based and iss.issue_type == issue_type and iss.raw_finding == raw_finding and iss.file_path == file_path
                        for iss in issues
                    )
                    if not is_duplicate:
                        issues.append(
                            SecurityIssue(
                                line_number=line_num_1based,
                                line_content=masked_line,
                                issue_type=issue_type,
                                severity=severity,
                                description=f"Potential {issue_type} detected (Rule: {rule_name}).", # Add Rule name
                                file_path=file_path, # Use the original file_path string
                                raw_finding=raw_finding # Store the actual matched finding
                            )
                        )
        return issues

    @classmethod
    def _compile_patterns(cls, config: CodeConCatConfig) -> Dict[str, Tuple[re.Pattern, str, SecuritySeverity]]:
        """Compiles built-in and custom regex patterns."""
        compiled = {}
        # Built-in
        for name, (regex_str, issue_type, severity) in cls.BUILT_IN_PATTERNS.items():
            try:
                compiled[name] = (re.compile(regex_str), issue_type, severity)
            except re.error as e:
                logger.error(f"Invalid built-in security pattern '{name}': {e}")
        # Custom
        for custom in config.security_custom_patterns:
            # Ensure custom is the dataclass instance after validation in config
            if not isinstance(custom, CustomSecurityPattern):
                 logger.error(f"Skipping invalid custom security pattern structure: {custom}")
                 continue
            if custom.name in compiled:
                 logger.warning(f"Custom security pattern '{custom.name}' overrides a built-in pattern.")
            try:
                severity = SecuritySeverity[custom.severity.upper()]
                compiled[custom.name] = (re.compile(custom.regex), custom.name, severity) # Use custom name as issue type
            except re.error as e:
                 logger.error(f"Failed to compile custom security pattern '{custom.name}': {e}")
            except KeyError:
                 # This should ideally be caught by config validation, but double-check
                 logger.error(f"Invalid severity in custom security pattern '{custom.name}': {custom.severity}")

        return compiled

    @classmethod
    def _should_ignore_path(cls, abs_path: Path, config: CodeConCatConfig) -> bool:
        """Checks if the file path matches any ignore glob patterns."""
        # Convert to string and normalize slashes for consistent matching
        path_str = str(abs_path).replace("\\", "/")
        for pattern in config.security_ignore_paths:
             # Ensure pattern is treated as a glob pattern
             # fnmatch handles OS path separators differences to some extent
             if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(abs_path.name, pattern):
                 return True
             # More robust check: walk up the path parts
             # Convert pattern to use '/' if needed for consistency with path_str
             normalized_pattern = pattern.replace("\\", "/")
             try:
                # Check if any parent directory matches the pattern using glob-style matching
                if any(fnmatch.fnmatch(str(p).replace("\\", "/"), normalized_pattern) for p in abs_path.parents):
                    return True
                # Also check relative path components if pattern doesn't start with '/' or drive letter
                if not normalized_pattern.startswith(('/', '*')) and not re.match(r'[a-zA-Z]:', normalized_pattern):
                     if any(fnmatch.fnmatch(part, normalized_pattern) for part in abs_path.parts):
                         return True
             except Exception as e:
                 logger.warning(f"Error matching ignore path pattern '{pattern}' against '{path_str}': {e}")

        return False

    @classmethod
    def _should_ignore_finding(cls, finding: str, config: CodeConCatConfig) -> bool:
        """Checks if the specific finding matches any ignore regex patterns."""
        for pattern_str in config.security_ignore_patterns:
            try:
                if re.search(pattern_str, finding):
                    return True
            except re.error as e: # Catch regex compilation errors
                logger.warning(f"Invalid regex in security_ignore_patterns: '{pattern_str}'. Error: {e}")
        return False

    @classmethod
    def _has_inline_ignore(cls, line: str) -> bool:
        """Checks for inline ignore comments."""
        return bool(cls.INLINE_IGNORE_PATTERN.search(line))

    @classmethod
    def _determine_severity(cls, default_severity: SecuritySeverity, abs_path: Path, config: CodeConCatConfig) -> SecuritySeverity:
        """Adjusts severity based on context (e.g., test files)."""
        # Example: Downgrade severity if in a 'test' or 'example' directory/file
        path_str = str(abs_path).lower().replace("\\", "/")
        is_test_or_example = (
            "/tests/" in path_str or
            "/test/" in path_str or
            "/examples/" in path_str or
            "/example/" in path_str or
            abs_path.name.startswith("test_") or
            abs_path.name.endswith(("_test.py", "_spec.rb", ".test.js", ".spec.js", ".test.ts", ".spec.ts"))
            # Add more common test file patterns if needed
        )

        if is_test_or_example:
            if default_severity == SecuritySeverity.CRITICAL:
                return SecuritySeverity.HIGH
            if default_severity == SecuritySeverity.HIGH:
                return SecuritySeverity.MEDIUM
            if default_severity == SecuritySeverity.MEDIUM:
                 return SecuritySeverity.LOW
            # LOW and INFO remain as they are

        return default_severity

    @staticmethod
    def _mask_sensitive_data(line: str, pattern_obj: re.Pattern, match: re.Match) -> str:
        """Masks the sensitive part found by the regex match in the line."""
        try:
            # Try to mask only the first captured group if it exists and is non-empty,
            # otherwise mask the whole match.
            sensitive_group_index = 1 # Default to first capture group
            if pattern_obj.groups >= sensitive_group_index and match.group(sensitive_group_index):
                 start, end = match.span(sensitive_group_index)
                 finding = match.group(sensitive_group_index)
            else: # Fallback to whole match (group 0)
                 start, end = match.span(0)
                 finding = match.group(0)

            # Basic masking: show first/last few chars
            mask_len = len(finding)
            if mask_len == 0: # Should not happen with valid match, but handle defensively
                return line
            elif mask_len > 8:
                masked_finding = finding[:3] + "****" + finding[-3:]
            elif mask_len > 4:
                 masked_finding = finding[:2] + "****" + finding[-2:]
            elif mask_len > 2:
                 masked_finding = finding[0] + "****" + finding[-1]
            else:
                 masked_finding = "****"

            # Replace the identified part (group 1 or group 0) in the original line
            return line[:start] + masked_finding + line[end:]
        except Exception as e:
             logger.warning(f"Error masking sensitive data: {e}. Falling back to generic mask.", exc_info=True)
             # Fallback if masking logic fails: mask the entire matched span
             return line[:match.start()] + "[***MASKED***]" + line[match.end():]

    @classmethod
    def format_issues(cls, issues: List[SecurityIssue], config: CodeConCatConfig) -> str:
        """ Formats the list of security issues into a readable string. """
        if not issues:
            return "Security Scan Results: No issues found above threshold."

        formatted = ["Security Scan Results:", "=" * 20]
        # Sort by severity (descending), then file_path, then line number
        issues.sort(key=lambda x: (x.severity, x.file_path, x.line_number), reverse=True)

        count = 0
        for issue in issues:
            # Final check against the threshold (should be redundant if filtering works correctly)
            if issue.severity >= config.min_severity:
                count += 1
                formatted.extend([
                     f"\nSeverity: {issue.severity.name}", # Display severity name
                     f"Type: {issue.issue_type}",
                     f"File: {issue.file_path}",
                     f"Line {issue.line_number}: {issue.line_content.strip()}", # Show masked line
                     # Optionally show raw finding if needed for debugging/context, but be careful!
                     # f"Finding: {issue.raw_finding}",
                     f"Description: {issue.description}",
                     "-" * 20,
                ])

        if count == 0:
            return f"Security Scan Results: No issues found at or above the '{config.min_severity.name}' threshold."
        else:
            formatted.insert(1, f"Found {count} issue(s) at or above the '{config.min_severity.name}' threshold:")
            return "\n".join(formatted)
