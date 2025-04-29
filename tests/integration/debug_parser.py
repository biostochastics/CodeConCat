#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Diagnostic script to debug parser issues in multi-language corpus tests.
"""

import os
import traceback
from codeconcat.base_types import CodeConCatConfig


def read_file_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def debug_c_parser():
    print("\n=== C Parser Diagnostic ===")

    # Find test files
    corpus_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "parser_test_corpus")

    c_dir = os.path.join(corpus_dir, "c")
    if not os.path.exists(c_dir):
        print(f"C test directory not found: {c_dir}")
        return

    c_files = []
    for file in os.listdir(c_dir):
        if os.path.isfile(os.path.join(c_dir, file)):
            c_files.append(os.path.join(c_dir, file))

    if not c_files:
        print("No C files found for testing")
        return

    print(f"Found {len(c_files)} C files: {c_files}")

    # Get first file for testing
    file_path = c_files[0]
    print(f"\nTesting C parser with: {file_path}")

    # Read file
    content = read_file_content(file_path)
    if content is None:
        print("Failed to read file content")
        return

    print(f"File content length: {len(content)}")

    # Test parser
    config = CodeConCatConfig(use_enhanced_parsers=True)

    try:
        # Try with enhanced parser
        from codeconcat.parser.language_parsers.enhanced_c_family_parser import (
            EnhancedCFamilyParser,
        )

        parser = EnhancedCFamilyParser()
        parser.language = "c"

        print("Successfully created enhanced C parser")

        # Try parsing
        print("Attempting to parse file...")
        try:
            result = parser.parse(content, file_path)
            print("Parse successful!")
            print(f"Result type: {type(result)}")
            print(f"Declarations: {len(result.declarations)}")
            print(f"Imports: {len(result.imports)}")

            # Print first few declarations
            if result.declarations:
                print("\nSample declarations:")
                for i, decl in enumerate(result.declarations[:3]):
                    print(f"  {i+1}. {decl.name} (kind: {decl.kind})")
            else:
                print("\nNo declarations found")

        except Exception as e:
            print(f"Parser.parse() failed: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"Error creating parser: {e}")
        traceback.print_exc()


def debug_go_parser():
    print("\n=== Go Parser Diagnostic ===")

    # Find test files
    corpus_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "parser_test_corpus")

    go_dir = os.path.join(corpus_dir, "go")
    if not os.path.exists(go_dir):
        print(f"Go test directory not found: {go_dir}")
        return

    go_files = []
    for file in os.listdir(go_dir):
        if os.path.isfile(os.path.join(go_dir, file)) and file.endswith(".go"):
            go_files.append(os.path.join(go_dir, file))

    if not go_files:
        print("No Go files found for testing")
        return

    print(f"Found {len(go_files)} Go files: {go_files}")

    # Get first file for testing
    file_path = go_files[0]
    print(f"\nTesting Go parser with: {file_path}")

    # Read file
    content = read_file_content(file_path)
    if content is None:
        print("Failed to read file content")
        return

    print(f"File content length: {len(content)}")

    # Test parser
    config = CodeConCatConfig(use_enhanced_parsers=True)

    try:
        # Try with enhanced parser
        from codeconcat.parser.language_parsers.enhanced_go_parser import EnhancedGoParser

        parser = EnhancedGoParser()

        print("Successfully created enhanced Go parser")

        # Try parsing
        print("Attempting to parse file...")
        try:
            result = parser.parse(content, file_path)
            print("Parse successful!")
            print(f"Result type: {type(result)}")
            print(f"Declarations: {len(result.declarations)}")
            print(f"Imports: {len(result.imports)}")

            # Print first few declarations
            if result.declarations:
                print("\nSample declarations:")
                for i, decl in enumerate(result.declarations[:3]):
                    print(f"  {i+1}. {decl.name} (kind: {decl.kind})")
            else:
                print("\nNo declarations found")

        except Exception as e:
            print(f"Parser.parse() failed: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"Error creating parser: {e}")
        traceback.print_exc()


def debug_rust_parser():
    print("\n=== Rust Parser Diagnostic ===")

    # Find test files
    corpus_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "parser_test_corpus")

    rust_dir = os.path.join(corpus_dir, "rust")
    if not os.path.exists(rust_dir):
        print(f"Rust test directory not found: {rust_dir}")
        return

    rust_files = []
    for file in os.listdir(rust_dir):
        if os.path.isfile(os.path.join(rust_dir, file)) and file.endswith(".rs"):
            rust_files.append(os.path.join(rust_dir, file))

    if not rust_files:
        print("No Rust files found for testing")
        return

    print(f"Found {len(rust_files)} Rust files: {rust_files}")

    # Get first file for testing
    file_path = rust_files[0]
    print(f"\nTesting Rust parser with: {file_path}")

    # Read file
    content = read_file_content(file_path)
    if content is None:
        print("Failed to read file content")
        return

    print(f"File content length: {len(content)}")

    # Test parser
    config = CodeConCatConfig(use_enhanced_parsers=True)

    try:
        # Try with enhanced parser
        from codeconcat.parser.language_parsers.enhanced_rust_parser import EnhancedRustParser

        parser = EnhancedRustParser()

        print("Successfully created enhanced Rust parser")

        # Try parsing
        print("Attempting to parse file...")
        try:
            result = parser.parse(content, file_path)
            print("Parse successful!")
            print(f"Result type: {type(result)}")
            print(f"Declarations: {len(result.declarations)}")
            print(f"Imports: {len(result.imports)}")

            # Print first few declarations
            if result.declarations:
                print("\nSample declarations:")
                for i, decl in enumerate(result.declarations[:3]):
                    print(f"  {i+1}. {decl.name} (kind: {decl.kind})")
            else:
                print("\nNo declarations found")

        except Exception as e:
            print(f"Parser.parse() failed: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"Error creating parser: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    print("Running parser diagnostics...")
    debug_c_parser()
    debug_go_parser()
    debug_rust_parser()
    print("\nDiagnostics complete")
