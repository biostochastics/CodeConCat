"""
Setup script for installing semgrep and the Apiiro ruleset.
"""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..errors import ValidationError

logger = logging.getLogger(__name__)

# Constants
APIIRO_RULESET_URL = "https://github.com/apiiro/malicious-code-ruleset.git"


def install_semgrep():
    """
    Install semgrep using pip.

    Returns:
        bool: True if installation successful, False otherwise

    Raises:
        ValidationError: If installation fails
    """
    try:
        logger.info("Installing semgrep...")
        subprocess.run(["pip", "install", "semgrep"], check=True, capture_output=True, text=True)

        logger.info("Semgrep installed successfully.")
        # Find the installed semgrep path
        import shutil

        semgrep_path = shutil.which("semgrep")
        if not semgrep_path:
            logger.error("Semgrep installed but executable not found in PATH")
            return False
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install semgrep: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error installing semgrep: {e}")
        return False


def install_apiiro_ruleset(target_dir: str = None):
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
        target_dir = Path(__file__).parent / "rules" / "apiiro-ruleset"
    else:
        target_dir = Path(target_dir)

    # Create the directory if it doesn't exist
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created new directory at {target_dir}")
    else:
        logger.debug(f"Using existing directory at {target_dir}")

    try:
        # Clone the repository
        logger.info(f"Cloning Apiiro ruleset to {target_dir}...")
        with tempfile.TemporaryDirectory() as temp_dir:
            subprocess.run(
                ["git", "clone", APIIRO_RULESET_URL, temp_dir],
                check=True,
                capture_output=True,
                text=True,
            )

            # Copy rules to target directory
            for rule_file in Path(temp_dir).glob("**/*.yaml"):
                rel_path = rule_file.relative_to(temp_dir)
                dest_path = target_dir / rel_path
                if not dest_path.parent.exists():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Created subdirectory: {dest_path.parent}")
                shutil.copy(rule_file, dest_path)
                logger.debug(f"Copied rule file: {rel_path} to {dest_path}")

        logger.info(f"Apiiro ruleset installed to {target_dir}")
        return str(target_dir)

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone Apiiro ruleset: {e.stderr}")
        raise ValidationError(f"Failed to install Apiiro ruleset: {e.stderr}")
    except Exception as e:
        logger.error(f"Error installing Apiiro ruleset: {e}")
        raise ValidationError(f"Error installing Apiiro ruleset: {e}")
