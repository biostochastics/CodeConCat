"""Version information for CodeConcat.

CENTRAL VERSION SOURCE OF TRUTH
===============================
This file is the single source of truth for CodeConcat's version number.

AUTO-SYNC: When you edit this file and commit, the pre-commit hook
`sync-version` will automatically update:
  - pyproject.toml (version field)
  - README.md (version badge)

When releasing a new version:
1. Update __version__ in this file
2. Commit - the hook will sync pyproject.toml and README.md automatically
3. Update CHANGELOG.md with release notes
4. Tag and release

All code should import version from here:
    from codeconcat.version import __version__
"""

__version__ = "0.9.0"
