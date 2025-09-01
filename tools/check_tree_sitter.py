#!/usr/bin/env python3
"""
Standalone Tree-sitter grammar verification tool for CodeConCat.

This script checks if tree-sitter is installed and available,
without depending on importing from the codeconcat package.
"""

import logging
import os
import sys
import traceback
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Define the languages to check
LANGUAGES = [
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "cpp",
    "csharp",
    "go",
    "php",
    "rust",
    "julia",
    "r",
]


def check_tree_sitter_core() -> bool:
    """Check if the tree-sitter core library is installed."""
    try:
        import tree_sitter

        version = getattr(tree_sitter, "__version__", "unknown")
        logger.info(f"✅ tree-sitter core library found (version: {version})")

        # Check if Language class is available
        if hasattr(tree_sitter, "Language"):
            logger.info("✅ tree-sitter Language class is available")
            return True
        else:
            logger.error("❌ tree-sitter is installed but the Language class is not available")
            return False
    except ImportError as e:
        logger.error(f"❌ tree-sitter core library not found: {e}")
        return False


def check_tree_sitter_grammars() -> Tuple[bool, List[str], List[str]]:
    """
    Check if the tree-sitter grammar shared libraries are available.

    Returns:
        Tuple containing:
        - Overall success flag
        - List of successful languages
        - List of failed languages with error messages
    """
    success = True
    successful_langs = []
    failed_langs = []

    # Check if tree-sitter core is available first
    if not check_tree_sitter_core():
        return False, [], ["tree-sitter core library not installed or incomplete"]

    # Check if tree-sitter is available
    try:
        import importlib.util

        # Use find_spec to check if the module is available without importing it
        if importlib.util.find_spec("tree_sitter") is None:
            return False, [], []

        # Look for grammar .so files in the site-packages directory
        site_packages = None
        for path in sys.path:
            if path.endswith("site-packages"):
                site_packages = path
                break

        if not site_packages:
            logger.error("❌ Could not find site-packages directory in sys.path")
            return False, [], ["Could not find site-packages directory"]

        logger.info(f"Searching for tree-sitter grammars in: {site_packages}")

        # Check each language
        for lang in LANGUAGES:
            try:
                # Check for .so files for this language
                grammar_name = f"tree_sitter_{lang.lower()}.so"

                # Special cases for JS/TS and C/C++
                if lang in ["javascript", "typescript"]:
                    grammar_name = "tree_sitter_javascript.so"
                elif lang in ["c", "cpp"]:
                    grammar_name = "tree_sitter_cpp.so"

                # Look for the grammar file in various locations
                grammar_found = False
                grammar_paths = []

                # Check in site-packages
                for root, _dirs, files in os.walk(site_packages):
                    if grammar_name in files:
                        grammar_path = os.path.join(root, grammar_name)
                        grammar_paths.append(grammar_path)
                        grammar_found = True

                # If found, mark as successful
                if grammar_found:
                    logger.info(f"✅ {lang}: Grammar found at {grammar_paths[0]}")
                    successful_langs.append(lang)
                else:
                    logger.error(f"❌ {lang}: Grammar not found")
                    failed_langs.append(f"{lang}: Grammar file '{grammar_name}' not found")
                    success = False

            except Exception as e:
                error_msg = f"{lang}: Unexpected error: {e}"
                logger.error(f"❌ {error_msg}", exc_info=True)
                failed_langs.append(f"{error_msg} - {traceback.format_exc()}")
                success = False

    except ImportError as e:
        logger.error(f"❌ Failed to import tree-sitter: {e}")
        return False, [], [f"Failed to import tree-sitter: {e}"]

    return success, successful_langs, failed_langs


def main():
    """Main entry point for the verification script."""
    print("CodeConCat Tree-sitter Grammar Verification Tool")
    print("================================================\n")

    # Run verification
    success, successful_langs, failed_langs = check_tree_sitter_grammars()

    # Print summary
    if success:
        print(f"\n✅ All {len(successful_langs)} Tree-sitter grammars are properly installed.")
        print(f"Supported languages: {', '.join(sorted(successful_langs))}")
        return 0
    else:
        print("\n❌ Tree-sitter dependency check failed.")
        print(f"✅ Successful: {len(successful_langs)} languages")
        print(f"❌ Failed: {len(failed_langs)} languages")

        # Print detailed errors
        if failed_langs:
            print("\nError details:")
            for i, error in enumerate(failed_langs, 1):
                print(f"  {i}. {error}")

        print("\nSuggestions for fixing:")
        print("  1. Run 'pip install -U tree-sitter' to ensure the core library is installed")
        print(
            "  2. Check that your Python environment has the necessary compilers for native extensions"
        )
        print("  3. Try reinstalling CodeConCat to rebuild all Tree-sitter grammars")
        return 1


if __name__ == "__main__":
    sys.exit(main())
