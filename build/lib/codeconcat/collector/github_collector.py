import os
import tempfile
import shutil
import subprocess
from typing import List
from codeconcat.types import CodeConCatConfig
from codeconcat.collector.local_collector import collect_local_files


def collect_github_files(github_url: str, config: CodeConCatConfig) -> List[str]:
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
