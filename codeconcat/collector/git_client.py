"""Git client for handling repository operations.

This module provides a unified GitClient class that encapsulates all Git operations
including cloning, fetching, and checking out repositories. It supports both synchronous
and asynchronous operations while maintaining security best practices.
"""

import asyncio
import logging
import os
import re
import subprocess

from codeconcat.processor.security_processor import SecurityProcessor

logger = logging.getLogger(__name__)


class GitURLParser:
    """Parser for Git URLs and shorthand notations."""

    @staticmethod
    def parse(url: str) -> tuple[str, str, str | None]:
        """Parse Git URL or shorthand into owner, repo, and potentially ref.

        Args:
            url: Git repository URL or shorthand (e.g., owner/repo).

        Returns:
            Tuple of (owner, repo, ref) where ref may be None.

        Raises:
            ValueError: If URL format is invalid.
        """
        # Handle GitHub shorthand notation (owner/repo or owner/repo/ref)
        if "/" in url and not url.startswith(("http", "git@")):
            parts = url.split("/")
            if len(parts) >= 2:
                owner = parts[0]
                repo = parts[1].replace(".git", "")  # Remove .git if present
                ref = (
                    "/".join(parts[2:]) if len(parts) > 2 else None
                )  # Join remaining parts for ref
                logger.debug(f"Parsed shorthand: owner={owner}, repo={repo}, ref={ref}")
                return owner, repo, ref

        # Handle full HTTPS/SSH URLs (basic parsing)
        # Example: https://github.com/owner/repo.git
        # Example: git@github.com:owner/repo.git
        # Example: https://github.com/owner/repo/tree/branch/or/tag
        match_https = re.match(
            r"https?://(?:www\.)?github\.com/([^/]+)/([^/\.]+)(?:\.git)?(?:/tree/([^/]+))?", url
        )
        match_ssh = re.match(r"git@github\.com:([^/]+)/([^/\.]+)(?:\.git)?", url)

        if match_https:
            owner, repo, ref = match_https.group(1), match_https.group(2), match_https.group(3)
            logger.debug(f"Parsed HTTPS URL: owner={owner}, repo={repo}, ref={ref}")
            return owner, repo, ref
        if match_ssh:
            owner, repo = match_ssh.group(1), match_ssh.group(2)
            ref = None  # Ref isn't typically in the base SSH URL
            logger.debug(f"Parsed SSH URL: owner={owner}, repo={repo}, ref={ref}")
            return owner, repo, ref

        raise ValueError(
            "Invalid Git URL or shorthand. Use formats like 'owner/repo', 'owner/repo/branch', "
            "'https://github.com/owner/repo', 'git@github.com:owner/repo.git'"
        )


class GitClient:
    """Client for Git repository operations with security features."""

    def __init__(self, token: str | None = None):
        """Initialize GitClient with optional authentication token.

        Args:
            token: GitHub personal access token for private repositories.
        """
        self.token = token

    def build_clone_url(self, url: str, owner: str, repo: str) -> str:  # noqa: ARG002
        """Build GitHub clone URL with optional token authentication.

        Args:
            url: Original URL (used for reference).
            owner: Repository owner.
            repo: Repository name.

        Returns:
            HTTPS URL suitable for cloning, with token if available.
        """
        # Sanitize owner and repo names to prevent injection
        safe_owner = SecurityProcessor.sanitize_command_arg(owner)
        safe_repo = SecurityProcessor.sanitize_command_arg(repo)

        # Always construct a standard HTTPS URL for cloning
        base_url = f"https://github.com/{safe_owner}/{safe_repo}.git"

        if self.token:
            # Sanitize token to prevent injection
            safe_token = SecurityProcessor.sanitize_command_arg(self.token)
            # Insert token into URL for authentication
            return base_url.replace("https://", f"https://{safe_token}@")
        return base_url

    async def run_command_async(
        self, command: list[str], cwd: str | None = None, timeout: float = 120.0
    ) -> tuple[int, str, str]:
        """Run a git command asynchronously with proper error handling.

        Args:
            command: Command and arguments to run.
            cwd: Working directory for the command.
            timeout: Maximum time to wait for command completion.

        Returns:
            Tuple of (return_code, stdout, stderr).
        """
        try:
            logger.debug(f"Running async git command: {' '.join(command)}")

            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *command, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                return_code = process.returncode
            except asyncio.TimeoutError:
                logger.error(f"Git command timed out after {timeout} seconds")
                process.kill()
                await process.wait()
                return -1, "", f"Command timed out after {timeout} seconds"

            stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""

            return return_code or 0, stdout_text, stderr_text

        except (OSError, asyncio.TimeoutError, UnicodeDecodeError) as e:
            logger.error(f"Error running git command: {e}")
            return -1, "", str(e)

    def run_command_sync(
        self, command: list[str], cwd: str | None = None, timeout: float = 120.0
    ) -> tuple[int, str, str]:
        """Run a git command synchronously.

        Args:
            command: Command and arguments to run.
            cwd: Working directory for the command.
            timeout: Maximum time to wait for command completion.

        Returns:
            Tuple of (return_code, stdout, stderr).
        """
        try:
            logger.debug(f"Running sync git command: {' '.join(command)}")
            result = subprocess.run(
                command, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timed out after {timeout} seconds")
            return -1, "", f"Command timed out after {timeout} seconds"
        except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as e:
            logger.error(f"Error running git command: {e}")
            return -1, "", str(e)

    async def clone_async(self, url: str, owner: str, repo: str, ref: str, temp_dir: str) -> bool:
        """Clone a repository asynchronously.

        Args:
            url: Original repository URL.
            owner: Repository owner.
            repo: Repository name.
            ref: Branch, tag, or commit to checkout.
            temp_dir: Directory to clone into.

        Returns:
            True if successful, False otherwise.
        """
        # Validate temp_dir path for security
        safe_temp_dir = SecurityProcessor.validate_path(os.getcwd(), temp_dir)

        clone_url = self.build_clone_url(url, owner, repo)
        logger.info(f"Attempting to clone from URL: {clone_url}")

        # Try direct clone with specific ref
        clone_command = [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            ref,
            "--no-tags",
            clone_url,
            str(safe_temp_dir),
        ]

        return_code, stdout, stderr = await self.run_command_async(clone_command)

        if return_code == 0:
            logger.info(f"Successfully cloned ref '{ref}' directly.")
            return True

        # If direct clone failed, try fallback approach
        logger.warning(f"Initial clone failed (code: {return_code}), attempting fallback...")
        logger.warning(f"Clone stderr: {stderr.strip()}")

        # Clone default branch first
        clone_command_default = [
            "git",
            "clone",
            "--depth",
            "1",
            "--no-tags",
            clone_url,
            str(safe_temp_dir),
        ]

        return_code, stdout, stderr = await self.run_command_async(clone_command_default)

        if return_code != 0:
            logger.error(f"Failed to clone default branch (code: {return_code}).")
            logger.error(f"Clone stderr: {stderr.strip()}")
            return False

        # Fetch the specific ref
        fetch_command = [
            "git",
            "-C",
            str(safe_temp_dir),
            "fetch",
            "origin",
            ref,
            "--depth",
            "1",
        ]

        return_code, stdout, stderr = await self.run_command_async(
            fetch_command, cwd=str(safe_temp_dir)
        )

        if return_code != 0:
            logger.error(f"Failed to fetch target ref '{ref}' (code: {return_code}).")
            logger.error(f"Fetch stderr: {stderr.strip()}")
            logger.warning("Proceeding with content from default branch clone.")
            return True  # Still return True as we have the default branch

        # Checkout the fetched ref
        checkout_command = ["git", "-C", str(safe_temp_dir), "checkout", "FETCH_HEAD"]
        return_code, stdout, stderr = await self.run_command_async(
            checkout_command, cwd=str(safe_temp_dir)
        )

        if return_code != 0:
            logger.error(f"Failed to checkout fetched ref '{ref}' (code: {return_code}).")
            logger.error(f"Checkout stderr: {stderr.strip()}")
            return False

        logger.info(f"Successfully checked out ref '{ref}'.")
        return True

    def clone_sync(self, url: str, owner: str, repo: str, ref: str, temp_dir: str) -> bool:
        """Clone a repository synchronously.

        Args:
            url: Original repository URL.
            owner: Repository owner.
            repo: Repository name.
            ref: Branch, tag, or commit to checkout.
            temp_dir: Directory to clone into.

        Returns:
            True if successful, False otherwise.
        """
        clone_url = self.build_clone_url(url, owner, repo)
        logger.info(f"Attempting to clone from URL: {clone_url}")

        # Try direct clone with specific ref
        clone_command = [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            ref,
            "--no-tags",
            clone_url,
            temp_dir,
        ]

        return_code, stdout, stderr = self.run_command_sync(clone_command)

        if return_code == 0:
            logger.info(f"Successfully cloned ref '{ref}' directly.")
            return True

        # If direct clone failed, try fallback approach
        logger.warning(f"Initial clone failed (code: {return_code}), attempting fallback...")
        logger.warning(f"Clone stderr: {stderr.strip()}")

        # Clone default branch first
        clone_command_default = [
            "git",
            "clone",
            "--depth",
            "1",
            "--no-tags",
            clone_url,
            temp_dir,
        ]

        return_code, stdout, stderr = self.run_command_sync(clone_command_default)

        if return_code != 0:
            logger.error(f"Failed to clone default branch (code: {return_code}).")
            logger.error(f"Clone stderr: {stderr.strip()}")
            return False

        # Fetch the specific ref
        fetch_command = [
            "git",
            "-C",
            temp_dir,
            "fetch",
            "origin",
            ref,
            "--depth",
            "1",
        ]

        return_code, stdout, stderr = self.run_command_sync(fetch_command, cwd=temp_dir)

        if return_code != 0:
            logger.error(f"Failed to fetch target ref '{ref}' (code: {return_code}).")
            logger.error(f"Fetch stderr: {stderr.strip()}")
            logger.warning("Proceeding with content from default branch clone.")
            return True  # Still return True as we have the default branch

        # Checkout the fetched ref
        checkout_command = ["git", "-C", temp_dir, "checkout", "FETCH_HEAD"]
        return_code, stdout, stderr = self.run_command_sync(checkout_command, cwd=temp_dir)

        if return_code != 0:
            logger.error(f"Failed to checkout fetched ref '{ref}' (code: {return_code}).")
            logger.error(f"Checkout stderr: {stderr.strip()}")
            return False

        logger.info(f"Successfully checked out ref '{ref}'.")
        return True
