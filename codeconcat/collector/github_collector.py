"""Remote Git repository collector for CodeConcat - GitPython-based implementation.

This module provides functionality to clone and collect files from remote Git repositories
using the GitPython library for more robust and maintainable Git operations.

Key Features:
    - Support for GitHub, GitLab, Bitbucket, and other Git services
    - Token authentication for private repositories
    - Shallow cloning for improved performance
    - Automatic fallback from 'main' to 'master' branch
    - Both synchronous and asynchronous interfaces

Example:
    >>> from codeconcat.collector.github_collector import collect_git_repo
    >>> files, temp_dir = collect_git_repo("owner/repo", config)
    >>> print(f"Collected {len(files)} files")
"""

import asyncio
import logging
import re
import tempfile

from git import Repo
from git.exc import GitCommandError

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.collector.local_collector import collect_local_files

logger = logging.getLogger(__name__)


def parse_git_url(url: str) -> tuple[str, str, str | None]:
    """Parse Git URL or shorthand into owner, repo, and ref.

    Supports multiple formats:
    - GitHub shorthand: owner/repo or owner/repo#branch
    - HTTPS URLs: https://github.com/owner/repo.git
    - SSH URLs: git@github.com:owner/repo.git
    - URLs with refs: https://github.com/owner/repo/tree/branch

    Args:
        url: Git repository URL or shorthand.

    Returns:
        Tuple of (owner, repo, ref) where ref may be None.

    Raises:
        ValueError: If URL format is invalid.
    """
    # Handle GitHub shorthand notation (owner/repo or owner/repo#ref)
    if "/" in url and not url.startswith(("http", "git@", "ssh://")):
        # Check for ref specified with # (common convention)
        if "#" in url:
            base_url, ref = url.split("#", 1)
        else:
            base_url = url
            ref = None

        parts = base_url.split("/")
        if len(parts) == 2:
            owner = parts[0]
            repo = parts[1].replace(".git", "")
            logger.debug(f"Parsed shorthand: owner={owner}, repo={repo}, ref={ref}")
            return owner, repo, ref
        elif len(parts) > 2:
            # Support owner/repo/tree/branch format
            owner = parts[0]
            repo = parts[1].replace(".git", "")
            ref = "/".join(parts[2:])
            return owner, repo, ref

    # Handle full HTTPS URLs
    match_https = re.match(
        r"https?://(?:www\.)?github\.com/([^/]+)/([^/\.]+)(?:\.git)?(?:/tree/([^/]+))?", url
    )
    if match_https:
        owner, repo, ref = match_https.group(1), match_https.group(2), match_https.group(3)
        logger.debug(f"Parsed HTTPS URL: owner={owner}, repo={repo}, ref={ref}")
        return owner, repo, ref

    # Handle SSH URLs
    match_ssh = re.match(r"git@github\.com:([^/]+)/([^/\.]+)(?:\.git)?", url)
    if match_ssh:
        owner, repo = match_ssh.group(1), match_ssh.group(2)
        logger.debug(f"Parsed SSH URL: owner={owner}, repo={repo}, ref=None")
        return owner, repo, None

    # Handle GitLab and other Git hosting services
    match_gitlab = re.match(
        r"https?://(?:www\.)?gitlab\.com/([^/]+)/([^/\.]+)(?:\.git)?(?:/-/tree/([^/]+))?", url
    )
    if match_gitlab:
        owner, repo, ref = match_gitlab.group(1), match_gitlab.group(2), match_gitlab.group(3)
        logger.debug(f"Parsed GitLab URL: owner={owner}, repo={repo}, ref={ref}")
        return owner, repo, ref

    raise ValueError(
        "Invalid Git URL or shorthand. Supported formats: 'owner/repo', 'owner/repo#branch', "
        "'https://github.com/owner/repo', 'git@github.com:owner/repo.git'"
    )


def _build_clone_url(url: str, owner: str, repo: str, token: str | None = None) -> str:
    """Build the appropriate clone URL for a repository.

    Args:
        url: Original URL (for reference).
        owner: Repository owner.
        repo: Repository name.
        token: Optional GitHub token for authentication.

    Returns:
        Clone URL with authentication if token is provided.
    """
    # Build base URL based on the service
    if "gitlab" in url.lower():
        base_url = f"https://gitlab.com/{owner}/{repo}.git"
    elif "bitbucket" in url.lower():
        base_url = f"https://bitbucket.org/{owner}/{repo}.git"
    else:
        # Default to GitHub
        base_url = f"https://github.com/{owner}/{repo}.git"

    # Add token authentication if available
    if token:
        # Insert token for HTTPS authentication
        return base_url.replace("https://", f"https://{token}@")

    return base_url


def _clone_repository(
    clone_url: str, target_dir: str, target_ref: str = "main", depth: int | None = 1
) -> Repo:
    """Clone a repository using GitPython.

    Args:
        clone_url: URL to clone from.
        target_dir: Directory to clone into.
        target_ref: Branch/tag/commit to checkout (default: main).
        depth: Clone depth for shallow clones (None for full clone).

    Returns:
        GitPython Repo object.

    Raises:
        GitCommandError: If cloning fails.
    """
    logger.info(f"Cloning repository (ref: {target_ref})")

    try:
        # Perform shallow clone for efficiency (depth=1)
        if depth:
            repo = Repo.clone_from(
                clone_url, target_dir, branch=target_ref, depth=depth, no_single_branch=False
            )
        else:
            # Full clone if depth is None
            repo = Repo.clone_from(clone_url, target_dir, branch=target_ref)

        logger.info(f"Successfully cloned repository to {target_dir}")
        return repo

    except GitCommandError as e:
        # Try with 'master' if 'main' fails
        if target_ref == "main" and "not found" in str(e):
            logger.info("'main' branch not found, trying 'master'...")
            return _clone_repository(clone_url, target_dir, "master", depth)
        raise


async def collect_git_repo_async(
    source_url_in: str, config: CodeConCatConfig
) -> tuple[list[ParsedFileData], str]:
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
    with tempfile.TemporaryDirectory(prefix="codeconcat_clone_") as temp_dir:
        try:
            # Build clone URL with optional authentication
            clone_url = _build_clone_url(source_url_in, owner, repo_name, config.github_token)

            # Clone repository using GitPython in thread executor (GitPython is synchronous)
            loop = asyncio.get_event_loop()
            repo = await loop.run_in_executor(
                None,
                _clone_repository,
                clone_url,
                temp_dir,
                target_ref,
                1,  # Shallow clone for efficiency
            )

            # Log repository information
            logger.info("Repository cloned successfully")
            logger.debug(
                f"Active branch: {repo.active_branch if not repo.head.is_detached else 'detached HEAD'}"
            )
            logger.debug(f"Commit: {repo.head.commit.hexsha[:8]}")

            # Collect files using the local collector
            logger.info(f"Collecting files from cloned repository at {temp_dir}")
            files = await loop.run_in_executor(None, collect_local_files, temp_dir, config)
            logger.info(f"Found {len(files)} files in repository '{owner}/{repo_name}'")
            return files, temp_dir

        except GitCommandError as e:
            logger.error(f"Git operation failed: {e}")
            return [], ""
        except (OSError, PermissionError, ValueError) as e:
            logger.error(f"Error processing Git repository: {e}")
            return [], ""
        except Exception as e:
            logger.error(f"Unexpected error during repository collection: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return [], ""


def collect_git_repo(
    source_url_in: str, config: CodeConCatConfig
) -> tuple[list[ParsedFileData], str]:
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
    except (OSError, RuntimeError, asyncio.TimeoutError, Exception) as e:
        # Handle any exceptions from async execution
        logger.error(f"Error in synchronous Git repository collection: {e}")
        return [], ""
