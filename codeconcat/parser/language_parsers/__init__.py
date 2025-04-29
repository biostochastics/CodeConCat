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
    ClassPatterns,
    CommentPatterns,
    DocstringPatterns,
    FunctionPatterns,
    ImportPatterns,
    C_FAMILY_MODIFIERS,
)

# Import mappers - will be used by get_language_parser

# Dictionary mapping languages to their parser class names for regex parsers
REGEX_PARSER_MAP = {
    # DEPRECATED: Standard parsers (will be removed in future versions)
    # These are kept for backward compatibility and as final fallbacks
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

# Dictionary mapping languages to their parser class names for tree-sitter parsers
# NOTE: As of April 2025, the codebase has been updated to use tree-sitter-language-pack
# for more reliable language loading across different Python versions (including 3.12/3.13)
# and platforms. This resolves previous compatibility issues with individual grammar packages.
#
# If you're experiencing issues loading any language, ensure you have the latest version of
# tree-sitter-language-pack installed: pip install tree-sitter-language-pack>=0.7.2
#
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

# Dictionary mapping language extensions to language names
LANGUAGE_EXTENSION_MAP = {
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
}
