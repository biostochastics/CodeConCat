"""GitHub repository collector for CodeConcat."""

import re
import subprocess
import tempfile
from typing import List, Optional, Tuple
import os
import shutil
import logging

from github import Github, GithubException
from github.Repository import Repository

from ..base_types import CodeConCatConfig, ParsedFileData
from .local_collector import collect_local_files

logger = logging.getLogger(__name__)


def parse_github_url(url: str) -> Tuple[str, str, Optional[str]]:
    """Parse GitHub URL or shorthand into owner, repo, and ref."""
    # Handle shorthand notation (owner/repo)
    if "/" in url and not url.startswith("http"):
        parts = url.split("/")
        owner = parts[0]
        repo = parts[1]
        ref = parts[2] if len(parts) > 2 else None
        return owner, repo, ref

    # Handle full URLs
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?", url)
    if match:
        return match.group(1), match.group(2), match.group(3)

    raise ValueError(
        "Invalid GitHub URL or shorthand. Use format 'owner/repo', 'owner/repo/branch', "
        "or 'https://github.com/owner/repo'"
    )


def collect_github_files(github_url: str, config: CodeConCatConfig) -> List[ParsedFileData]:
    """
    Collect files from a GitHub repository.
    
    Args:
        github_url: GitHub repository URL or shorthand (owner/repo)
        config: Configuration object
        
    Returns:
        List[ParsedFileData]: List of parsed file data objects
    """
    owner, repo_name, url_ref = parse_github_url(github_url)
    
    # Use explicit ref if provided, otherwise use ref from URL
    target_ref = config.github_ref or url_ref or "main"
    
    # Create a temporary directory for cloning
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Build clone URL with token if available
            clone_url = build_clone_url(github_url, config.github_token)
            
            # Clone the repository
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", target_ref, clone_url, temp_dir],
                check=True,
                capture_output=True,
                text=True,
            )
            
            # Create a new config with temp_dir as target_path
            github_config = CodeConCatConfig(
                target_path=temp_dir,
                github_url=config.github_url,
                github_token=config.github_token,
                github_ref=config.github_ref,
                include_languages=config.include_languages,
                exclude_languages=config.exclude_languages,
                include_paths=config.include_paths,
                exclude_paths=config.exclude_paths,
                extract_docs=config.extract_docs,
                merge_docs=config.merge_docs,
                doc_extensions=config.doc_extensions,
                custom_extension_map=config.custom_extension_map,
                output=config.output,
                format=config.format,
                max_workers=config.max_workers,
                disable_tree=config.disable_tree,
                disable_copy=config.disable_copy,
                disable_annotations=config.disable_annotations,
                disable_symbols=config.disable_symbols,
                disable_ai_context=config.disable_ai_context,
            )
            
            logger.info(f"Collecting files from {temp_dir} with config: {github_config}")
            files = collect_local_files(temp_dir, github_config)
            logger.info(f"Found {len(files)} files")
            return files
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error cloning repository: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"Error processing GitHub repository: {e}")
            return []


def build_clone_url(github_url: str, token: Optional[str] = None) -> str:
    """Build GitHub clone URL with optional token."""
    if "/" in github_url and not github_url.startswith("http"):
        # Convert shorthand to full URL
        owner, repo, _ = parse_github_url(github_url)
        github_url = f"https://github.com/{owner}/{repo}"
    
    if token:
        # Insert token into URL
        return github_url.replace("https://", f"https://{token}@")
    return github_url


def _get_repo(g: Github, repo_name: str) -> Optional[Repository]:
    """Get repository object, handling potential errors."""
    try:
        return g.get_repo(repo_name)
    except GithubException as e:
        logger.error(f"Error accessing repository: {e}")
        return None
