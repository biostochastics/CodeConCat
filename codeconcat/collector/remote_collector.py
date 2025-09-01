"""Remote Git repository collector for CodeConcat."""

import logging
import re
import subprocess
import tempfile
import traceback
from typing import List, Optional, Tuple

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.collector.local_collector import collect_local_files

logger = logging.getLogger(__name__)


def parse_git_url(url: str) -> Tuple[str, str, Optional[str]]:
    """Parse Git URL or shorthand into owner, repo, and potentially ref."""
    # Handle GitHub shorthand notation (owner/repo or owner/repo/ref)
    if "/" in url and not url.startswith(("http", "git@")):
        parts = url.split("/")
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1].replace(".git", "")  # Remove .git if present
            ref = "/".join(parts[2:]) if len(parts) > 2 else None  # Join remaining parts for ref
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


def collect_git_repo(
    source_url_in: str, config: CodeConCatConfig
) -> Tuple[List[ParsedFileData], str]:
    """
    Collect files from a remote Git repository by cloning it.

    Args:
        source_url_in: Git repository URL or shorthand (e.g., owner/repo).
        config: Configuration object.

    Returns:
        Tuple[List[ParsedFileData], str]: List of parsed file data objects and the path to the temporary directory used.
    """
    try:
        owner, repo_name, url_ref = parse_git_url(source_url_in)
    except ValueError as e:
        logger.error(f"Failed to parse source URL '{source_url_in}': {e}")
        return [], ""

    # Use explicit ref from config if provided, otherwise use ref parsed from URL, default to 'main'
    target_ref = config.source_ref or url_ref or "main"
    logger.info(f"Targeting ref: '{target_ref}' for repo: '{owner}/{repo_name}'")

    # Create a temporary directory for cloning
    # Don't use context manager so directory persists until caller cleans it up
    temp_dir = tempfile.mkdtemp(prefix="codeconcat_")
    try:
        # Build clone URL with token if available
        clone_url = build_git_clone_url(source_url_in, owner, repo_name, config.github_token)
        logger.info(f"Attempting to clone from URL: {clone_url}")

        # Clone the repository
        # Use --no-tags to avoid fetching all tags, fetch only the target branch/ref
        clone_command = [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            target_ref,
            "--no-tags",  # Avoid fetching all tags
            clone_url,
            temp_dir,
        ]
        logger.info(f"Running git clone command: {' '.join(clone_command)}")
        # Use stderr=subprocess.PIPE to capture errors better
        result = subprocess.run(
            clone_command,
            check=False,  # Check manually below
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Specific ref clone failed, try cloning the default branch first
            logger.warning(
                f"Failed to clone specific ref '{target_ref}' directly (code: {result.returncode})."
            )
            logger.warning(f"Clone stderr: {result.stderr.strip()}")
            # Clone default branch first, then fetch the specific ref
            clone_command_default = [
                "git",
                "clone",
                "--depth",
                "1",
                "--no-tags",
                build_git_clone_url(
                    source_url_in, owner, repo_name, config.github_token
                ),  # Use default branch implicitly
                temp_dir,
            ]
            result_default = subprocess.run(
                clone_command_default,
                check=False,
                capture_output=True,
                text=True,
            )

            if result_default.returncode != 0:
                logger.error(f"Failed to clone default branch (code: {result_default.returncode}).")
                logger.error(f"Clone stderr: {result_default.stderr.strip()}")
                return [], ""

            fetch_command = [
                "git",
                "-C",
                temp_dir,
                "fetch",
                "origin",
                target_ref,
                "--depth",
                "1",
            ]
            logger.info(f"Running fetch command: {' '.join(fetch_command)}")
            result_fetch = subprocess.run(
                fetch_command,
                check=False,
                capture_output=True,
                text=True,
            )

            if result_fetch.returncode != 0:
                logger.error(
                    f"Failed to fetch target ref '{target_ref}' (code: {result_fetch.returncode})."
                )
                logger.error(f"Fetch stderr: {result_fetch.stderr.strip()}")
                # Proceed with default branch content if fetch fails?
                logger.warning("Proceeding with content from default branch clone.")
                # No need to checkout here, already have the default branch
            else:
                # Checkout the fetched ref
                checkout_command = ["git", "-C", temp_dir, "checkout", "FETCH_HEAD"]
                logger.info(f"Running checkout command: {' '.join(checkout_command)}")
                result_checkout = subprocess.run(
                    checkout_command,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result_checkout.returncode != 0:
                    logger.error(
                        f"Failed to checkout fetched ref '{target_ref}' (code: {result_checkout.returncode})."
                    )
                    logger.error(f"Checkout stderr: {result_checkout.stderr.strip()}")
                    return [], ""
        else:
            logger.info(f"Successfully cloned ref '{target_ref}' directly.")

        # Collect files using the local collector on the temporary directory
        logger.info(f"Collecting files from temporary directory: {temp_dir}")
        # Pass temp_dir and original config directly
        config.target_path = temp_dir  # Update config.target_path
        files = collect_local_files(temp_dir, config)
        logger.info(f"Found {len(files)} files in cloned repository.")
        return files, temp_dir  # Return files and temp_dir path

    except subprocess.CalledProcessError as e:
        # This might not be reached if check=False, handled by returncode check
        logger.error(f"Error during git operation for '{repo_name}' (Return code: {e.returncode}).")
        logger.error(f"Command run: {' '.join(e.cmd)}")
        logger.error(f"Stderr: {e.stderr.strip() if e.stderr else 'N/A'}")
        logger.error(f"Stdout: {e.stdout.strip() if e.stdout else 'N/A'}")
        return [], ""
    except Exception as e:
        logger.error(
            f"Error processing Git repository: {e}\nConfig: {config}\nTraceback: {traceback.format_exc()}"
        )
        return [], ""


def build_git_clone_url(
    _source_url_in: str, owner: str, repo: str, token: Optional[str] = None
) -> str:
    """Build GitHub clone URL with optional token. Ensures HTTPS format."""
    # Always construct a standard HTTPS URL for cloning
    base_url = f"https://github.com/{owner}/{repo}.git"

    if token:
        # Insert token into URL for authentication
        return base_url.replace("https://", f"https://{token}@")
    return base_url
