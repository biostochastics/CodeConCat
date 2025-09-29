"""Remote Git repository collector for CodeConcat - DEPRECATED.

This module is deprecated and maintained only for backward compatibility.
Please use codeconcat.collector.github_collector instead.
"""

import warnings

# Import from the refactored github_collector module
from codeconcat.collector.github_collector import (
    _build_clone_url as build_git_clone_url,
)
from codeconcat.collector.github_collector import (
    collect_git_repo,
    parse_git_url,
)

# Show deprecation warning when this module is imported
warnings.warn(
    "remote_collector module is deprecated and will be removed in a future version. "
    "Please import from codeconcat.collector.github_collector instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export functions for backward compatibility
__all__ = ["collect_git_repo", "parse_git_url", "build_git_clone_url"]
