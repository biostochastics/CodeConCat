"""
Async Semgrep-based security validation for code.

This module uses semgrep to scan code files for security issues using
the Apiiro malicious code ruleset with async subprocess execution.
"""

import asyncio
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..errors import ValidationError
from ..utils.path_security import validate_safe_path

logger = logging.getLogger(__name__)


class AsyncSemgrepValidator:
    """Async validator that uses semgrep to scan code for security issues."""

    def __init__(self, ruleset_path: Optional[str] = None):
        """
        Initialize the async semgrep validator.

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

    async def scan_file(
        self, file_path: Union[str, Path], language: Optional[str] = None
    ) -> List[Dict]:
        """
        Scan a file for security issues using semgrep asynchronously.

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

        # Validate path for security
        file_path = validate_safe_path(file_path)
        if not file_path.exists():
            raise ValidationError(f"File does not exist: {file_path}")

        # Determine language if not provided
        if not language:
            language = self._detect_language(file_path)
            if not language:
                logger.debug(f"Could not determine language for {file_path}. Skipping scan.")
                return []

        # Run semgrep asynchronously
        with tempfile.TemporaryDirectory() as temp_dir:
            # Prepare command - ensure semgrep_path is not None
            assert self.semgrep_path is not None, (
                "semgrep_path should not be None after is_available() check"
            )
            cmd = [
                self.semgrep_path,
                "--config",
                self.ruleset_path,
            ]

            # Add custom rules if they exist
            custom_rules_path = Path(__file__).parent / "rules" / "custom_security_rules.yaml"
            if custom_rules_path.exists():
                cmd.extend(["--config", str(custom_rules_path)])

            # Use validated safe path
            cmd.extend(["--json", "--output", f"{temp_dir}/results.json", str(file_path)])

            # Add language filter if provided
            if language:
                cmd.extend(["--lang", language])

            try:
                # Run semgrep asynchronously
                logger.debug(f"Running semgrep async: {' '.join(cmd)}")

                # Create subprocess
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                # Wait for completion with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=120.0,  # 2 minute timeout
                    )
                except asyncio.TimeoutError as e:
                    process.kill()
                    await process.wait()
                    raise ValidationError("Semgrep scan timed out after 120 seconds") from e

                # Check for errors - exit code 1 is actually OK (findings found)
                if process.returncode not in (0, 1):
                    logger.error(f"Semgrep error: {stderr.decode('utf-8', errors='replace')}")
                    raise ValidationError(
                        f"Semgrep scan failed: {stderr.decode('utf-8', errors='replace')}"
                    )

                # Parse results
                results_file = Path(f"{temp_dir}/results.json")
                if results_file.exists():
                    with open(results_file) as f:
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
                raise ValidationError(f"Failed to scan file with semgrep: {e}") from e

    async def scan_directory(
        self, directory: Union[str, Path], languages: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Scan a directory for security issues asynchronously.

        Args:
            directory: Path to the directory to scan
            languages: Optional list of languages to scan

        Returns:
            Dictionary mapping file paths to lists of findings
        """
        if not self.is_available():
            logger.warning("Semgrep is not installed. Cannot scan for security issues.")
            return {}

        # Validate path for security
        directory = validate_safe_path(directory)
        if not directory.exists() or not directory.is_dir():
            raise ValidationError(f"Directory does not exist: {directory}")

        # Run semgrep on the directory asynchronously
        with tempfile.TemporaryDirectory() as temp_dir:
            # Prepare command - ensure semgrep_path is not None
            assert self.semgrep_path is not None, (
                "semgrep_path should not be None after is_available() check"
            )
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
                # Run semgrep asynchronously
                logger.debug(f"Running semgrep async: {' '.join(cmd)}")

                # Create subprocess
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                # Wait for completion with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=300.0,  # 5 minute timeout for directories
                    )
                except asyncio.TimeoutError as e:
                    process.kill()
                    await process.wait()
                    raise ValidationError("Semgrep scan timed out after 300 seconds") from e

                # Check for errors
                if process.returncode not in (0, 1):  # 1 means findings were found
                    logger.error(f"Semgrep error: {stderr.decode('utf-8', errors='replace')}")
                    raise ValidationError(
                        f"Semgrep scan failed: {stderr.decode('utf-8', errors='replace')}"
                    )

                # Parse results
                results_file = Path(f"{temp_dir}/results.json")
                if results_file.exists():
                    with open(results_file) as f:
                        scan_results = json.load(f)

                    # Group findings by file
                    findings_by_file: Dict[str, List[Dict]] = {}
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
                raise ValidationError(f"Failed to scan directory with semgrep: {e}") from e

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """
        Detect the language of a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name as expected by semgrep, or None if unknown
        """
        # Local import to avoid circular imports
        from ..parser.unified_pipeline import determine_language

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
        if language is None:
            return None
        return language_to_semgrep.get(language)


# Create a singleton instance
async_semgrep_validator = AsyncSemgrepValidator()
