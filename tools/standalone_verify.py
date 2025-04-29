#!/usr/bin/env python3
"""
Standalone Tree-sitter dependency verification tool for CodeConCat.

This script checks if all the required Tree-sitter grammars are correctly
installed and available, without depending on the main codeconcat package.
"""

import importlib.util
import logging
import os
import sys
import traceback
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Define the tree-sitter parser map - Copy from the actual code
TREE_SITTER_PARSER_MAP = {
    "python": "TreeSitterPythonParser",
    "java": "TreeSitterJavaParser",
    "javascript": "TreeSitterJsTsParser",
    "typescript": "TreeSitterJsTsParser",
    "c": "TreeSitterCppParser",
    "cpp": "TreeSitterCppParser",
    "csharp": "TreeSitterCSharpParser",
    "go": "TreeSitterGoParser",
    "php": "TreeSitterPhpParser",
    "rust": "TreeSitterRustParser",
    "julia": "TreeSitterJuliaParser",
    "r": "TreeSitterRParser",
}


def verify_tree_sitter_dependencies() -> Tuple[bool, List[str], List[str]]:
    """
    Verify that Tree-sitter and all language grammars are properly installed.

    Returns:
        Tuple containing:
        - Overall success (True if all dependencies are available)
        - List of successful language grammars
        - List of failed language grammars with error messages
    """
    success = True
    successful_languages = []
    failed_languages = []

    # First, check if tree-sitter itself is installed
    try:
        import tree_sitter

        logger.info(
            f"✅ tree-sitter core library found (version: {getattr(tree_sitter, '__version__', 'unknown')})"
        )
    except ImportError as e:
        logger.error(f"❌ tree-sitter core library not found: {e}")
        return (
            False,
            [],
            ["tree-sitter core library not found. Please install with 'pip install tree-sitter'."],
        )

    # Check if Language class is available
    if not hasattr(tree_sitter, "Language"):
        logger.error("❌ tree-sitter is installed but the Language class is not available")
        return (
            False,
            [],
            [
                "tree-sitter is installed but appears to be incomplete. Try reinstalling with 'pip install -U tree-sitter'."
            ],
        )

    # For each language in TREE_SITTER_PARSER_MAP, try to load the parser
    for language, parser_class_name in TREE_SITTER_PARSER_MAP.items():
        try:
            # Try to dynamically import the parser module
            module_name = f"codeconcat.parser.language_parsers.tree_sitter_{language}_parser"

            # Handle special cases
            if language in ["javascript", "typescript"]:
                module_name = "codeconcat.parser.language_parsers.tree_sitter_js_ts_parser"
            elif language in ["c", "cpp"]:
                module_name = "codeconcat.parser.language_parsers.tree_sitter_cpp_parser"

            # Load the module and try to instantiate the parser
            logger.info(f"Checking {language} grammar...")

            # First just check if the module exists
            try:
                spec = importlib.util.find_spec(module_name)
                if spec is None:
                    error_msg = f"{language}: Parser module not found"
                    logger.error(f"❌ {error_msg}")
                    failed_languages.append(error_msg)
                    success = False
                    continue

                # Try to load the actual Language object for this language
                ts_lang_var = None

                # Attempt to locate the module where the Language object is defined
                lang_module_path = os.path.join(
                    os.path.dirname(spec.origin),
                    (
                        f"tree_sitter_{language.lower()}.so"
                        if language not in ["javascript", "typescript", "c", "cpp"]
                        else (
                            "tree_sitter_javascript.so"
                            if language in ["javascript", "typescript"]
                            else "tree_sitter_cpp.so"
                        )
                    ),
                )

                if os.path.exists(lang_module_path):
                    logger.info(f"✅ {language}: Grammar file found at {lang_module_path}")
                    successful_languages.append(language)
                else:
                    error_msg = f"{language}: Grammar file not found at {lang_module_path}"
                    logger.error(f"❌ {error_msg}")
                    failed_languages.append(error_msg)
                    success = False

            except ImportError as e:
                error_msg = f"{language}: Failed to import parser module: {e}"
                logger.error(f"❌ {error_msg}")
                failed_languages.append(error_msg)
                success = False

        except Exception as e:
            error_msg = f"{language}: Unexpected error: {e}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            failed_languages.append(f"{error_msg} - {traceback.format_exc()}")
            success = False

    return success, successful_languages, failed_languages


def main():
    """Main entry point for the verification script."""
    print("CodeConCat Tree-sitter Grammar Verification Tool")
    print("================================================\n")

    # Run verification
    success, successful_langs, failed_langs = verify_tree_sitter_dependencies()

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
