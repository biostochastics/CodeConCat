#!/usr/bin/env python3

"""
Debug utilities for comparing parsers and generating test files.

This module provides tools for:
1. Comparing basic and enhanced parsers for accuracy and reliability
2. Generating test files for all supported languages
3. Creating visual debug output to help identify parser issues
"""

import logging
import os
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from codeconcat.base_types import CodeConCatConfig, Declaration, ParseResult
from codeconcat.parser.enable_debug import enable_all_parser_debug_logging
from codeconcat.parser.file_parser import get_language_parser

# No need for external utils, we'll use standard file operations

# Enable debug logging for all parsers
enable_all_parser_debug_logging()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Define supported languages with their file extensions
SUPPORTED_LANGUAGES = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "julia": ".jl",
    "java": ".java",
    "c": ".c",
    "cpp": ".cpp",
    "csharp": ".cs",
    "go": ".go",
    "php": ".php",
    "ruby": ".rb",
    "rust": ".rs",
    "r": ".R",
}


@dataclass
class ParserComparisonResult:
    """Data class to store the results of parser comparison."""

    language: str
    file_path: str
    basic_result: Optional[ParseResult] = None
    enhanced_result: Optional[ParseResult] = None
    tree_sitter_result: Optional[ParseResult] = None

    # Metrics
    basic_metrics: Dict[str, Any] = field(default_factory=dict)
    enhanced_metrics: Dict[str, Any] = field(default_factory=dict)
    tree_sitter_metrics: Dict[str, Any] = field(default_factory=dict)

    # Analysis
    declaration_diffs: List[str] = field(default_factory=list)
    import_diffs: List[str] = field(default_factory=list)
    nested_structure_diffs: List[str] = field(default_factory=list)


def compute_declaration_metrics(declarations: List[Declaration]) -> Dict[str, Any]:
    """
    Compute metrics about declarations found by a parser.

    Args:
        declarations: List of Declaration objects

    Returns:
        Dictionary with metrics about declarations
    """

    # Count total declarations including nested ones
    def count_declarations(decl_list):
        total = len(decl_list)
        for decl in decl_list:
            total += count_declarations(decl.children)
        return total

    # Count declarations by type
    def count_by_type(decl_list):
        """Count the number of declarations by type, including nested children.
        Parameters:
            - decl_list (List[Declaration]): A list of declaration objects to count types from.
        Returns:
            - Dict[str, int]: A dictionary where keys are declaration types and values are the counts of those types.
        """
        counts: Dict[str, int] = {}
        for decl in decl_list:
            kind = decl.kind
            counts[kind] = counts.get(kind, 0) + 1

            # Count children by type
            child_counts = count_by_type(decl.children)
            for k, v in child_counts.items():
                counts[k] = counts.get(k, 0) + v

        return counts

    # Measure nesting depth
    def max_nesting_depth(decl_list, current_depth=0):
        """Calculate the maximum nesting depth of a list of declarations.
        Parameters:
            - decl_list (list): A list of declaration elements, each potentially containing nested children.
            - current_depth (int, optional): The current depth of nesting, default is 0.
        Returns:
            - int: The maximum depth of nested declarations in the list."""
        if not decl_list:
            return current_depth

        depths = [current_depth]
        for decl in decl_list:
            depths.append(max_nesting_depth(decl.children, current_depth + 1))

        return max(depths)

    # Collect all declaration full paths (parent.child.grandchild)
    def collect_declaration_paths(decl_list, parent_path=""):
        paths = []
        for decl in decl_list:
            current_path = f"{parent_path}.{decl.name}" if parent_path else decl.name
            paths.append(f"{decl.kind}:{current_path}")
            paths.extend(collect_declaration_paths(decl.children, current_path))
        return paths

    total_count = count_declarations(declarations)
    type_counts = count_by_type(declarations)
    max_depth = max_nesting_depth(declarations)
    decl_paths = collect_declaration_paths(declarations)

    return {
        "total_declarations": total_count,
        "top_level_declarations": len(declarations),
        "declaration_types": type_counts,
        "max_nesting_depth": max_depth,
        "declaration_paths": set(decl_paths),
    }


def compare_parsers_for_file(file_path: str) -> ParserComparisonResult:
    """
    Compare basic, enhanced, and tree-sitter parsers for a given file.

    Args:
        file_path: Path to the file to parse

    Returns:
        ParserComparisonResult with metrics and differences
    """
    # Determine language from file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    language = None

    for lang, ext in SUPPORTED_LANGUAGES.items():
        if (
            isinstance(ext, str)
            and ext == file_ext
            or isinstance(ext, (list, tuple))
            and file_ext in ext
        ):
            language = lang
            break

    if not language:
        logger.warning(f"Could not determine language for file: {file_path}")
        return ParserComparisonResult(language="unknown", file_path=file_path)

    logger.info(f"Comparing parsers for {language} file: {file_path}")

    # Create result object
    result = ParserComparisonResult(language=language, file_path=file_path)

    # Read file content
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return result

    # Create a minimal config for testing with required fields
    config = CodeConCatConfig(
        parser_engine="tree_sitter",
        fallback_to_regex=True,
        use_enhanced_parsers=False,
        use_enhanced_pipeline=False,
        target_path=".",
        source_url=None,
        github_token=None,
        source_ref=None,
        use_gitignore=False,
        use_default_excludes=False,
        include_languages=None,
        enable_semgrep=False,
        semgrep_languages=None,
        install_semgrep=False,
        strict_security=False,
        enable_external_semgrep=False,
        semgrep_ruleset=None,
        xml_processing_instructions=False,
        mask_output_content=False,
        enable_compression=False,
        compression_level="standard",
        compression_placeholder="[Code compressed for brevity]",
        compression_keep_threshold=50,
        analysis_prompt=None,
    )

    # Parse with basic regex parser
    try:
        basic_parser = get_language_parser(language, config)
        if basic_parser:
            result.basic_result = basic_parser.parse(content, file_path)
            result.basic_metrics = compute_declaration_metrics(result.basic_result.declarations)
    except Exception as e:
        logger.error(f"Error with basic parser for {file_path}: {e}")

    # Parse with enhanced regex parser
    try:
        enhanced_parser = get_language_parser(language, config)
        if enhanced_parser:
            result.enhanced_result = enhanced_parser.parse(content, file_path)
            result.enhanced_metrics = compute_declaration_metrics(
                result.enhanced_result.declarations
            )
    except Exception as e:
        logger.error(f"Error with enhanced parser for {file_path}: {e}")

    # Parse with tree-sitter parser
    try:
        tree_sitter_parser = get_language_parser(language, config)
        if tree_sitter_parser:
            result.tree_sitter_result = tree_sitter_parser.parse(content, file_path)
            result.tree_sitter_metrics = compute_declaration_metrics(
                result.tree_sitter_result.declarations
            )
    except Exception as e:
        logger.error(f"Error with tree-sitter parser for {file_path}: {e}")

    # Analyze differences
    result = analyze_parser_differences(result)

    return result


def analyze_parser_differences(result: ParserComparisonResult) -> ParserComparisonResult:
    """
    Analyze differences between parser outputs.

    Args:
        result: ParserComparisonResult to analyze

    Returns:
        Updated ParserComparisonResult with difference analysis
    """
    # Compare declaration counts
    if result.basic_result and result.enhanced_result:
        basic_count = result.basic_metrics["total_declarations"]
        enhanced_count = result.enhanced_metrics["total_declarations"]

        if enhanced_count != basic_count:
            result.declaration_diffs.append(
                f"Declaration count differs: basic={basic_count}, enhanced={enhanced_count}"
            )

        # Compare declaration paths
        basic_paths = result.basic_metrics.get("declaration_paths", set())
        enhanced_paths = result.enhanced_metrics.get("declaration_paths", set())

        missing_in_enhanced = basic_paths - enhanced_paths
        if missing_in_enhanced:
            result.declaration_diffs.append(
                f"Declarations found in basic but missing in enhanced: {missing_in_enhanced}"
            )

        new_in_enhanced = enhanced_paths - basic_paths
        if new_in_enhanced:
            result.declaration_diffs.append(
                f"New declarations found in enhanced: {new_in_enhanced}"
            )

        # Compare nesting
        basic_depth = result.basic_metrics["max_nesting_depth"]
        enhanced_depth = result.enhanced_metrics["max_nesting_depth"]

        if enhanced_depth > basic_depth:
            result.nested_structure_diffs.append(
                f"Enhanced parser found deeper nesting: basic={basic_depth}, enhanced={enhanced_depth}"
            )

    # Compare with tree-sitter if available
    if result.tree_sitter_result and result.enhanced_result:
        # Compare enhanced vs tree-sitter
        enhanced_count = result.enhanced_metrics["total_declarations"]
        ts_count = result.tree_sitter_metrics["total_declarations"]

        if abs(enhanced_count - ts_count) > 2:  # Allow small differences
            result.declaration_diffs.append(
                f"Significant difference between enhanced ({enhanced_count}) and tree-sitter ({ts_count})"
            )

        # Compare declaration paths
        enhanced_paths = result.enhanced_metrics.get("declaration_paths", set())
        ts_paths = result.tree_sitter_metrics.get("declaration_paths", set())

        missing_in_ts = enhanced_paths - ts_paths
        if missing_in_ts:
            result.declaration_diffs.append(
                f"Declarations found in enhanced but missing in tree-sitter: {missing_in_ts}"
            )

        new_in_ts = ts_paths - enhanced_paths
        if new_in_ts:
            result.declaration_diffs.append(f"New declarations found in tree-sitter: {new_in_ts}")

    # Compare imports
    if result.basic_result and result.enhanced_result:
        basic_imports = set(result.basic_result.imports)
        enhanced_imports = set(result.enhanced_result.imports)

        missing_imports = basic_imports - enhanced_imports
        if missing_imports:
            result.import_diffs.append(
                f"Imports found in basic but missing in enhanced: {missing_imports}"
            )

        new_imports = enhanced_imports - basic_imports
        if new_imports:
            result.import_diffs.append(f"New imports found in enhanced: {new_imports}")

    return result


def print_parser_comparison_report(result: ParserComparisonResult):
    """
    Print a detailed report of parser comparison results.

    Args:
        result: ParserComparisonResult to report on
    """
    print(f"\n{'=' * 80}")
    print(f"PARSER COMPARISON REPORT: {result.file_path}")
    print(f"{'=' * 80}")
    print(f"Language: {result.language}")

    # Print metrics for each parser
    parsers = [
        ("Basic Regex", result.basic_result, result.basic_metrics),
        ("Enhanced Regex", result.enhanced_result, result.enhanced_metrics),
        ("Tree-sitter", result.tree_sitter_result, result.tree_sitter_metrics),
    ]

    for name, parse_result, metrics in parsers:
        if parse_result:
            print(f"\n{name} Parser Metrics:")
            print(f"  Total Declarations: {metrics.get('total_declarations', 0)}")
            print(f"  Top-level Declarations: {metrics.get('top_level_declarations', 0)}")
            print(f"  Maximum Nesting Depth: {metrics.get('max_nesting_depth', 0)}")

            if "declaration_types" in metrics:
                print("  Declaration Types:")
                for kind, count in metrics["declaration_types"].items():
                    print(f"    {kind}: {count}")

            print(f"  Imports: {len(parse_result.imports)}")
            if parse_result.error:
                print(f"  ERROR: {parse_result.error}")

    # Print differences
    if result.declaration_diffs:
        print("\nDeclaration Differences:")
        for diff in result.declaration_diffs:
            print(f"  * {diff}")

    if result.import_diffs:
        print("\nImport Differences:")
        for diff in result.import_diffs:
            print(f"  * {diff}")

    if result.nested_structure_diffs:
        print("\nNested Structure Differences:")
        for diff in result.nested_structure_diffs:
            print(f"  * {diff}")

    print(f"\n{'=' * 80}\n")


def create_minimal_test_file(language: str, output_dir: Optional[str] = None) -> str:
    """
    Create a minimal test file with representative features for a given language.

    Args:
        language: Language to create test file for
        output_dir: Directory to write the file to (uses temp dir if None)

    Returns:
        Path to the created test file
    """
    if language not in SUPPORTED_LANGUAGES:
        logger.error(f"Unsupported language: {language}")
        return ""

    # Get file extension for language
    ext = SUPPORTED_LANGUAGES[language]
    if isinstance(ext, (list, tuple)):
        ext = ext[0]

    # Create sample code based on language
    sample_code = ""

    if language == "python":
        sample_code = '''"""
Module level docstring for Python test file.
"""

import os
import sys
from typing import List, Dict, Optional

# Global variable
VERSION = "1.0.0"

class TestClass:
    """Test class with nested method."""

    def __init__(self, name: str):
        """Initialize with name."""
        self.name = name

    def outer_method(self, value: int = 0) -> int:
        """Method containing a nested function."""
        def inner_function(x):
            """Nested function docstring."""
            return x * 2

        return inner_function(value)

def top_level_function(param1: str, param2: int = 0) -> Dict:
    """A top-level function with type hints."""
    result = {"param1": param1, "param2": param2}

    # Nested class in function
    class LocalClass:
        """A class defined inside a function."""
        def local_method(self):
            return "local result"

    return result

# Decorated function
@staticmethod
def decorated_function():
    """Function with a decorator."""
    pass
'''
    elif language == "javascript" or language == "typescript":
        sample_code = """/**
 * Module level comment for JavaScript test file.
 */

import { Component } from 'react';
import * as utils from './utils';

// Global constant
const VERSION = "1.0.0";

/**
 * A test class with nested components
 */
class TestClass {
    /**
     * Constructor for the test class
     */
    constructor(name) {
        this.name = name;
    }

    /**
     * Instance method with a nested function
     */
    outerMethod(value = 0) {
        /**
         * A nested function inside a method
         */
        function innerFunction(x) {
            return x * 2;
        }

        return innerFunction(value);
    }

    /**
     * Static method
     */
    static staticMethod() {
        return "static result";
    }
}

/**
 * Top-level function with a nested function
 */
function topLevelFunction(param1, param2 = 0) {
    /**
     * Nested function inside top-level function
     */
    function nestedFunction() {
        return "nested result";
    }

    return {
        param1,
        param2,
        nested: nestedFunction()
    };
}

// Arrow function
const arrowFunction = () => {
    return "arrow result";
};

// React component (JSX/TSX)
function Component() {
    return (
        <div>
            <h1>Test Component</h1>
        </div>
    );
}
"""
    elif language == "julia":
        sample_code = '''"""
Module level docstring for Julia test file.
"""

module TestModule

using Test
import Base: show

# Global constant
const VERSION = "1.0.0"

"""
A test structure with fields and methods.
"""
struct TestStruct
    name::String
    value::Int
end

"""
Show method for TestStruct.
"""
function show(io::IO, t::TestStruct)
    print(io, "TestStruct($(t.name), $(t.value))")
end

"""
A top-level function with nested function.
"""
function outer_function(param1::String, param2::Int=0)
    """
    Inner function docstring.
    """
    function inner_function(x)
        return x * 2
    end

    return Dict("param1" => param1, "param2" => param2, "result" => inner_function(param2))
end

"""
A macro for testing.
"""
macro test_macro(expr)
    return :(println($expr))
end

# Nested module
module NestedModule
    """
    Function in nested module.
    """
    function nested_function()
        return "nested result"
    end
end

end # module TestModule
'''
    else:
        # Default minimal template for other languages
        sample_code = f"""
// Test file for {language}

// Import statements
import standard_lib;

/**
 * A test class
 */
class TestClass {{
    /**
     * Constructor
     */
    constructor() {{
        // Initialize
    }}

    /**
     * A method
     */
    testMethod() {{
        // Implementation
    }}
}}

/**
 * A global function
 */
function testFunction() {{
    // Function body
}}
"""

    # Determine output path
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="codeconcat_parser_test_")

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"test_{language}{ext}")

    # Write file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(sample_code)
        logger.info(f"Created test file: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error creating test file for {language}: {e}")
        return ""


def create_test_files_for_all_languages(output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Create test files for all supported languages.

    Args:
        output_dir: Directory to write files to (uses temp dir if None)

    Returns:
        Dictionary mapping languages to created file paths
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="codeconcat_parser_tests_")

    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Creating test files in: {output_dir}")

    result = {}
    for language in SUPPORTED_LANGUAGES:
        file_path = create_minimal_test_file(language, output_dir)
        if file_path:
            result[language] = file_path

    return result


def run_parser_comparison(file_path: str):
    """
    Run parser comparison for a specific file and print the report.

    Args:
        file_path: Path to the file to analyze
    """
    result = compare_parsers_for_file(file_path)
    print_parser_comparison_report(result)


def run_parser_comparison_for_all_languages(output_dir: Optional[str] = None):
    """
    Create test files for all languages and run parser comparison on them.

    Args:
        output_dir: Directory to write test files to
    """
    test_files = create_test_files_for_all_languages(output_dir)

    for language, file_path in test_files.items():
        print(f"\nTesting {language}...")
        run_parser_comparison(file_path)


def main():
    """Command-line entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Debug and compare parsers for CodeConCat")
    parser.add_argument("--file", help="Path to a specific file to analyze")
    parser.add_argument("--language", help="Create and test a specific language")
    parser.add_argument("--output-dir", help="Directory to write test files to")
    parser.add_argument("--all", action="store_true", help="Test all supported languages")

    args = parser.parse_args()

    if args.file:
        run_parser_comparison(args.file)
    elif args.language:
        if args.language not in SUPPORTED_LANGUAGES:
            logger.error(f"Unsupported language: {args.language}")
            print(f"Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}")
            return 1

        file_path = create_minimal_test_file(args.language, args.output_dir)
        if file_path:
            run_parser_comparison(file_path)
    elif args.all:
        run_parser_comparison_for_all_languages(args.output_dir)
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
