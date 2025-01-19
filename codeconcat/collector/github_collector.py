import re
import subprocess
import tempfile
from typing import List, Optional, Tuple

from github import Github, GithubException
from github.Repository import Repository

from ..base_types import CodeConCatConfig
from .local_collector import collect_local_files


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


def collect_github_files(github_url: str, config: CodeConCatConfig) -> List[str]:
    owner, repo_name, url_ref = parse_github_url(github_url)

    # Use explicit ref if provided, otherwise use ref from URL
    target_ref = config.ref or url_ref or "main"

    g = Github(config.github_token) if config.github_token else Github()
    repo = _get_repo(g, repo_name)
    if repo is None:
        return []

    try:
        # Verify ref exists
        repo.get_commit(target_ref)
    except GithubException:
        try:
            # Try as a branch/tag name
            branches = [b.name for b in repo.get_branches()]
            tags = [t.name for t in repo.get_tags()]
            if target_ref not in branches and target_ref not in tags:
                raise ValueError(
                    f"Reference '{target_ref}' not found. Available branches: {branches}, "
                    f"tags: {tags}"
                )
        except GithubException as e:
            raise ValueError(f"Error accessing repository: {str(e)}")

    contents = []
    for content in repo.get_contents("", ref=target_ref):
        if content.type == "file":
            contents.append(content.decoded_content.decode("utf-8"))
        elif content.type == "dir":
            contents.extend(_collect_dir_contents(repo, content.path, target_ref))

    return contents


def _get_repo(g: Github, repo_name: str) -> Optional[Repository]:
    try:
        repo = g.get_repo(repo_name)
        return repo
    except (ValueError, GithubException) as e:
        print(f"Error getting repository {repo_name}: {str(e)}")
        return None


def _collect_dir_contents(repo: Repository, path: str, ref: str) -> List[str]:
    """Recursively collect contents from a directory."""
    contents = []
    for content in repo.get_contents(path, ref=ref):
        if content.type == "file":
            contents.append(content.decoded_content.decode("utf-8"))
        elif content.type == "dir":
            contents.extend(_collect_dir_contents(repo, content.path, ref))
    return contents


def collect_github_files_legacy(github_url: str, config: CodeConCatConfig) -> List[str]:
    temp_dir = tempfile.mkdtemp(prefix="codeconcat_github_")
    try:
        clone_url = build_clone_url(github_url, config.github_token)
        print(f"[CodeConCat] Cloning from {clone_url} into {temp_dir}")
        subprocess.run(["git", "clone", "--depth=1", clone_url, temp_dir], check=True)

        file_paths = collect_local_files(temp_dir, config)
        return file_paths

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone GitHub repo: {e}") from e
    finally:
        # Optionally remove the temp directory
        # shutil.rmtree(temp_dir, ignore_errors=True)
        pass


def build_clone_url(github_url: str, token: str) -> str:
    if token and "https://" in github_url:
        parts = github_url.split("https://", 1)
        return f"https://{token}@{parts[1]}"
    return github_url
