"""
Diagnostic tools for CodeConCat.

This module provides diagnostic utilities for checking dependencies,
debugging parsing issues, and validating the codebase setup.
"""

import importlib
import logging
import traceback
from typing import Any

from codeconcat.parser.language_parsers import TREE_SITTER_PARSER_MAP

logger = logging.getLogger(__name__)


def verify_tree_sitter_dependencies() -> tuple[bool, list[str], list[str]]:
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

            # Import the module and class
            module = importlib.import_module(module_name)
            parser_class = getattr(module, parser_class_name)

            # Try to instantiate the parser (this should load the grammar)
            parser_instance = parser_class()

            # Verify that the parser attribute exists and is initialized
            if hasattr(parser_instance, "parser") and parser_instance.parser:
                logger.info(f"✅ {language}: Successfully loaded tree-sitter grammar")
                successful_languages.append(language)
            else:
                error_msg = (
                    f"{language}: Parser instantiated but parser attribute is None or missing"
                )
                logger.error(f"❌ {error_msg}")
                failed_languages.append(error_msg)
                success = False

        except ImportError as e:
            error_msg = f"{language}: Failed to import parser module: {e}"
            logger.error(f"❌ {error_msg}")
            failed_languages.append(error_msg)
            success = False
        except AttributeError as e:
            error_msg = f"{language}: Failed to find parser class: {e}"
            logger.error(f"❌ {error_msg}")
            failed_languages.append(error_msg)
            success = False
        except Exception as e:
            error_msg = f"{language}: Unexpected error: {e}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            failed_languages.append(f"{error_msg} - {traceback.format_exc()}")
            success = False

    return success, successful_languages, failed_languages


def diagnose_parser(language: str, file_path: str | None = None) -> tuple[bool, dict]:
    """
    Run diagnostic checks on the parser for a specific language.

    Args:
        language: The language to diagnose
        file_path: Optional path to a specific file to parse as a test

    Returns:
        Tuple containing:
        - Success flag (True if diagnostics completed without errors)
        - Dictionary of diagnostic results and information
    """
    from codeconcat.base_types import CodeConCatConfig
    from codeconcat.parser.unified_pipeline import get_language_parser

    results: dict[str, Any] = {
        "language": language,
        "parsers_found": {},
        "parsers_tested": {},
        "test_file": file_path,
        "errors": [],
    }

    # Create a minimal config for testing
    config = CodeConCatConfig.model_validate(
        {
            "target_path": ".",
            "disable_tree": False,
            "use_enhanced_parsers": True,
            "fallback_to_regex": True,
        }
    )

    # Try to load all parser types for this language
    parser_types = ["tree_sitter", "enhanced", "standard"]

    for parser_type in parser_types:
        try:
            parser_instance = get_language_parser(language, config, parser_type=parser_type)
            if parser_instance:
                parser_name = type(parser_instance).__name__
                results["parsers_found"][parser_type] = parser_name

                # If the parser implements the EnhancedParserInterface, check capabilities
                if hasattr(parser_instance, "get_capabilities") and callable(
                    parser_instance.get_capabilities
                ):
                    try:
                        capabilities = parser_instance.get_capabilities()
                        results["parsers_found"][f"{parser_type}_capabilities"] = capabilities
                    except Exception as e:
                        results["errors"].append(
                            f"Error getting capabilities for {parser_name}: {e}"
                        )

                # If a test file is provided, try to parse it
                if file_path:
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()

                        parse_result = parser_instance.parse(content, file_path)

                        # Summarize the parse result
                        results["parsers_tested"][parser_type] = {
                            "success": not parse_result.error,
                            "declarations_count": len(parse_result.declarations),
                            "imports_count": len(parse_result.imports),
                            "error": parse_result.error,
                            "engine_used": parse_result.engine_used,
                        }
                    except Exception as e:
                        results["errors"].append(f"Error parsing test file with {parser_name}: {e}")
                        results["parsers_tested"][parser_type] = {"success": False, "error": str(e)}
            else:
                results["parsers_found"][parser_type] = None
        except Exception as e:
            results["errors"].append(f"Error loading {parser_type} parser for {language}: {e}")
            results["parsers_found"][parser_type] = {"success": False, "error": str(e)}

    return len(results["errors"]) == 0, results
