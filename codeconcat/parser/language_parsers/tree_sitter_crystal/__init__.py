"""Tree-sitter Crystal language support for CodeConCat.

This module provides the tree-sitter-crystal grammar for parsing Crystal source files.
The grammar is built from the crystal-lang-tools/tree-sitter-crystal repository.
"""

import contextlib
import fcntl
import logging
import os
import platform
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Pinned commit hash for stable grammar (crystal-lang-tools/tree-sitter-crystal)
# Using latest stable commit as of implementation
# Update this as needed for grammar improvements
CRYSTAL_GRAMMAR_COMMIT = "main"  # Use main branch for latest

# Try to import the compiled binding
try:
    from ._binding import language

    BINDING_AVAILABLE = True
except ImportError:
    BINDING_AVAILABLE = False

    # Fallback function that builds and loads the language dynamically
    def language():
        """Get the tree-sitter Language object for Crystal.

        This fallback function builds the Crystal grammar on-demand if the compiled
        binding is not available.

        Returns:
            The Crystal language object for tree-sitter parsing.

        Raises:
            RuntimeError: If the Crystal grammar library cannot be loaded.
        """
        # Build the binding if not available
        _build_and_install_binding()

        # Try importing again
        try:
            from ._binding import language as _lang

            return _lang()
        except ImportError as e:
            raise RuntimeError("Failed to import Crystal language binding after building") from e


def _get_cache_dir():
    """Get the cache directory for tree-sitter grammars.

    Uses environment variable CODECONCAT_CACHE_DIR if set,
    otherwise falls back to system-appropriate cache directory.

    Returns:
        Path: The cache directory path
    """
    if "CODECONCAT_CACHE_DIR" in os.environ:
        cache_dir = Path(os.environ["CODECONCAT_CACHE_DIR"]) / "tree-sitter-grammars"
    else:
        # Use XDG_CACHE_HOME on Linux/Unix, or platform-appropriate temp dir
        if platform.system() in ("Linux", "Darwin"):
            cache_base = os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
            cache_dir = Path(cache_base) / "codeconcat" / "tree-sitter-grammars"
        else:
            cache_dir = Path(tempfile.gettempdir()) / "codeconcat" / "tree-sitter-grammars"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _build_and_install_binding():
    """Build and install the Crystal grammar binding with thread-safe locking.

    This function uses file-based locking to prevent race conditions when
    multiple processes attempt to build the grammar simultaneously.

    Raises:
        RuntimeError: If building the grammar fails.
    """
    binding_dir = Path(__file__).parent
    binding_so = binding_dir / "_binding.so"

    # Use lock file to prevent race conditions
    lock_file = binding_dir / ".build.lock"

    # Open lock file with proper permissions
    lock_fd = None
    try:
        lock_fd = open(lock_file, "w")  # noqa: SIM115

        # Acquire exclusive lock (blocks until available)
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        except OSError as e:
            logger.warning(f"Could not acquire build lock, proceeding without lock: {e}")

        # Double-check if binding exists after acquiring lock
        # (another process may have built it while we were waiting)
        if binding_so.exists():
            logger.debug("Crystal grammar binding already exists")
            return

        # Get cache directory
        cache_dir = _get_cache_dir()
        repo_path = cache_dir / "tree-sitter-crystal"

        # Clone or update repository
        if not repo_path.exists():
            logger.info("Downloading tree-sitter-crystal grammar...")
            try:
                # Clone the repository
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "https://github.com/crystal-lang-tools/tree-sitter-crystal.git",
                        str(repo_path),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=60,
                )

                logger.info("Tree-sitter-crystal grammar downloaded")
            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode() if e.stderr else "No error output"
                raise RuntimeError(
                    f"Failed to clone tree-sitter-crystal repository: {stderr}"
                ) from e
            except subprocess.TimeoutExpired as e:
                raise RuntimeError(f"Git clone timed out after {e.timeout} seconds") from e

        # Verify Crystal grammar exists
        if not repo_path.exists():
            raise RuntimeError(f"Crystal grammar directory not found after clone: {repo_path}")

        # Build the binding
        try:
            import sysconfig

            parser_c = repo_path / "src" / "parser.c"
            scanner_c = repo_path / "src" / "scanner.c"  # Crystal grammar has a scanner
            binding_c = binding_dir / "binding.c"

            if not parser_c.exists():
                raise RuntimeError(f"Parser source file not found: {parser_c}")

            if not binding_c.exists():
                raise RuntimeError(f"Binding source file not found: {binding_c}")

            # Get Python include directory
            python_include = sysconfig.get_paths()["include"]

            # Create temporary output file for atomic replacement
            binding_tmp = binding_so.with_suffix(".so.tmp")

            # Determine the appropriate compiler flags
            if platform.system() == "Darwin":
                # macOS - use -undefined dynamic_lookup for Python extensions
                cmd = [
                    "cc",
                    "-bundle",
                    "-fPIC",
                    "-o",
                    str(binding_tmp),
                    str(binding_c),
                    str(parser_c),
                ]
                # Add scanner if it exists
                if scanner_c.exists():
                    cmd.append(str(scanner_c))
                cmd.extend(
                    [
                        "-I",
                        str(repo_path / "src"),
                        "-I",
                        python_include,
                        "-undefined",
                        "dynamic_lookup",
                    ]
                )
            elif platform.system() == "Linux":
                # Linux
                cmd = [
                    "gcc",
                    "-shared",
                    "-fPIC",
                    "-o",
                    str(binding_tmp),
                    str(binding_c),
                    str(parser_c),
                ]
                # Add scanner if it exists
                if scanner_c.exists():
                    cmd.append(str(scanner_c))
                cmd.extend(
                    [
                        "-I",
                        str(repo_path / "src"),
                        "-I",
                        python_include,
                    ]
                )
            else:
                # Windows (untested)
                raise RuntimeError(
                    "Windows is not yet supported for dynamic Crystal grammar building"
                )

            # Compile with timeout
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)

            # Atomic rename to prevent TOCTOU issues
            binding_tmp.replace(binding_so)

            logger.info(f"Crystal grammar binding built successfully at {binding_so}")

        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Compilation timed out after {e.timeout} seconds") from e
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else "No error output"
            raise RuntimeError(f"Failed to build Crystal grammar binding: {stderr}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to build Crystal grammar binding: {e}") from e

    finally:
        # Release lock and clean up
        if lock_fd is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()

            # Clean up lock file
            with contextlib.suppress(OSError):
                lock_file.unlink()


__all__ = [
    "language",
]
