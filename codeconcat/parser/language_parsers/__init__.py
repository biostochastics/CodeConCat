# file: codeconcat/parser/language_parsers/__init__.py

"""
Language parser module for CodeConcat.

This module contains parsers for various programming languages using three approaches:
1. Tree-sitter (preferred): Language-specific parsers based on the Tree-sitter parsing library
2. Enhanced Regex (fallback): Improved regex-based parsers with shared patterns and better error handling
3. Standard Regex (legacy): Original regex-based parsers (DEPRECATED, will be removed in future versions)

The unified parsing pipeline automatically tries these parsers in order, following a progressive
fallback strategy. Each parser implements the ParserInterface, and enhanced parsers implement
the EnhancedParserInterface with additional capabilities.
"""

# Export the base interfaces
from .base_parser import BaseParser
from .enhanced_base_parser import EnhancedBaseParser
from .pattern_library import (
    C_FAMILY_MODIFIERS,
    ClassPatterns,
    CommentPatterns,
    DocstringPatterns,
    FunctionPatterns,
    ImportPatterns,
    create_pattern_with_modifiers,
)

__all__ = [
    "BaseParser",
    "EnhancedBaseParser",
    "ClassPatterns",
    "FunctionPatterns",
    "ImportPatterns",
    "CommentPatterns",
    "DocstringPatterns",
    "C_FAMILY_MODIFIERS",
    "create_pattern_with_modifiers",
]

# Import mappers - will be used by get_language_parser

# Dictionary mapping languages to their parser class names for regex parsers
REGEX_PARSER_MAP = {
    # DEPRECATED: Standard parsers (will be removed in future versions)
    # These are kept for backward compatibility and as final fallbacks
    # in the progressive parser pipeline
    # in the progressive parser pipeline
    "python": "PythonParser",
    "java": "JavaParser",
    "javascript": "JsTsParser",
    "typescript": "JsTsParser",
    "c": "CppParser",
    "cpp": "CppParser",
    "csharp": "CsharpParser",
    "go": "GoParser",
    "php": "PhpParser",
    "rust": "RustParser",
    "r": "RParser",
    "julia": "JuliaParser",
    "config": "TomlParser",
    "toml": "TomlParser",
    "swift": "SwiftParser",
    # Enhanced parsers (preferred regex-based parsers)
    "python_enhanced": "EnhancedPythonParser",
    "csharp_enhanced": "EnhancedCSharpParser",
    "javascript_enhanced": "EnhancedJSTypeScriptParser",
    "typescript_enhanced": "EnhancedJSTypeScriptParser",
    "julia_enhanced": "EnhancedJuliaParser",
    "go_enhanced": "EnhancedGoParser",
    "rust_enhanced": "EnhancedRustParser",
    "php_enhanced": "EnhancedPHPParser",
    "r_enhanced": "EnhancedRParser",
}

# Check for Tree-sitter availability and conditionally define parser map
try:
    # Use importlib.util to check for availability instead of importing directly
    import importlib.util

    has_tree_sitter = importlib.util.find_spec("tree_sitter") is not None
    has_ts_language_pack = importlib.util.find_spec("tree_sitter_language_pack") is not None

    # Only proceed if both are available
    if has_tree_sitter and has_ts_language_pack:
        # Tree-sitter is available, define the full mapping
        TREE_SITTER_AVAILABLE = True

    # Dictionary mapping languages to their parser class names for tree-sitter parsers
    # NOTE: As of April 2025, the codebase has been updated to use tree-sitter-language-pack
    # for more reliable language loading across different Python versions (including 3.12/3.13)
    # and platforms. This resolves previous compatibility issues with individual grammar packages.
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
        "swift": "TreeSitterSwiftParser",
    }

    import logging

    logger = logging.getLogger(__name__)
    logger.info("Tree-sitter support is available")

except ImportError:
    # Tree-sitter or tree-sitter-language-pack is not available
    TREE_SITTER_AVAILABLE = False
    TREE_SITTER_PARSER_MAP = {}

    import logging

    logger = logging.getLogger(__name__)
    logger.warning(
        "Tree-sitter support is not available. Install with: pip install tree-sitter-language-pack>=0.7.2"
        " - Falling back to regex-based parsers."
    )

# Dictionary mapping language extensions to language names (case-insensitive)
# Use a dictionary comprehension to normalize all extensions to lowercase
LANGUAGE_EXTENSION_MAP = {
    ext.lower(): lang
    for ext, lang in {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".r": "r",
        ".jl": "julia",
        ".rs": "rust",
        ".cpp": "cpp",
        ".cxx": "cpp",
        ".cc": "cpp",
        ".hpp": "cpp",
        ".hxx": "cpp",
        ".h": "c",
        ".c": "c",
        ".cs": "csharp",
        ".java": "java",
        ".go": "go",
        ".php": "php",
        ".swift": "swift",
    }.items()
}
