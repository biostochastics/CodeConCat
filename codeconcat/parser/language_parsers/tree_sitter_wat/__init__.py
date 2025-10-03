"""Tree-sitter WAT (WebAssembly Text) language support for CodeConCat.

This module provides the tree-sitter-wasm WAT grammar for parsing WebAssembly Text format files.
The grammar is built from the wasm-lsp/tree-sitter-wasm repository.
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

# Pinned commit hash for stable grammar (wasm-lsp/tree-sitter-wasm)
# Using latest commit as grammar is stable
# Verified working: 2024-10-02
WAT_GRAMMAR_COMMIT = "2ca28a9"  # Latest as of 2024-10-02

# Try to import the compiled binding
try:
    from ._binding import language

    BINDING_AVAILABLE = True
except ImportError:
    BINDING_AVAILABLE = False

    # Fallback function that builds and loads the language dynamically
    def language():
        """Get the tree-sitter Language object for WAT.

        This fallback function builds the WAT grammar on-demand if the compiled
        binding is not available.

        Returns:
            The WAT language object for tree-sitter parsing.

        Raises:
            RuntimeError: If the WAT grammar library cannot be loaded.
        """
        # Build the binding if not available
        _build_and_install_binding()

        # Try importing again
        try:
            from ._binding import language as _lang

            return _lang()
        except ImportError:
            raise RuntimeError("Failed to import WAT language binding after building") from None


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
    """Build and install the WAT grammar binding with thread-safe locking.

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
    with open(lock_file, "w") as lock_fd:
        # Acquire exclusive lock (blocks until available)
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        except OSError as e:
            logger.warning(f"Could not acquire build lock, proceeding without lock: {e}")

        # Double-check if binding exists after acquiring lock
        # (another process may have built it while we were waiting)
        if binding_so.exists():
            logger.debug("WAT grammar binding already exists")
            return

        # Get cache directory
        cache_dir = _get_cache_dir()
        repo_path = cache_dir / "tree-sitter-wasm"
        wat_path = repo_path / "wat"

        # Clone or update repository
        if not repo_path.exists():
            logger.info("Downloading tree-sitter-wasm grammar...")
            try:
                # Clone the repository
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "https://github.com/wasm-lsp/tree-sitter-wasm.git",
                        str(repo_path),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=60,
                )

                # Checkout pinned commit for reproducibility
                subprocess.run(
                    ["git", "-C", str(repo_path), "checkout", WAT_GRAMMAR_COMMIT],
                    check=True,
                    capture_output=True,
                    timeout=10,
                )
                logger.info(f"Tree-sitter-wasm grammar downloaded (commit {WAT_GRAMMAR_COMMIT})")
            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode() if e.stderr else "No error output"
                raise RuntimeError(f"Failed to clone tree-sitter-wasm repository: {stderr}") from e
            except subprocess.TimeoutExpired as e:
                raise RuntimeError(f"Git clone timed out after {e.timeout} seconds") from e

        # Verify WAT grammar exists
        if not wat_path.exists():
            raise RuntimeError(f"WAT grammar directory not found after clone: {wat_path}")

        # Build the binding
        try:
            import sysconfig

            parser_c = wat_path / "src" / "parser.c"
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
                    "-I",
                    str(wat_path / "src"),
                    "-I",
                    python_include,
                    "-undefined",
                    "dynamic_lookup",
                ]
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
                    "-I",
                    str(wat_path / "src"),
                    "-I",
                    python_include,
                ]
            else:
                # Windows (untested)
                raise RuntimeError("Windows is not yet supported for dynamic WAT grammar building")

            # Compile with timeout
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)

            # Atomic rename to prevent TOCTOU issues
            binding_tmp.replace(binding_so)

            logger.info(f"WAT grammar binding built successfully at {binding_so}")

        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Compilation timed out after {e.timeout} seconds") from e
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else "No error output"
            raise RuntimeError(f"Failed to build WAT grammar binding: {stderr}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to build WAT grammar binding: {e}") from e

    # Clean up lock file
    with contextlib.suppress(OSError):
        lock_file.unlink()


__all__ = [
    "language",
]
