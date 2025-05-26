"""
Semgrep-based security validation for code.

This module uses semgrep to scan code files for security issues using
the Apiiro malicious code ruleset.
"""

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..errors import ValidationError

logger = logging.getLogger(__name__)


class SemgrepValidator:
    """Validator that uses semgrep to scan code for security issues."""

    def __init__(self, ruleset_path: Optional[str] = None):
        """
        Initialize the semgrep validator.

        Args:
            ruleset_path: Optional path to the ruleset directory or YAML file.
                          If None, will use the bundled/installed ruleset.
        """
        self.semgrep_path = shutil.which("semgrep")
        if not self.semgrep_path:
            logger.warning("Semgrep not found in PATH. Security scanning will be disabled.")

        self.ruleset_path = ruleset_path or self._get_default_ruleset_path()

    def _get_default_ruleset_path(self) -> str:
        """Get the path to the default ruleset."""
        # First check if we have a bundled ruleset
        bundled_path = Path(__file__).parent / "rules" / "apiiro-ruleset"
        if bundled_path.exists():
            return str(bundled_path)

        # Otherwise, return a path to the official GitHub repo
        return "https://github.com/apiiro/malicious-code-ruleset"

    def is_available(self) -> bool:
        """Check if semgrep is available."""
        return self.semgrep_path is not None

    def scan_file(self, file_path: Union[str, Path], language: Optional[str] = None) -> List[Dict]:
        """
        Scan a file for security issues using semgrep.

        Args:
            file_path: Path to the file to scan
            language: Optional language override

        Returns:
            List of findings as dictionaries

        Raises:
            ValidationError: If semgrep is not installed or scan fails
        """
        if not self.is_available():
            raise ValidationError("Semgrep is not installed. Cannot scan for security issues.")

        file_path = Path(file_path)
        if not file_path.exists():
            raise ValidationError(f"File does not exist: {file_path}")

        # Determine language if not provided
        if not language:
            language = self._detect_language(file_path)
            if not language:
                logger.debug(f"Could not determine language for {file_path}. Skipping scan.")
                return []

        # Run semgrep
        with tempfile.TemporaryDirectory() as temp_dir:
            # Prepare command
            cmd = [
                self.semgrep_path,
                "--config",
                self.ruleset_path,
            ]

            # Add custom rules if they exist
            custom_rules_path = Path(__file__).parent / "rules" / "custom_security_rules.yaml"
            if custom_rules_path.exists():
                cmd.extend(["--config", str(custom_rules_path)])

            cmd.extend(["--json", "--output", f"{temp_dir}/results.json", str(file_path)])

            # Add language filter if provided
            if language:
                cmd.extend(["--lang", language])

            try:
                # Run semgrep
                logger.debug(f"Running semgrep: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,  # Don't raise an exception on non-zero exit
                )

                # Check for errors - exit code 1 is actually OK (findings found)
                if result.returncode != 0 and result.returncode != 1:
                    logger.error(f"Semgrep error: {result.stderr}")
                    raise ValidationError(f"Semgrep scan failed: {result.stderr}")

                # Parse results
                results_file = Path(f"{temp_dir}/results.json")
                if results_file.exists():
                    with open(results_file, "r") as f:
                        scan_results = json.load(f)

                    # Extract findings
                    findings = []
                    for result in scan_results.get("results", []):
                        findings.append(
                            {
                                "type": "semgrep",
                                "rule_id": result.get("check_id", "unknown"),
                                "message": result.get("extra", {}).get("message", "Unknown issue"),
                                "severity": result.get("extra", {}).get("severity", "WARNING"),
                                "line": result.get("start", {}).get("line", 0),
                                "column": result.get("start", {}).get("col", 0),
                                "path": result.get("path", str(file_path)),
                                "snippet": result.get("extra", {}).get("lines", ""),
                            }
                        )

                    return findings

                return []

            except Exception as e:
                logger.error(f"Error running semgrep: {e}")
                raise ValidationError(f"Failed to scan file with semgrep: {e}")

    def scan_directory(
        self, directory: Union[str, Path], languages: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Scan a directory for security issues.

        Args:
            directory: Path to the directory to scan
            languages: Optional list of languages to scan

        Returns:
            Dictionary mapping file paths to lists of findings
        """
        if not self.is_available():
            logger.warning("Semgrep is not installed. Cannot scan for security issues.")
            return {}

        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            raise ValidationError(f"Directory does not exist: {directory}")

        # Run semgrep on the directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Prepare command
            cmd = [
                self.semgrep_path,
                "--config",
                self.ruleset_path,
                "--json",
                "--output",
                f"{temp_dir}/results.json",
                str(directory),
            ]

            # Add language filter if provided
            if languages:
                for lang in languages:
                    cmd.extend(["--lang", lang])

            try:
                # Run semgrep
                logger.debug(f"Running semgrep: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,  # Don't raise an exception on non-zero exit
                )

                # Check for errors
                if result.returncode != 0 and result.returncode != 1:  # 1 means findings were found
                    logger.error(f"Semgrep error: {result.stderr}")
                    raise ValidationError(f"Semgrep scan failed: {result.stderr}")

                # Parse results
                results_file = Path(f"{temp_dir}/results.json")
                if results_file.exists():
                    with open(results_file, "r") as f:
                        scan_results = json.load(f)

                    # Group findings by file
                    findings_by_file = {}
                    for result in scan_results.get("results", []):
                        file_path = result.get("path", "unknown")
                        if file_path not in findings_by_file:
                            findings_by_file[file_path] = []

                        findings_by_file[file_path].append(
                            {
                                "type": "semgrep",
                                "rule_id": result.get("check_id", "unknown"),
                                "message": result.get("extra", {}).get("message", "Unknown issue"),
                                "severity": result.get("extra", {}).get("severity", "WARNING"),
                                "line": result.get("start", {}).get("line", 0),
                                "column": result.get("start", {}).get("col", 0),
                                "snippet": result.get("extra", {}).get("lines", ""),
                            }
                        )

                    return findings_by_file

                return {}

            except Exception as e:
                logger.error(f"Error running semgrep: {e}")
                raise ValidationError(f"Failed to scan directory with semgrep: {e}")

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """
        Detect the language of a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name as expected by semgrep, or None if unknown
        """
        # Local import to avoid circular imports
        from ..parser.file_parser import determine_language

        # Map CodeConCat language names to semgrep language identifiers
        language_to_semgrep = {
            "python": "python",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "go": "go",
            "ruby": "ruby",
            "php": "php",
            "c": "c",
            "cpp": "cpp",
            "csharp": "csharp",
            "scala": "scala",
            "kotlin": "kotlin",
            "rust": "rust",
        }

        language = determine_language(str(file_path))
        return language_to_semgrep.get(language)


# Create a singleton instance
semgrep_validator = SemgrepValidator()
