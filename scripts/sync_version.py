#!/usr/bin/env python3
"""Sync version from codeconcat/version.py to pyproject.toml and README.md.

This script is run as a pre-commit hook to ensure version consistency
across all files that reference the version number.

Usage:
    python scripts/sync_version.py

Exit codes:
    0 - All files already in sync or successfully updated
    1 - Files were updated (signals pre-commit to re-stage)
"""

import re
import sys
from pathlib import Path


def get_version_from_source() -> str:
    """Extract version from codeconcat/version.py."""
    version_file = Path(__file__).parent.parent / "codeconcat" / "version.py"
    content = version_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Could not find __version__ in codeconcat/version.py")
    return match.group(1)


def update_pyproject_toml(version: str) -> bool:
    """Update version in pyproject.toml. Returns True if changed."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject_path.read_text()

    # Match version = "x.y.z" in [tool.poetry] section
    pattern = r'(^\[tool\.poetry\].*?^version\s*=\s*")[^"]+(")'
    new_content = re.sub(pattern, rf"\g<1>{version}\2", content, flags=re.MULTILINE | re.DOTALL)

    if new_content != content:
        pyproject_path.write_text(new_content)
        print(f"Updated pyproject.toml to version {version}")
        return True
    return False


def update_readme(version: str) -> bool:
    """Update version badge in README.md. Returns True if changed."""
    readme_path = Path(__file__).parent.parent / "README.md"
    content = readme_path.read_text()

    # Match version badge: [![Version](https://img.shields.io/badge/version-X.Y.Z-blue)]
    pattern = r"(\[!\[Version\]\(https://img\.shields\.io/badge/version-)[^-]+(-blue\)\])"
    new_content = re.sub(pattern, rf"\g<1>{version}\2", content)

    if new_content != content:
        readme_path.write_text(new_content)
        print(f"Updated README.md version badge to {version}")
        return True
    return False


def main() -> int:
    """Main entry point."""
    try:
        version = get_version_from_source()
        print(f"Source version: {version}")

        changed = False
        changed |= update_pyproject_toml(version)
        changed |= update_readme(version)

        if changed:
            print("Version files updated. Please re-stage the changes.")
            return 1  # Signal to pre-commit that files were modified
        else:
            print("All version files are in sync.")
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
