"""Remote Git repository collector for CodeConcat - Async version with backward compatibility."""

import asyncio
import logging
import re
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


async def run_git_command(
    command: List[str], cwd: Optional[str] = None, timeout: float = 120.0
) -> Tuple[int, str, str]:
    """
    Run a git command asynchronously with proper error handling.

    Args:
        command: Command and arguments to run
        cwd: Working directory for the command
        timeout: Maximum time to wait for command completion

    Returns:
        Tuple of (return_code, stdout, stderr)
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

    except Exception as e:
        logger.error(f"Error running git command: {e}")
        return -1, "", str(e)


async def collect_git_repo_async(
    source_url_in: str, config: CodeConCatConfig
) -> Tuple[List[ParsedFileData], str]:
    """
    Async version: Collect files from a remote Git repository by cloning it.

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
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Build clone URL with token if available
            clone_url = build_git_clone_url(source_url_in, owner, repo_name, config.github_token)
            logger.info(f"Attempting to clone from URL: {clone_url}")

            # Clone the repository
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

            logger.info("Running async git clone command")
            return_code, stdout, stderr = await run_git_command(clone_command)

            if return_code != 0:
                # Attempt fetch if clone failed (might be a specific commit SHA not on a branch HEAD)
                logger.warning(f"Initial clone failed (code: {return_code}), attempting fetch...")
                logger.warning(f"Clone stderr: {stderr.strip()}")

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

                return_code_default, stdout_default, stderr_default = await run_git_command(
                    clone_command_default
                )

                if return_code_default != 0:
                    logger.error(f"Failed to clone default branch (code: {return_code_default}).")
                    logger.error(f"Clone stderr: {stderr_default.strip()}")
                    return [], ""

                # Fetch the specific ref
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

                logger.info("Running fetch command")
                return_code_fetch, stdout_fetch, stderr_fetch = await run_git_command(
                    fetch_command, cwd=temp_dir
                )

                if return_code_fetch != 0:
                    logger.error(
                        f"Failed to fetch target ref '{target_ref}' (code: {return_code_fetch})."
                    )
                    logger.error(f"Fetch stderr: {stderr_fetch.strip()}")
                    # Proceed with default branch content if fetch fails?
                    logger.warning("Proceeding with content from default branch clone.")
                    # No need to checkout here, already have the default branch
                else:
                    # Checkout the fetched ref
                    checkout_command = ["git", "-C", temp_dir, "checkout", "FETCH_HEAD"]
                    logger.info("Running checkout command")
                    return_code_checkout, stdout_checkout, stderr_checkout = await run_git_command(
                        checkout_command, cwd=temp_dir
                    )

                    if return_code_checkout != 0:
                        logger.error(
                            f"Failed to checkout fetched ref '{target_ref}' (code: {return_code_checkout})."
                        )
                        logger.error(f"Checkout stderr: {stderr_checkout.strip()}")
                        return [], ""
            else:
                logger.info(f"Successfully cloned ref '{target_ref}' directly.")

            # Collect files using the local collector on the temporary directory
            logger.info(f"Collecting files from temporary directory: {temp_dir}")
            # Pass temp_dir and original config directly
            # Note: collect_local_files is still synchronous, could be made async in future
            loop = asyncio.get_event_loop()
            files = await loop.run_in_executor(None, collect_local_files, temp_dir, config)
            logger.info(f"Found {len(files)} files in cloned repository.")
            return files, temp_dir  # Return files and temp_dir path

        except Exception as e:
            logger.error(
                f"Error processing Git repository: {e}\nConfig: {config}\nTraceback: {traceback.format_exc()}"
            )
            return [], ""


def collect_git_repo(
    source_url_in: str, config: CodeConCatConfig
) -> Tuple[List[ParsedFileData], str]:
    """
    Synchronous wrapper for backward compatibility.
    Collect files from a remote Git repository by cloning it.

    Args:
        source_url_in: Git repository URL or shorthand (e.g., owner/repo).
        config: Configuration object.

    Returns:
        Tuple[List[ParsedFileData], str]: List of parsed file data objects and the path to the temporary directory used.
    """
    # Check if we're already in an event loop
    try:
        try:
            asyncio.get_running_loop()
            # We're in an async context, but called synchronously
            # This is not ideal but we'll handle it
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, collect_git_repo_async(source_url_in, config))
                return future.result()
        except RuntimeError:
            # No event loop running, we can create one
            return asyncio.run(collect_git_repo_async(source_url_in, config))
    except Exception as e:
        # Handle any exceptions from async execution
        logger.error(f"Error in synchronous Git repository collection: {e}")
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
