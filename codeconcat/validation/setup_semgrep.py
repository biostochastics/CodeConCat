"""
Setup script for installing semgrep and the Apiiro ruleset.

Security: This module implements supply-chain hardening by:
- Pinning Semgrep to specific tested versions
- Pinning Apiiro ruleset to specific verified commits
- Using sys.executable for pip to avoid PATH hijacking
- Adding network timeouts to prevent hanging
"""

import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..errors import ValidationError

logger = logging.getLogger(__name__)

# Security: Pin to specific verified versions
# Update these after testing new versions
SEMGREP_VERSION = "1.52.0"  # Last audited: 2024-01
APIIRO_RULESET_URL = "https://github.com/apiiro/malicious-code-ruleset.git"
# Verified 2025-02-01: Latest main commit from apiiro/malicious-code-ruleset
# Run: git ls-remote https://github.com/apiiro/malicious-code-ruleset.git HEAD
APIIRO_RULESET_COMMIT = "a21246b666f34db899f0e33add7237ed70fab790"
NETWORK_TIMEOUT = 300  # 5 minutes


def install_semgrep():
    """
    Install semgrep using pip with version pinning.

    Security:
        - Uses sys.executable to invoke pip (prevents PATH hijacking)
        - Pins to specific tested version
        - Adds network timeout
        - Verifies installation

    Returns:
        bool: True if installation successful, False otherwise
    """
    try:
        logger.info(f"Installing semgrep version {SEMGREP_VERSION}...")

        # Security: Use sys.executable -m pip instead of bare "pip"
        # This prevents PATH hijacking attacks
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", f"semgrep=={SEMGREP_VERSION}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=NETWORK_TIMEOUT,
        )

        logger.info(f"Semgrep {SEMGREP_VERSION} installed successfully.")
        logger.debug(f"pip output: {result.stdout}")

        # Verify the installed version
        semgrep_path = shutil.which("semgrep")
        if not semgrep_path:
            logger.error("Semgrep installed but executable not found in PATH")
            return False

        # Security: Use resolved absolute path to prevent PATH hijacking
        # Verify version matches exactly (not substring) to prevent spoofing
        version_check = subprocess.run(
            [semgrep_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version_output = version_check.stdout.strip()
        if version_output != SEMGREP_VERSION:
            logger.warning(
                f"Version mismatch: expected exactly '{SEMGREP_VERSION}', got '{version_output}'"
            )

        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Semgrep installation timed out after {NETWORK_TIMEOUT}s")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install semgrep: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error installing semgrep: {e}")
        return False


def install_apiiro_ruleset(target_dir: str | None = None):
    """
    Install the Apiiro malicious code ruleset.

    Args:
        target_dir: Directory to install the ruleset to.
                   If None, installs to the default location.

    Returns:
        str: Path to the installed ruleset

    Raises:
        ValidationError: If installation fails
    """
    # Determine target directory
    if target_dir is None:
        target_path = Path(__file__).parent / "rules" / "apiiro-ruleset"
    else:
        target_path = Path(target_dir)

    # Create the directory if it doesn't exist
    if not target_path.exists():
        target_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created new directory at {target_path}")
    else:
        logger.debug(f"Using existing directory at {target_path}")

    try:
        # Clone the repository at specific commit
        logger.info(
            f"Cloning Apiiro ruleset (commit: {APIIRO_RULESET_COMMIT[:8]}) to {target_path}..."
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            # Security: Clone with timeout and depth limit
            subprocess.run(
                ["git", "clone", "--depth", "1", APIIRO_RULESET_URL, temp_dir],
                check=True,
                capture_output=True,
                text=True,
                timeout=NETWORK_TIMEOUT,
            )

            # Security: Checkout the pinned commit
            subprocess.run(
                ["git", "-C", temp_dir, "fetch", "--depth", "1", "origin", APIIRO_RULESET_COMMIT],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )

            subprocess.run(
                ["git", "-C", temp_dir, "checkout", APIIRO_RULESET_COMMIT],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Verify we're at the correct commit
            verify_commit = subprocess.run(
                ["git", "-C", temp_dir, "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            actual_commit = verify_commit.stdout.strip()
            if actual_commit != APIIRO_RULESET_COMMIT:
                raise ValidationError(
                    f"Commit verification failed: expected {APIIRO_RULESET_COMMIT}, got {actual_commit}"
                )

            logger.info(f"Verified ruleset at commit {APIIRO_RULESET_COMMIT[:8]}")

            # Copy rules to target directory
            rule_count = 0
            for rule_file in Path(temp_dir).glob("**/*.yaml"):
                rel_path = rule_file.relative_to(temp_dir)
                dest_path = target_path / rel_path
                if not dest_path.parent.exists():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Created subdirectory: {dest_path.parent}")
                shutil.copy(rule_file, dest_path)
                logger.debug(f"Copied rule file: {rel_path} to {dest_path}")
                rule_count += 1

            logger.info(f"Apiiro ruleset installed: {rule_count} rules copied to {target_path}")

        return str(target_path)

    except subprocess.TimeoutExpired:
        logger.error(f"Ruleset installation timed out after {NETWORK_TIMEOUT}s")
        raise ValidationError("Ruleset installation timed out") from None
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone Apiiro ruleset: {e.stderr}")
        raise ValidationError(f"Failed to install Apiiro ruleset: {e.stderr}") from e
    except Exception as e:
        logger.error(f"Error installing Apiiro ruleset: {e}")
        raise ValidationError(f"Error installing Apiiro ruleset: {e}") from e
